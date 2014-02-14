from operator import methodcaller, attrgetter
from collections import MutableSequence
from copy import deepcopy
from sys import modules
import re
import os

from models_cisco import IOSHostnameLine, IOSRouteLine, IOSIntfLine
from models_cisco import IOSAccessLine, IOSInterfaceGlobal
from models_cisco import IOSCfgLine

### ipaddr is optional, and Apache License 2.0 is compatible with GPLv3 per
###   the ASL web page: http://www.apache.org/licenses/GPL-compatibility.html
try:
    from ipaddr import IPv4Network, IPv6Network
except ImportError:
    # I raise an ImportError below ipaddr is required
    pass

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

class CiscoConfParse(object):
    """Parses Cisco IOS configurations and answers queries about the configs

        Parameters
        ----------

        config : :py:func:`list` or :py:func:`str`
             A list of configuration statements, or a configuration file 
             path to be parsed
        comment : :py:func:`str`, optional
             A comment delimiter.  This should only be changed when 
             parsing non-Cisco IOS configurations, which do not use a ! 
             as the comment delimiter.  `comment` defaults to '!'

        Returns
        -------

        CiscoConfParse : :py:func:`object`
             An instance of a CiscoConfParse object.

        Attributes
        ----------

        ConfigObjs : :py:func:`dict`
             This contains all :class:`IOSCfgLine` object instances, which are generated from the configuration that is parsed.  The :py:func:`dict` is keyed by an :py:func:`int`, which is the line number of the configuration line.  The value of the :py:func:`dict` is the :class:`IOSCfgLine` instance for that line number.

        Examples
        --------

        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ] 
        >>> p = CiscoConfParse(config)
        >>> p
        <CiscoConfParse: 2 lines / comment delimiter: '!' / factory: False>
        >>> p.ConfigObjs
        <IOSConfigList, comment='!', conf=[<IOSCfgLine # 0 'logging trap debugging'>, <IOSCfgLine # 1 'logging 172.28.26.15'>]>
        >>>
    """

    def __init__(self, config="", comment="!", debug=False, factory=False):
        """Initialize the class, read the config, and spawn the parser"""

        # re: modules usage... thank you Delnan
        # http://stackoverflow.com/a/5027393
        if (factory is True) and (bool(modules.get('ipaddr', False)) is False):
            raise ImportError("Could not import ipaddr module.  ciscoconfparse.CiscoConfParse only requires the ipaddr module when called with factory=True.")

        # all IOSCfgLine object instances...
        self.comment_delimiter = comment
        self.factory = factory
        self.ConfigObjs = None

        if isinstance(config, list):
            # we already have a list object, simply call the parser
            self.ConfigObjs = IOSConfigList(config, comment, debug, factory)
        elif isinstance(config, str):
            # Try opening as a file
            try:
                # string - assume a filename... open file, split and parse
                f = open(config)
                text = f.read()
                rgx = re.compile("\r*\n+")
                self.ConfigObjs = IOSConfigList(rgx.split(text), comment, debug, 
                    factory)
            except IOError:
                print("FATAL: CiscoConfParse could not open '%s'" % config)
                raise RuntimeError
        else:
            raise RuntimeError("FATAL: CiscoConfParse() received" + \
                " an invalid argument\n")

    def __repr__(self):
        return "<CiscoConfParse: %s lines / comment delimiter: '%s' / factory: %s>" % (len(self.ConfigObjs), self.comment_delimiter, self.factory)


    @property
    def ioscfg(self):
        ## I keep this here to emulate the legacy ciscoconfparse behavior
        return [obj.text for obj in self.ConfigObjs]

    @property
    def objs(self):
        return self.ConfigObjs


    def atomic(self):
        """Call this to manually fix up ConfigObjs relationships after non-atomic insertions / deletions"""
        self.ConfigObjs._bootstrap_from_text()

    def find_objects(self, linespec, exactmatch=False, ignore_ws=False):
        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)
        return self._find_line_OBJ(linespec, exactmatch)

    def find_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """This method is the equivalent of a simple configuration grep
        (Case-sensitive).

        Parameters
        ----------

        linespec : :py:func:`str`
             Text regular expression for the line to be matched
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching configuration lines
        """
        retval = list()

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

        Parameters
        ----------

        linespec : :py:func:`str`
             Text regular expression for the line to be matched
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching configuration lines

        Examples
        --------

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
     
        Parameters
        ----------

        linespec : :py:func:`str`
             Text regular expression for the line to be matched
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching configuration lines

        Examples
        --------

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
            if (parent.has_children is True):
                allobjs.update(set(self._find_all_child_OBJ(parent)))
            allobjs.add(parent)
        return list(map(attrgetter('text'), sorted(allobjs)))

    def find_blocks(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all siblings matching the linespec, then find all parents of
        those siblings. Return a list of config lines sorted by line number,
        lowest first.  Note: any children of the siblings should NOT be
        returned.

        Parameters
        ----------

        linespec : :py:func:`str`
             Text regular expression for the line to be matched
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching configuration lines


        Examples
        --------

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
        """
        tmp = set([])
        retval = list()

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
        for lineobject in deepcopy(tmp):
            for pobj in lineobject.all_parents:
                tmp.add(pobj)

        return list(map(attrgetter('text'), sorted(tmp)))

    def find_parents_w_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all children matching childspec, and return a list of
        parents that matched the parentspec.

        Parameters
        ----------

        parentspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the parent's line
        childspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the child's line
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching parent configuration lines

        Examples
        --------

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

        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        retval = set([])
        childobjs = self._find_line_OBJ(childspec)
        parentspec_re = re.compile(parentspec)
        for child in childobjs:
            parents = child.all_parents
            match_parentspec = False
            for parent in parents:
                if parentspec_re.search(parent.text):
                    match_parentspec = True
            if (match_parentspec is True):
                for parent in parents:
                    retval.add(parent)
        return list(map(attrgetter('text'), sorted(retval)))

    def find_parents_wo_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all parents matching parentspec, and return a list of
        parents that did NOT have children match the childspec.  For
        simplicity, this method only finds oldest_ancestors without immediate
        children that match.

        Parameters
        ----------

        parentspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the parent's line
        childspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the child's line
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching parent configuration lines

        Examples
        --------

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

        if ignore_ws:
            parentspec = self._build_space_tolerant_regex(parentspec)
            childspec = self._build_space_tolerant_regex(childspec)

        retval = set([])
        ## Iterate over all parents, find those with non-matching children
        for parentobj in [obj for obj in self.ConfigObjs.all_parents \
            if (obj.oldest_ancestor and obj.re_search(parentspec))]:

            match_childspec = False
            for childobj in parentobj.children:
                if childobj.re_search(childspec):
                    match_childspec = True
            if (match_childspec is False):
                ## We found a parent without a child matching the
                ##    childspec
                retval.add(parentobj)

        return list(map(attrgetter('text'), sorted(retval)))

    def find_children_w_parents(self, parentspec, childspec, ignore_ws=False):
        """Parse through the children of all parents matching parentspec, 
        and return a list of children that matched the childspec.

        Parameters
        ----------

        parentspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the parent's line
        childspec : :py:func:`str`
             Text regular expression for the line to be matched; this must
             match the child's line
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        ignore_ws : :py:func:`bool`
             boolean that controls whether whitespace is ignored

        Returns
        -------

        retval : :py:func:`list`
            A list of matching child configuration lines

        Examples
        --------

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
        parentspec_re = re.compile(parentspec)
        childspec_re = re.compile(childspec)
        for child in childobjs:
            parents = child.all_parents
            match_parentspec = False
            for parent in parents:
                if re.search(parentspec, parent.text):
                    retval.add(child)

        return list(map(attrgetter('text'), sorted(retval)))

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
        """Find all objects whose text matches linespec, and insert 'insertstr' after those line objects"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        last_idx = len(objs) - 1
        local_atomic = False & atomic
        for idx, obj in enumerate(objs):
            if idx==last_idx:
                local_atomic = True & atomic
            self.ConfigObjs.insert(obj, insertstr, 
                atomic=local_atomic)

        ## Return the matching lines
        return list(map(attrgetter('text'), sorted(objs)))

    def insert_after_child(self, parentspec, childspec, insertstr="", 
        exactmatch=False, excludespec=None, ignore_ws=False, atomic=True):
        """Find all objects whose text matches linespec and have a child matching childspec, and insert 'insertstr' after those child objects"""
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
                    retval.append(self.ConfigObjs.insert(cobj, 
                        insertstr, atomic=False))
                else:
                    pass
        if modified:
            self.ConfigObjs.maintain_obj_sanity()
        return retval

    def delete_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all objects whose text matches linespec, and delete it"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        last_idx = len(objs) - 1
        #atomic = False
        for idx, obj in enumerate(objs):
            #if idx==last_idx:
            #    atomic = True
            del self.ConfigObjs[obj.linenum]

    def replace_lines(self, linespec, replacestr, excludespec=None, exactmatch=False,
        atomic=True):
        """This method is a text search and replace (Case-sensitive).  You can
        optionally exclude lines from replacement by including a string (or
        compiled regular expression) in `excludespec`.

        Parameters
        ----------

        linespec : :py:func:`str`
             Text regular expression for the line to be matched
        replacestr : :py:func:`str`
             Text used to replace strings matching linespec
        excludespec : :py:func:`str`
             Text regular expression used to reject lines, which would 
             otherwise be replaced
        exactmatch : :py:func:`bool`
             boolean that controls whether partial matches are valid
        atomic : :py:func:`bool`
             boolean that controls whether the config is reparsed after replacement (default True)

        Returns
        -------

        retval : :py:func:`list`
            A list of changed configuration lines


        Examples
        --------

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
        """Replace lines matching `childspec` within the immediate children of lines which match `parentspec`"""
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

        # OLD (slow) code, before lamba, re.compile and filter
        #retval = list()
        #for lineobj in self.ConfigObjs:
        #    if not exactmatch and re.search(linespec, lineobj.text):
        #        retval.append(lineobj)
        #    elif exactmatch and re.search("^%s$" % linespec, lineobj.text):
        #        retval.append(lineobj)
        #    else:
                # No regexp match case
        #        pass
        #return retval

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

    ## Removed 20140202
    #def _find_child_OBJ(self, lineobject):
    #    """SEMI-PRIVATE: Takes a single object and returns a list of immediate
    #    children"""
    #    retval = lineobject.children
    #    return retval

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

    ### Removed 20140202
    #def _find_parent_OBJ(self, lineobject):
    #    """SEMI-PRIVATE: Takes a singe object and returns a list of parent
    #    objects in the correct order"""
    #    retval = set([])
    #    me = lineobject
    #    while (me.parent!=me):
    #        retval.add(me.parent)
    #        me = me.parent
    #    return sorted(retval)

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
    """A custom list to hold IOSCfgLine objects"""
    def __init__(self, data=None, comment_delimiter='!', debug=False, 
        factory=False):
        super(IOSConfigList, self).__init__()

        self._list = list()
        self.DBGFLAG = debug
        self.comment_delimiter = comment_delimiter
        self.factory = factory
        if isinstance(data, list) and (data):
            self._bootstrap_obj_init(data)
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

    def __repr__(self):
        return """<IOSConfigList, comment='%s', conf=%s>""" % (self.comment_delimiter, self._list)

    def _bootstrap_from_text(self):
        ## Ultimate goal: get rid of all reparsing from text... it's very slow
        ## reparse all objects from their text attributes... this is *very* slow
        self._list = self._bootstrap_obj_init(list(map(attrgetter('text'), self._list)))

    def insert_before(self, robj, val, atomic=True):
        ## Insert something before robj
        if isinstance(robj, str):
            raise ValueError

        if isinstance(val, str):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter)
            else:
                obj = IOSCfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii, obj)

        if atomic:
            # Reparse the whole config as a text list
            #     this also calls maintain_obj_sanity()
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    def insert(self, robj, val, atomic=True):
        ## Insert something after robj
        if isinstance(robj, str):
            raise ValueError

        if isinstance(val, str):
            if self.factory:
                obj = ConfigLineFactory(text=val, 
                    comment_delimiter=self.comment_delimiter)
            else:
                obj = IOSCfgLine(text=val, 
                    comment_delimiter=self.comment_delimiter)

        ## FIXME: This shouldn't be required
        self._reassign_linenums()

        ii = self._list.index(robj)
        if not (ii is None):
            ## Do insertion here
            self._list.insert(ii+1, obj)

        if atomic:
            # Reparse the whole config as a text list
            #     this also calls maintain_obj_sanity()
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()


    def append(self, val, atomic=True):
        list_idx = len(self._list)
        self.insert(list_idx, val, atomic)

    def _bootstrap_obj_init(self, text_list=[]):
        """Accept a text list and format into proper objects"""
        # Append text lines as IOSCfgLine objects...
        tmp = list()
        for idx, line in enumerate(text_list):
            # Reject empty lines
            if line.strip()=='':
                continue
            if not self.factory:
                obj          = IOSCfgLine(line, self.comment_delimiter)
            else:
                obj = ConfigLineFactory(line, self.comment_delimiter)

            obj.confobj  = self
            obj.linenum  = idx
            obj.indent   = len(line) - len(line.lstrip())

            tmp.append(obj)

        self._list = tmp
        self.maintain_obj_sanity()
        return tmp

    def maintain_obj_sanity(self):
        ## call maintain_obj_sanity() after we finish inserting new stuff...

        self._link_firstchildren_to_parent()
        self._find_orphans()
        ## Make adjustments to the IOS banners because these currently show up
        ##  as individual lines, instead of a parent / child relationship.
        ##  This means finding each banner statement, and associating the
        ##  subsequent lines as children.
        self._mark_banner("login", "ios")
        self._mark_banner("motd", "ios")
        self._mark_banner("exec", "ios")
        self._mark_banner("incoming", "ios")
        self._mark_banner("motd", "catos")
        self._mark_banner("telnet", "catos")
        self._mark_banner("lcd", "catos")

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

    def _link_firstchildren_to_parent(self, DBGFLAG=False):
        ## Walk through the config and look for the "first" child
        parent_indent = None 
        for obj in self.iter_with_comments():
            if (parent_indent is None):
                parent_indent = obj.indent

            if DBGFLAG or self.DBGFLAG:
                print("_link_firstchildren_to_parent:\n  finding children of PARENT: %s\n" % repr(obj))

            # Determine if this is the "first" child...
            #   Note: other children will be orphaned until we walk the
            #   config again.
            if (obj.indent > parent_indent):
                # child is indented more, so this is a child

                if DBGFLAG or self.DBGFLAG:
                    ## Ignore pylint warnings here
                    print("       Attaching CHILD Line #%s: '%s'\n   to 'PARENT: %s" % (obj.linenum, obj.text, parent_obj.text))

                # Add child to the parent's object
                parent_obj.add_child(obj)
                if (parent_indent==0):
                    parent_obj.oldest_ancestor = True
                # Add parent to the child's object
                obj.add_parent(parent_obj)

            ## These must be the statements in the loop
            parent_obj = obj
            parent_indent = obj.indent

    def _find_orphans(self, DBGFLAG=False):
        ## Look for orphaned children, these SHOULD be indented the same
        ##  number of spaces as the "first" child.  However, we must only
        ##  look inside our "extended family"

        for obj in self.all_parents:
            if (DBGFLAG is True):
                print("_find_orphans: Parent  : %s" % repr(obj))
                print("_find_orphans: Children:\n      %s" % \
                    [repr(ii) for ii in obj.children])

            if (obj.oldest_ancestor is True):
                # Look for immediate children
                self._id_unknown_children(obj)
                ## this SHOULD find all other children in the family...
                candidate_children = list()
                for cobj in obj.children:
                    candidate_children.append(cobj)
                for cobj in candidate_children:
                    if self._id_unknown_children(cobj):
                        # Appending any new children to candidate_children as
                        #  we find new children
                        for new in cobj.children:
                            candidate_children.append(new)

    def _mark_banner(self, banner_str, os):
        """Identify all multiline entries matching the mlinespec (this is
        typically used for banners).  Associate parent / child relationships,
        as well setting the oldest_ancestor."""
        ## mlinespec must be in the form:
        ##  ^banner\slogin\.+?(\^\S*)
        ##
        ##   Note: the text in parenthesis will be used as the multiline-end
        ##         delimiter
        start_banner = False
        end_banner = False
        ii = 0
        if (os=="ios"):
            prefix = ""
        elif (os=="catos"):
            prefix = "set "
        else:
            raise RuntimeError("FATAL: _mark_banner(): received " + \
                "an invalid value for 'os'")
        while (start_banner is False) & (ii < len(self._list)):
            if re.search(prefix+"banner\s+"+banner_str+"\s+\^\S+", \
                self._list[ii].text):
                # Found the start banner at ii
                start_banner = True
                kk = ii + 1
            else:
                ii += 1

        if (start_banner is True):
            while (end_banner is False) & (kk < len(self._list)):
                if  self._list[kk].is_comment:
                    # Note: We are depending on a "!" after the banner... why
                    #       can't a normal regex work with IOS banners!?
                    #       Therefore the endpoint is at ( kk - 1)


                    ## Debugging only...
                    # print "found endpoint: line %s, text %s" % \
                    #    (kk - 1, self.ioscfg[kk - 1])
                    #
                    # Set oldest_ancestor on the parent
                    self._list[ii].oldest_ancestor = True
                    for mm in range(ii + 1, (kk)):
                        # Associate parent with the child
                        self._list[ii].add_child(self._list[mm])
                        # Associate child with the parent
                        self._list[mm].add_parent(self._list[ii])
                    end_banner = True
                else:
                    kk += 1
        # Return our success or failure status
        return end_banner

    def _id_unknown_children(self, obj, DBGFLAG=False):
        """Walk through the configuration and look for configuration child
        lines that have not already been identified"""
        found_unknown_child = False
        parent_indent = obj.indent
        child_indent  = obj.child_indent
        # more_children is False once the parent finds one of his siblings
        more_children = True

        if DBGFLAG or self.DBGFLAG:
            print("_id_unknown_children():")
            print("Parent       : %s" % obj.verbose)

        ## If I want to catch all child comments, use iter_with_comments()
        for iiobj in self.iter_no_comments(obj.linenum + 1):
            if DBGFLAG or self.DBGFLAG:
                print("   Line #%s is child? '%s'" % (iiobj.linenum, 
                    iiobj.text))

            if (iiobj.indent==0):
                # Cannot be a child with no indent
                return False

            elif (iiobj.indent==child_indent) and more_children:
                # we have found a potential orphan... also could be the
                #  first child
                iiobj.add_parent(obj)
                found_unknown_child = obj.add_child(iiobj)
                if DBGFLAG or self.DBGFLAG:
                    if (found_unknown_child is True):
                        print("    YES, adding unknown child to Line #%s" % obj.linenum) 

            elif (iiobj.indent==parent_indent):
                return found_unknown_child

        return found_unknown_child

    def _id_family_endpoint(self, obj):
        """This method can start with any child object, and traces through its
        parents to the oldest_ancestor.  When it finds the oldest_ancestor, it
        looks for the family_endpoint attribute."""
        for tobj in self.iter_no_comments(obj.linenum):
            if (tobj.family_endpoint>0) and \
                (tobj.parent.oldest_ancestor is True):
                return tobj.family_endpoint

        if (tobj.linenum==self.last_index):
            # FATAL: we searched to the end of the configuration and did not
            #  find a valid family endpoint.  This is bad, there is something
            #  wrong with IOSCfgLine relationships if you get this message.
            raise RuntimeError("FATAL: Could not resolve family " + \
                "endpoint while starting from configuration line " + \
                "number %s" % tobj.linenum)
        else:
            raise RuntimeError("FATAL: Found invalid family_endpoint " + \
                "while considering: %s. Validate IOSCfgLine relationships" %\
                repr(obj))

    def _mark_family_endpoints(self, parents):
        """Find the endpoint of the config 'family'
        A family starts when a config line with *no* indentation spawns
        'children'. A family ends when there are no more children.  See class
        IOSCfgLine for an example. This method modifies attributes inside 
        IOSCfgLine instances"""
        if self.DBGFLAG:
            print("_mark_family_endpoints:\n  finding children of PARENTS: %s\n" % parents)
        lastobj = self # so pylint won't complain
        for parent in parents:
            if self.DBGFLAG:
                print("   Finding family_endpoint for: Line #%s: '%s'" % (parent.linenum, parent.text))

            if (parent.indent==0) and parent.has_children:
                # we are at the oldest ancestor
                parent.oldest_ancestor = True

                # start searching for the family endpoint
                in_family = False
                for obj in self.iter_no_comments(parent.linenum):
                    if in_family and (obj.indent==0):
                        if self.DBGFLAG:
                            # Ignore pylint warnings here
                            print("      ID family_endpoint: Line #%s: '%s'" % (lastobj.linenum, lastobj.text))
                        in_family = False
                        break
                    elif obj.indent>0:
                        if self.DBGFLAG:
                            print("      Inside family: Line #%s: '%s'" % (obj.linenum, obj.text))
                        in_family = True
                    lastobj = obj
                    # Special case if we cycle through the config and don't
                    # find an endpoint. It usually happens if CiscoConfParse
                    # is called with an array containing a single interface
                    # config stanza and no "end" statement
                else:
                    if self.DBGFLAG:
                        print("      No family_endpoint for: Line #%s: '%s'" % (parent.linenum, parent.text))
                if in_family:
                    if self.DBGFLAG:
                        print("      ID family_endpoint: Line #%s: %s" % (obj.linenum, obj.text))

    @property
    def text_lines(self):
        return [str(obj) for obj in self._list] 

    @property
    def all_parents(self):
        return [obj for obj in self._list if obj.has_children]

    @property
    def last_index(self):
        return (self.__len__()-1)



