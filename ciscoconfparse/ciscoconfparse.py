from operator import methodcaller, attrgetter
from collections import MutableSequence, Iterator
import time
import re
import os

from models_cisco import IOSHostnameLine, IOSRouteLine, IOSIntfLine
from models_cisco import IOSAccessLine, IOSIntfGlobal
from models_cisco import IOSAaaLoginAuthenticationLine
from models_cisco import IOSAaaEnableAuthenticationLine
from models_cisco import IOSAaaCommandsAuthorizationLine
from models_cisco import IOSAaaCommandsAccountingLine
from models_cisco import IOSAaaExecAccountingLine
from models_cisco import IOSAaaGroupServerLine
from models_cisco import IOSCfgLine

from models_asa import ASAObjGroupNetwork
from models_asa import ASAObjGroupService
from models_asa import ASAHostnameLine
from models_asa import ASAObjNetwork
from models_asa import ASAObjService
from models_asa import ASAIntfGlobal
from models_asa import ASAIntfLine
from models_asa import ASACfgLine
from models_asa import ASAName

from models_junos import JunosCfgLine


""" ciscoconfparse.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2007-2015 David Michael Pennington

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

## Docstring props: http://stackoverflow.com/a/1523456/667301
__version_tuple__ = (1, 2, 10)
__version__ = '.'.join(map(str, __version_tuple__))
__email__ = "mike /at\ pennington [dot] net"
__author__ = "David Michael Pennington <{0}>".format(__email__)
__copyright__ = "2007-{0}, {1}".format(time.strftime('%Y'), __author__)
__license__ = "GPL"
__status__ = "Production"

class CiscoConfParse(object):
    """Parses Cisco IOS configurations and answers queries about the configs"""

    def __init__(self, config="", comment="!", debug=False, factory=False, 
        linesplit_rgx=r"\r*\n+", ignore_blank_lines=True, syntax='ios'):
        """Initialize CiscoConfParse.

           Kwargs:
               - config (list or str): A list of configuration statements, or a configuration file path to be parsed
               - comment (str): A comment delimiter.  This should only be changed when parsing non-Cisco IOS configurations, which do not use a !  as the comment delimiter.  ``comment`` defaults to '!'
               - debug (bool): ``debug`` defaults to False, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug output is not particularly friendly
               - factory (bool): ``factory`` defaults to False; if set ``True``, it enables a beta-quality configuration line classifier.
               - linesplit_rgx (str): ``linesplit_rgx`` is used when parsing configuration files to find where new configuration lines are.  It is best to leave this as the default, unless you're working on a system that uses unusual line terminations (for instance something besides Unix, OSX, or Windows)
               - ignore_blank_lines (bool): ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration (ref: Github Issue #2), or you are parsing configurations which naturally have blank lines (such as Cisco Nexus configurations).
               - syntax (str): ``syntax`` defaults to 'ios'; You can choose from the following values: ios, asa

           Attributes:
               - comment_delimiter (str): A string containing the comment-delimiter
               - ConfigObjs (:class:`~ciscoconfparse.IOSConfigList`) : A custom list, which contains all parsed :class:`~models_cisco.IOSCfgLine` instances.
               - all_parents (list) : A list of all parent :class:`~models_cisco.IOSCfgLine` instances.
               - last_index (int) : An integer with the last index in ``ConfigObjs``
           Returns:
               - An instance of a :class:`~ciscoconfparse.CiscoConfParse` object


           This example illustrates how to parse a simple Cisco IOS configuration
           with :class:`~ciscoconfparse.CiscoConfParse` into a variable called 
           ``parse``.  This example also illustrates what the ``ConfigObjs`` 
           and ``ioscfg`` attributes contain.

           .. code-block:: python
              :emphasize-lines: 5

              >>> config = [
              ...     'logging trap debugging',
              ...     'logging 172.28.26.15',
              ...     ] 
              >>> parse = CiscoConfParse(config)
              >>> parse
              <CiscoConfParse: 2 lines / syntax: ios / comment delimiter: '!' / factory: False>
              >>> parse.ConfigObjs
              <IOSConfigList, comment='!', conf=[<IOSCfgLine # 0 'logging trap debugging'>, <IOSCfgLine # 1 'logging 172.28.26.15'>]>
              >>> parse.ioscfg
              ['logging trap debugging', 'logging 172.28.26.15']
              >>>

        """

        # all IOSCfgLine object instances...
        self.comment_delimiter = comment
        self.factory = factory
        self.ConfigObjs = None
        self.syntax = syntax

        if isinstance(config, list) or isinstance(config, Iterator):
            if syntax=='ios':
                # we already have a list object, simply call the parser
                self.ConfigObjs = IOSConfigList(data=config, 
                    comment_delimiter=comment, 
                    debug=debug, 
                    factory=factory, 
                    ignore_blank_lines=ignore_blank_lines,
                    syntax='ios',
                    CiscoConfParse=self)
            elif syntax=='asa':
                # we already have a list object, simply call the parser
                self.ConfigObjs = ASAConfigList(data=config, 
                    comment_delimiter=comment, 
                    debug=debug, 
                    factory=factory, 
                    ignore_blank_lines=ignore_blank_lines,
                    syntax='asa',
                    CiscoConfParse=self)
            elif syntax=='junos':
                ## FIXME I am shamelessly abusing the IOSConfigList for now...
                # we already have a list object, simply call the parser
                config = self.convert_braces_to_ios(config)
                self.ConfigObjs = IOSConfigList(data=config, 
                    comment_delimiter=comment, 
                    debug=debug, 
                    factory=factory, 
                    ignore_blank_lines=ignore_blank_lines,
                    syntax='junos',
                    CiscoConfParse=self)
            else:
                raise ValueError("FATAL: '{}' is an unknown syntax".format(syntax))

        elif isinstance(config, str):
            # Try opening as a file
            try:
                if syntax=='ios':
                    # string - assume a filename... open file, split and parse
                    f = open(config, mode="rU")
                    text = f.read()
                    rgx = re.compile(linesplit_rgx)
                    self.ConfigObjs = IOSConfigList(rgx.split(text), 
                        comment_delimiter=comment, 
                        debug=debug,
                        factory=factory,
                        ignore_blank_lines=ignore_blank_lines,
                        syntax='ios',
                        CiscoConfParse=self)
                elif syntax=='asa':
                    # string - assume a filename... open file, split and parse
                    f = open(config, mode="rU")
                    text = f.read()
                    rgx = re.compile(linesplit_rgx)
                    self.ConfigObjs = ASAConfigList(rgx.split(text), 
                        comment_delimiter=comment, 
                        debug=debug,
                        factory=factory,
                        ignore_blank_lines=ignore_blank_lines,
                        syntax='asa',
                        CiscoConfParse=self)

                elif syntax=='junos':
                    # string - assume a filename... open file, split and parse
                    f = open(config, mode="rU")
                    text = f.read()
                    rgx = re.compile(linesplit_rgx)

                    config = self.convert_braces_to_ios(rgx.split(text))
                    ## FIXME I am shamelessly abusing the IOSConfigList for now...
                    self.ConfigObjs = IOSConfigList(config,
                        comment_delimiter=comment, 
                        debug=debug,
                        factory=factory,
                        ignore_blank_lines=ignore_blank_lines,
                        syntax='junos',
                        CiscoConfParse=self)
                else:
                    raise ValueError("FATAL: '{}' is an unknown syntax".format(syntax))

            except IOError:
                print("[FATAL] CiscoConfParse could not open '%s'" % config)
                raise RuntimeError
        else:
            raise RuntimeError("[FATAL] CiscoConfParse() received" + 
                " an invalid argument\n")
        self.ConfigObjs.CiscoConfParse = self

    def __repr__(self):
        return "<CiscoConfParse: %s lines / syntax: %s / comment delimiter: '%s' / factory: %s>" % (len(self.ConfigObjs), self.syntax, self.comment_delimiter, self.factory)


    @property
    def ioscfg(self):
        """A list containing all text configuration statements"""
        ## I keep this here to emulate the legacy ciscoconfparse behavior
        return list(map(attrgetter('text'), self.ConfigObjs))

    @property
    def objs(self):
        """An alias to the ``ConfigObjs`` attribute"""
        return self.ConfigObjs

    def atomic(self):
        """Call :func:`~ciscoconfparse.CiscoConfParse.atomic` to manually fix 
        up ``ConfigObjs`` relationships 
        after modifying a parsed configuration.  This method is slow; try to 
        batch calls to :func:`~ciscoconfparse.CiscoConfParse.atomic()` if 
        possible.

        .. warning::

           If you modify a configuration after parsing it with 
           :class:`~ciscoconfparse.CiscoConfParse`, you *must* call 
           :func:`~ciscoconfparse.CiscoConfParse.commit` or 
           :func:`~ciscoconfparse.CiscoConfParse.atomic` before searching 
           the configuration again with methods such as 
           :func:`~ciscoconfparse.CiscoConfParse.find_objects` or 
           :func:`~ciscoconfparse.CiscoConfParse.find_lines`.  Failure to 
           call :func:`~ciscoconfparse.CiscoConfParse.commit` or 
           :func:`~ciscoconfparse.CiscoConfParse.atomic` on config 
           modifications could lead to unexpected search results.
        """
        self.ConfigObjs._bootstrap_from_text()

    def commit(self):
        """Alias for calling the :func:`~ciscoconfparse.CiscoConfParse.atomic` 
        method.  This method is slow; try to batch calls to 
        :func:`~ciscoconfparse.CiscoConfParse.commit()` if possible.

        .. warning::

           If you modify a configuration after parsing it with 
           :class:`~ciscoconfparse.CiscoConfParse`, you *must* call 
           :func:`~ciscoconfparse.CiscoConfParse.commit` or 
           :func:`~ciscoconfparse.CiscoConfParse.atomic` before searching 
           the configuration again with methods such as 
           :func:`~ciscoconfparse.CiscoConfParse.find_objects` or 
           :func:`~ciscoconfparse.CiscoConfParse.find_lines`.  Failure to 
           call :func:`~ciscoconfparse.CiscoConfParse.commit` or 
           :func:`~ciscoconfparse.CiscoConfParse.atomic` on config 
           modifications could lead to unexpected search results.
        """
        self.atomic()

    def convert_braces_to_ios(self, input_list, stop_width=4):
        ## Note to self, I made this regex fairly junos-specific...
        LINE_RE = re.compile(r'^\s*([^\{\}].*)*\s*([\{\}\;])(\s\#.+)*$')

        def line_level(input):
            level_offset = 0
            mm = LINE_RE.search(input)
            if not (mm is None):
                line = mm.group(1) or ''
                term_char = mm.group(2).strip()
                if term_char=='{':
                    level_offset = 1
                elif term_char=='}':
                    level_offset = -1
                return line, level_offset
            elif input.strip()=='':
                ## pass blank lines back
                return input, 0
            else:
                raise ValueError("Could not parse: '{0}'".format(input))

        lines = list()
        offset = 0
        STOP_WIDTH = stop_width
        for tmp in input_list:
            line, line_offset = line_level(tmp.strip())
            if line:
                lines.append(" "*STOP_WIDTH*offset+line)
            offset += line_offset
        return lines


    

    def find_objects(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text 
        matches ``linespec`` and return the :class:`~models_cisco.IOSCfgLine` 
        objects in a python list.  
        :func:`~ciscoconfparse.CiscoConfParse.find_objects` is similar to 
        :func:`~ciscoconfparse.CiscoConfParse.find_lines`; however, the former 
        returns a list of :class:`~models_cisco.IOSCfgLine` objects, while the 
        latter returns a list of text configuration statements.  Going 
        forward, I strongly encourage people to start using 
        :func:`~ciscoconfparse.CiscoConfParse.find_objects` instead of 
        :func:`~ciscoconfparse.CiscoConfParse.find_lines`.

        Args:
            - linespec (str): A string or python regular expression, which should be matched
        Kwargs:
            - exactmatch (bool): Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.
            - ignore_ws (bool): boolean that controls whether whitespace is ignored.  Default is False.

        Returns:
            - list.  A list of matching :class:`~ciscoconfparse.IOSCfgLine` objects

        This example illustrates the difference between 
        :func:`~ciscoconfparse.CiscoConfParse.find_objects` and 
        :func:`~ciscoconfparse.CiscoConfParse.find_lines`.

        .. code-block:: python
           :emphasize-lines: 12,15

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
           >>> parse.find_objects(r'^interface')
           [<IOSCfgLine # 1 'interface Serial1/0'>, <IOSCfgLine # 4 'interface Serial1/1'>]
           >>>
           >>> parse.find_lines(r'^interface')
           ['interface Serial1/0', 'interface Serial1/1']
           >>>

        """
        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)
        return self._find_line_OBJ(linespec, exactmatch)

    def find_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """This method is the equivalent of a simple configuration grep
        (Case-sensitive).

        Args:
            - linespec (str): Text regular expression for the line to be matched

        Kwargs:
            - exactmatch (bool): Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.
            - ignore_ws (bool): boolean that controls whether whitespace is ignored.  Default is False.

        Returns:
            - list.  A list of matching configuration lines
        """
        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)

        if (exactmatch is False):
            # Return the lines in self.ioscfg, which match linespec
            return list(filter(re.compile(linespec).search, self.ioscfg))
        else:
            # Return the lines in self.ioscfg, which match (exactly) linespec
            return list(filter(re.compile("^%s$" % linespec).search, self.ioscfg))

    def find_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and their immediate
        children.  This method is different than :meth:`find_all_children`,
        because :meth:`find_all_children` finds children of children.
        :meth:`find_children` only finds immediate children.

        Args:
            - linespec (str): Text regular expression for the line to be matched
        Kwargs:
            - exactmatch (bool): boolean that controls whether partial matches are valid
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching configuration lines

        Suppose you are interested in finding all immediate children of the 
        `archive` statements in the following configuration...

        .. code::

           username ddclient password 7 107D3D232342041E3A
           archive
            log config
             logging enable
             hidekeys
            path ftp://ns.foo.com//tftpboot/Foo-archive
           !

        Using the config above, we expect to find the following config lines...

        .. code::

           archive
            log config
            path ftp://ns.foo.com//tftpboot/Foo-archive

        We would accomplish this by querying `find_children('^archive')`...

        .. code-block:: python
           :emphasize-lines: 11

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['username ddclient password 7 107D3D232342041E3A',
           ...           'archive',
           ...           ' log config',
           ...           '  logging enable',
           ...           '  hidekeys',
           ...           ' path ftp://ns.foo.com//tftpboot/Foo-archive',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_children('^archive')
           ['archive', ' log config', ' path ftp://ns.foo.com//tftpboot/Foo-archive']
           >>>
        """
        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)

        if (exactmatch is False):
            parentobjs = self._find_line_OBJ(linespec)
        else:
            parentobjs = self._find_line_OBJ("^%s$" % linespec)

        allobjs = set([])
        for parent in parentobjs:
            if (parent.has_children is True):
                allobjs.update(set(parent.children))
            allobjs.add(parent)

        return list(map(attrgetter('text'), sorted(allobjs)))

    def find_all_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and all their children.  
        This method is different than :meth:`find_children`, because
        :meth:`find_all_children` finds children of children.
        :meth:`find_children` only finds immediate children.
     
        Args:
            - linespec (str): Text regular expression for the line to be matched
        Kwargs:
            - exactmatch (bool): boolean that controls whether partial matches are valid
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching configuration lines

        Suppose you are interested in finding all `archive` statements in
        the following configuration...

        .. code::

           username ddclient password 7 107D3D232342041E3A
           archive
            log config
             logging enable
             hidekeys
            path ftp://ns.foo.com//tftpboot/Foo-archive
           !

        Using the config above, we expect to find the following config lines...

        .. code::

           archive
            log config
             logging enable
             hidekeys
            path ftp://ns.foo.com//tftpboot/Foo-archive

        We would accomplish this by querying `find_all_children('^archive')`...

        .. code-block:: python
           :emphasize-lines: 11

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['username ddclient password 7 107D3D232342041E3A',
           ...           'archive',
           ...           ' log config',
           ...           '  logging enable',
           ...           '  hidekeys',
           ...           ' path ftp://ns.foo.com//tftpboot/Foo-archive',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_all_children('^archive')
           ['archive', ' log config', '  logging enable', '  hidekeys', ' path ftp://ns.foo.com//tftpboot/Foo-archive']
           >>>
        """

        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)

        if (exactmatch is False):
            parentobjs = self._find_line_OBJ(linespec)
        else:
            parentobjs = self._find_line_OBJ("^%s$" % linespec)

        allobjs = set([])
        for parent in parentobjs:
            allobjs.add(parent)
            allobjs.update(set(parent.all_children))
        return list(map(attrgetter('text'), sorted(allobjs)))

    def find_blocks(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all siblings matching the linespec, then find all parents of
        those siblings. Return a list of config lines sorted by line number,
        lowest first.  Note: any children of the siblings should NOT be
        returned.

        Args:
            - linespec (str): Text regular expression for the line to be matched
        Kwargs:
            - exactmatch (bool): boolean that controls whether partial matches are valid
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching configuration lines


        This example finds `bandwidth percent` statements in following config, 
        the siblings of those `bandwidth percent` statements, as well
        as the parent configuration statements required to access them.

        .. code::

           !
           policy-map EXTERNAL_CBWFQ
            class IP_PREC_HIGH
             priority percent 10
             police cir percent 10
               conform-action transmit
               exceed-action drop
            class IP_PREC_MEDIUM
             bandwidth percent 50
             queue-limit 100
            class class-default
             bandwidth percent 40
             queue-limit 100
           policy-map SHAPE_HEIR
            class ALL
             shape average 630000
             service-policy EXTERNAL_CBWFQ
           !

        The following config lines should be returned:

        .. code::

           policy-map EXTERNAL_CBWFQ
            class IP_PREC_MEDIUM
             bandwidth percent 50
             queue-limit 100
            class class-default
             bandwidth percent 40
             queue-limit 100

        We do this by quering `find_blocks('bandwidth percent')`...

        .. code-block:: python
           :emphasize-lines: 22,25

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!', 
           ...           'policy-map EXTERNAL_CBWFQ', 
           ...           ' class IP_PREC_HIGH', 
           ...           '  priority percent 10', 
           ...           '  police cir percent 10', 
           ...           '    conform-action transmit', 
           ...           '    exceed-action drop', 
           ...           ' class IP_PREC_MEDIUM', 
           ...           '  bandwidth percent 50', 
           ...           '  queue-limit 100', 
           ...           ' class class-default', 
           ...           '  bandwidth percent 40', 
           ...           '  queue-limit 100', 
           ...           'policy-map SHAPE_HEIR', 
           ...           ' class ALL', 
           ...           '  shape average 630000', 
           ...           '  service-policy EXTERNAL_CBWFQ', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_blocks('bandwidth percent')
           ['policy-map EXTERNAL_CBWFQ', ' class IP_PREC_MEDIUM', '  bandwidth percent 50', '  queue-limit 100', ' class class-default', '  bandwidth percent 40', '  queue-limit 100']
           >>>
           >>> p.find_blocks(' class class-default')
           ['policy-map EXTERNAL_CBWFQ', ' class IP_PREC_HIGH', ' class IP_PREC_MEDIUM', ' class class-default']
           >>>

        """
        tmp = set([])

        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)

        # Find line objects maching the spec
        if (exactmatch is False):
            objs = self._find_line_OBJ(linespec)
        else:
            objs = self._find_line_OBJ("^%s$" % linespec)

        for obj in objs:
            tmp.add(obj)
            # Find the siblings of this line
            sib_objs = self._find_sibling_OBJ(obj)
            for sib_obj in sib_objs:
                tmp.add(sib_obj)

        # Find the parents for everything
        pobjs = set([])
        for lineobject in tmp:
            for pobj in lineobject.all_parents:
                pobjs.add(pobj)
        tmp.update(pobjs)

        return list(map(attrgetter('text'), sorted(tmp)))

    def find_objects_w_child(self, parentspec, childspec, ignore_ws=False):
        """Return a list of parent :class:`~models_cisco.IOSCfgLine` objects, 
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be 
        returned.

        Args:
            - parentspec (str): Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line
        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching parent :class:`~models_cisco.IOSCfgLine` objects

        This example uses :func:`~ciscoconfparse.find_objects_w_child()` to 
        find all ports that are members of access vlan 300 in following 
        config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/2
           interface FastEthernet0/3

        We do this by quering `find_objects_w_child()`; we set our 
        parent as `^interface` and set the child as `switchport access 
        vlan 300`.

        .. code-block:: python
           :emphasize-lines: 18

           >>> config = ['!', 
           ...           'interface FastEthernet0/1', 
           ...           ' switchport access vlan 532', 
           ...           ' spanning-tree vlan 532 cost 3', 
           ...           '!', 
           ...           'interface FastEthernet0/2', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!', 
           ...           'interface FastEthernet0/3', 
           ...           ' duplex full', 
           ...           ' speed 100', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_objects_w_child('^interface', 
           ...     'switchport access vlan 300')
           ...
           [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
           >>>
        """

        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        return list(filter(lambda x: x.re_search_children(childspec), 
            self.find_objects(parentspec)))

    def find_parents_w_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all children matching childspec, and return a list of
        parents that matched the parentspec.  Only the parent lines will be
        returned.

        Args:
            - parentspec (str): Text regular expression for the line to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line
        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching parent configuration lines

        This example finds all ports that are members of access vlan 300 
        in following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/2
           interface FastEthernet0/3

        We do this by quering `find_parents_w_child()`; we set our 
        parent as `^interface` and set the child as 
        `switchport access vlan 300`.

        .. code-block:: python
           :emphasize-lines: 18

           >>> config = ['!', 
           ...           'interface FastEthernet0/1', 
           ...           ' switchport access vlan 532', 
           ...           ' spanning-tree vlan 532 cost 3', 
           ...           '!', 
           ...           'interface FastEthernet0/2', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!', 
           ...           'interface FastEthernet0/3', 
           ...           ' duplex full', 
           ...           ' speed 100', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_parents_w_child('^interface', 'switchport access vlan 300')
           ['interface FastEthernet0/2', 'interface FastEthernet0/3']
           >>>

        """
        tmp = self.find_objects_w_child(parentspec, childspec, 
            ignore_ws=ignore_ws)
        return list(map(attrgetter('text'), tmp))

    def find_objects_wo_child(self, parentspec, childspec, ignore_ws=False):
        """Return a list of parent :class:`~models_cisco.IOSCfgLine` objects, which matched the ``parentspec`` and whose children did not match ``childspec``.  Only the parent :class:`~models_cisco.IOSCfgLine` objects will be returned.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

        Args:
            - parentspec (str): Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line
        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching parent configuration lines

        This example finds all ports that are autonegotiating in the following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/1
           interface FastEthernet0/2

        We do this by quering `find_objects_wo_child()`; we set our 
        parent as `^interface` and set the child as `speed\s\d+` (a 
        regular-expression which matches the word 'speed' followed by
        an integer).

        .. code-block:: python
           :emphasize-lines: 18

           >>> config = ['!', 
           ...           'interface FastEthernet0/1', 
           ...           ' switchport access vlan 532', 
           ...           ' spanning-tree vlan 532 cost 3', 
           ...           '!', 
           ...           'interface FastEthernet0/2', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!', 
           ...           'interface FastEthernet0/3', 
           ...           ' duplex full', 
           ...           ' speed 100', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_objects_wo_child(r'^interface', r'speed\s\d+')
           [<IOSCfgLine # 1 'interface FastEthernet0/1'>, <IOSCfgLine # 5 'interface FastEthernet0/2'>]
           >>>
        """

        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        return [obj for obj in self.find_objects(parentspec) 
            if not obj.re_search_children(childspec)]

    def find_parents_wo_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all parents matching parentspec, and return a list of parents that did NOT have children match the childspec.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

        Args:
            - parentspec (str): Text regular expression for the line to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line
        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored

        Returns:
            - list.  A list of matching parent configuration lines

        This example finds all ports that are autonegotiating in the 
        following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/1
           interface FastEthernet0/2

        We do this by quering `find_parents_wo_child()`; we set our 
        parent as `^interface` and set the child as `speed\s\d+` (a 
        regular-expression which matches the word 'speed' followed by
        an integer).

        .. code-block:: python
           :emphasize-lines: 18

           >>> config = ['!', 
           ...           'interface FastEthernet0/1', 
           ...           ' switchport access vlan 532', 
           ...           ' spanning-tree vlan 532 cost 3', 
           ...           '!', 
           ...           'interface FastEthernet0/2', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!', 
           ...           'interface FastEthernet0/3', 
           ...           ' duplex full', 
           ...           ' speed 100', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_parents_wo_child('^interface', 'speed\s\d+')
           ['interface FastEthernet0/1', 'interface FastEthernet0/2']
           >>>

        """
        tmp = self.find_objects_wo_child(parentspec, childspec, 
            ignore_ws=ignore_ws)
        return list(map(attrgetter('text'), tmp))

    def find_children_w_parents(self, parentspec, childspec, ignore_ws=False):
        """Parse through the children of all parents matching parentspec, 
        and return a list of children that matched the childspec.

        Args:
            - parentspec (str): Text regular expression for the line to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line

        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored 

        Returns:
            - list.  A list of matching child configuration lines

        This example finds the port-security lines on FastEthernet0/1 in 
        following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            switchport port-security
            switchport port-security violation protect
            switchport port-security aging time 5
            switchport port-security aging type inactivity
            spanning-tree portfast
            spanning-tree bpduguard enable
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
            spanning-tree bpduguard enable
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
            spanning-tree bpduguard enable
           !

        The following lines should be returned:

        .. code::

            switchport port-security
            switchport port-security violation protect
            switchport port-security aging time 5
            switchport port-security aging type inactivity

        We do this by quering `find_children_w_parents()`; we set our 
        parent as `^interface` and set the child as 
        `switchport port-security`.

        .. code-block:: python
           :emphasize-lines: 25

           >>> config = ['!', 
           ...           'interface FastEthernet0/1', 
           ...           ' switchport access vlan 532', 
           ...           ' switchport port-security', 
           ...           ' switchport port-security violation protect', 
           ...           ' switchport port-security aging time 5', 
           ...           ' switchport port-security aging type inactivity', 
           ...           ' spanning-tree portfast', 
           ...           ' spanning-tree bpduguard enable', 
           ...           '!', 
           ...           'interface FastEthernet0/2', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           ' spanning-tree bpduguard enable', 
           ...           '!', 
           ...           'interface FastEthernet0/3', 
           ...           ' duplex full', 
           ...           ' speed 100', 
           ...           ' switchport access vlan 300', 
           ...           ' spanning-tree portfast', 
           ...           ' spanning-tree bpduguard enable', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_children_w_parents('^interface\sFastEthernet0/1', \
           'port-security')
           [' switchport port-security', ' switchport port-security violation protect', ' switchport port-security aging time 5', ' switchport port-security aging type inactivity']
           >>>

        """
        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        retval = set([])
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = child.all_parents
            for parent in parents:
                if re.search(parentspec, parent.text):
                    retval.add(child)

        return list(map(attrgetter('text'), sorted(retval)))

    def find_objects_w_parents(self, parentspec, childspec, ignore_ws=False):
        """Parse through the children of all parents matching parentspec, 
        and return a list of child objects, which matched the childspec.

        Args:
            - parentspec (str): Text regular expression for the line to be matched; this must match the parent's line
            - childspec (str): Text regular expression for the line to be matched; this must match the child's line

        Kwargs:
            - ignore_ws (bool): boolean that controls whether whitespace is ignored 

        Returns:
            - list.  A list of matching child objects

        This example finds the object for "ge-0/0/0" under "interfaces" in the
        following config...

        .. code::

            interfaces 
                ge-0/0/0 
                    unit 0 
                        family ethernet-switching 
                            port-mode access
                            vlan 
                                members VLAN_FOO
                ge-0/0/1 
                    unit 0 
                        family ethernet-switching 
                            port-mode trunk
                            vlan 
                                members all
                            native-vlan-id 1
                vlan 
                    unit 0 
                        family inet 
                            address 172.16.15.5/22


        The following object should be returned:

        .. code::

            <IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>

        We do this by quering `find_childobj_w_parents()`; we set our 
        parent as `^\s*interface` and set the child as 
        `^\s+ge-0/0/1`.

        .. code-block:: python
           :emphasize-lines: 21,22

           >>> config = ['interfaces',
           ...           '    ge-0/0/0',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode access',
           ...           '                vlan',
           ...           '                    members VLAN_FOO',
           ...           '    ge-0/0/1',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode trunk',
           ...           '                vlan',
           ...           '                    members all',
           ...           '                native-vlan-id 1',
           ...           '    vlan',
           ...           '        unit 0',
           ...           '            family inet',
           ...           '                address 172.16.15.5/22',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.find_objects_w_parents('^\s*interfaces', \
           r'\s+ge-0/0/1')
           [<IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>]
           >>>

        """
        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        retval = set([])
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = child.all_parents
            for parent in parents:
                if re.search(parentspec, parent.text):
                    retval.add(child)

        return sorted(retval)


    def find_lineage(self, linespec, exactmatch=False):
        """Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors / children in the direct line.  Cousins or
        aunts / uncles are *not* returned.  Note, all children
        of this object are returned."""
        tmp = self.find_objects(linespec, exactmatch=exactmatch)
        if len(tmp)>1:
            raise ValueError("linespec must be unique")
        return [obj.text for obj in tmp[0].lineage]

    def has_line_with(self, linespec):
        return self.ConfigObjs.has_line_with(linespec)

    def insert_before(self, linespec, insertstr="", exactmatch=False, 
        ignore_ws=False, atomic=True):
        """Find all objects whose text matches linespec, and insert 'insertstr' before those line objects"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        last_idx = len(objs) - 1
        local_atomic = False & atomic
        for idx, obj in enumerate(objs):
            if (idx==last_idx):
                local_atomic = True & atomic
            self.ConfigObjs.insert_before(obj, insertstr, 
                atomic=local_atomic)

        ## Return the matching lines
        return list(map(attrgetter('text'), sorted(objs)))

    def insert_after(self, linespec, insertstr="", exactmatch=False, 
        ignore_ws=False, atomic=True):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text 
        matches ``linespec``, and insert ``insertstr`` after those line 
        objects"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        last_idx = len(objs) - 1
        local_atomic = False & atomic
        for idx, obj in enumerate(objs):
            if idx==last_idx:
                local_atomic = True & atomic
            self.ConfigObjs.insert_after(obj, insertstr, 
                atomic=local_atomic)

        ## Return the matching lines
        return list(map(attrgetter('text'), sorted(objs)))

    def insert_after_child(self, parentspec, childspec, insertstr="", 
        exactmatch=False, excludespec=None, ignore_ws=False, atomic=True):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text 
        matches ``linespec`` and have a child matching ``childspec``, and 
        insert an :class:`~models_cisco.IOSCfgLine` object for ``insertstr`` 
        after those child objects."""
        retval = list()
        modified = False
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and re.search(excludespec, pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in pobj.children:
                if excludespec and re.search(excludespec, cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif re.search(childspec, cobj.text):
                    modified = True
                    retval.append(self.ConfigObjs.insert_after(cobj, 
                        insertstr, atomic=False))
                else:
                    pass
        return retval

    def delete_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text 
        matches linespec, and delete the object"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        #atomic = False
        for idx, obj in enumerate(objs):
            #if idx==last_idx:
            #    atomic = True
            del self.ConfigObjs[obj.linenum]

    def prepend_line(self, linespec):
        """Unconditionally insert an :class:`~models_cisco.IOSCfgLine` object
        for ``linespec`` (a text line) at the top of the configuration"""
        self.ConfigObjs.insert(0, linespec)
        return self.ConfigObjs[0]

    def append_line(self, linespec):
        """Unconditionally insert ``linespec`` (a text line) at the end of the 
        configuration

        Args:
            - linespec (str): Text IOS configuration line

        Returns:
            - The parsed :class:`~models_cisco.IOSCfgLine` instance

        """
        lines = self.ioscfg
        lines.append(linespec)
        self.ConfigObjs._bootstrap_obj_init(text_list=lines)
        return self.ConfigObjs[-1]

    def replace_lines(self, linespec, replacestr, excludespec=None, 
        exactmatch=False, atomic=True):
        """This method is a text search and replace (Case-sensitive).  You can
        optionally exclude lines from replacement by including a string (or
        compiled regular expression) in `excludespec`.

        Args:
            - linespec (str): Text regular expression for the line to be matched
            - replacestr (str): Text used to replace strings matching linespec

        Kwargs:
            - excludespec (str): Text regular expression used to reject lines, which would otherwise be replaced.  Default value of ``excludespec`` is None, which means nothing is excluded
            - exactmatch (bool): boolean that controls whether partial matches are valid
            - atomic (bool): boolean that controls whether the config is reparsed after replacement (default True)

        Returns:
            - list. A list of changed configuration lines

        This example finds statements with `EXTERNAL_CBWFQ` in following 
        config, and replaces all matching lines (in-place) with `EXTERNAL_QOS`.
        For the purposes of this example, let's assume that we do *not* want
        to make changes to any descriptions on the policy.

        .. code::

           !
           policy-map EXTERNAL_CBWFQ
            description implement an EXTERNAL_CBWFQ policy
            class IP_PREC_HIGH
             priority percent 10
             police cir percent 10
               conform-action transmit
               exceed-action drop
            class IP_PREC_MEDIUM
             bandwidth percent 50
             queue-limit 100
            class class-default
             bandwidth percent 40
             queue-limit 100
           policy-map SHAPE_HEIR
            class ALL
             shape average 630000
             service-policy EXTERNAL_CBWFQ
           !

        We do this by calling `replace_lines(linespec='EXTERNAL_CBWFQ', 
        replacestr='EXTERNAL_QOS', excludespec='description')`...

        .. code-block:: python
           :emphasize-lines: 23

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!', 
           ...           'policy-map EXTERNAL_CBWFQ', 
           ...           ' description implement an EXTERNAL_CBWFQ policy',
           ...           ' class IP_PREC_HIGH', 
           ...           '  priority percent 10', 
           ...           '  police cir percent 10', 
           ...           '    conform-action transmit', 
           ...           '    exceed-action drop', 
           ...           ' class IP_PREC_MEDIUM', 
           ...           '  bandwidth percent 50', 
           ...           '  queue-limit 100', 
           ...           ' class class-default', 
           ...           '  bandwidth percent 40', 
           ...           '  queue-limit 100', 
           ...           'policy-map SHAPE_HEIR', 
           ...           ' class ALL', 
           ...           '  shape average 630000', 
           ...           '  service-policy EXTERNAL_CBWFQ', 
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config)
           >>> p.replace_lines('EXTERNAL_CBWFQ', 'EXTERNAL_QOS', 'description')
           ['policy-map EXTERNAL_QOS', '  service-policy EXTERNAL_QOS']
           >>>

        Now when we call `p.find_blocks('policy-map EXTERNAL_QOS')`, we get the
        changed configuration, which has the replacements except on the 
        policy-map's description.

        >>> p.find_blocks('EXTERNAL_QOS')
        ['policy-map EXTERNAL_QOS', ' description implement an EXTERNAL_CBWFQ policy', ' class IP_PREC_HIGH', ' class IP_PREC_MEDIUM', ' class class-default', 'policy-map SHAPE_HEIR', ' class ALL', '  shape average 630000', '  service-policy EXTERNAL_QOS']
        >>>
        """
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        if excludespec:
            excludespec_re = re.compile(excludespec)

        for obj in self._find_line_OBJ(linespec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(obj.text):
                # Exclude replacements on lines which match excludespec
                continue
            retval.append(obj.re_sub(linespec, replacestr))

        if self.factory and atomic:
            #self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()

        return retval

    def replace_children(self, parentspec, childspec, replacestr, 
        excludespec=None, exactmatch=False, atomic=True):
        """Replace lines matching `childspec` within the immediate children of lines which match `parentspec`

        Args:
            - parentspec (str): Text IOS configuration line
            - childspec (str): Text IOS configuration line, or regular expression
            - replacestr (str): Text IOS configuration, which should replace text matching ``childspec``.

        Kwargs:
            - excludespec (str): A regular expression, which indicates ``childspec`` lines which *must* be skipped.  If ``excludespec`` is None, no lines will be excluded.
            - exactmatch (bool): Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.

        Returns:
            - list.  A list of changed :class:`~models_cisco.IOSCfgLine` instances.

        """
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        childspec_re   = re.compile(childspec)
        if excludespec:
            excludespec_re = re.compile(excludespec)
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in pobj.children:
                if excludespec and excludespec_re.search(cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif childspec_re.search(cobj.text):
                    retval.append(cobj.re_sub(childspec, replacestr))
                else:
                    pass

        if self.factory and atomic:
            self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()
        return retval

    def replace_all_children(self, parentspec, childspec, replacestr, 
        excludespec=None, exactmatch=False, atomic=False):
        """Replace lines matching `childspec` within all children (recursive) of lines whilch match `parentspec`"""
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        childspec_re   = re.compile(childspec)
        if excludespec:
            excludespec_re = re.compile(excludespec)
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in self._find_all_child_OBJ(pobj):
                if excludespec and excludespec_re.search(cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif childspec_re.search(cobj.text):
                    retval.append(cobj.re_sub(childspec, replacestr))
                else:
                    pass

        if self.factory and atomic:
            self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()

        return retval

    def req_cfgspec_all_diff(self, cfgspec, ignore_ws=False):
        """
        req_cfgspec_all_diff takes a list of required configuration lines,
        parses through the configuration, and ensures that none of cfgspec's
        lines are missing from the configuration.  req_cfgspec_all_diff
        returns a list of missing lines from the config.

        One example use of this method is when you need to enforce routing
        protocol standards, or standards against interface configurations.

        **Example**

        .. doctest::

           >>> config = [
           ...     'logging trap debugging',
           ...     'logging 172.28.26.15',
           ...     ] 
           >>> p = CiscoConfParse(config)
           >>> required_lines = [
           ...     "logging 172.28.26.15",
           ...     "logging 172.16.1.5",
           ...     ]
           >>> diffs = p.req_cfgspec_all_diff(required_lines)
           >>> diffs
           ['logging 172.16.1.5']
           >>>
        """

        if ignore_ws:
            cfgspec = self._build_space_tolerant_regex(cfgspec)

        skip_cfgspec = dict()
        retval = list()
        matches = self._find_line_OBJ("[a-zA-Z]")
        ## Make a list of unnecessary cfgspec lines
        for lineobj in matches:
            for reqline in cfgspec:
                if lineobj.text.strip() == reqline.strip():
                    skip_cfgspec[reqline] = True
        ## Add items to be configured
        ## TODO: Find a way to add the parent of the missing lines
        for line in cfgspec:
            if not skip_cfgspec.get(line, False):
                retval.append(line)

        return retval

    def req_cfgspec_excl_diff(self, linespec, uncfgspec, cfgspec):
        """
        req_cfgspec_excl_diff accepts a linespec, an unconfig spec, and
        a list of required configuration elements.  Return a list of
        configuration diffs to make the configuration comply.  **All** other
        config lines matching the linespec that are *not* listed in the
        cfgspec will be removed with the uncfgspec regex.

        Uses for this method include the need to enforce syslog, acl, or
        aaa standards.

        **Example**

        .. doctest::

           >>> config = [
           ...     'logging trap debugging',
           ...     'logging 172.28.26.15',
           ...     ] 
           >>> p = CiscoConfParse(config)
           >>> required_lines = [
           ...     "logging 172.16.1.5",
           ...     "logging 1.10.20.30",
           ...     "logging 192.168.1.1",
           ...     ]
           >>> linespec = "logging\s+\d+\.\d+\.\d+\.\d+"
           >>> unconfspec = linespec
           >>> diffs = p.req_cfgspec_excl_diff(linespec, unconfspec, 
           ...     required_lines)
           >>> diffs
           ['no logging 172.28.26.15', 'logging 172.16.1.5', 'logging 1.10.20.30', 'logging 192.168.1.1']
           >>>
        """
        violate_objs = list()
        uncfg_objs = list()
        skip_cfgspec = dict()
        retval = list()
        matches = self._find_line_OBJ(linespec)
        ## Make a list of lineobject violations
        for lineobj in matches:
            # Look for config lines to unconfigure
            accept_lineobj = False
            for reqline in cfgspec:
                if (lineobj.text.strip()==reqline.strip()):
                    accept_lineobj = True
                    skip_cfgspec[reqline] = True
            if (accept_lineobj is False):
                # If a violation is found...
                violate_objs.append(lineobj)
                result = re.search(uncfgspec, lineobj.text)
                # add uncfgtext to the violator's lineobject
                lineobj.add_uncfgtext(result.group(0))
        ## Make the list of unconfig objects, recurse through parents
        for vobj in violate_objs:
            parent_objs = vobj.all_parents
            for parent_obj in parent_objs:
                uncfg_objs.append(parent_obj)
            uncfg_objs.append(vobj)
        retval = self._objects_to_uncfg(uncfg_objs, violate_objs)
        ## Add missing lines...
        ## TODO: Find a way to add the parent of the missing lines
        for line in cfgspec:
            if not skip_cfgspec.get(line, False):
                retval.append(line)

        return retval

    def save_as(self, filepath):
        """Save a text copy of the configuration at ``filepath``; this
        method uses the OperatingSystem's native line separators (such as
        ``\\r\\n`` in Windows)."""
        with open(filepath, 'w') as newconf:
            for line in self.ioscfg:
                newconf.write(line+os.linesep)


    ### The methods below are marked SEMI-PRIVATE because they return an object
    ###  or iterable of objects instead of the configuration text itself.
    def _build_space_tolerant_regex(self, linespec):
        """SEMI-PRIVATE: Accept a string, and return a string with all
        spaces replaced with '\s+'"""

        # Unicode below
        backslash = '\x5c'

        linespec = re.sub('\s+', backslash+"s+", linespec)

        return linespec

    def _find_line_OBJ(self, linespec, exactmatch=False):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""
        ## NOTE TO SELF: do not remove _find_line_OBJ(); used by Cisco employees
        if not exactmatch:
            # Return objects whose text attribute matches linespec
            linespec_re = re.compile(linespec)
        elif exactmatch:
            # Return objects whose text attribute matches linespec exactly
            linespec_re = re.compile("^%s$" % linespec)
        return list(filter(lambda obj: linespec_re.search(obj.text), self.ConfigObjs))

    def _find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    def _find_all_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of
        decendants in all 'children' / 'grandchildren' / etc... after it.
        It should NOT return the children of siblings"""
        # sort the list, and get unique objects
        retval = set(lineobject.children)
        for candidate in lineobject.children:
            if candidate.has_children:
                for child in candidate.children:
                    retval.add(child)
        retval = sorted(retval)
        return retval

    def _unique_OBJ(self, objectlist):
        """SEMI-PRIVATE: Returns a list of unique objects (i.e. with no
        duplicates).
        The returned value is sorted by configuration line number
        (lowest first)"""
        retval = set([])
        for obj in objectlist:
            retval.add(obj)
        return sorted(retval)

    def _objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = list()
        unconfdict = dict()
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self._unique_OBJ(objectlist):
            if (unconfdict.get(obj, None)=="DEFINED"):
                retval.append(obj.uncfgtext)
            else:
                retval.append(obj.text)
        return retval


class IOSConfigList(MutableSequence):
    """A custom list to hold :class:`~models_cisco.IOSCfgLine` objects.  Most people will never need to use this class directly.
    """

    def __init__(self, data=None, comment_delimiter='!', debug=False,
        factory=False, ignore_blank_lines=True, syntax='ios', CiscoConfParse=None):
        """Initialize the class.

        Kwargs:
            - data (list): A list of parsed :class:`~models_cisco.IOSCfgLine` objects
            - comment (str): A comment delimiter.  This should only be changed when parsing non-Cisco IOS configurations, which do not use a !  as the comment delimiter.  ``comment`` defaults to '!'
            - debug (bool): ``debug`` defaults to False, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug output is not particularly friendly
            - ignore_blank_lines (bool): ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration (ref: Github Issue #2).

        Returns:
           - An instance of an :class:`~ciscoconfparse.IOSConfigList` object.

        """
        #data = kwargs.get('data', None)
        #comment_delimiter = kwargs.get('comment_delimiter', '!')
        #debug = kwargs.get('debug', False)
        #factory = kwargs.get('factory', False)
        #ignore_blank_lines = kwargs.get('ignore_blank_lines', True)
        #syntax = kwargs.get('syntax', 'ios')
        #CiscoConfParse = kwargs.get('CiscoConfParse', None)
        super(IOSConfigList, self).__init__()

        self._list = list()
        self.CiscoConfParse = CiscoConfParse
        self.DBGFLAG = debug
        self.comment_delimiter = comment_delimiter
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.syntax = syntax
        self.dna = 'IOSConfigList'

        ## Support either a list or a generator instance
        if getattr(data, '__iter__', False):
            self._list = self._bootstrap_obj_init(data)
        else:
            self._list = list()

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]
        self._bootstrap_from_text()

    def __setitem__(self, ii, val):
        return self._list[ii]

    def __str__(self):
        return self.__repr__()

    def __enter__(self):
        # Add support for with statements...
        # FIXME: *with* statements dont work
        for obj in self._list:
            yield obj

    def __exit__(self, *args, **kwargs):
        # FIXME: *with* statements dont work
        self._list[0].confobj.CiscoConfParse.atomic()

    def __repr__(self):
        return """<IOSConfigList, comment='%s', conf=%s>""" % (self.comment_delimiter, self._list)


    def _bootstrap_from_text(self):
        ## reparse all objects from their text attributes... this is *very* slow
        ## Ultimate goal: get rid of all reparsing from text... 
        self._list = self._bootstrap_obj_init(list(map(attrgetter('text'), self._list)))

    def has_line_with(self, linespec):
        return bool(filter(methodcaller('re_search', linespec), self._list))

    def insert_before(self, robj, val, atomic=True):
        ## Insert something before robj
        if getattr(robj, 'capitalize', False):
            # robj must not be a string...
            raise ValueError

        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter, 
                    syntax=self.syntax)
            elif self.syntax=='ios':
                obj = IOSCfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def insert_after(self, robj, val, atomic=True):
        ## Insert something after robj
        if getattr(robj, 'capitalize', False):
            raise ValueError

        ## If val is a string...
        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax)
            elif self.syntax=='ios':
                obj = IOSCfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ## FIXME: This shouldn't be required
        ## Removed 2015-01-24 during rewrite...
        #self._reassign_linenums()

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii+1, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def insert(self, ii, val, atomic=True):
        ## Insert something at index ii
        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax)
            elif self.syntax=='ios':
                obj = IOSCfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)
            else:
                raise ValueError('FATAL insert string - Cannot insert "{0}"'.format(val))
        else:
            raise ValueError('FATAL insert - Cannot insert "{0}"'.format(val))

        self._list.insert(ii, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def append(self, val, atomic=True):
        list_idx = len(self._list)
        self.insert(list_idx, val, atomic)

    def _banner_mark_regex(self, REGEX):
        banner_objs = list(filter(lambda obj: REGEX.search(obj.text), self._list))
        for parent in banner_objs:
            idx = parent.linenum
            parent.oldest_ancestor = True
            bannerchar = parent.text.strip()[-1]
            while True:
                idx += 1
                try:
                    obj = self._list[idx]
                    if obj.text.strip()==bannerchar:
                        parent.children.append(obj)
                        parent.child_indent = 0
                        obj.parent = parent
                        break
                    elif obj.is_comment and (obj.indent==0):
                        break
                    parent.children.append(obj)
                    parent.child_indent = 0
                    obj.parent = parent
                except IndexError:
                    break

    def _bootstrap_obj_init(self, text_list):
        """Accept a text list and format into proper objects"""
        # Append text lines as IOSCfgLine objects...
        BANNER_STR = set(['login',
            'motd', 'incoming', 'incoming', 
            'telnet', 'lcd',
            ])
        BANNER_RE = re.compile('|'.join([r'^(set\s+)*banner\s+{0}'.format(ii) for ii in BANNER_STR]))
        retval = list()
        idx = 0

        max_indent = 0
        parents = dict()
        for line in text_list:
            # Reject empty lines if ignore_blank_lines...
            if self.ignore_blank_lines and line.strip()=='':
                continue
            # 
            if not self.factory:
                obj = IOSCfgLine(line, self.comment_delimiter)
            elif self.syntax=='ios':
                obj = ConfigLineFactory(line, self.comment_delimiter,
                    syntax='ios')
            else:
                raise ValueError

            obj.confobj  = self
            obj.linenum  = idx
            indent   = len(line) - len(line.lstrip())
            obj.indent = indent

            is_config_line = obj.is_config_line

            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent<max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(lambda ii: ii>=indent, sorted(parents.keys(), reverse=True))
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards, 
                ##    we can use a cached parent
                parent = parents.get(indent, None)

            ## If indented, walk backwards and find the parent...
            ## 1.  Assign parent to the child
            ## 2.  Assign child to the parent
            ## 3.  Assign parent's child_indent
            ## 4.  Maintain oldest_ancestor
            if (indent>0) and not (parent is None):
                ## Add the line as a child (parent was cached)
                self._add_child_to_parent(retval, idx, indent, parent, obj)
            elif (indent>0) and (parent is None):
                ## Walk backwards to find parent, and add the line as a child
                candidate_parent_index = idx - 1
                while candidate_parent_index>=0:
                    candidate_parent = retval[candidate_parent_index]
                    if (candidate_parent.indent<indent) and \
                        candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent      # Cache the parent
                        if indent==0:
                            parent.oldest_ancestor = True
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent==0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent>max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval
        self._banner_mark_regex(BANNER_RE)
        return retval

    def _add_child_to_parent(self, _list, idx, indent, parentobj, childobj):
        if childobj.is_comment and (_list[idx-1].indent>indent):
            ## I *really* hate making this exception, but legacy 
            ##   ciscoconfparse never marked a comment as a child 
            ##   when the line immediately above it was indented more
            ##   than the comment line
            pass
        else:
            parentobj.children.append(childobj)
            childobj.parent = parentobj
            childobj.parent.child_indent = indent

    def iter_with_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx>=begin_index):
                yield obj

    def iter_no_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx>=begin_index) and (not obj.is_comment):
                yield obj

    def _reassign_linenums(self):
        # Call this after any insertion or deletion
        for idx, obj in enumerate(self._list):
            obj.linenum = idx

    @property
    def all_parents(self):
        return [obj for obj in self._list if obj.has_children]

    @property
    def last_index(self):
        return (self.__len__()-1)


