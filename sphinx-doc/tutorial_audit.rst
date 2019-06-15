Example Usage: A Contrived Configuration Audit
==============================================

Suppose you have a large switched network and need to run audits on your 
configurations; assume you need to build configurations which conform to the 
following criteria:

* Access switchports *must* be configured with ``storm-control``
* Trunk ports *must not* have port-security
* Timestamps must be enabled on logging and debug messages

You should follow the following steps.

Assume that you start with the following Cisco IOS configuration saved as ``short.conf`` (All the interfaces need to be changed, to conform with audit requirements):

.. code-block:: none

    ! Filename: short.conf
    !
    interface FastEthernet0/1
     switchport mode access
     switchport access vlan 532
    !
    interface FastEthernet0/2
     switchport mode trunk
     switchport trunk allowed 300,532
     switchport nonegotiate
     switchport port-security maximum 2
     switchport port-security violation restrict
     switchport port-security
    !
    interface FastEthernet0/3
     switchport mode access
     switchport access vlan 300
    !
    end

Next, we build this script to read and change the config:

.. code-block:: python

   from ciscoconfparse import CiscoConfParse

   def standardize_intfs(parse):

       ## Search all switch interfaces and modify them
       #
       # r'^interface.+?thernet' is a regular expression, for ethernet intfs
       for intf in parse.find_objects(r'^interface.+?thernet'):

           has_stormcontrol = intf.has_child_with(r' storm-control broadcast')
           is_switchport_access = intf.has_child_with(r'switchport mode access')
           is_switchport_trunk = intf.has_child_with(r'switchport mode trunk')

           ## Add missing features
           if is_switchport_access and (not has_stormcontrol):
               intf.append_to_family(' storm-control action trap')
               intf.append_to_family(' storm-control broadcast level 0.4 0.3')

           ## Remove dot1q trunk misconfiguration...
           elif is_switchport_trunk:
               intf.delete_children_matching('port-security')

   ## Parse the config
   parse = CiscoConfParse('short.conf')

   ## Add a new switchport at the bottom of the config...
   parse.append_line('interface FastEthernet0/4')
   parse.append_line(' switchport')
   parse.append_line(' switchport mode access')
   parse.append_line('!')
   parse.commit()     # commit() **must** be called before searching again

   ## Search and standardize the interfaces...
   standardize_intfs(parse)
   parse.commit()     # commit() **must** be called before searching again

   ## I'm illustrating regular expression usage in has_line_with()
   if not parse.has_line_with(r'^service\stimestamp'):
       ## prepend_line() adds a line at the top of the configuration
       parse.prepend_line('service timestamps debug datetime msec localtime show-timezone')
       parse.prepend_line('service timestamps log datetime msec localtime show-timezone')

   ## Write the new configuration
   parse.save_as('short.conf.new')

Normally, `regular expressions`_ should be used in ``.has_child_with()``; 
however, you can technically get away with the bare strings that I used in 
``standardize_intfs()`` in some cases.  That said, `regular expressions`_ are 
more powerful, and reliable when searching text.  Usage of 
the :func:`~models_cisco.IOSCfgLine.has_line_with()` and 
:func:`~models_cisco.IOSCfgLine.find_objects()` methods illustrate regular 
expression syntax.

After the script runs, the new configuration (``short.conf.new``) looks like this:

.. code-block:: python

    service timestamps log datetime msec localtime show-timezone
    service timestamps debug datetime msec localtime show-timezone
    !
    interface FastEthernet0/1
     switchport mode access
     switchport access vlan 532
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    interface FastEthernet0/2
     switchport mode trunk
     switchport trunk allowed 300,532
     switchport nonegotiate
    !
    interface FastEthernet0/3
     switchport mode access
     switchport access vlan 300
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    interface FastEthernet0/4
     switchport
     switchport mode access
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    end

The script:

 * *Added* an access switchport: ``interface FastEthernet0/4``
 * *Added* ``storm-control`` to Fa0/1, Fa0/3, and Fa0/4
 * *Removed* ``port-security`` from Fa0/2
 * *Added* ``timestamps`` to logs and debug messages

.. _`regular expressions`: https://docs.python.org/3/howto/regex.html
