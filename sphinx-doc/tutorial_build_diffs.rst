Example Usage: Build configuration diffs
========================================

Getting diffs is a common need when something happens and you want to know "what changed" between
two configs.  This example will demonstrate how to find diffs between two configurations.


Baseline Configurations
-----------------------

bucksnort_before.conf
^^^^^^^^^^^^^^^^^^^^^

This tutorial will run all the queries this example base configuration, the "before" version is shown below.

.. code-block:: none
   :linenos:

   ! Filename: /tftpboot/bucksnort_before.conf
   !
   hostname bucksnort
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
   !

bucksnort_after.conf
^^^^^^^^^^^^^^^^^^^^

This tutorial will run diff against this example after configuration, which has MPLS enabled on 'Serial1/0'.

.. code-block:: none
   :linenos:

   ! Filename: /tftpboot/bucksnort_after.conf
   !
   hostname bucksnort
   !
   interface Ethernet0/0
    ip address 1.1.2.1 255.255.255.0
    no cdp enable
   !
   interface Serial1/0
    encapsulation ppp
    ip address 1.1.1.1 255.255.255.252
    mpls ip
   !
   interface Serial1/1
    encapsulation ppp
    ip address 1.1.1.5 255.255.255.252
   !

Diff Script
-----------

The script below will build read the configurations from disk and check to see whether
there are diffs.

.. code-block:: python

   >>> from ciscoconfparse.ciscoconfparse import Diff
   >>> # Parse the original configuration
   >>> before_lines = open('/tftpboot/bucksnort_before.conf').read().splitlines()
   >>> after_lines = open('/tftpboot/bucksnort_after.conf').read().splitlines()
   >>> diff = Diff(hostname='bucksnort', old_config=before_lines, new_config=after_lines)
   >>> diff.diff()
   ['interface Serial1/0', ' mpls ip']
   >>>
   >>> for line in diff.diff():
   ...     print(line)
   ...
   !
   interface Serial1/0
    mpls ip
   !
   >>>

Rollback Script
---------------

The script below will build read the configurations from disk and build rollback diff configs.

.. code-block:: python

   >>> from ciscoconfparse.ciscoconfparse import Diff
   >>> # Parse the original configuration
   >>> before_lines = open('/tftpboot/bucksnort_before.conf').read().splitlines()
   >>> after_lines = open('/tftpboot/bucksnort_after.conf').read().splitlines()
   >>> diff = Diff(hostname='bucksnort', old_config=before_lines, new_config=after_lines)
   >>> diff.diff()
   ['interface Serial1/0', ' mpls ip']
   >>>
   >>> for line in diff.rollback():
   ...     print(line)
   ...
   !
   interface Serial1/0
    no mpls ip
   !
   >>>
