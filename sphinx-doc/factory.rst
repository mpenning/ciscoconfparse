.. _factory:

=======
factory
=======

``factory`` is an experimental feature to derive more information about configurations by using
several different configuration objects for a given ``syntax``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02sw01.conf', syntax='ios', factory=True)
   >>> hsrp_intf = parse.find_parent_objects("interface", " standby")
   >>>

The most developed factory is ``ios``.

.. note::
   ``factory`` is an experimental feature; to enable it, parse with ``factory=True``.
   If something doesn't work, it's a feature, not a bug.

.. warning::
   Anything about ``factory`` parsing can change at any time (but mostly does not).

factory=True example
--------------------

This is an example of getting an :class:`~ciscoconfparse.ccp_util.IPv4Obj()` for an interface that was parsed with ``factory=True``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_08.ios", syntax="ios", factory=True)
   >>> hsrp_intfs = parse.find_parent_objects("interface", " standby")
   >>>
   >>> hsrp_intfs[0]
   <IOSIntfLine # 231 'interface FastEthernet0/0' primary_ipv4: '172.16.2.1/24'>
   >>>
   >>> hsrp_intfs[0].ipv4
   <IPv4Obj 172.16.2.1/24>
   >>>

factory=False example
---------------------

This is the same operation with ``factory=False``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_08.ios", syntax="ios", factory=False)
   >>> hsrp_intfs = parse.find_parent_objects("interface", " standby")
   >>>
   >>> hsrp_intfs[0]
   <IOSCfgLine # 231 'interface FastEthernet0/0'>
   >>>
   >>> hsrp_intfs[0].ipv4
   2023-11-18 07:00:21.216 | ERROR    | ciscoconfparse.ccp_abc:__getattr__:142 - The ipv4 attribute does not exist
   2023-11-18 07:00:21.217 | ERROR    | __main__:<module>:1 - An error has been caught in function '<module>', process 'MainProcess' (111007), thread 'MainThread' (139675861627520):
   Traceback (most recent call last):

     File "/home/mpenning/fixme/ciscoconfparse/ciscoconfparse/ccp_abc.py", line 138, in __getattr__
       retval = getattr(object, attr)
                                └ 'ipv4'

   AttributeError: type object 'object' has no attribute 'ipv4'
   >>>

