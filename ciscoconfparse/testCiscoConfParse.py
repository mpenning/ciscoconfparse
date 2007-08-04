#!/usr/bin/env python

from ciscoconfparse import *
import unittest

class knownValues(unittest.TestCase):

   c01 = [
   'policy-map QOS_1',
   ' class GOLD',
   '  priority percent 10',
   ' !',
   ' class SILVER',
   '  bandwidth 30',
   '  random-detect',
   ' !',
   ' class BRONZE',
   '  random-detect',
   '!',
   'interface Serial 1/0',
   ' encapsulation ppp',
   ' ip address 1.1.1.1 255.255.255.252',
   '!',
   'access-list 101 deny tcp any any eq 25 log',
   'access-list 101 permit ip any any',
   '!',
   'banner login ^C'
   'This is a router, and you cannot have it.',
   'Log off now while you still can type. I break the fingers',
   'of all tresspassers.',
   '^C',
   'alias exec showthang show ip route vrf THANG',
   ]

   c01_intf = [
   'interface Serial 1/0',
   ]

   c01_pmap_children = [
   'policy-map QOS_1',
   ' class GOLD',
   ' class SILVER',
   ' class BRONZE',
   ]

   c01_pmap_all_children = [
   'policy-map QOS_1',
   ' class GOLD',
   '  priority percent 10',
   ' class SILVER',
   '  bandwidth 30',
   '  random-detect',
   ' class BRONZE',
   '  random-detect',
   ]


   c02 = [
   'interface Serial1/0',
   ' encapsulation ppp',
   ' ip address 1.1.1.1 255.255.255.252',
   ]

   #--------------------------------

   find_lines_Values = ( 
   ( c01, [ "interface", False ], c01_intf ),
   )

   find_children_Values = ( 
   ( c01, [ "policy-map", False ], c01_pmap_children ),
   ( c01, [ "policy-map", True ], False),
   )

   find_all_children_Values = ( 
   ( c01, [ "policy-map", False ], c01_pmap_all_children ),
   ( c01, [ "policy-map", True ], False),
   )

   #--------------------------------

   def testValues_find_lines(self):
      for config, args, resultGood in self.find_lines_Values:
         cfg = CiscoConfParse( config )
         result = cfg.find_lines( args[0], args[1] )
         self.assertEqual( resultGood, result )


   def testValues_find_children(self):
      for config, args, resultGood in self.find_children_Values:
         cfg = CiscoConfParse( config )
         result = cfg.find_children( args[0], args[1] )
         self.assertEqual( resultGood, result )


   def testValues_find_all_children(self):
      for config, args, resultGood in self.find_all_children_Values:
         cfg = CiscoConfParse( config )
         result = cfg.find_all_children( args[0], args[1] )
         self.assertEqual( resultGood, result )


if __name__ == "__main__":
    unittest.main()