class ASAConfigList(MutableSequence):
    """A custom list to hold :class:`~models_asa.ASACfgLine` objects.  Most 
       people will never need to use this class directly.


    """
    def __init__(self, data=None, comment_delimiter='!', debug=False, 
        factory=False, ignore_blank_lines=True, syntax='asa', CiscoConfParse=None):
        """Initialize the class.

        Kwargs:
            - data (list): A list of parsed :class:`~models_asa.ASACfgLine` objects
            - comment (str): A comment delimiter.  This should only be changed when parsing non-Cisco IOS configurations, which do not use a !  as the comment delimiter.  ``comment`` defaults to '!'
            - debug (bool): ``debug`` defaults to False, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug output is not particularly friendly
            - ignore_blank_lines (bool): ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration.

        Attributes:
            - names (dict): A Python dictionary, which maps a Cisco ASA name to a string representing the address
            - object_group_network (dict): A Python dictionary, which maps a Cisco ASA object-group network name to the :class:`~models_asa.ASAObjNetwork` object
            - object_group_service (dict): A Python dictionary, which maps a Cisco ASA object-group service name to the :class:`~models_asa.ASAObjService` object
 
        Returns:
            - An instance of an :class:`~ciscoconfparse.ASAConfigList` object.
 
        """
        super(ASAConfigList, self).__init__()

        self._list = list()
        self.CiscoConfParse = CiscoConfParse
        self.DBGFLAG = debug
        self.comment_delimiter = comment_delimiter
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.syntax = syntax
        self.dna = 'ASAConfigList'

        ## Support either a list or a generator instance
        if getattr(data, '__iter__', False):
            self._bootstrap_obj_init(data)
        else:
            self._list = list()

        ###
        ### Internal structures
        self._RE_NAMES = re.compile(r'^\s*name\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)')
        self._RE_OBJNET = re.compile(r'^\s*object-group\s+network\s+(\S+)')
        self._RE_OBJSVC = re.compile(r'^\s*object-group\s+service\s+(\S+)')

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]
        self._bootstrap_from_text()

    def __setitem__(self, ii, val):
        return self._list[ii]

    def __str__(self):
        return self.__repr__()

    def __enter__(self):
        # Add support for with statements...
        # FIXME: *with* statements dont work
        for obj in self._list:
            yield obj

    def __exit__(self, *args, **kwargs):
        # FIXME: *with* statements dont work
        self._list[0].confobj.CiscoConfParse.atomic()

    def __repr__(self):
        return """<ASAConfigList, comment='%s', conf=%s>""" % (self.comment_delimiter, self._list)

    def _bootstrap_from_text(self):
        ## reparse all objects from their text attributes... this is *very* slow
        ## Ultimate goal: get rid of all reparsing from text... 
        self._list = self._bootstrap_obj_init(list(map(attrgetter('text'), self._list)))

    def has_line_with(self, linespec):
        return bool(filter(methodcaller('re_search', linespec), self._list))

    def insert_before(self, robj, val, atomic=True):
        ## Insert something before robj
        if getattr(robj, 'capitalize', False):
            raise ValueError

        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter, 
                    syntax=self.syntax)
            elif self.syntax=='asa':
                obj = ASACfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def insert_after(self, robj, val, atomic=True):
        ## Insert something after robj
        if getattr(robj, 'capitalize', False):
            raise ValueError

        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax)
            elif self.syntax=='asa':
                obj = ASACfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ## FIXME: This shouldn't be required
        self._reassign_linenums()

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii+1, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def insert(self, ii, val, atomic=True):
        ## Insert something at index ii
        if getattr(val, 'capitalize', False):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax)
            elif self.syntax=='asa':
                obj = ASACfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        self._list.insert(ii, obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()


    def append(self, val, atomic=True):
        list_idx = len(self._list)
        self.insert(list_idx, val, atomic)

    def _bootstrap_obj_init(self, text_list):
        """Accept a text list and format into proper objects"""
        # Append text lines as IOSCfgLine objects...
        retval = list()
        idx = 0

        max_indent = 0
        parents = dict()
        for line in text_list:
            # Reject empty lines if ignore_blank_lines...
            if self.ignore_blank_lines and line.strip()=='':
                continue

            if self.syntax=='asa' and self.factory:
                obj = ConfigLineFactory(line, self.comment_delimiter,
                    syntax='asa')
            elif self.syntax=='asa' and not self.factory:
                obj = IOSCfgLine(text=line,
                    comment_delimiter=self.comment_delimiter)
            else:
                raise ValueError

            obj.confobj  = self
            obj.linenum  = idx
            indent   = len(line) - len(line.lstrip())
            obj.indent = indent

            is_config_line = obj.is_config_line


            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent<max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(lambda ii: ii>=indent, sorted(parents.keys(), reverse=True))
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards, 
                ##    we can use a cached parent
                parent = parents.get(indent, None)

            ## If indented, walk backwards and find the parent...
            ## 1.  Assign parent to the child
            ## 2.  Assign child to the parent
            ## 3.  Assign parent's child_indent
            ## 4.  Maintain oldest_ancestor
            if (indent>0) and not (parent is None):
                ## Add the line as a child (parent was cached)
                self._add_child_to_parent(retval, idx, indent, parent, obj)
            elif (indent>0) and (parent is None):
                ## Walk backwards to find parent, and add the line as a child
                candidate_parent_index = idx - 1
                while candidate_parent_index>=0:
                    candidate_parent = retval[candidate_parent_index]
                    if (candidate_parent.indent<indent) and \
                        candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent      # Cache the parent
                        if indent==0:
                            parent.oldest_ancestor = True
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent==0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent>max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval
        ## Insert ASA-specific banner processing here, if required
        return retval

    def _add_child_to_parent(self, _list, idx, indent, parentobj, childobj):
        if childobj.is_comment and (_list[idx-1].indent>indent):
            ## I *really* hate making this exception, but legacy 
            ##   ciscoconfparse never marked a comment as a child 
            ##   when the line immediately above it was indented more
            ##   than the comment line
            pass
        else:
            parentobj.children.append(childobj)
            childobj.parent = parentobj
            childobj.parent.child_indent = indent

    def iter_with_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx>=begin_index):
                yield obj

    def iter_no_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx>=begin_index) and (not obj.is_comment):
                yield obj

    def _reassign_linenums(self):
        # Call this after any insertion or deletion
        for idx, obj in enumerate(self._list):
            obj.linenum = idx

    @property
    def all_parents(self):
        return [obj for obj in self._list if obj.has_children]

    @property
    def last_index(self):
        return (self.__len__()-1)


    ###
    ### ASA-specific stuff here...
    ###
    @property
    def names(self):
        """Return a dictionary of name to address mappings"""
        retval = dict()
        name_rgx = self._RE_NAMES
        for obj in self.CiscoConfParse.find_objects(name_rgx):
            addr = obj.re_match_typed(name_rgx, group=1, result_type=str)
            name = obj.re_match_typed(name_rgx, group=2, result_type=str)
            retval[name] = addr
        return retval

    @property
    def object_group_network(self):
        """Return a dictionary of name to object-group network mappings"""
        retval = dict()
        obj_rgx = self._RE_OBJNET
        for obj in self.CiscoConfParse.find_objects(obj_rgx):
            name = obj.re_match_typed(obj_rgx, group=1, result_type=str)
            retval[name] = obj
        return retval

    @property
    def object_group_service(self):
        """Return a dictionary of name to object-group service mappings"""
        retval = dict()
        obj_rgx = self._RE_OBJSVC
        for obj in self.CiscoConfParse.find_objects(obj_rgx):
            name = obj.re_match_typed(obj_rgx, group=1, result_type=str)
            retval[name] = obj
        return retval


