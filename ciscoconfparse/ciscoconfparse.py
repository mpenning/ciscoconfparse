#!/usr/bin/env python

import sys
import re
import os

""" ciscoconfparse.py - Parse & Query IOS-style configurations
     Copyright (C) 2007-2009 David Michael Pennington

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
    """Parses Cisco IOS configurations and answers queries about the configs"""

    DBGFLAG = False

    def __init__(self, config="", comment="!"):
        """Initialize the class, read the config, and spawn the parser"""
        self.comment_regex = self.build_comment_regex(comment)
        if type(config) == type(['a', 'b']):
            # we already have a list object, simply call the parser
            ioscfg = config
            self.parse(ioscfg)
        elif type(config) == type("ab"):
            try:
                # string - assume a filename... open file, split and parse
                f = open(config)
                text = f.read()
                rgx = re.compile("\r*\n+")
                ioscfg = rgx.split(text)
                self.parse(ioscfg)
            except IOError:
                print "FATAL: CiscoConfParse could not open '%s'" % config
                raise RuntimeError
        else:
            raise RuntimeError("FATAL: CiscoConfParse() received" + \
                " an invalid argument\n")

    def parse(self, ioscfg):
        """Iterate over the configuration and generate a linked list of IOS
        commands."""
        DBGFLAG = False
        self.ioscfg = ioscfg
        # Dictionary mapping line number to objects
        self.lineObjDict = {}
        # List of all parent objects
        self.allparentobjs = []
        ## Generate a (local) indentation list
        indentation = []
        for ii in range(len(self.ioscfg)):
            # indentation[ii] is the number of leading spaces in the line
            indentation.append(len(self.ioscfg[ii]) - \
                len(self.ioscfg[ii].lstrip()))
            # Build an IOSCfgLine object for each line, associate with a
            # config dictionary
            lineobject = IOSCfgLine(ii)
            lineobject.add_text(self.ioscfg[ii])
            self.lineObjDict[ii] = lineobject
        ## Walk through the config and look for the "first" child
        for ii in range(len(self.ioscfg)):
            # skip any IOS config comments
            if (not re.search("^\s*" + self.comment_regex, self.ioscfg[ii])):
                current_indent = indentation[ii]
                # Determine if this is the "first" child...
                #   Note: other children will be orphaned until we walk the
                #   config again.
                if ((ii + 1) < len(self.ioscfg)):
                    # Note below that ii is the PARENT's line number
                    if (indentation[ii + 1] > current_indent):
                        if(not re.search(self.comment_regex, \
                            self.ioscfg[ii + 1])):
                            if DBGFLAG or self.DBGFLAG:
                                print "parse:\n   Attaching CHILD:'%s'\n   " +\
                                    "to 'PARENT:%s'" % \
                                    (self.lineObjDict[ii + 1].text, \
                                    self.lineObjDict[ii].text)
                            # Add child to the parent's object
                            lineobject = self.lineObjDict[ii]
                            lineobject.add_child(self.lineObjDict[ii + 1], \
                                indentation[ii + 1])
                            if current_indent == 0:
                                lineobject.assert_oldest_ancestor()
                            self.allparentobjs.append(lineobject)
                            # Add parent to the child's object
                            lineobject = self.lineObjDict[ii + 1]
                            lineobject.add_parent(self.lineObjDict[ii])
        ## Look for orphaned children, these SHOULD be indented the same
        ##  number of spaces as the "first" child.  However, we must only
        ##  look inside our "extended family"
        self.mark_family_endpoints(self.allparentobjs, indentation)
        for lineobject in self.allparentobjs:
            if DBGFLAG == True:
                print "parse: Parent  : %s" % lineobject.text
                print "parse: Children:\n      %s" % \
                    self.objects_to_lines(lineobject.children)
            if indentation[lineobject.linenum] == 0:
                # Look for immediate children
                self.id_unknown_children(lineobject, indentation)
                ## this SHOULD find all other children in the family...
                candidate_children = []
                for child in lineobject.children:
                    candidate_children.append(child)
                for child in candidate_children:
                    if self.id_unknown_children(child, indentation):
                        # Appending any new children to candidate_children as
                        #  we find new children
                        for new in child.children:
                            candidate_children.append(new)
        ## Make adjustments to the IOS banners because these currently show up
        ##  as individual lines, instead of a parent / child relationship.  i
        ##  This means finding each banner statement, and associating the
        ##  subsequent lines as children.
        self.mark_banner("login", "ios", indentation)
        self.mark_banner("motd", "ios", indentation)
        self.mark_banner("exec", "ios", indentation)
        self.mark_banner("incoming", "ios", indentation)
        self.mark_banner("motd", "catos", indentation)
        self.mark_banner("telnet", "catos", indentation)
        self.mark_banner("lcd", "catos", indentation)

    def mark_banner(self, banner_str, os, indentation):
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
        if os == "ios":
            prefix = ""
        elif os == "catos":
            prefix = "set "
        else:
            raise RuntimeError("FATAL: mark_banner(): received " + \
                "an invalid value for 'os'")
        while (start_banner == False) & (ii < len(self.ioscfg)):
            if re.search(prefix+"banner\s+"+banner_str+"\s+\^\S+", \
                self.ioscfg[ii]):
                # Found the start banner at ii
                start_banner = True
                kk = ii + 1
            else:
                ii += 1
        if (start_banner == True):
            while (end_banner == False) & (kk < len(self.ioscfg)):
                if re.search("^\s*" + self.comment_regex, self.ioscfg[kk]):
                    # Note: We are depending on a comment after the banner... 
                    #       why can't a normal regex work with IOS banners!?
                    #       Therefore the endpoint is at ( kk - 1)


                    ## Debugging only...
                    # print "found endpoint: line %s, text %s" % \
                    #    (kk - 1, self.ioscfg[kk - 1])
                    #
                    # Set oldest_ancestor on the parent
                    self.lineObjDict[ii].assert_oldest_ancestor()
                    for mm in range(ii + 1, (kk)):
                        # Associate parent with the child
                        self.lineObjDict[ii].add_child(self.lineObjDict[mm], \
                            indentation[ii])
                        # Associate child with the parent
                        self.lineObjDict[mm].add_parent(self.lineObjDict[ii])
                    end_banner = True
                else:
                    kk += 1
        # Return our success or failure status
        return end_banner

    def fix_multiline_entries(self, re_code, indentation):
        """Identify all multiline entries matching the mlinespec (this is
        typically used for banners).  Associate parent / child relationships,
        as well setting the oldest_ancestor."""
        ##
        ## Note: I wanted this to work for banners, but have never figured out
        ##       how to make the re_compile code set re_code.group(1).
        ##       Right now, I'm using mark_banner()
        ##
        ## re_code should be a lambda function such as:
        ##  re.compile("^banner\slogin\.+?(\^\S*)"
        ##  The text in parenthesis will be used as the multiline-end delimiter
        for ii in range(len(self.ioscfg)):
            ## submitted code will pass a compiled regular expression
            result = re_search(self.ioscfg[ii])
            if re_code.search(self.ioscfg[ii]):
                end_string = result.re_code.group(1)
                print "Got end_string = %s" % end_string
                for kk in range((ii + 1), len(self.ioscfg)):
                    if re.search(end_string, ioscfg[kk]) == True:
                        print "found endpoint: %s" % ioscfg[kk]
                        # Set the parent attributes
                        self.lineObjDict[ii].assert_oldest_ancestor()
                        for mm in range(ii + 1, (kk + 1)):
                            # Associate parent with the child
                            self.lineObjDict[ii].add_child(\
                                self.lineObjDict[mm], indentation[ii])
                            # Associate child with the parent
                            self.lineObjDict[mm].add_parent(\
                                self.lineObjDict[ii])

    def id_unknown_children(self, lineobject, indentation):
        """Walk through the configuration and look for configuration child
        lines that have not already been identified"""
        found_unknown_child = False
        child_indent = lineobject.child_indent
        parent_indent = indentation[lineobject.linenum]
        # more_children is False once the parent finds one of his siblings
        more_children = True
        DBGFLAG = False
        if DBGFLAG or self.DBGFLAG:
            print "Parent       : %s" % self.ioscfg[lineobject.linenum]
        for ii in range(lineobject.linenum + 1, \
            self.id_family_endpoint(lineobject, len(self.ioscfg))):
            if DBGFLAG or self.DBGFLAG:
                print "       C?    : %s" % self.ioscfg[ii]
            if not re.search("^\s*" + self.comment_regex, self.ioscfg[ii]):
                if indentation[ii] == parent_indent:
                    more_children = False
                if (indentation[ii] == child_indent) and more_children:
                    # we have found a potential orphan... also could be the
                    #  first child
                    self.lineObjDict[ii].add_parent(lineobject)
                    found_unknown_child = lineobject.add_child(\
                        self.lineObjDict[ii], indentation[ii])
                    if DBGFLAG or self.DBGFLAG:
                        if found_unknown_child == True:
                            print "    New child: %s" % self.ioscfg[ii]
        return found_unknown_child

    def id_family_endpoint(self, lineobject, last_cfg_line):
        """This method can start with any child object, and traces through its
        parents to the oldest_ancestor.  When it finds the oldest_ancestor, it
        looks for the family_endpoint attribute."""
        ii = 0
        source_linenum = lineobject.linenum
        while (ii < last_cfg_line) & (lineobject.oldest_ancestor == False):
            # Find the parent, try again...
            lineobject = lineobject.parent
            ii += 1
        if ii == last_cfg_line:
            # You have now searched to the end of the configuration and did not
            #  find a valid family endpoint.  This is bad, there is something
            #  wrong with IOSCfgLine relationships if you get this message.
            raise RuntimeError("FATAL: Could not resolve family " + \
                "endpoint while starting from configuration line " + \
                "number %s" % source_linenum)
        if lineobject.family_endpoint > 0:
            return lineobject.family_endpoint
        else:
            raise RuntimeError("FATAL: Found invalid family endpoint " + \
                "while considering: '%s'  Validate IOSCfgLine relationships" %\
                self.ioscfg[lineobject.linenum])

    def mark_family_endpoints(self, parents, indentation):
        """Find the endpoint of the config 'family'
        A family starts when a config line with *no* indentation spawns
        'children'. A family ends when there are no more children.  See class
        IOSCfgLine for an example. This method modifies attributes inside the
        IOSCfgLine class"""
        for parent in parents:
            ii = parent.linenum
            current_indent = indentation[ii]
            if current_indent == 0:
                # we are at the oldest ancestor
                parent.assert_oldest_ancestor()
                # start searching for the family endpoint
                last_line = ii
                ii += 1
                # reject endpoints in IOS comments
                if not re.search("^\s*" + self.comment_regex, self.ioscfg[ii]):
                    found_endpoint = False
                    while (not found_endpoint) and (ii < len(indentation)):
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
                    if found_endpoint == False:
                        parent.set_family_endpoint(ii)

    def find_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """This method is the equivalent of a simple configuration grep
        (Case-sensitive)."""
        retval = []

        if ignore_ws:
            linespec = self.build_space_tolerant_regex(linespec)

        for line in self.ioscfg:
            if exactmatch == False:
                if re.search(linespec, line):
                    retval.append(line)
            else:
                if re.search("^%s$"% linespec, line):
                    retval.append(line)
        return retval

    def find_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and their immediate
        children"""

        if ignore_ws:
            linespec = self.build_space_tolerant_regex(linespec)

        if exactmatch == False:
            parentobjs = self.find_line_OBJ(linespec)
        else:
            parentobjs = self.find_line_OBJ("^%s$" % linespec)
        allobjs = []
        for parent in parentobjs:
            childobjs = self.find_child_OBJ(parent)
            if parent.has_children == True:
                for child in childobjs:
                    allobjs.append(child)
            allobjs.append(parent)
        allobjs = self.unique_OBJ(allobjs)
        retval = self.objects_to_lines(allobjs)

        return retval

    def find_all_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and all their children"""

        if ignore_ws:
            linespec = self.build_space_tolerant_regex(linespec)

        if exactmatch == False:
            parentobjs = self.find_line_OBJ(linespec)
        else:
            parentobjs = self.find_line_OBJ("^%s$" % linespec)
        allobjs = []
        for parent in parentobjs:
            childobjs = self.find_all_child_OBJ(parent)
            if parent.has_children == True:
                for child in childobjs:
                    allobjs.append(child)
            allobjs.append(parent)
        allobjs = self.unique_OBJ(allobjs)
        retval = self.objects_to_lines(allobjs)

        return retval

    def find_blocks(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all siblings matching the linespec, then find all parents of
        those siblings. Return a list of config lines sorted by line number,
        lowest first.  Note: any children of the siblings should NOT be
        returned."""
        dct = {}
        retval = []

        if ignore_ws:
            linespec = self.build_space_tolerant_regex(linespec)

        # Find lines maching the spec
        if exactmatch == False:
            lines = self.find_line_OBJ(linespec)
        else:
            lines = self.find_line_OBJ("^%s$" % linespec)
        for line in lines:
            dct[line.linenum] = line
            # Find the siblings of this line
            alist = self.find_sibling_OBJ(line)
            for this in alist:
                dct[this.linenum] = this
        # Find the parents for everything
        for (line, lineobject) in dct.items():
            alist = self.find_parent_OBJ(lineobject)
            for this in alist:
                dct[this.linenum] = this
        for line in sorted(dct.keys()):
            retval.append(self.ioscfg[line])

        return retval

    def find_parents_w_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all children matching childspec, and return a list of
        parents that matched the parentspec."""

        if ignore_ws:
            parentspec = self.build_space_tolerant_regex(parentspec)
            childspec = self.build_space_tolerant_regex(childspec)

        retval = []
        childobjs = self.find_line_OBJ(childspec)
        for child in childobjs:
            parents = self.find_parent_OBJ(child)
            match_parentspec = False
            for parent in parents:
                if re.search(parentspec, self.ioscfg[parent.linenum]):
                    match_parentspec = True
            if match_parentspec == True:
                for parent in parents:
                    retval.append(parent)
        retval = self.unique_OBJ(retval)
        retval = self.objects_to_lines(retval)

        return retval

    def find_parents_wo_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all parents matching parentspec, and return a list of
        parents that did NOT have children match the childspec.  For
        simplicity, this method only finds oldest_ancestors without immediate
        children that match."""

        if ignore_ws:
            parentspec = self.build_space_tolerant_regex(parentspec)
            childspec = self.build_space_tolerant_regex(childspec)

        retval = []
        ## Iterate over all parents, find those with non-matching children
        for parentobj in self.allparentobjs:
            if parentobj.oldest_ancestor == True:
                if re.search(parentspec, self.ioscfg[parentobj.linenum]):
                    ## Now determine whether the child matches
                    match_childspec = False
                    childobjs = self.find_child_OBJ(parentobj)
                    for childobj in childobjs:
                        if re.search(childspec, self.ioscfg[childobj.linenum]):
                            match_childspec = True
                    if match_childspec == False:
                        ## We found a parent without a child matching the
                        ##    childspec
                        retval.append(parentobj)
        retval = self.objects_to_lines(self.unique_OBJ(retval))

        return retval

    def req_cfgspec_all_diff(self, cfgspec, ignore_ws=False):
        """
        req_cfgspec_all_diff takes a list of required configuration lines,
        parses through the configuration, and ensures that none of cfgspec's
        lines are missing from the configuration.  req_cfgspec_all_diff
        returns a list of missing lines from the config.

        One example use of this method is when you need to enforce routing
        protocol standards, or standards against interface configurations.
        """

        if ignore_ws:
            cfgspec = self.build_space_tolerant_regex(cfgspec)

        skip_cfgspec = {}
        retval = []
        matches = self.find_line_OBJ("[a-zA-Z]")
        ## Make a list of unnecessary cfgspec lines
        for lineobj in matches:
            for reqline in cfgspec:
                if lineobj.text.strip() == reqline.strip():
                    skip_cfgspec[reqline] = "YES"
        ## Add items to be configured
        for line in cfgspec:
            if not skip_cfgspec.has_key(line):
                retval.append(line)

        return retval

    def req_cfgspec_excl_diff(self, linespec, uncfgspec, cfgspec):
        """
        req_cfgspec_excl_diff accepts a linespec, an unconfig spec, and
        a list of required configuration elements.  Return a list of
        configuration diffs to make the configuration comply.  **All** other
        config lines matching the linespec that are *not* listed in the
        cfgspec will be removed with the uncfgspec regex.

        Example uses of this method include the need to enforce syslog, acl, or
        aaa standards.
        """
        violate_objs = []
        uncfg_objs = []
        skip_cfgspec = {}
        retval = []
        matches = self.find_line_OBJ(linespec)
        ## Make a list of lineobject violations
        for lineobj in matches:
            accept_lineobj = False
            for reqline in cfgspec:
                if lineobj.text.strip() == reqline.strip():
                    accept_lineobj = True
                    skip_cfgspec[reqline] = "YES"
            if accept_lineobj == False:
                violate_objs.append(lineobj)
                result = re.search(uncfgspec, lineobj.text)
                # add uncfgtext to the violator's lineobject
                lineobj.add_uncfgtext(result.group(0))
        ## Make the list of unconfig objects
        for vobj in violate_objs:
            parent_objs = self.find_parent_OBJ(vobj)
            for parent_obj in parent_objs:
                uncfg_objs.append(parent_obj)
            uncfg_objs.append(vobj)
        retval = self.objects_to_uncfg(uncfg_objs, violate_objs)
        ## Add items to be configured
        for line in cfgspec:
            if not skip_cfgspec.has_key(line):
                retval.append(line)

        return retval

    ### The methods below are marked SEMI-PRIVATE because they return an object
    ###  or list of objects instead of the configuration text itself.

    def build_space_tolerant_regex(self, linespec):
        """SEMI-PRIVATE: Accept a string, and return a string with all
        spaces replaced with '\s+'"""

        # Unicode below
        backslash = u'\x5c'

        linespec = re.sub('\s+', backslash+"s+", linespec)

        return linespec

    def build_comment_regex(self, comment):
        """PRIVATE: Accept a string, and return a string joined with |"""
        comment_regex = "|".join(comment)
        return comment_regex

    def find_line_OBJ(self, linespec):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""
        retval = []
        for ii in self.lineObjDict:
            if re.search(linespec, self.ioscfg[ii]):
                retval.append(self.lineObjDict[ii])
        return retval

    def find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    def find_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of immediate
        children"""
        retval = lineobject.children
        return retval

    def find_all_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of
        decendants in all 'children' / 'grandchildren' / etc... after it.
        It should NOT return the children of siblings"""
        retval = lineobject.children
        retval = self.unique_OBJ(retval)   # sort the list, and get unique
                                           # objects
        for candidate in retval:
            if len(candidate.children) > 0:
                for child in candidate.children:
                    retval.append(child)
        retval = self.unique_OBJ(retval)   # ensure there are no duplicates,
                                           # belt & suspenders style
        return retval

    def find_parent_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of parent
        objects in the correct order"""
        retval = []
        me = lineobject
        while me.parent != me:
            retval.append(me.parent)
            me = me.parent
        return self.unique_OBJ(retval)

    def unique_OBJ(self, objectlist):
        """SEMI-PRIVATE: Returns a list of unique objects (i.e. with no
        duplicates).
        The returned value is sorted by configuration line number
        (lowest first)"""
        dct = {}
        retval = []
        for object in objectlist:
            dct[object.linenum] = object
        for ii in sorted(dct.keys()):
            retval.append(dct[ii])
        return retval

    def objects_to_lines(self, objectlist):
        """SEMI-PRIVATE: Accept a list of objects and return a list of lines.
        NOTE: The lines will NOT be reordered by this method.  Always call
        unique_OBJ() before this method."""
        retval = []
        for obj in objectlist:
            retval.append(self.ioscfg[obj.linenum])
        return retval

    def objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = []
        unconfdict = {}
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self.unique_OBJ(objectlist):
            if unconfdict[obj] == "DEFINED":
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
        self.parent = self
        self.child_indent = 0
        self.children = []
        self.has_children = False
        self.oldest_ancestor = False
        self.family_endpoint = 0
        self.linenum = linenum

    def add_parent(self, parentobj):
        ## In a perfect world, I would check parentobj's type
        self.parent = parentobj
        return True

    def add_child(self, childobj, indent):
        ## In a perfect world, I would check childobj's type
        ##
        ## Add the child, unless we already know it
        already_know_child = False
        for child in self.children:
            if child == childobj:
                already_know_child = True
        if already_know_child == False:
            self.children.append(childobj)
            self.child_indent = indent
            self.has_children = True
            return True
        else:
            return False

    def add_text(self, text):
        self.text = text

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

    def text(self):
        return self.text

    def uncfgtext(self):
        """unconftext is defined during special method calls.  Do not assume it
        is automatically populated."""
        return self.uncfgtext

class CiscoPassword(object):

    def __init__(self):
        self

    def decrypt(self, ep):
        """Cisco Type 7 password decryption.  Converted from perl code that was
        written by jbash /|at|\ cisco.com"""

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
            print "WARNING: password decryption failed."
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
        print pp.decrypt(opts.arg1)
        sys.exit(1)
    elif opts.method == "help":
        print "Valid methods and their arguments:"
        print "   find_lines:             arg1=linespec"
        print "   find_children:          arg1=linespec"
        print "   find_all_children:      arg1=linespec"
        print "   find_blocks:            arg1=linespec"
        print "   find_parents_w_child:   arg1=parentspec  arg2=childspec"
        print "   find_parents_wo_child:  arg1=parentspec  arg2=childspec"
        print "   req_cfgspec_excl_diff:  arg1=linespec    arg2=uncfgspec" + \
            "   arg3=cfgspec"
        print "   req_cfgspec_all_diff:   arg1=cfgspec"
        print "   decrypt:                arg1=encrypted_passwd"
        sys.exit(1)
    else:
        raise RuntimeError("'%s' is an unknown method (-m)." % opts.method)

    if len(diff) > 0:
        for line in diff:
            print line
    else:
        raise RuntimeError("FATAL: ciscoconfparse was called with unknown" + \
            " parameters")
