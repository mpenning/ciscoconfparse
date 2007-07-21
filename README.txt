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
IOSCfgLine objects themselves.  This gives you a flexible mechanism to 
build your own custom queries, because the IOSCfgLine objects store all the
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
  1.7  req_cfgspec_excl_diff( self, linespec, uncfgspec, cfgspec ):
  1.8  req_cfgspec_all_diff( self, cfgspec ):


2.  Query methods returning a list of IOSCfgLine objects.
  2.1  find_line_OBJ( self, linespec ):
  2.2  find_sibling_OBJ( self, lineobject ):
  2.3  find_child_OBJ( self, lineobject):
  2.4  find_all_child_OBJ( self, lineobject ):
  2.5  find_parent_OBJ( self, lineobject ):

3.  Methods for manipulating IOSCfgLine objects
  3.1  unique_OBJ( self, objectlist ):
  3.2  objects_to_lines( self, objectlist ):
  3.3  objects_to_uncfg( self, objectlist, unconflist ):

4.  Query methods on IOSCfgLine objects
  4.1  parent(self):
  4.2  children(self):
  4.3  has_children(self):
  4.4  child_indent(self):
  4.5  oldest_ancestor(self):
  4.6  family_endpoint(self):
  4.7  linenum(self):
  4.8  text(self):
  4.9  uncfgtext(self):


5.  Methods for parsing the configuration: I won't bother explaining here...
    You have the source if you are interested :-).


BASIC USAGE
===========
#!/usr/bin/env python
from ciscoconfparse import *

parse = CiscoConfParse("/tftpboot/bucksnort.conf")

# Return a list of all ATM interfaces and subinterfaces
atm_intfs = parse.find_lines("^interface\sATM")

# Return a list of all interfaces with a certain QOS policy
qos_intfs = parse.find_parents_w_child( "^interf", "service-policy QOS_01" )

# Return a list of all active interfaces (i.e. not shutdown)
active_intfs = parse.find_parents_wo_child( "^interf", "shutdown" )


The examples/ directory in the distribution contains more usage cases, 
including sample configs to parse.  When enforcing configuration standards,
the req_cfgspec_excl_diff() method is very useful; this module will accept a
list or required command entries (confspec) and return a list of diffs to make
the configuration compliant.  Note that this command ONLY works for global
configuration commands at the moment; interface-level commands are not supported
by req_cfgspec_excl_diff() right now.  Examples of its usage are included.


FAQ
===
Q1.  Is there a way to use this module with perl?
A1.  Yes, I do this myself.  Install the python package as you normally would
     and import it into perl with Inline.pm and Inline::Python from CPAN.


DOWNLOAD
========
http://www.python.org/pypi/ciscoconfparse/


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

This software is (c) 2007 by David Michael Pennington.  It can be
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