class CiscoPassword(object):

    def __init__(self):
        self

    def decrypt(self, ep):
        """Cisco Type 7 password decryption.  Converted from perl code that was
        written by jbash [~at~] cisco.com; enhancements suggested by 
        rucjain [~at~] cisco.com"""

        xlat = (0x64, 0x73, 0x66, 0x64, 0x3b, 0x6b, 0x66, 0x6f, 0x41, 0x2c,
               0x2e, 0x69, 0x79, 0x65, 0x77, 0x72, 0x6b, 0x6c, 0x64, 0x4a,
               0x4b, 0x44, 0x48, 0x53, 0x55, 0x42, 0x73, 0x67, 0x76, 0x63,
               0x61, 0x36, 0x39, 0x38, 0x33, 0x34, 0x6e, 0x63, 0x78, 0x76,
               0x39, 0x38, 0x37, 0x33, 0x32, 0x35, 0x34, 0x6b, 0x3b, 0x66,
               0x67, 0x38, 0x37)

        dp = ""
        regex = re.compile("^(..)(.+)")
        if not (len(ep) & 1):
            result = regex.search(ep)
            try:
                s, e = int(result.group(1)), result.group(2)
            except ValueError:
                # typically get a ValueError for int( result.group(1))) because
                # the method was called with an unencrypted password.  For now
                # SILENTLY bypass the error
                s, e = (0, "")
            for ii in range(0, len(e), 2):
                # int( blah, 16) assumes blah is base16... cool
                magic = int(re.search(".{%s}(..)" % ii, e).group(1), 16)
                # Wrap around after 53 chars...
                newchar = "%c" % (magic ^ int(xlat[int(s%53)]))
                dp = dp + str(newchar)
                s = s + 1
        #if s > 53:
        #    print("[DEBUG] WARNING: password decryption failed.")
        return dp

