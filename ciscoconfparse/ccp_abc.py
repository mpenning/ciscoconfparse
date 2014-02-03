from collections import MutableSequence
from types import TypeType
from abc import ABCMeta
import re
import os

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


##
##-------------  Config Line ABC
##


class BaseCfgLine(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        """Accept an IOS line number and initialize family relationship
        attributes"""
        self.linenum = -1
        self.parent = self
        self.text = ""
        self.child_indent = 0
        self.children = list()
        self.oldest_ancestor = False
        self.is_comment = False
        self.indent = 0            # Whitespace indentation on the object
        self.confobj = None        # Reference to the list object which owns it

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)


    def __str__(self):
        ## If called in a string context, return the config line
        # TODO: make this return __repr__ one day, 
        #     but it breaks a lot of stuff now
        return self.__repr__()
        #return self.text

    def __eq__(self, val):
        return isinstance(val, BaseCfgLine) and \
            (self.classname==val.classname) and \
            (self.hash_arg==val.hash_arg)

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
    def classname(self):
        return self.__class__.__name__

    @property
    def has_children(self):
        if len(self.children)>0:
            return True
        return False

    @property
    def hash_arg(self):
        # Just a unique string or each object instance
        return str(self.linenum)+self.text

    def _list_bootstrap(self):
        # Call this when I want to reparse everything
        #     (which is very slow)
        self.confobj._bootstrap_from_text()

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

    def insert_before(self, insertstr, atomic=True):
        ## BaseCfgLine.insert_before(), insert a single line before this object
        local_atomic=atomic
        return self.confobj.insert(self.linenum-1, insertstr, atomic=local_atomic)

    def insert_after(self, insertstr, atomic=True):
        ## BaseCfgLine.insert_after(), insert a single line after this object
        local_atomic=atomic
        return self.confobj.insert(self.linenum, insertstr, atomic=local_atomic)

    def replace(self, linespec, replacestr, atomic=True):
        # This is a little slower than calling BaseCfgLine.re_sub directly...
        return self.re_sub(linespec, replacestr, atomic)

    def re_sub(self, regex, replacergx, atomic=True):
        retval = re.sub(regex, replacergx, self.text)
        self.text = retval
        if atomic:
            # We might need to reparse from scratch to 
            #    ensure all objects are parsed 
            #    correctly after the text substitution
            self._list_bootstrap()
        return retval

    def re_match(self, regex, group=1):
        mm = re.search(regex, self.text)
        if not (mm is None):
            return mm.group(group)
        return None

    def re_search(self, regex):
        mm = re.search(regex, self.text)
        if not (mm is None):
            return self.text
        return None

    def re_search_children(self, regex):
        retval = list()
        for cobj in self.children:
            if cobj.re_search(regex):
                retval.append(cobj)
        return retval

    def re_match_typed(self, regex, group=1, result_type=str, default=''):
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
    def is_parent(self):
        return bool(self.has_children)

    @property
    def siblings(self):
        indent = self.indent
        return [obj for obj in self.parent.children if (obj.indent==indent)]

    @classmethod
    def is_object_for(cls, line=""):
        return False

