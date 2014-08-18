from operator import methodcaller, attrgetter
from abc import ABCMeta
import re
import os

""" ciscoconfparse.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2007-2014 David Michael Pennington

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


class BaseCfgLine(object):
    __metaclass__ = ABCMeta

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
        self.indent = 0            # Whitespace indentation on the object
        self.confobj = None        # Reference to the list object which owns it
        self.hash_arg = None

        self.set_comment_bool()

    def __repr__(self):
        if not self.is_child:
            return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)
        else:
            return "<%s # %s '%s' (parent is # %s)>" % (self.classname, 
                self.linenum, self.text, self.parent.linenum)


    def __str__(self):
        return self.__repr__()

    def __eq__(self, val):
        # OLD and slow code:
        #return isinstance(val, BaseCfgLine) and \
        #    (self.hash_arg)==(val.hash_arg)
        try:
            ##   try / except is much faster than isinstance();
            ##   I added hash_arg() inline below for speed... whenever I change
            ##   hash_arg(), I *must* change this
            return (str(self.linenum)+self.text)==(str(val.linenum)+val.text)
        except:
            return False

    def __gt__(self, val):
        if (self.linenum>val.linenum):
            return True
        return False

    def __lt__(self, val):
        # Ref: http://stackoverflow.com/a/7152796/667301
        if (self.linenum<val.linenum):
            return True
        return False

    def __hash__(self):
        return hash(self.hash_arg)

    def hash_arg(self):
        # Just a unique string or each object instance
        return str(self.linenum)+self.text

    def set_comment_bool(self):
        retval = None
        ## Use this instead of a regex... nontrivial speed enhancement
        tmp = self.text.lstrip()
        if len(tmp)>0 and \
            (self.comment_delimiter==tmp[len(self.comment_delimiter)-1]):
            retval = True
        else:
            retval = False
        self.is_comment = retval
        return retval

    @property
    def family_endpoint(self):
        if self.children==[]:
            return 0
        else:
            return self.children[-1].linenum

    @property
    def verbose(self):
        if self.has_children:
            return "<%s # %s '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>" % (self.classname, self.linenum, self.text, self.child_indent, len(self.children), self.family_endpoint) 
        else:
            return "<%s # %s '%s' (no_children / family_endpoint: %s)>" % (self.classname, self.linenum, self.text, self.family_endpoint) 

    @property
    def all_parents(self):
        retval = set([])
        me = self
        while (me.parent!=me):
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
        if len(self.children)>0:
            return True
        return False


    def _list_reassign_linenums(self):
        # Call this when I want to reparse everything
        #     (which is very slow)
        self.confobj._reassign_linenums()

    def add_parent(self, parentobj):
        """Add a reference to parentobj, on this object"""
        ## In a perfect world, I would check parentobj's type
        ##     with isinstance(), but I'm not ready to take the perf hit
        self.parent = parentobj
        return True

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

    def add_uncfgtext(self, unconftext):
        """unconftext is defined during special method calls.  Do not assume it
        is automatically populated."""
        ## remove any preceeding "no "
        conftext = re.sub("\s*no\s+", "", unconftext)
        myindent = self.parent.child_indent
        self.uncfgtext = myindent * " " + "no " + conftext

    def delete(self, recurse=True):
        """Delete this object.  By default, if a parent object is deleted, the child objects are also deleted; this happens because ``recurse`` defaults True.
        """
        if recurse:
            for child in self.children:
                child.delete()
        del self.confobj._list[self.linenum]
        self._list_reassign_linenums()

    def delete_children_matching(self, linespec):
        """Delete any child :class:`~models_cisco.IOSCfgLine` objects which 
        match ``linespec``.

        Parameters
        ----------

        linespec : str, required
             A string or python regular expression, which should be matched.  

        Returns
        -------

        retval : list
            A list of :class:`~models_cisco.IOSCfgLine` objects which were 
            deleted.

        Examples
        --------

        This example illustrates how you can use 
        :func:`~ccp_abc.delete_children_matching` to delete any description 
        on an interface.

        .. code-block:: python
           :emphasize-lines: 15

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
           ...     print line
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
        cobjs = filter(methodcaller('re_search', linespec), self.children)
        retval = map(attrgetter('text'), cobjs)
        # Delete the children
        map(methodcaller('delete'), cobjs)
        return retval

    def has_child_with(self, linespec):
        return bool(filter(methodcaller('re_search', linespec), self.children))

    def insert_before(self, insertstr):
        """insert_before()"""
        ## BaseCfgLine.insert_before(), insert a single line before this object
        local_atomic=False
        retval = self.confobj.insert_before(self, insertstr, atomic=local_atomic)
        return retval

    def insert_after(self, insertstr):
        """insert_after()"""
        ## BaseCfgLine.insert_after(), insert a single line after this object
        local_atomic=False
        retval = self.confobj.insert_after(self, insertstr, atomic=local_atomic)
        return retval

    def append_to_family(self, insertstr):
        """Append an :class:`~models_cisco.IOSCfgLine` object with ``insertstr``
        to the bottom of the current configuration family.

        Parameters
        ----------

        insertstr : str, required
             A string which contains the text configuration to be apppended.
        default : str, optional
             A string which contains the text default value

        Returns
        -------

        retval : str
            The text matched by the regular expression group; if there is no
            match, None is returned.

        Examples
        --------

        This example illustrates how you can use 
        :func:`~ccp_abc.append_to_family` to add a 
        ``carrier-delay`` to each interface.

        .. code-block:: python
           :emphasize-lines: 13

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
           >>>
           >>> for line in parse.ioscfg:
           ...     print line
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
        ## BaseCfgLine.append_to_family(), insert a single line after this 
        ##  object's children
        local_atomic=False
        last_child = self.children[-1]
        retval = self.confobj.insert_after(last_child, insertstr, 
            atomic=local_atomic)
        return retval

    def replace(self, linespec, replacestr, ignore_rgx=None):
        """Replace all strings matching ``linespec`` with ``replacestr`` in 
        the :class:`~models_cisco.IOSCfgLine` object; however, if the 
        :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``, then 
        the text is *not* replaced.  The ``replace()`` method is simply an 
        alias to the ``re_sub()`` method.

        Parameters
        ----------

        linespec : str, required
             A string or python regular expression, which should be matched
        replacestr : str, required
             A string or python regular expression, which should replace the
             text matched by ``linespec``.
        ignore_rgx : str, optional
             A string or python regular expression; the replacement is skipped
             if :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``.
             ``ignore_rgx`` defaults to None, which means no lines matching
             ``linespec`` are skipped.
             

        Returns
        -------

        retval : str
            The new text after replacement

        Examples
        --------

        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.replace` to replace ``Serial1`` with 
        ``Serial0`` in a configuration...

        .. code-block:: python
           :emphasize-lines: 14

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
           ...     print "OLD", obj.text
           ...     obj.replace(r'Serial1', r'Serial0')
           ...     print "  NEW", obj.text
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

        linespec : str, required
             A string or python regular expression, which should be matched
        replacestr : str, required
             A string or python regular expression, which should replace the
             text matched by ``linespec``.
        ignore_rgx : str, optional
             A string or python regular expression; the replacement is skipped
             if :class:`~models_cisco.IOSCfgLine` text matches ``ignore_rgx``.
             ``ignore_rgx`` defaults to None, which means no lines matching
             ``linespec`` are skipped.
             

        Returns
        -------

        retval : str
            The new text after replacement

        Examples
        --------

        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.re_sub` to replace ``Serial1`` with 
        ``Serial0`` in a configuration...

        .. code-block:: python
           :emphasize-lines: 14

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
           ...     print "OLD", obj.text
           ...     obj.re_sub(r'Serial1', r'Serial0')
           ...     print "  NEW", obj.text
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
        if retval.strip()=='':
            self.delete()
            return
        self.text = retval
        self.set_comment_bool()
        return retval

    def re_match(self, regex, group=1, default=""):
        """Use ``regex`` to search the :class:`~models_cisco.IOSCfgLine` text and return the regular expression group, at the integer index.

        Parameters
        ----------

        regex : str, required
             A string or python regular expression, which should be matched.  
             This regular expression should contain parenthesis, which bound a 
             match group.
        group : int, optional
             An integer which specifies the desired group to be returned.
             ``group`` defaults to 1.
        default : optional
             The default value to be returned, if there is no match.  By default
             an empty string is returned if there is no match.

        Returns
        -------

        retval : str
            The text matched by the regular expression group; if there is no
            match, ``default`` is returned.

        Examples
        --------

        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine..re_match` to store the mask of the 
        interface which owns "1.1.1.5" in a variable called ``netmask``.

        .. code-block:: python
           :emphasize-lines: 13

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
           >>> print "The netmask is", netmask
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

        regex : str, required
             A string or python regular expression, which should be matched.  
        default : optional
             A value which is returned if :func:`~ccp_abc.re_search()` doesn't 
             find a match while looking for ``regex``.

        Returns
        -------

        retval : str
            The :class:`~models_cisco.IOSCfgLine` text which matched.  If 
            there is no match, ``default`` is returned.
        """
        ## TODO: use re.escape(regex) on all regex, instead of bare regex
        mm = re.search(regex, self.text)
        if not (mm is None):
            return self.text
        return default

    def re_search_children(self, regex):
        """Use ``regex`` to search the text contained in the children of 
        this :class:`~models_cisco.IOSCfgLine`.

        Parameters
        ----------

        regex : str, required
             A string or python regular expression, which should be matched.  

        Returns
        -------

        retval : list
            A list of matching :class:`~models_cisco.IOSCfgLine` objects which 
            matched.  If there is no match, an empty :py:func:`list` is 
            returned.
        """
        retval = list()
        for cobj in self.children:
            if cobj.re_search(regex):
                retval.append(cobj)
        return retval

    def re_match_typed(self, regex, group=1, result_type=str, default=''):
        """Use ``regex`` to search the :class:`~models_cisco.IOSCfgLine` text 
        and return the contents of the regular expression group, at the 
        integer index, cast as ``result_type``; if there is no match, 
        ``default`` is returned.

        Parameters
        ----------

        regex : str, required
             A string or python regular expression, which should be matched.  
             This regular expression should contain parenthesis, which bound a 
             match group.
        group : int, optional
             An integer which specifies the desired group to be returned.
             ``group`` defaults to 1.
        result_type : type, optional
             A python type (typically one of: ``str``, ``int``, or ``float``).               All returned values are cast as ``result_type``, which defaults 
             to ``str``.
        default : optional
             The default value to be returned, if there is no match.

        Returns
        -------

        retval : ``result_type``
            The text matched by the regular expression group; if there is no
            match, ``default`` is returned.  All values are cast as 
            ``result_type``.

        Examples
        --------

        This example illustrates how you can use 
        :func:`~models_cisco.IOSCfgLine.re_match_typed` to build an 
        association between an interface name, and its numerical slot value.  
        The name will be cast as :py:func:`str`, and the slot will be cast as 
        :py:func:`int`.

        .. code-block:: python
           :emphasize-lines: 14,15,16,17,18

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
           ...     print "Interface {0} is in slot {1}".format(name, slot)
           ...
           Interface Serial1/0 is in slot 1
           Interface Serial2/0 is in slot 2
           >>>
        """
        mm = re.search(regex, self.text)
        if not (mm is None):
            return result_type(mm.group(group)) or result_type(default)
        return result_type(default)

    def re_match_iter_typed(self, regex, group=1, result_type=str, default=''):
        ## iterate through children, and return the matching value 
        ##  (cast as result_type) from the first child.text that matches regex

        if isinstance(default, bool) and (default is True):
            ## Not using self.re_match_iter_typed(default=True), because I want
            ##   to be sure I build the correct API for match=False
            ##
            ## Ref IOSIntfLine.has_dtp for an example of how to code around
            ##   this while I build the API
            raise NotImplementedError

        for cobj in self.children:
            mm = re.search(regex, cobj.text)
            if not (mm is None):
                return result_type(mm.group(group))
        return result_type(default)

    def reset(self):
        # For subclass APIs
        raise NotImplementedError

    def build_reset_string(self):
        # For subclass APIs
        raise NotImplementedError

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
    def is_parent(self):
        return bool(self.has_children)

    @property
    def is_child(self):
        return not bool(self.parent==self)

    @property
    def siblings(self):
        indent = self.indent
        return [obj for obj in self.parent.children if (obj.indent==indent)]

    @classmethod
    def is_object_for(cls, line=""):
        return False