def ConfigLineFactory(text="", comment_delimiter="!", syntax='ios'):
    # Complicted & Buggy
    #classes = [j for (i,j) in globals().iteritems() if isinstance(j, TypeType) and issubclass(j, BaseCfgLine)]

    ## Manual and simple
    if syntax=='ios':
        classes = [IOSIntfLine, IOSRouteLine, IOSAccessLine, 
            IOSAaaLoginAuthenticationLine, IOSAaaEnableAuthenticationLine,
            IOSAaaCommandsAuthorizationLine, IOSAaaCommandsAccountingLine,
            IOSAaaExecAccountingLine, IOSAaaGroupServerLine,
            IOSHostnameLine, IOSIntfGlobal, IOSCfgLine]  # This is simple
    elif syntax=='asa':
        classes = [ASAName, ASAObjNetwork, ASAObjService, 
            ASAObjGroupNetwork, ASAObjGroupService, 
            ASAIntfLine, ASAIntfGlobal, 
            ASAHostnameLine, ASACfgLine]
    for cls in classes:
        if cls.is_object_for(text):
            inst = cls(text=text, 
                comment_delimiter=comment_delimiter) # instance of the proper subclass
            return inst
    raise ValueError("Could not find an object for '%s'" % line)

### TODO: Add unit tests below
if __name__ == '__main__':
    import optparse
    pp = optparse.OptionParser()
    pp.add_option("-c", dest="config", help="Config file to be parsed",
                        metavar = "FILENAME")
    pp.add_option("-m", dest="method", help="Command for parsing",
                        metavar = "METHOD")
    pp.add_option("--a1", dest="arg1", help="Command's first argument",
                     metavar = "ARG")
    pp.add_option("--a2", dest="arg2", help="Command's second argument",
                     metavar = "ARG")
    pp.add_option("--a3", dest="arg3", help="Command's third argument",
                     metavar = "ARG")
    (opts, args) = pp.parse_args()

    if opts.method == "find_lines":
        diff = CiscoConfParse(opts.config).find_lines(opts.arg1)
    elif opts.method == "find_children":
        diff = CiscoConfParse(opts.config).find_children(opts.arg1)
    elif opts.method == "find_all_children":
        diff = CiscoConfParse(opts.config).find_all_children(opts.arg1)
    elif opts.method == "find_blocks":
        diff = CiscoConfParse(opts.config).find_blocks(opts.arg1)
    elif opts.method == "find_parents_w_child":
        diff = CiscoConfParse(opts.config).find_parents_w_child(opts.arg1,
                 opts.arg2)
    elif opts.method == "find_parents_wo_child":
        diff = CiscoConfParse(opts.config).find_parents_wo_child(opts.arg1,
                 opts.arg2)
    elif opts.method == "req_cfgspec_excl_diff":
        diff = CiscoConfParse(opts.config).req_cfgspec_excl_diff(opts.arg1,
                 opts.arg2, opts.arg3.split(","))
    elif opts.method == "req_cfgspec_all_diff":
        diff = CiscoConfParse(opts.config).req_cfgspec_all_diff(
                 opts.arg1.split(","))
    elif opts.method == "decrypt":
        pp = CiscoPassword()
        print(pp.decrypt(opts.arg1))
        exit(1)
    elif opts.method == "help":
        print("Valid methods and their arguments:")
        print("   find_lines:             arg1=linespec")
        print("   find_children:          arg1=linespec")
        print("   find_all_children:      arg1=linespec")
        print("   find_blocks:            arg1=linespec")
        print("   find_parents_w_child:   arg1=parentspec  arg2=childspec")
        print("   find_parents_wo_child:  arg1=parentspec  arg2=childspec")
        print("   req_cfgspec_excl_diff:  arg1=linespec    arg2=uncfgspec" + \
            "   arg3=cfgspec")
        print("   req_cfgspec_all_diff:   arg1=cfgspec")
        print("   decrypt:                arg1=encrypted_passwd")
        exit(1)
    else:
        import doctest
        doctest.testmod()
        exit(0)

    if len(diff) > 0:
        for line in diff:
            print(line)
    else:
        raise RuntimeError("FATAL: ciscoconfparse was called with unknown" + \
            " parameters")
