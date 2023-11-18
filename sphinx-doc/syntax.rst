.. _syntax:

syntax
------

``syntax`` is used with all configurations.  By default ``ios`` syntax is used and it's
a good default for many vendor configurations (without braces).

This configuration parse reads the configuration as ``ios`` syntax by default:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02sw01.conf')
   >>>

This configuration parse explicitly reads the configuration as ``asa`` syntax:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02fw01.conf', syntax='asa')
   >>>

``syntax`` offers a way to handle these situations:

- Is the config delimited with braces or indentation?
- Which configuration object is used to represent configuration lines?
- These configuration objects offer the following information:

  - Is a configuration line an interface?
  - Is an interface a switchport?
  - Is an interface administratively shutdown?

