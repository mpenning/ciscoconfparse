#!/usr/bin/env python

import sys
import re
import os

""" ciscoconfparse.py - Parse & Query IOS-style configurations
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
        <CiscoConfParse: 2 lines / comment delimiter: '!'>
        >>> p.ConfigObjs
        {0: <IOSCfgLine # 0 'logging trap debugging' (child_indent: 0 / family_endpoint: 0)>, 1: <IOSCfgLine # 1 'logging 172.28.26.15' (child_indent: 0 / family_endpoint: 0)>}
        >>>
    """

    DBGFLAG = False

    def __init__(self, config="", comment="!"):
        """Initialize the class, read the config, and spawn the parser"""

        # Dictionary mapping line number to objects
        self.ConfigObjs = dict()
        # List of all parent objects
        self.allparentobjs = list()
        self.comment_delimiter = comment
        self.comment_regex = self._build_comment_regex(comment)

        if isinstance(config, list):
            # we already have a list object, simply call the parser
            ioscfg = config
            self._parse(ioscfg)
        elif isinstance(config, str):
            try:
                # string - assume a filename... open file, split and parse
                f = open(config)
                text = f.read()
                rgx = re.compile("\r*\n+")
                ioscfg = rgx.split(text)
                self._parse(ioscfg)
            except IOError:
                print("FATAL: CiscoConfParse could not open '%s'" % config)
                raise RuntimeError
        else:
            raise RuntimeError("FATAL: CiscoConfParse() received" + \
                " an invalid argument\n")

    def __repr__(self):
        return "<CiscoConfParse: %s lines / comment delimiter: '%s'>" % (len(self.ioscfg), self.comment_delimiter)

    def _parse(self, ioscfg):
        """Iterate over the configuration and generate a linked 
        structure of IOS commands.
        """
        DBGFLAG = False
        self.ioscfg = ioscfg   # ioscfg is a text list
        # Dictionary mapping line number to objects
        self.ConfigObjs = dict()
        # List of all parent objects
        self.allparentobjs = list()
        ## Generate a (local) indentation list
        indentation = list()
        for ii, cfg_line in enumerate(self.ioscfg):
            # indentation[ii] is the number of leading spaces in the line
            indent_level = len(cfg_line) - len(cfg_line.lstrip())
            indentation.append(indent_level)
            # Build an IOSCfgLine object for each line, associate with a
            # config dictionary
            lineobject        = IOSCfgLine(ii)
            lineobject.text   = cfg_line
            lineobject.indent = indent_level
            self.ConfigObjs[ii] = lineobject
        ## Walk through the config and look for the "first" child
        for ii, cfg_line in enumerate(self.ioscfg):
            # skip any IOS config comments
            if (not re.search("^\s*" + self.comment_regex, cfg_line)):
                current_indent = indentation[ii]
                # Determine if this is the "first" child...
                #   Note: other children will be orphaned until we walk the
                #   config again.
                if ((ii+1) < len(self.ioscfg)):
                    # Note below that ii is the PARENT's line number
                    if (indentation[ii+1] > current_indent):
                        # higher indentation, so we found a child...
                        childobj = self.ConfigObjs[ii+1]
                        if(not re.search(self.comment_regex, self.ioscfg[ii+1])):
                            if DBGFLAG or self.DBGFLAG:
                                print("parse:\n   Attaching CHILD:'%s'\n   " +\
                                    "to 'PARENT:%s'" % \
                                    (childobj.text, self.ConfigObjs[ii].text))
                            # Add child to the parent's object
                            lineobject = self.ConfigObjs[ii]
                            lineobject.add_child(childobj)
                            if (current_indent==0):
                                lineobject.assert_oldest_ancestor()
                            self.allparentobjs.append(lineobject)
                            # Add parent to the child's object
                            childobj.add_parent(self.ConfigObjs[ii])
        ## Look for orphaned children, these SHOULD be indented the same
        ##  number of spaces as the "first" child.  However, we must only
        ##  look inside our "extended family"
        self._mark_family_endpoints(self.allparentobjs, indentation)
        for lineobject in self.allparentobjs:
            if (DBGFLAG is True):
                print("parse: Parent  : %s" % lineobject.text)
                print("parse: Children:\n      %s" % \
                    self._objects_to_lines(lineobject.children))
            if (lineobject.indent==0):
                # Look for immediate children
                self._id_unknown_children(lineobject, indentation)
                ## this SHOULD find all other children in the family...
                candidate_children = list()
                for child in lineobject.children:
                    candidate_children.append(child)
                for child in candidate_children:
                    if self._id_unknown_children(child, indentation):
                        # Appending any new children to candidate_children as
                        #  we find new children
                        for new in child.children:
                            candidate_children.append(new)
        ## Make adjustments to the IOS banners because these currently show up
        ##  as individual lines, instead of a parent / child relationship.  i
        ##  This means finding each banner statement, and associating the
        ##  subsequent lines as children.
        self._mark_banner("login", "ios", indentation)
        self._mark_banner("motd", "ios", indentation)
        self._mark_banner("exec", "ios", indentation)
        self._mark_banner("incoming", "ios", indentation)
        self._mark_banner("motd", "catos", indentation)
        self._mark_banner("telnet", "catos", indentation)
        self._mark_banner("lcd", "catos", indentation)

    def _mark_banner(self, banner_str, os, indentation):
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
        while (start_banner is False) & (ii < len(self.ioscfg)):
            if re.search(prefix+"banner\s+"+banner_str+"\s+\^\S+", \
                self.ioscfg[ii]):
                # Found the start banner at ii
                start_banner = True
                kk = ii + 1
            else:
                ii += 1
        if (start_banner is True):
            while (end_banner is False) & (kk < len(self.ioscfg)):
                if re.search("^\s*" + self.comment_regex, self.ioscfg[kk]):
                    # Note: We are depending on a "!" after the banner... why
                    #       can't a normal regex work with IOS banners!?
                    #       Therefore the endpoint is at ( kk - 1)


                    ## Debugging only...
                    # print "found endpoint: line %s, text %s" % \
                    #    (kk - 1, self.ioscfg[kk - 1])
                    #
                    # Set oldest_ancestor on the parent
                    self.ConfigObjs[ii].assert_oldest_ancestor()
                    for mm in range(ii + 1, (kk)):
                        # Associate parent with the child
                        self.ConfigObjs[ii].add_child(self.ConfigObjs[mm])
                        # Associate child with the parent
                        self.ConfigObjs[mm].add_parent(self.ConfigObjs[ii])
                    end_banner = True
                else:
                    kk += 1
        # Return our success or failure status
        return end_banner

    def _fix_multiline_entries(self, re_code, indentation):
        """Identify all multiline entries matching the mlinespec (this is
        typically used for banners).  Associate parent / child relationships,
        as well setting the oldest_ancestor."""
        ##
        ## Note: I wanted this to work for banners, but have never figured out
        ##       how to make the re_compile code set re_code.group(1).
        ##       Right now, I'm using _mark_banner()
        ##
        ## re_code should be a lambda function such as:
        ##  re.compile("^banner\slogin\.+?(\^\S*)"
        ##  The text in parenthesis will be used as the multiline-end delimiter
        for ii,line in enumerate(self.ioscfg):
            ## submitted code will pass a compiled regular expression
            result = re_search(line)
            if re_code.search(line):
                end_string = result.re_code.group(1)
                print("Got end_string = %s" % end_string)
                for kk in range((ii + 1), len(self.ioscfg)):
                    if not (re.search(end_string, ioscfg[kk]) is None):
                        print("found endpoint: %s" % ioscfg[kk])
                        # Set the parent attributes
                        self.ConfigObjs[ii].assert_oldest_ancestor()
                        for mm in range(ii + 1, (kk + 1)):
                            # Associate parent with the child
                            self.ConfigObjs[ii].add_child(self.ConfigObjs[mm])
                            # Associate child with the parent
                            self.ConfigObjs[mm].add_parent(\
                                self.ConfigObjs[ii])

    def _id_unknown_children(self, lineobject, indentation):
        """Walk through the configuration and look for configuration child
        lines that have not already been identified"""
        found_unknown_child = False
        parent_indent = lineobject.indent
        child_indent  = lineobject.child_indent
        # more_children is False once the parent finds one of his siblings
        more_children = True
        DBGFLAG = False
        if DBGFLAG or self.DBGFLAG:
            print("Parent       : %s" % self.ioscfg[lineobject.linenum])
        for ii in range(lineobject.linenum + 1, \
            self._id_family_endpoint(lineobject, len(self.ioscfg))):
            if DBGFLAG or self.DBGFLAG:
                print("       C?    : %s" % self.ioscfg[ii])
            if not re.search("^\s*" + self.comment_regex, self.ioscfg[ii]):
                if (indentation[ii]==parent_indent):
                    more_children = False
                if (indentation[ii]==child_indent) and more_children:
                    # we have found a potential orphan... also could be the
                    #  first child
                    self.ConfigObjs[ii].add_parent(lineobject)
                    found_unknown_child = lineobject.add_child(self.ConfigObjs[ii])
                    if DBGFLAG or self.DBGFLAG:
                        if (found_unknown_child is True):
                            print("    New child: %s" % self.ioscfg[ii])
        return found_unknown_child

    def _id_family_endpoint(self, lineobject, last_cfg_line):
        """This method can start with any child object, and traces through its
        parents to the oldest_ancestor.  When it finds the oldest_ancestor, it
        looks for the family_endpoint attribute."""
        ii = 0
        source_linenum = lineobject.linenum
        while (ii<last_cfg_line) & (lineobject.oldest_ancestor is False):
            # Find the parent, try again...
            lineobject = lineobject.parent
            ii += 1
        if (ii==last_cfg_line):
            # FATAL: we searched to the end of the configuration and did not
            #  find a valid family endpoint.  This is bad, there is something
            #  wrong with IOSCfgLine relationships if you get this message.
            raise RuntimeError("FATAL: Could not resolve family " + \
                "endpoint while starting from configuration line " + \
                "number %s" % source_linenum)
        if (lineobject.family_endpoint>0):
            return lineobject.family_endpoint
        else:
            raise RuntimeError("FATAL: Found invalid family endpoint " + \
                "while considering: '%s'  Validate IOSCfgLine relationships" %\
                self.ioscfg[lineobject.linenum])

    def _mark_family_endpoints(self, parents, indentation):
        """Find the endpoint of the config 'family'
        A family starts when a config line with *no* indentation spawns
        'children'. A family ends when there are no more children.  See class
        IOSCfgLine for an example. This method modifies attributes inside 
        IOSCfgLine instances"""
        for parent in parents:
            ii = parent.linenum
            if (parent.indent==0):
                # we are at the oldest ancestor
                parent.assert_oldest_ancestor()
                # start searching for the family endpoint
                ii += 1
                # reject endpoints in IOS comments
                if not re.search("^\s*" + self.comment_regex, self.ioscfg[ii]):
                    found_endpoint = False
                    while (not found_endpoint) and (ii<len(indentation)):
                        if indentation[ii] == 0:
                            found_endpoint = True
                            ## Fixed a bug below... used to set it to ii
                            parent.set_family_endpoint(ii)
                        else:
                            ii += 1
                    # Special case if we cycle through the config and don't
                    # find an endpoint. It usually happens if CiscoConfParse
                    # is called with an array containing a single interface
                    # config stanza and no "end" statement
                    if (found_endpoint is False):
                        parent.set_family_endpoint(ii)

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

        for line in self.ioscfg:
            if (exactmatch is False):
                if re.search(linespec, line):
                    retval.append(line)
            else:
                if re.search("^%s$" % linespec, line):
                    retval.append(line)
        return retval

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
                childobjs = self._find_child_OBJ(parent)
                for child in childobjs:
                    allobjs.add(child)
            allobjs.add(parent)
        #allobjs = self._unique_OBJ(allobjs)
        retval = self._objects_to_lines(sorted(allobjs))

        return retval

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

        if exactmatch == False:
            parentobjs = self._find_line_OBJ(linespec)
        else:
            parentobjs = self._find_line_OBJ("^%s$" % linespec)
        allobjs = list()
        for parent in parentobjs:
            if (parent.has_children is True):
                childobjs = self._find_all_child_OBJ(parent)
                for child in childobjs:
                    allobjs.append(child)
            allobjs.append(parent)
        allobjs = self._unique_OBJ(allobjs)
        retval = self._objects_to_lines(allobjs)

        return retval

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
        dct = dict()
        retval = list()

        if ignore_ws:
            linespec = self._build_space_tolerant_regex(linespec)

        # Find line objects maching the spec
        if (exactmatch is False):
            lines = self._find_line_OBJ(linespec)
        else:
            lines = self._find_line_OBJ("^%s$" % linespec)
        for line in lines:
            dct[line.linenum] = line
            # Find the siblings of this line
            alist = self._find_sibling_OBJ(line)
            for this in alist:
                dct[this.linenum] = this
        # Find the parents for everything
        for (line, lineobject) in list(dct.items()):
            alist = self._find_parent_OBJ(lineobject)
            for this in alist:
                dct[this.linenum] = this
        for ii in sorted(dct.keys()):
            retval.append(self.ioscfg[ii])

        return retval

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

        retval = list()
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = self._find_parent_OBJ(child)
            match_parentspec = False
            for parent in parents:
                #if re.search(parentspec, self.ioscfg[parent.linenum]):
                if re.search(parentspec, parent.text):
                    match_parentspec = True
            if (match_parentspec is True):
                for parent in parents:
                    retval.append(parent)
        retval = self._unique_OBJ(retval)
        retval = self._objects_to_lines(retval)

        return retval

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

        retval = list()
        ## Iterate over all parents, find those with non-matching children
        for parentobj in self.allparentobjs:
            if (parentobj.oldest_ancestor is True):
                #if re.search(parentspec, self.ioscfg[parentobj.linenum]):
                if re.search(parentspec, parentobj.text):
                    ## Now determine whether the child matches
                    match_childspec = False
                    childobjs = self._find_child_OBJ(parentobj)
                    for childobj in childobjs:
                        #if re.search(childspec, self.ioscfg[childobj.linenum]):
                        if re.search(childspec, childobj.text):
                            match_childspec = True
                    if (match_childspec is False):
                        ## We found a parent without a child matching the
                        ##    childspec
                        retval.append(parentobj)
        retval = self._objects_to_lines(self._unique_OBJ(retval))

        return retval

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

        retval = list()
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = self._find_parent_OBJ(child)
            match_parentspec = False
            for parent in parents:
                #if re.search(parentspec, self.ioscfg[parent.linenum]):
                if re.search(parentspec, parent.text):
                    retval.append(child)

        retval = self._unique_OBJ(retval)
        retval = self._objects_to_lines(retval)

        return retval

    def replace_lines(self, linespec, replacestr, excludespec=None, exactmatch=False):
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
        for obj in self._find_line_OBJ(linespec, exactmatch=exactmatch):

            if excludespec and re.search(excludespec, obj.text):
                # Exclude replacements on lines which match excludespec
                continue

            # FIXME
            # Due to the way I originally implemented ciscoconfparse as 
            # a python novice, I also have to *manually* replace the same 
            # line in self.ioscfg
            self.ioscfg[obj.linenum] = obj.replace(linespec, replacestr)
            retval.append(obj.text)

        return retval

    def replace_children(self, parentspec, childspec, replacestr, 
        excludespec=None, exactmatch=False):
        """Replace lines matching `childspec` within the immediate children of lines which match `parentspec`"""
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and re.search(excludespec, pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in self._find_child_OBJ(pobj):
                if excludespec and re.search(excludespec, cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif re.search(childspec, cobj.text):
                    # FIXME
                    # Due to the way I originally implemented ciscoconfparse as 
                    # a python novice, I also have to *manually* replace the 
                    # same line in self.ioscfg
                    self.ioscfg[cobj.linenum] = cobj.replace(childspec, 
                        replacestr)
                    retval.append(cobj.text)
                else:
                    pass
        return retval

    def replace_all_children(self, parentspec, childspec, replacestr, 
        excludespec=None, exactmatch=False):
        """Replace lines matching `childspec` within all children (recursive) of lines whilch match `parentspec`"""
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and re.search(excludespec, pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in self._find_all_child_OBJ(pobj):
                if excludespec and re.search(excludespec, cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif re.search(childspec, cobj.text):
                    # FIXME
                    # Due to the way I originally implemented ciscoconfparse as 
                    # a python novice, I also have to *manually* replace the 
                    # same line in self.ioscfg
                    self.ioscfg[cobj.linenum] = cobj.replace(childspec, 
                        replacestr)
                    retval.append(cobj.text)
                else:
                    pass
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
            parent_objs = self._find_parent_OBJ(vobj)
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
    ###  or list of objects instead of the configuration text itself.

    def _build_space_tolerant_regex(self, linespec):
        """SEMI-PRIVATE: Accept a string, and return a string with all
        spaces replaced with '\s+'"""

        # Unicode below
        backslash = '\x5c'

        linespec = re.sub('\s+', backslash+"s+", linespec)

        return linespec

    def _build_comment_regex(self, comment):
        """Accept a string, and return a string joined with a |"""
        comment_regex = "|".join(comment)
        return comment_regex


    def _find_line_OBJ(self, linespec, exactmatch=False):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""
        retval = list()
        for lineobj in list(self.ConfigObjs.values()):
            if not exactmatch and re.search(linespec, lineobj.text):
                retval.append(lineobj)
            elif exactmatch and re.search("^%s$" % linespec, lineobj.text):
                retval.append(lineobj)
            else:
                # No regexp match case
                pass
        return retval

    def _find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    def _find_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of immediate
        children"""
        retval = lineobject.children
        return retval

    def _find_all_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of
        decendants in all 'children' / 'grandchildren' / etc... after it.
        It should NOT return the children of siblings"""
        # sort the list, and get unique objects
        retval = self._unique_OBJ(lineobject.children)
        for candidate in retval:
            if (len(candidate.children)>0):
                for child in candidate.children:
                    retval.append(child)
        retval = self._unique_OBJ(retval)  # ensure there are no duplicates,
                                           # belt & suspenders style
        return retval

    def _find_parent_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of parent
        objects in the correct order"""
        retval = set([])
        me = lineobject
        while (me.parent!=me):
            retval.add(me.parent)
            me = me.parent
        return sorted(retval)

    def _unique_OBJ(self, objectlist):
        """SEMI-PRIVATE: Returns a list of unique objects (i.e. with no
        duplicates).
        The returned value is sorted by configuration line number
        (lowest first)"""
        retval = set([])
        for obj in objectlist:
            retval.add(obj)
        return sorted(retval)

    def _objects_to_lines(self, objectlist):
        """SEMI-PRIVATE: Accept a list of objects and return a list of lines.
        NOTE: The lines will NOT be reordered by this method.  Always call
        _unique_OBJ() before this method."""
        retval = list()
        for obj in objectlist:
            retval.append(obj.text)
        return retval

    def _objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = list()
        unconfdict = dict()
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self._unique_OBJ(objectlist):
            if (unconfdict[obj]=="DEFINED"):
                retval.append(obj.uncfgtext)
            else:
                retval.append(obj.text)
        return retval

class IOSCfgLine(object):
    """Manage IOS Config line parent / child relationships"""
    ### Example of family relationships
    ###
    #Line01:policy-map QOS_1
    #Line02: class GOLD
    #Line03:  priority percent 10
    #Line04: class SILVER
    #Line05:  bandwidth 30
    #Line06:  random-detect
    #Line07: class default
    #Line08:!
    #Line09:interface Serial 1/0
    #Line10: encapsulation ppp
    #Line11: ip address 1.1.1.1 255.255.255.252
    #Line12:!
    #Line13:access-list 101 deny tcp any any eq 25 log
    #Line14:access-list 101 permit ip any any
    #
    # parents: 01, 02, 04, 09
    # children: of 01 = 02, 04, 07
    #           of 02 = 03
    #           of 04 = 05, 06
    #           of 09 = 10, 11
    # siblings: 05 and 06
    #           10 and 11
    # oldest_ancestors: 01, 09
    # families: 01, 02, 03, 04, 05, 06, 07
    #           09, 10, 11
    # family_endpoints: 07, 11
    #

    def __init__(self, linenum):
        """Accept an IOS line number and initialize family relationship
        attributes"""
        self.linenum = linenum
        self.parent = self
        self.text = ""
        self.child_indent = 0
        self.children = list()
        self.has_children = False
        self.oldest_ancestor = False
        self.family_endpoint = 0
        self.indent = 0            # Whitespace indentation on the object

    def __repr__(self):
        return "<IOSCfgLine # %s '%s' (child_indent: %s / family_endpoint: %s)>" % (self.linenum, self.text, self.child_indent, self.family_endpoint)

    def __eq__(self, val):
        if (self.linenum==val.linenum):
            return True
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
        # Ref: http://stackoverflow.com/a/7152650/667301
        return hash(repr(self))

    def add_parent(self, parentobj):
        ## In a perfect world, I would check parentobj's type
        ##     with isinstance(), but I'm not ready to take the perf hit
        self.parent = parentobj
        return True

    def add_child(self, childobj):
        ## In a perfect world, I would check childobj's type
        ##     with isinstance(), but I'm not ready to take the perf hit
        ##
        ## Add the child, unless we already know it
        if not (childobj in self.children):
            self.children.append(childobj)
            self.child_indent = childobj.indent
            self.has_children = True
            return True
        else:
            return False

    def add_uncfgtext(self, unconftext):
        ## remove any preceeding "no "
        conftext = re.sub("\s*no\s+", "", unconftext)
        myindent = self.parent.child_indent
        self.uncfgtext = myindent * " " + "no " + conftext

    def assert_oldest_ancestor(self):
        self.oldest_ancestor = True

    def set_family_endpoint(self, endpoint):
        # SHOULD only be set non-zero on an oldest_ancestor
        self.family_endpoint = endpoint

    def parent(self):
        return self.parent

    def children(self):
        return self.children

    def has_children(self):
        return self.has_children

    def child_indent(self):
        return self.child_indent

    def oldest_ancestor(self):
        return self.oldest_ancestor

    def family_endpoint(self):
        return self.family_endpoint

    def linenum(self):
        return self.linenum

    def uncfgtext(self):
        """unconftext is defined during special method calls.  Do not assume it
        is automatically populated."""
        return self.uncfgtext

    def replace(self, linespec, replacestr):
        self.text = re.sub(linespec, replacestr, self.text)
        return self.text

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
        sys.exit(1)
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
        sys.exit(1)
    else:
        import doctest
        doctest.testmod()
        sys.exit(0)

    if len(diff) > 0:
        for line in diff:
            print(line)
    else:
        raise RuntimeError("FATAL: ciscoconfparse was called with unknown" + \
            " parameters")