class CiscoPassword(object):

    def __init__(self):
        self

    def decrypt(self, ep):
        """Cisco Type 7 password decryption.  Converted from perl code that was
        written by jbash [~at~] cisco.com"""

        xlat = (0x64, 0x73, 0x66, 0x64, 0x3b, 0x6b, 0x66, 0x6f, 0x41, 0x2c,
                    0x2e, 0x69, 0x79, 0x65, 0x77, 0x72, 0x6b, 0x6c, 0x64, 0x4a,
                    0x4b, 0x44, 0x48, 0x53, 0x55, 0x42)

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
                if s <= 25:
                    # Algorithm appears unpublished after s = 25
                    newchar = "%c" % (magic ^ int(xlat[int(s)]))
                else:
                    newchar = "?"
                dp = dp + str(newchar)
                s = s + 1
        if s > 25:
            print("WARNING: password decryption failed.")
        return dp

def ConfigLineFactory(text="", comment_delimiter="!", syntax='ios'):
    # Complicted & Buggy
    #classes = [j for (i,j) in globals().iteritems() if isinstance(j, TypeType) and issubclass(j, BaseCfgLine)]

    ## Manual and simple
    classes = [IOSIntfLine, IOSRouteLine, IOSAccessLine,
        IOSHostnameLine, IOSInterfaceGlobal, IOSCfgLine]  # This is simple
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
