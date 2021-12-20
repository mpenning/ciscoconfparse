from __future__ import absolute_import
from operator import methodcaller, attrgetter
from abc import ABCMeta, abstractmethod
from copy import deepcopy
import inspect
import re
import os

from ciscoconfparse.ccp_util import junos_unsupported, UnsupportedFeatureWarning
from ciscoconfparse.ccp_util import IPv4Obj

from loguru import logger as ccp_logger

r""" ccp_abc.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021      David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2014-2019 David Michael Pennington at Samsung Data Services

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""

##
##-------------  Config Line ABC
##


class BaseCfgLine(object, metaclass=ABCMeta):
    # deprecating py2.foo metaclass syntax in version 1.6.8...
    #__metaclass__ = ABCMeta

    def __init__(self, text="", comment_delimiter="!"):
        """Accept an IOS line number and initialize family relationship
        attributes"""
        self.comment_delimiter = comment_delimiter
        self.text = text
        self.linenum = -1
        self.parent = self
        self.child_indent = 0
        self.is_comment = None
        self.children = list()
        self.oldest_ancestor = False
        self.indent = 0  # Whitespace indentation on the object
        self.confobj = None  # Reference to the list object which owns it
        self.feature = ""  # Major feature description
        self.feature_param1 = ""  # Parameter1 of the feature
        self.feature_param2 = ""  # Parameter2 of the feature (if req'd)

        self.set_comment_bool()

    def __repr__(self):
        if not self.is_child:
            return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)
        else:
            return "<%s # %s '%s' (parent is # %s)>" % (
                self.classname,
                self.linenum,
                self.text,
                self.parent.linenum,
            )

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        ##   I inlined the hash() argument below for speed... whenever I change
        ##   self.__eq__() I *must* change this
        return hash(str(self.linenum) + self.text)

    def __gt__(self, val):
        if self.linenum > val.linenum:
            return True
        return False

    def __eq__(self, val):
        try:
            ##   try / except is much faster than isinstance();
            ##   I added hash_arg() inline below for speed... whenever I change
            ##   self.__hash__() I *must* change this
            return (str(self.linenum) + self.text) == (str(val.linenum) + val.text)
        except:
            return False

    def __lt__(self, val):
        # Ref: http://stackoverflow.com/a/7152796/667301
        if self.linenum < val.linenum:
            return True
        return False

    def set_comment_bool(self):
        delimiters = set(self.comment_delimiter)
        retval = None
        ## Use this instead of a regex... nontrivial speed enhancement
        tmp = self.text.lstrip()
        for delimit_char in delimiters:
            if len(tmp) > 0 and (delimit_char == tmp[len(delimit_char) - 1]):
                retval = True
                break
            else:
                retval = False
        self.is_comment = retval
        return retval

    @property
    def dna(self):
        return self.classname

    @property
    def hash_children(self):
        """Return a unique hash of all children (if the number of children > 0)"""
        if len(self.children) > 0:
            return hash(tuple(self.children))
        else:
            return 0

    @property
    def family_endpoint(self):
        if self.children == []:
            return 0
        else:
            return self.children[-1].linenum

    @property
    def verbose(self):
        if self.has_children:
            return (
                "<%s # %s '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>"
                % (
                    self.classname,
                    self.linenum,
                    self.text,
                    self.child_indent,
                    len(self.children),
                    self.family_endpoint,
                )
            )
        else:
            return "<%s # %s '%s' (no_children / family_endpoint: %s)>" % (
                self.classname,
                self.linenum,
                self.text,
                self.family_endpoint,
            )

    @property
    def all_parents(self):
        retval = set([])
        me = self
        while me.parent != me:
            retval.add(me.parent)
            me = me.parent
        return sorted(retval)

    @property
    def all_children(self):
        retval = set([])
        if self.has_children:
            for child in self.children:
                retval.add(child)
                retval.update(child.all_children)
        return sorted(retval)

    @property
    def classname(self):
        return self.__class__.__name__

    @property
    def has_children(self):
        if len(self.children) > 0:
            return True
        return False

    @property
    def is_config_line(self):
        """Return a boolean for whether this is a config statement; returns False if this object is a blank line, or a comment"""
        if len(self.text.strip()) > 0 and not self.is_comment:
            return True
        return False

    def _list_reassign_linenums(self):
        # Call this when I want to reparse everything
        #     (which is very slow)

        # NOTE - 1.5.30 removed this method (which was only called 
        #     by confobj.delete()) in favor of a simpler approach
        #     in confobj.delete()
        #
        # def _list_reassign_linenums(self):
        #     self.confobj._reassign_linenums()
        raise NotImplementedError()

    @junos_unsupported
    def add_parent(self, parentobj):
        """Add a reference to parentobj, on this object"""
        ## In a perfect world, I would check parentobj's type
        ##     with isinstance(), but I'm not ready to take the perf hit
        self.parent = parentobj
        return True

    @junos_unsupported
    def add_child(self, childobj):
        """Add references to childobj, on this object"""
        ## In a perfect world, I would check childobj's type
        ##     with isinstance(), but I'm not ready to take the perf hit
        ##
        ## Add the child, unless we already know it
        if not (childobj in self.children):
            self.children.append(childobj)
            self.child_indent = childobj.indent
            return True
        else:
            return False

    @junos_unsupported
    def add_uncfgtext(self, unconftext):
        """unconftext is defined during special method calls.  Do not assume it
        is automatically populated."""
        ## remove any preceeding "no "
        conftext = re.sub(r"\s*no\s+", "", unconftext)
        myindent = self.parent.child_indent
        self.uncfgtext = myindent * " " + "no " + conftext

    @junos_unsupported
    def delete(self, recurse=True):
        """Delete this object.  By default, if a parent object is deleted, the child objects are also deleted; this happens because ``recurse`` defaults True.
        """
        if recurse:
            # NOTE - 1.5.30 changed this from iterating over self.children
            #        to self.all_children
            #for child in self.children:
            for child in sorted(self.all_children, reverse=True):
                child.delete()

        ## Consistency check to refuse deletion of the wrong object...
        ##    only delete if the line numbers are consistent
        text = self.text
        linenum = self.linenum
        if self.confobj._list[self.linenum].text == text:
            del self.confobj._list[self.linenum]

            # renumber remaining objects after this deletion...
            #
            # NOTE 1.5.30 removed self._list_reassign_linenums() to speed up
            #     obj.delete() behavior... instead we just iterate through
            #     the list of remaining objects and renumber them
            # 
            #self._list_reassign_linenums()
            for obj in self.confobj._list[self.linenum:]:
                obj.linenum = linenum
                linenum += 1

    @junos_unsupported
    def delete_children_matching(self, linespec):
        """Delete any child :class:`~models_cisco.IOSCfgLine` objects which 
        match ``linespec``.

        Parameters
        ----------
        linespec : str
            A string or python regular expression, which should be matched.  

        Returns
        -------
        list
            A list of :class:`~models_cisco.IOSCfgLine` objects which were deleted.

        Examples
        --------
        This example illustrates how you can use 
        :func:`~ccp_abc.delete_children_matching` to delete any description 
        on an interface.

        .. code-block:: python
           :emphasize-lines: 16

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' description Some lame description',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial1/1',
           ...     ' description Another lame description',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects(r'^interface'):
           ...     obj.delete_children_matching(r'description')
           >>>
           >>> for line in parse.ioscfg:
           ...     print(line)
           ...
           !
           interface Serial1/0
            ip address 1.1.1.1 255.255.255.252
           !
           interface Serial1/1
            ip address 1.1.1.5 255.255.255.252
           !
           >>>
        """
        cobjs = filter(methodcaller("re_search", linespec), self.children)
        retval = [ii.text for ii in cobjs]
        # Delete the children
        map(methodcaller("delete"), cobjs)
        return retval

    def has_child_with(self, linespec):
        return bool(filter(methodcaller("re_search", linespec), self.children))

    @junos_unsupported
    def insert_before(self, insertstr):
        """Usage:
            confobj.insert_before('! insert text before this confobj')"""
        retval = None

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        error =  "FATAL CALL: in %s line %s %s(insertstr='%s')" % (calling_filename, calling_lineno, calling_function, insertstr)
        if isinstance(insertstr, str) is True:
            retval = self.confobj.insert_before(self, insertstr, atomic=False)

        elif isinstance(insertstr, IOSCfgLine) is True:
            retval = self.confobj.insert_before(self, insertstr.text, atomic=False)
        else:
            raise ValueError(error)
        #retval = self.confobj.insert_after(self, insertstr, atomic=False)
        return retval

    @junos_unsupported
    def insert_after(self, insertstr):
        """Usage:
            confobj.insert_after('! insert text after this confobj')"""

        # Fail if insertstr is not the correct object type...
        #   only strings and *CfgLine() are allowed...
        if not getattr(insertstr, "capitalize", False) and not isinstance(insertstr, 'BaseCfgLine'):
            error = "Cannot insert object type - %s" % type(insertstr)
            ccp_logger.error(error)
            raise NotImplementedError(error)

        retval = None

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        error =  "FATAL CALL: in %s line %s %s(insertstr='%s')" % (calling_filename, calling_lineno, calling_function, insertstr)

        if self.confobj.debug >= 1:
            ccp_logger.debug("Inserting '%s' after '%s'" % (insertstr, self))

        if getattr(insertstr, "capitalize", False):
            # Handle insertion of a plain-text line
            retval = self.confobj.insert_after(self, insertstr, atomic=False)

        elif isinstance(insertstr, 'BaseCfgLine'):
            # Handle insertion of a configuration line obj such as IOSCfgLine()
            retval = self.confobj.insert_after(self, insertstr.text, atomic=False)

        else:
            ccp_logger.error(error)
            raise ValueError(error)

        #retval = self.confobj.insert_after(self, insertstr, atomic=False)
        return retval

    @junos_unsupported
    def append_to_family(
        self, insertstr, indent=-1, auto_indent_width=1, auto_indent=False
    ):
        """Append an :class:`~models_cisco.IOSCfgLine` object with ``insertstr``
        as a child at the bottom of the current configuration family.

        Parameters
        ----------
        insertstr : str
            A string which contains the text configuration to be apppended.
        indent : int
            The amount of indentation to use for the child line; by default, the number of left spaces provided with ``insertstr`` are respected.  However, you can manually set the indent level when ``indent``>0.  This option will be ignored, if ``auto_indent`` is True.
        auto_indent_width : int
            Amount of whitespace to automatically indent
        auto_indent : bool
            Automatically indent the child to ``auto_indent_width``

        Returns
        -------
        str
            The text matched by the regular expression group; if there is no match, None is returned.

        Examples
        --------
        This example illustrates how you can use 
        :func:`~ccp_abc.append_to_family` to add a 
        ``carrier-delay`` to each interface.

        .. code-block:: python
           :emphasize-lines: 14

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial1/1',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects(r'^interface'):
           ...     obj.append_to_family(' carrier-delay msec 500')
           ...
           >>> parse.commit()
           >>>
           >>> for line in parse.ioscfg:
           ...     print(line)
           ...
           !
           interface Serial1/0
            ip address 1.1.1.1 255.255.255.252
            carrier-delay msec 500
           !
           interface Serial1/1
            ip address 1.1.1.5 255.255.255.252
            carrier-delay msec 500
           !
           >>>
        """
        ## Build the string to insert with proper indentation...
        if auto_indent:
            insertstr = (" " * (self.indent + auto_indent_width)) + insertstr.lstrip()
        elif indent > 0:
            insertstr = (" " * (self.indent + indent)) + insertstr.lstrip()

        ## BaseCfgLine.append_to_family(), insert a single line after this
        ##  object's children
        try:
            last_child = self.all_children[-1]
            retval = self.confobj.insert_after(last_child, insertstr, atomic=False)
        except IndexError:
            # The object has no children
            retval = self.confobj.insert_after(self, insertstr, atomic=False)

        return retval

    @junos_unsupported
    def replace(self, linespec, replacestr, ignore_rgx=None):
        """Replace all strings matching ``linespec`` with ``replacestr`` in 
        the :class:`~models_cisco.IOSCfgLine` object; however, if the 
        :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``, then 
        the text is *not* replaced.  The ``replace()`` method is simply an 
        alias to the ``re_sub()`` method.

        Parameters
        ----------
        linespec : str
            A string or python regular expression, which should be matched
        replacestr : str
            A string or python regular expression, which should replace the text matched by ``linespec``.
        ignore_rgx : str
            A string or python regular expression; the replacement is skipped if :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``.  ``ignore_rgx`` defaults to None, which means no lines matching ``linespec`` are skipped.

        Returns
        -------
        str
            The new text after replacement

        Examples
        --------
        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.replace` to replace ``Serial1`` with 
        ``Serial0`` in a configuration...

        .. code-block:: python
           :emphasize-lines: 15

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial1/1',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects('Serial'):
           ...     print("OLD {}".format(obj.text))
           ...     obj.replace(r'Serial1', r'Serial0')
           ...     print("  NEW {}".format(obj.text))
           OLD interface Serial1/0
             NEW interface Serial0/0
           OLD interface Serial1/1
             NEW interface Serial0/1
           >>>
        """

        # This is a little slower than calling BaseCfgLine.re_sub directly...
        return self.re_sub(linespec, replacestr, ignore_rgx)

    def re_sub(self, regex, replacergx, ignore_rgx=None):
        """Replace all strings matching ``linespec`` with ``replacestr`` in the :class:`~models_cisco.IOSCfgLine` object; however, if the :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``, then the text is *not* replaced.

        Parameters
        ----------
        regex : str
            A string or python regular expression, which should be matched.
        replacergx : str
            A string or python regular expression, which should replace the text matched by ``regex``.
        ignore_rgx : str
            A string or python regular expression; the replacement is skipped if :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``.  ``ignore_rgx`` defaults to None, which means no lines matching ``regex`` are skipped.
             

        Returns
        -------
        str
            The new text after replacement

        Examples
        --------
        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.re_sub` to replace ``Serial1`` with 
        ``Serial0`` in a configuration...

        .. code-block:: python
           :emphasize-lines: 15

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial1/1',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects('Serial'):
           ...     print("OLD {}".format(obj.text))
           ...     obj.re_sub(r'Serial1', r'Serial0')
           ...     print("  NEW {}".format(obj.text))
           OLD interface Serial1/0
             NEW interface Serial0/0
           OLD interface Serial1/1
             NEW interface Serial0/1
           >>>
        """
        # When replacing objects, check whether they should be deleted, or
        #   whether they are a comment

        if ignore_rgx and re.search(ignore_rgx, self.text):
            return self.text

        retval = re.sub(regex, replacergx, self.text)
        # Delete empty lines
        if retval.strip() == "":
            self.delete()
            return
        self.text = retval
        self.set_comment_bool()
        return retval

    def re_match(self, regex, group=1, default=""):
        r"""Use ``regex`` to search the :class:`~models_cisco.IOSCfgLine` text and return the regular expression group, at the integer index.

        Parameters
        ----------
        regex : str
            A string or python regular expression, which should be matched.  This regular expression should contain parenthesis, which bound a match group.
        group : int
            An integer which specifies the desired regex group to be returned.  ``group`` defaults to 1.
        default : str
            The default value to be returned, if there is no match.  By default an empty string is returned if there is no match.

        Returns
        -------
        str
            The text matched by the regular expression group; if there is no match, ``default`` is returned.

        Examples
        --------
        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine..re_match` to store the mask of the 
        interface which owns "1.1.1.5" in a variable called ``netmask``.

        .. code-block:: python
           :emphasize-lines: 14

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial1/1',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> for obj in parse.find_objects(r'ip\saddress'):
           ...     netmask = obj.re_match(r'1\.1\.1\.5\s(\S+)')
           >>>
           >>> print("The netmask is", netmask)
           The netmask is 255.255.255.252
           >>>
        """
        mm = re.search(regex, self.text)
        if not (mm is None):
            return mm.group(group)
        return default

    def re_search(self, regex, default=""):
        """Use ``regex`` to search this :class:`~models_cisco.IOSCfgLine`'s
        text.

        Parameters
        ----------
        regex : str
            A string or python regular expression, which should be matched.  
        default : str
            A value which is returned if :func:`~ccp_abc.re_search()` doesn't find a match while looking for ``regex``.

        Returns
        -------
        str
            The :class:`~models_cisco.IOSCfgLine` text which matched.  If there is no match, ``default`` is returned.

        """
        ## TODO: use re.escape(regex) on all regex, instead of bare regex
        mm = re.search(regex, self.text)
        if not (mm is None):
            return self.text
        return default

    def re_search_children(self, regex, recurse=False):
        """Use ``regex`` to search the text contained in the children of 
        this :class:`~models_cisco.IOSCfgLine`.

        Parameters
        ----------
        regex : str
            A string or python regular expression, which should be matched.  
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)

        Returns
        -------
        list
            A list of matching :class:`~models_cisco.IOSCfgLine` objects which matched.  If there is no match, an empty :py:func:`list` is returned.

        """
        if recurse is False:
            return [cobj for cobj in self.children if cobj.re_search(regex)]
        else:
            return [cobj for cobj in self.all_children if cobj.re_search(regex)]

    def re_match_typed(
        self, regex, group=1, untyped_default=False, result_type=str, default=""
    ):
        r"""Use ``regex`` to search the :class:`~models_cisco.IOSCfgLine` text 
        and return the contents of the regular expression group, at the 
        integer ``group`` index, cast as ``result_type``; if there is no match, 
        ``default`` is returned.

        Parameters
        ----------
        regex : str
            A string or python regular expression, which should be matched.  This regular expression should contain parenthesis, which bound a match group.
        group : int
            An integer which specifies the desired regex group to be returned.  ``group`` defaults to 1.
        result_type : type
            A type (typically one of: ``str``, ``int``, ``float``, or ``IPv4Obj``).  All returned values are cast as ``result_type``, which defaults to ``str``.
        default : any
            The default value to be returned, if there is no match.
        untyped_default : bool
            Set True if you don't want the default value to be typed

        Returns
        -------
        ``result_type``
            The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``, unless `untyped_default` is True.

        Examples
        --------
        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.re_match_typed` to build an 
        association between an interface name, and its numerical slot value.  
        The name will be cast as :py:func:`str`, and the slot will be cast as 
        :py:func:`int`.

        .. code-block:: python
           :emphasize-lines: 15,16,17,18,19

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial2/0',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>>
           >>> slots = dict()
           >>> for obj in parse.find_objects(r'^interface'):
           ...     name = obj.re_match_typed(regex=r'^interface\s(\S+)',
           ...         default='UNKNOWN')
           ...     slot = obj.re_match_typed(regex=r'Serial(\d+)',
           ...         result_type=int,
           ...         default=-1)
           ...     print("Interface {0} is in slot {1}".format(name, slot))
           ...
           Interface Serial1/0 is in slot 1
           Interface Serial2/0 is in slot 2
           >>>

        """
        mm = re.search(regex, self.text)
        if not (mm is None):
            if not (mm.group(group) is None):
                return result_type(mm.group(group))

        if untyped_default:
            return default
        else:
            return result_type(default)

    def re_match_iter_typed(
        self,
        regex,
        group=1,
        result_type=str,
        default="",
        untyped_default=False,
        recurse=False,
    ):
        r"""Use ``regex`` to search the children of 
        :class:`~models_cisco.IOSCfgLine` text and return the contents of 
        the regular expression group, at the integer ``group`` index, cast as 
        ``result_type``; if there is no match, ``default`` is returned.

        Parameters
        ----------
        regex : str
            A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which bound a match group.
        group : int
            An integer which specifies the desired regex group to be returned.  ``group`` defaults to 1.
        result_type : type
            A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ccp_util.IPv4Obj`).         All returned values are cast as ``result_type``, which defaults to ``str``.
        default : any
            The default value to be returned, if there is no match.
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)
        untyped_default : bool
            Set True if you don't want the default value to be typed

        Returns
        -------
        ``result_type``
            The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``, unless `untyped_default` is True.

        Notes
        -----
        This loops through the children (in order) and returns when the regex hits its first match.

        Examples
        --------
        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.re_match_iter_typed` to build an 
        :func:`~ccp_util.IPv4Obj` address object for each interface.

           >>> import re
           >>> from ciscoconfparse import CiscoConfParse
           >>> from ciscoconfparse.ccp_util import IPv4Obj
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Serial2/0',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> INTF_RE = re.compile(r'interface\s\S+')
           >>> ADDR_RE = re.compile(r'ip\saddress\s(\S+\s+\S+)')
           >>> for obj in parse.find_objects(INTF_RE):
           ...     print("{} {}".format(obj.text, obj.re_match_iter_typed(ADDR_RE, result_type=IPv4Obj)))
           interface Serial1/0 <IPv4Obj 1.1.1.1/30>
           interface Serial2/0 <IPv4Obj 1.1.1.5/30>
           >>>
        """
        ## iterate through children, and return the matching value
        ##  (cast as result_type) from the first child.text that matches regex

        # if (default is True):
        ## Not using self.re_match_iter_typed(default=True), because I want
        ##   to be sure I build the correct API for match=False
        ##
        ## Ref IOSIntfLine.has_dtp for an example of how to code around
        ##   this while I build the API
        #    raise NotImplementedError

        if recurse is False:
            for cobj in self.children:
                mm = re.search(regex, cobj.text)
                if not (mm is None):
                    return result_type(mm.group(group))
            ## Ref Github issue #121
            if untyped_default:
                return default
            else:
                return result_type(default)
        else:
            for cobj in self.all_children:
                mm = re.search(regex, cobj.text)
                if not (mm is None):
                    return result_type(mm.group(group))
            ## Ref Github issue #121
            if untyped_default:
                return default
            else:
                return result_type(default)

    def reset(self):
        # For subclass APIs
        raise NotImplementedError

    def build_reset_string(self):
        # For subclass APIs
        raise NotImplementedError

    @property
    def ioscfg(self):
        """Return a list with this the text of this object, and 
        with all children in the direct line."""
        retval = [self.text]
        retval.extend([ii.text for ii in self.all_children])
        return retval

    @property
    def lineage(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors / children in the direct line.  Cousins or
        aunts / uncles are *not* returned.  Note: all children of this 
        object are returned."""
        retval = self.all_parents
        retval.append(self)
        if self.children:
            retval.extend(self.all_children)
        return sorted(retval)

    @property
    def geneology(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors' objects in the direct line as well as this
        obj.  Cousins or aunts / uncles are *not* returned.  Note: children
        of this object are *not* returned."""
        retval = sorted(self.all_parents)
        retval.append(self)
        return retval

    @property
    def geneology_text(self):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors' .text field for all ancestors in the direct
        line as well as this obj.  Cousins or aunts / uncles are *not*
        returned.  Note: children of this object are *not* returned."""
        retval = [ii.text for ii in self.geneology]
        return retval

    @property
    def is_parent(self):
        return bool(self.has_children)

    @property
    def is_child(self):
        return not bool(self.parent == self)

    @property
    def siblings(self):
        indent = self.indent
        return [obj for obj in self.parent.children if (obj.indent == indent)]

    @classmethod
    def is_object_for(cls, line=""):
        return False
