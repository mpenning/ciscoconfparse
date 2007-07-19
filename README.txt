INTRO
=====
ciscoconfparse is a module for parsing through Cisco IOS-style configurations
and retrieving portions of the config based on a variety of query methods.

The package will process an IOS-style config and break it into a set of
linked parent / child relationships.  Then you issue queries against these 
relationships using a familiar family syntax model.  Queries can either be 
in the form of a simple string, or you can use regular expressions.  The API
provides powerful query tools, including the ability to find all parents that
have or do not have children matching a certain criteria.  This means it is 
easy to find the interface names of all layer2 trunks in a Catalyst 6500,
or retrieve a list of all interfaces with cdp disabled.  Until this package,
I know of no simple config-parsing APIs to do the same; it has traditionally 
been considered the domain of screen-scraping.  In conjunction with python's
sophisticated set-manipulation capabilities, your imagination is the limit.

The package also provides a set of methods to query and manipulate the 
IOSConfigLine objects themselves.  This gives you a flexible mechanism to 
build your own custom queries, because the IOSConfigLine objects store all the
parent / child hierarchy in them.

Examples of config family relationships are shown below...

Line01:policy-map QOS_1
Line02: class GOLD
Line03:  priority percent 10
Line04: class SILVER
Line05:  bandwidth 30
Line06:  random-detect
Line07: class default
Line08:!
Line09:interface Serial 1/0
Line10: encapsulation ppp
Line11: ip address 1.1.1.1 255.255.255.252
Line12:!
Line13:access-list 101 deny tcp any any eq 25 log
Line14:access-list 101 permit ip any any

 parents: 01, 02, 04, 09
 children: of 01 = 02, 04, 07
           of 02 = 03
           of 04 = 05, 06
           of 09 = 10, 11
 siblings: 05, 06
           10, 11
 oldest_ancestors: 01, 09
 families: 01, 02, 03, 04, 05, 06, 07
           09, 10, 11
 family_endpoints: 07, 11

Note that 01, 09, 13 and 14 are not considered siblings, nor are they part 
of the same family.  In fact, 13 and 14 do not belong to a family at all; they
have no children.

The package provides several types of methods:
1.  Query methods returning a list of text lines.
  1.1  find_lines( self, linespec ):
  1.2  find_children( self, linespec ):
  1.3  find_all_children( self, linespec ):
  1.4  find_blocks( self, blockspec ):
  1.5  find_parents_w_child( self, parentspec, childspec ):
  1.6  find_parents_wo_child( self, parentspec, childspec ):


2.  Query methods returning a list of IOSConfigLine objects.
  2.1  find_line_objects( self, linespec ):
  2.2  find_sibling_objects( self, lineobject ):
  2.3  find_child_objects( self, lineobject):
  2.4  find_all_child_objects( self, lineobject ):
  2.5  find_parent_objects( self, lineobject ):

3.  Methods for manipulating IOSConfigLine objects
  3.1  unique_objects( self, objectlist ):
  3.2  objects_to_lines( self, objectlist ):

4.  Query methods on IOSConfigLine objects
  4.1  parent(self):
  4.2  children(self):
  4.3  has_children(self):
  4.4  child_indent(self):
  4.5  oldest_ancestor(self):
  4.6  family_endpoint(self):
  4.7  linenum(self):
  4.8  text(self):



5.  Methods for parsing the configuration: I won't bother explaining here...
    You have the source if you are interested :-).


BASIC USAGE
===========
#!/usr/bin/env python
from ciscoconfparse import *

parse = CiscoConfParse("/tftpboot/bucksnort.conf")
atm_intfs = parse.find_lines("^interface\sATM")
qos_intfs = parse.find_parents_w_child( "^interf", "service-policy QOS_01" )
active_intfs = parse.find_parents_wo_child( "^interf", "shutdown" )


AUTHOR
======
David Michael Pennington, mike /|at|\ pennington.net

THANKS
======
Thanks to David Muir Sharnoff for his suggestion about making a special
case for IOS banners.  Thanks to everyone in advance for their bug reports 
and patience.  Sola Dei Gloria.


COPYRIGHT, LICENSE, and WARRANTY
================================
GNU General Public License, v3

This software is (c) David Michael Pennington.  It can be
reused under the terms of the GPL v3 license provided that proper
credit for the work of the author is preserved in the form  of this 
copyright notice and license for this package.

No warranty of any kind is expressed or implied.  By using this software, you 
are agreeing to assume ALL risks and David M Pennington shall NOT be liable 
for ANY damages resulting from its use.

If you chose to bring legal action against the author, you are automatically 
granting him the remainder of your lifetime salary, ownership of your 
retirement plan (you do have one, right??), the deed to your house assuming 
it isn't a pile of junk, and your perpetual indentured servitude under his 
direction.
