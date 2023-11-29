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

Also See
^^^^^^^^

- The :ref:`syntax_ios` page.
- The :ref:`syntax_nxos` page.
- The :ref:`syntax_iosxr` page.
