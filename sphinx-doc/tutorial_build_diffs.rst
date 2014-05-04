Example Usage: Build configuration diffs
========================================

Let's suppose we need to find all serial interfaces in a certain address range 
and configure them for the MPLS LDP protocol.  We will assume that all serial 
interfaces in 1.1.1.0/24 need to be configured with LDP.

Baseline Configuration
----------------------

This tutorial will run all the queries against a sample configuration, which is shown below.

.. code-block:: none
   :linenos:

   ! Filename: /tftpboot/bucksnort.conf
   !
   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !
   interface Ethernet0/0
    ip address 1.1.2.1 255.255.255.0
    no cdp enable
   !
   interface Serial1/0
    encapsulation ppp
    ip address 1.1.1.1 255.255.255.252
   !
   interface Serial1/1
    encapsulation ppp
    ip address 1.1.1.5 255.255.255.252
    service-policy output QOS_1
   !
   interface Serial1/2
    encapsulation hdlc
    ip address 1.1.1.9 255.255.255.252
   !
   class-map GOLD
    match access-group 102
   class-map SILVER
    match protocol tcp
   !
   access-list 101 deny tcp any any eq 25 log
   access-list 101 permit ip any any
   !
   access-list 102 permit tcp any host 1.5.2.12 eq 443
   access-list 102 deny ip any any
   !

Diff Script
-----------

The script below will build a list of serial interfaces, check to see whether 
they are in the correct address range.  If so, the script will build a diff to 
enable LDP.

.. code-block:: python
   :emphasize-lines: 6,8

   from ciscoconfparse import CiscoConfParse

   # Parse the original configuration
   parse = CiscoConfParse('/tftpboot/bucksnort.conf')

   # Build a blank configuration for diffs
   cfgdiffs = CiscoConfParse([])

   # Iterate over :class:`~IOSCfgLine` objects
   for intf in parse.find_objects("^interface Serial"):

      ## Search children of the interface for 1.1.1
      if (intf.re_search_children(r"ip\saddress\s1\.1\.1")):
         cfgdiffs.append_line("!")
         cfgdiffs.append_line(intf.text)  # Add the interface text
         cfgdiffs.append_line(" mpls ip")

Result:

.. code-block:: python

   >>> cfgdiffs.ioscfg
   ['interface Serial1/0', ' mpls ip', 'interface Serial1/1', ' mpls ip', 'interface Serial1/2', ' mpls ip']
   >>> for line in cfgdiffs.ioscfg:
   ...     print line
   ... 
   !
   interface Serial1/0
    mpls ip
   !
   interface Serial1/1
    mpls ip
   !
   interface Serial1/2
    mpls ip
   >>>

