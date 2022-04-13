Version: l.7.0, Released: 2022-03-04
------------------------------------

- Add HDiff(), remove NXOSConfigList() and ASAConfigList().

<h2>Version: l.6.38</h2>, Released: 2022-03-04
-------------------------------------

- Internal adjustments on previous commit

<h2>Version: l.6.37</h2>, Released: 2022-03-04
-------------------------------------

- Rename 'master' branch to 'main'
- Add config diff infrastructure (preparing to make heavy changes to diffs)

<h2>Version: l.6.36</h2>, Released: 2022-02-20
-------------------------------------

- Cosmetic changes to dns_query()

<h2>Version: l.6.35</h2>, Released: 2022-02-19
-------------------------------------

- Fix problems with ip_factory()

<h2>Version: 1.6.34</h2>, Released: 2022-02-16
-------------------------------------

- Add _ip property to IPv4Obj() and IPv6Obj()

<h2>Version: 1.6.33</h2>, Released: 2022-02-16
-------------------------------------

- Commit changes from develop to master

<h2>Version: 1.6.32</h2>, Released: 2022-02-16
-------------------------------------

- Add support for IPv4 Mapped IPv6 Addresses

<h2>Version: 1.6.31</h2>, Released: 2022-02-06
-------------------------------------

- Improve CiscoConfParse().__init__() Rip out redundant code

<h2>Version: 1.6.30</h2>, Released: 2022-02-04
-------------------------------------

- Fix BaseCfgLine().has_child_with() method

<h2>Version: 1.6.29</h2>, Released: 2022-01-29
-------------------------------------

- Re-organize / cleanup IPv4Obj, IPv6Obj

<h2>Version: 1.6.28</h2>, Released: 2022-01-28
-------------------------------------

- Make ip_factory() more resilient

<h2>Version: 1.6.27</h2>, Released: 2022-01-28
-------------------------------------

- Make ip_factory() more resilient

<h2>Version: 1.6.26</h2>, Released: 2022-01-26
-------------------------------------

- Fix issue raised in github PR #219

<h2>Version: 1.6.25</h2>, Released: 2022-01-26
-------------------------------------

- Remove old 'ipaddr' module requirement from Python2.7 days

<h2>Version: 1.6.24</h2>, Released: 2022-01-25
-------------------------------------

- Update CHANGES to match most recent github version

<h2>Version: 1.6.21</h2>, Released: 2022-01-12
-------------------------------------

- Commit with ccp_logger_control feature incompete

<h2>Version: 1.6.20</h2>, Released: 2022-01-11
-------------------------------------

- Code cleanup

<h2>Version: 1.6.19</h2>, Released: 2022-01-09
-------------------------------------

- Fix IPv6 bug in `ip_factory()`

<h2>Version: 1.6.18</h2>, Released: 2022-01-09
-------------------------------------

- Fix failed py36 test

<h2>Version: 1.6.17</h2>, Released: 2022-01-09
-------------------------------------

- Enhance regex_groups on find_object_branches

<h2>Version: 1.6.16</h2>, Released: 2022-01-07
-------------------------------------

- Add regex match group support to find_object_branches

<h2>Version: 1.6.15</h2>, Released: 2022-01-05
-------------------------------------

- Fix several problems in version 1.6.14

<h2>Version: 1.6.14</h2>, Released: 2022-01-01
-------------------------------------

- Ensure masklen and prefix are int objects for IPv4Obj and IPv6Obj network mask length

<h2>Version: 1.6.13</h2>, Released: 2021-12-31
-------------------------------------

- Add ccp_util.ip_factory()

<h2>Version: 1.6.12</h2>, Released: 2021-12-20
-------------------------------------

- Replace map() calls with equivalent list-comprehensions

<h2>Version: 1.6.11</h2>, Released: 2021-12-12
-------------------------------------

- Update IPv4Obj and IPv6Obj docs

<h2>Version: 1.6.10</h2>, Released: 2021-12-08
-------------------------------------

- Improve style and readability

<h2>Version: 1.6.9</h2>, Released: 2021-12-06
------------------------------------

- Small tweak

<h2>Version: 1.6.8</h2>, Released: 2021-12-03
------------------------------------

- Reorganize build infra and ccp data structures
- Fix Github issue #214
- Fix for issue documented in Github PR #217.

<h2>Version: 1.6.7</h2>, Released: 2021-11-22
------------------------------------

- Misc updates

<h2>Version: 1.6.6</h2>, Released: 2021-11-18
------------------------------------

- Build poetry infra

<h2>Version: 1.6.5</h2>, Released: 2021-11-18
------------------------------------

- Deprecate setuptools

<h2>Version: 1.6.4</h2>, Released: 2021-11-11
------------------------------------

- Rename loguru.logger's logger_id to handler_id

<h2>Version: 1.6.3</h2>, Released: 2021-11-11
------------------------------------

- Add an explicit logger_id parameter to ensure only intended loguru loggers are removed...

<h2>Version: 1.6.2</h2>, Released: 2021-11-11
------------------------------------

- Enhance ccp_logger_control()
- Added a "disable" and "enable" command to ccp_logger_control()

<h2>Version: 1.6.1</h2>, Released: 2021-11-11
------------------------------------

- Add ccp_logger_control()
- See Github issue #211.

<h2>Version: 1.6.0</h2>, Released: 2021-11-08
------------------------------------

- Fix race-condition for `CiscoConfParse` kwarg in IOSConfigList, NXOSConfigList, and ASAConfigList
- Add explicit configuration file encoding with default encoding from python's locale module
- Add tests to catch breakage similar to Github Issue #209
- Remove colorama dependency.

<h2>Version: 1.5.51</h2>, Released: 2021-11-01
-------------------------------------

- [config insert()s are broken See Github issue #209] New release with modified copyrights

<h2>Version: 1.5.50</h2>, Released: 2021-10-08
-------------------------------------

- [config insert()s are broken See Github issue #209] NOTE MODIFIED RELEASE
- Update copyrights, fix Github issue #208
- Also see https://stackoverflow.com/q/21064581/667301 as an alternative to deleting the original pypi package data

<h2>Version: 1.5.49</h2>, Released: 2021-10-08
-------------------------------------

- [config insert()s are broken See Github issue #209] Fix typos and syntax

<h2>Version: 1.5.48</h2>, Released: 2021-10-07
-------------------------------------

- [config insert()s are broken See Github issue #209] Changes to insert_before() and insert_after(), update Copyrights

<h2>Version: 1.5.47</h2>, Released: 2021-09-15
-------------------------------------

- Expose a proxy function to call ipaddress.collapse_addresses()

<h2>Version: 1.5.46</h2>, Released: 2021-07-17
-------------------------------------

- More logging work..
- prepare for debugging overhaul.

<h2>Version: 1.5.45</h2>, Released: 2021-07-17
-------------------------------------

- Refine error logging in setup.py

<h2>Version: 1.5.44</h2>, Released: 2021-07-17
-------------------------------------

- Fix get_metadata() returned value in setup.py

<h2>Version: 1.5.37</h2>, Released: 2021-07-17
-------------------------------------

- Rework version.json to metadata.json

<h2>Version: 1.5.36</h2>, Released: 2021-07-11
-------------------------------------

- Rework git remote (i.e
- origin) logic

<h2>Version: 1.5.35</h2>, Released: 2021-07-11
-------------------------------------

- Fix git tags in Makefile
- Deprecate py2.7 support

<h2>Version: 1.5.30</h2>, Released: 2021-03-01
-------------------------------------

- Add a helper-function: as_text_list()
- improve performance of .delete()

<h2>Version: 1.5.29</h2>, Released: 2021-01-28
-------------------------------------

- Fix __int__() and __index__() on IPv4Obj() and IPv6Obj()

<h2>Version: 1.5.28</h2>, Released: 2021-01-23
-------------------------------------

- Enhance ccp_util.CiscoRange() to parse a wider variety of string inputs

<h2>Version: 1.5.27</h2>, Released: 2021-01-23
-------------------------------------

- Remove slow code from ccp_util.CiscoRange()

<h2>Version: 1.5.26</h2>, Released: 2021-01-23
-------------------------------------

- Make ccp_util.L4Object().__repr__() more friendly

<h2>Version: 1.5.25</h2>, Released: 2021-01-23
-------------------------------------

- Fix Github Issue #195, merge PR #194, fix multiple unreported bugs in ccp_util.L4Object()

<h2>Version: 1.5.24</h2>, Released: 2021-01-06
-------------------------------------

- Fix Github Issue #178

<h2>Version: 1.5.23</h2>, Released: 2021-01-05
-------------------------------------

- Prevent find_object_branches() from using None

<h2>Version: 1.5.22</h2>, Released: 2020-11-27
-------------------------------------

- Fix Github issue #186 (replace variables named input)

<h2>Version: 1.5.21</h2>, Released: 2020-11-27
-------------------------------------

- Fix Github issue #187

<h2>Version: 1.5.20</h2>, Released: 2020-11-27
-------------------------------------

- Fix Github issue #185

<h2>Version: 1.5.19</h2>, Released: 2020-07-22
-------------------------------------

- Add __ne__() support to IPv4Obj and IPv6Obj

<h2>Version: 1.5.18</h2>, Released: 2020-07-21
-------------------------------------

- Fix Github issue #180 IPv4Obj() and IPv6Obj() cannot use logical compare ops with certain Python objects

<h2>Version: 1.5.17</h2>, Released: 2020-07-11
-------------------------------------

- Fix Python 2.7 packaging

<h2>Version: 1.5.7</h2>, Released: 2020-07-11
------------------------------------

- Revise IPv4Obj & IPv6Obj __lt__(), __gt__(), and __contains__() methods (impacts sorting behavior)
- reformatted documentation to latest numpydoc format
- Add version number as json data instead of raw text...

<h2>Version: 1.5.6</h2>, Released: 2020-06-27
------------------------------------

- Improve find_object_branches() speed
- reformat with black

<h2>Version: 1.5.5</h2>, Released: 2020-06-12
------------------------------------

- Beta-test new function: find_object_branches()

<h2>Version: 1.5.4</h2>, Released: 2020-04-12
------------------------------------

- Modify IPv4Obj().__add__() and IPv6Obj().__add__() (and __sub__()) methods return IPv4Obj()/IPv6Obj() objects
- Add support for int(), bin() and hex() on the IPv4Obj() and IPv6Obj()

<h2>Version: 1.5.3</h2>, Released: 2020-04-12
------------------------------------

- Fix IPv6Obj().packed and IPv6Obj().exploded
- add IPv4Obj().packed and IPv4Obj().exploded

<h2>Version: 1.5.2</h2>, Released: 2020-04-12
------------------------------------

- Add __add__() and __sub__() to IPv4Obj() and IPv6Obj()
- remove use of IPv6Obj().broadcast in IPv6Obj().__contains__()

<h2>Version: 1.5.1</h2>, Released: 2020-02-23
------------------------------------

- Remove embedded junos debugging

<h2>Version: 1.5.0</h2>, Released: 2020-02-23
------------------------------------

- Complete rewrite of junos parser (fix Github issue #70)
- deprecate support for Python 3.4

<h2>Version: 1.4.11</h2>, Released: 2019-12-05
-------------------------------------

- Github issue #170 Explicitly close() open filehandles

<h2>Version: 1.4.10</h2>, Released: 2019-11-25
-------------------------------------

- Integrate Github issue #169, add support for parsing pathlib.Path objects which contain a configuration

<h2>Version: 1.4.9</h2>, Released: 2019-11-22
------------------------------------

- Add .as_cidr_net and .as_cidr_addr on IPv4Obj and IPv6Obj

<h2>Version: 1.4.8</h2>, Released: 2019-11-21
------------------------------------

- Merge Github PR #168
- rename in_portchannel and is_portchannel

<h2>Version: 1.4.7</h2>, Released: 2019-09-10
------------------------------------

- Add support for NXOS vrf with dhcp helper-address

<h2>Version: 1.4.6</h2>, Released: 2019-09-10
------------------------------------

- Add support for NXOS dhcp helper-address (w/ factory=True)

<h2>Version: 1.4.5</h2>, Released: 2019-09-07
------------------------------------

- Add support for NXOS in find_interface_objects()

<h2>Version: 1.4.4</h2>, Released: 2019-09-07
------------------------------------

- Fix Github issue #162 and Github issue #164

<h2>Version: 1.4.3</h2>, Released: 2019-08-14
------------------------------------

- Fix Github issue #160
- Add parser for various NXOS features

<h2>Version: 1.4.2</h2>, Released: 2019-07-28
------------------------------------

- Fix Github issue #141
- NOTE This will break parsing helper-addresses under factory=True
- If you use this feature, please migrate your scripts to the new format

<h2>Version: 1.4.1</h2>, Released: 2019-07-28
------------------------------------

- Implement re_search_children() directly on the CiscoConfParse() object

<h2>Version: 1.4.0</h2>, Released: 2019-07-27
------------------------------------

- Fix Github issue #158, *KEYWORD CHANGE WARNING:* some methods formrely used a keyword called 'all_children'
- The new syntax is 'recurse' (ref: Github issue #159)

<h2>Version: 1.3.43</h2>, Released: 2019-07-05
-------------------------------------

- Attempt to fix Github issue #154

<h2>Version: 1.3.42</h2>, Released: 2019-06-27
-------------------------------------

- Fix Github issue #153

<h2>Version: 1.3.41</h2>, Released: 2019-06-27
-------------------------------------

- [RELEASE BROKEN] HSRP timers now return a float (used to return int)
- NXOS support for HSRP (Github issue #152)

<h2>Version: 1.3.40</h2>, Released: 2019-06-20
-------------------------------------

- Update version handling
- Github issue #122
- update sphinx documentation

<h2>Version: 1.3.39</h2>, Released: 2019-05-27
-------------------------------------

- Allow re_match_iter_typed() to use default=True

<h2>Version: 1.3.38</h2>, Released: 2019-05-27
-------------------------------------

- Add CiscoConfParse().re_match_iter_typed()

<h2>Version: 1.3.37</h2>, Released: 2019-05-12
-------------------------------------

- Take a step further towards full Python 3 compat (Github issue #98)

<h2>Version: 1.3.36</h2>, Released: 2019-04-22
-------------------------------------

- Refine Junos parsing (Github issue #142)

<h2>Version: 1.3.35</h2>, Released: 2019-04-20
-------------------------------------

- Refine IOS macro parsing (Github issue #144)

<h2>Version: 1.3.34</h2>, Released: 2019-04-19
-------------------------------------

- Add support for IOS macros (Github issue #143)

<h2>Version: 1.3.33</h2>, Released: 2019-04-07
-------------------------------------

- Merge Github PR #140 (delete_lines() bug)

<h2>Version: 1.3.32</h2>, Released: 2019-03-17
-------------------------------------

- Fix Github issue #135

<h2>Version: 1.3.31</h2>, Released: 2019-03-16
-------------------------------------

- Fix Github issues #131, 132, 133, 134

<h2>Version: 1.3.30</h2>, Released: 2019-02-18
-------------------------------------

- Fix bugs related to Python3 (Github issue #117)

<h2>Version: 1.3.29</h2>, Released: 2019-02-07
-------------------------------------

- Add IP helper-address parsing in models_cisco.py

<h2>Version: 1.3.28</h2>, Released: 2019-02-06
-------------------------------------

- Revert universal wheel packages (universal=0)

<h2>Version: 1.3.27</h2>, Released: 2019-01-26
-------------------------------------

- Build universal wheel packages

<h2>Version: 1.3.26</h2>, Released: 2019-01-26
-------------------------------------

- Build improvements ref Github issue #127, #128

<h2>Version: 1.3.25</h2>, Released: 2019-01-23
-------------------------------------

- Another swing at Github issue #127

<h2>Version: 1.3.24</h2>, Released: 2019-01-23
-------------------------------------

- Rollback fix for Github issue #127

<h2>Version: 1.3.23</h2>, Released: 2019-01-23
-------------------------------------

- Attempt to fix Github issue #127

<h2>Version: 1.3.22</h2>, Released: 2018-12-16
-------------------------------------

- Fix Github issue #124-126 and Github issue #110

<h2>Version: 1.3.21</h2>, Released: 2018-12-16
-------------------------------------

- Fix Github issue #121 and Github issue #123

<h2>Version: 1.3.20</h2>, Released: 2018-07-02
-------------------------------------

- Fix Github issue #114 (Py3.5 requires different open() syntax)

<h2>Version: 1.3.19</h2>, Released: 2018-06-23
-------------------------------------

- Fix Github issue #111 (banner parsing broken in some cases)

<h2>Version: 1.3.18</h2>, Released: 2018-06-09
-------------------------------------

- Add * to MANIFEST.in

<h2>Version: 1.3.17</h2>, Released: 2018-06-08
-------------------------------------

- Attempt to resolve Github issue #106

<h2>Version: 1.3.16</h2>, Released: 2018-06-01
-------------------------------------

- Add dns_query() zone transfer as text

<h2>Version: 1.3.15</h2>, Released: 2018-04-21
-------------------------------------

- Distrbution change

<h2>Version: 1.3.14</h2>, Released: 2018-04-21
-------------------------------------

- Attempt to fix unit tests

<h2>Version: 1.3.13</h2>, Released: 2018-04-21
-------------------------------------

- Fix Github issue #103, Python3 ccp_util imports

<h2>Version: 1.3.12</h2>, Released: 2018-04-16
-------------------------------------

- Upgrade comparison operations of IPv4Obj and IPv6Obj

<h2>Version: 1.3.11</h2>, Released: 2018-03-31
-------------------------------------

- Fix Github issue #101

<h2>Version: 1.3.10</h2>, Released: 2018-03-04
-------------------------------------

- Fix various bugs in dns_query()
- add a query duration to the DNSResponse() object

<h2>Version: 1.3.9</h2>, Released: 2018-03-03
------------------------------------

- Build dns_query() responses on a universal DNSResponse() object

<h2>Version: 1.3.8</h2>, Released: 2018-03-03
------------------------------------

- Fix Python3 packaging, Github issue #98

<h2>Version: 1.3.7</h2>, Released: 2018-03-03
------------------------------------

- [RELEASE BROKEN and removed from pypi]

<h2>Version: 1.3.6</h2>, Released: 2018-02-13
------------------------------------

- [RELEASE BROKEN and removed from pypi]

<h2>Version: 1.3.5</h2>, Released: 2018-02-13
------------------------------------

- [RELEASE BROKEN and removed from pypi]

<h2>Version: 1.3.4</h2>, Released: 2018-02-13
------------------------------------

- [RELEASE BROKEN and removed from pypi]

<h2>Version: 1.3.3</h2>, Released: 2018-02-13
------------------------------------

- [RELEASE BROKEN and removed from pypi]

<h2>Version: 1.3.2</h2>, Released: 2018-02-10
------------------------------------

- Add all_children flag to re_match_iter_typed() [RELEASE BROKEN]

<h2>Version: 1.3.1</h2>, Released: 2018-01-29
------------------------------------

- Raise DynamicErrorException on ipv4 dhcp interfaces

<h2>Version: 1.2.55</h2>, Released: 2018-01-25
-------------------------------------

- Add manual speed and duplex to models_nxos.py

<h2>Version: 1.2.54</h2>, Released: 2018-01-25
-------------------------------------

- Add manual speed and duplex to models_cisco.py

<h2>Version: 1.2.53</h2>, Released: 2018-01-25
-------------------------------------

- Attempt to fix Github issue #49

<h2>Version: 1.2.52</h2>, Released: 2018-01-25
-------------------------------------

- Alpha-quality nxos factory parser (ref: Github issue #71)

<h2>Version: 1.2.51</h2>, Released: 2018-01-24
-------------------------------------

- Fix packaging problem

<h2>Version: 1.2.50</h2>, Released: 2018-01-24
-------------------------------------

- Throw a ValueError on ipv4 dhcp factory interfaces

<h2>Version: 1.2.49</h2>, Released: 2017-07-23
-------------------------------------

- Fix doctest breakage

<h2>Version: 1.2.48</h2>, Released: 2017-07-23
-------------------------------------

- Fix Github issue #82

<h2>Version: 1.2.47</h2>, Released: 2017-03-05
-------------------------------------

- Fix Github issue #75, Github issue #76, Github issue #77

<h2>Version: 1.2.46</h2>, Released: 2017-01-09
-------------------------------------

- Normalize zero-padded IP address string inputs to IPv4Obj()

<h2>Version: 1.2.45</h2>, Released: 2017-01-05
-------------------------------------

- Add zero-padded ccp_util.IPv4Obj() strings, improve IPv4Obj() and IPv6Obj()

<h2>Version: 1.2.44</h2>, Released: 2016-11-25
-------------------------------------

- Improve parsing speed for the factory=True parser

<h2>Version: 1.2.43</h2>, Released: 2016-11-25
-------------------------------------

- Fix Github issue #63, add a new function: find_objects_w_all_children()

<h2>Version: 1.2.42</h2>, Released: 2016-11-24
-------------------------------------

- Fix Github issue #62, add a new object called CiscoRange()

<h2>Version: 1.2.41</h2>, Released: 2016-11-24
-------------------------------------

- Fix Github issue #51, Github issue #53, Github issue #57, Githbu issue #64, Github issue #65

<h2>Version: 1.2.40</h2>, Released: 2016-04-30
-------------------------------------

- Fix Github issue #44 (Could not parse 'ipv6 router ospf 6')
- Modify default value for access_vlan
- Add new is_portchannel property
- Update copyright dates
- Remove OSX from test matrix

<h2>Version: 1.2.39</h2>, Released: 2015-10-27
-------------------------------------

- Fix TravisCI breakage

<h2>Version: 1.2.38</h2>, Released: 2015-10-27
-------------------------------------

- Integrate PR #48, which fixes github issue #47

<h2>Version: 1.2.37</h2>, Released: 2015-07-06
-------------------------------------

- Fix Github issue #37 (sync_diff() includes double negatives)

<h2>Version: 1.2.36</h2>, Released: 2015-07-06
-------------------------------------

- Add dns6_lookup(), add tutorial

<h2>Version: 1.2.35</h2>, Released: 2015-07-03
-------------------------------------

- Fix issue with ipv6 route parsing

<h2>Version: 1.2.34</h2>, Released: 2015-07-03
-------------------------------------

- Add support for ipv6 static routes in models_cisco (Github issue #34)

<h2>Version: 1.2.33</h2>, Released: 2015-07-02
-------------------------------------

- Expand coverage of icmp and standard ACLs in models_asa

<h2>Version: 1.2.32</h2>, Released: 2015-07-01
-------------------------------------

- Add find_objects_dna()

<h2>Version: 1.2.31</h2>, Released: 2015-06-29
-------------------------------------

- Fix Github issue #39 (not parsing Junos comments correctly)

<h2>Version: 1.2.30</h2>, Released: 2015-06-27
-------------------------------------

- Enhance banner delimiter parsing

<h2>Version: 1.2.29</h2>, Released: 2015-06-27
-------------------------------------

- Add dns_lookup and reverse_dns_lookup in ccp_util

<h2>Version: 1.2.28</h2>, Released: 2015-06-27
-------------------------------------

- Fix build problem

<h2>Version: 1.2.27</h2>, Released: 2015-06-27
-------------------------------------

- termcolor -> colorama

<h2>Version: 1.2.27</h2>, Released: 2015-06-27
-------------------------------------

- Forgot to check in some updates...

<h2>Version: 1.2.26</h2>, Released: 2015-06-27
-------------------------------------

- Update debugging code

<h2>Version: 1.2.25</h2>, Released: 2015-06-23
-------------------------------------

- Modest ASAObjGroupNetwork speed improvements

<h2>Version: 1.2.24</h2>, Released: 2015-06-22
-------------------------------------

- Fix Github issue #41, improve IPv4Obj docs

<h2>Version: 1.2.23</h2>, Released: 2015-06-19
-------------------------------------

- Improve IPv4Obj parsing speed

<h2>Version: 1.2.22</h2>, Released: 2015-06-18
-------------------------------------

- Improve ASAAclLine Log level parsing support

<h2>Version: 1.2.21</h2>, Released: 2015-06-16
-------------------------------------

- Initial support for ASAAclLine parsing, partial commit for Github Issue #29

<h2>Version: 1.2.20</h2>, Released: 2015-06-11
-------------------------------------

- Increase ASA config parse speed (when parsed with factory=True)

<h2>Version: 1.2.19</h2>, Released: 2015-04-18
-------------------------------------

- Fix Github issue #33 Unicode path support, Github issue #36 Banner delimiter issues, Github issue #37 delete() broke in some situations

<h2>Version: 1.2.18</h2>, Released: 2015-04-08
-------------------------------------

- Fix Github issue #32 (ccp + py34 + windows broken).

<h2>Version: 1.2.17</h2>, Released: 2015-04-06
-------------------------------------

- Fix Github issue #31
- First steps towards IPv6Obj support.

<h2>Version: 1.2.16</h2>, Released: 2015-04-01
-------------------------------------

- Improve ip route detection in models_cisco, as requested by Github issue #30
- Convert more unit tests to native py.test format

<h2>Version: 1.2.15</h2>, Released: 2015-03-22
-------------------------------------

- Implement feature requested by Github issue #28 (Cisco ASA standby addrs), improve sync_diff() / fix bugs, add .geneology / .geneology_text features

<h2>Version: 1.2.14</h2>, Released: 2015-03-07
-------------------------------------

- Enhance config modification speed as documented in Github issue #26
- Implement find_interface_objects() as documented in Github issue #27
- Improved unit test coverage

<h2>Version: 1.2.13</h2>, Released: 2015-03-01
-------------------------------------

- Fix Github issue #25: Python3 bites me again

<h2>Version: 1.2.12</h2>, Released: 2015-03-01
-------------------------------------

- Fix Github issue #24: recursive dependencies in setup.py and ciscoconfparse/__init__.py

<h2>Version: 1.2.11</h2>, Released: 2015-03-01
-------------------------------------

- Converted unit-tests to py.test
- Fix Github issue #23 (banner detection bug), add sync_diff() feature from Github issue #22, improve setup.py script
- NOTE: going forward, sync_diff() will deprecate use of req_cfgspec_excl_diff()

<h2>Version: 1.2.10</h2>, Released: 2015-02-10
-------------------------------------

- Fix Github issue #21 in find_all_children(), update unit tests to detect github issue #21, add new-style example in examples/

<h2>Version: 1.2.9</h2>, Released: 2015-02-02
------------------------------------

- reduce package size, enhance generator support

<h2>Version: 1.2.8</h2>, Released: 2015-01-29
------------------------------------

- Add support for iterating over a generator (CiscoConfParse input, ref Github issue #19)

<h2>Version: 1.2.7</h2>, Released: 2015-01-26
------------------------------------

- Fix README, again
- pypi and github don't act the same way.

<h2>Version: 1.2.6</h2>, Released: 2015-01-26
------------------------------------

- Fix README, because it looks awful on pypi (they don't allow twitter embedding)

<h2>Version: 1.2.5</h2>, Released: 2015-01-26
------------------------------------

- Add 'indent' and 'auto_indent' options to append_to_family()

<h2>Version: 1.2.4</h2>, Released: 2015-01-25
------------------------------------

- Fix _unique_OBJ() to work in Python2.6, which doesn't have set comprehensions

<h2>Version: 1.2.3</h2>, Released: 2015-01-25
------------------------------------

- Add find_objects_w_parents()

<h2>Version: 1.2.2</h2>, Released: 2015-01-25
------------------------------------

- Add support for parsing Junos as a Cisco-IOS-style configuration github issue #17, fixed github issue #16 [Banners with comment characters in them are not parsed correctly], fixed github issue #15 [CiscoConfParse.append('config_line_here') is a null operation]

<h2>Version: 1.2.1</h2>, Released: 2015-01-24
------------------------------------

- More parsing speed optimizations, particularly in banner parsing
- Ripped out old, unused code

<h2>Version: 1.2.0</h2>, Released: 2015-01-24
------------------------------------

- Major parser rewrite: streamline parser, less spaghetti code, add ccp_abc.is_config_line
- This version *should* parse Cisco Nexus syntax now (but parse Cisco Nexus configs with ignore_blank_lines=False)
- Implement enhancement in github issue #6

<h2>Version: 1.1.24</h2>, Released: 2015-01-23
-------------------------------------

- Fix github issue #13 (ciscoconfparse did not parse correctly when ignore_blank_lines=True)
- some parent assignments were missed if blank lines were in the configuration

<h2>Version: 1.1.23</h2>, Released: 2015-01-17
-------------------------------------

- Update copyrights to 2015, use list comprehension in re_search_children() to increase speed

<h2>Version: 1.1.22</h2>, Released: 2014-12-04
-------------------------------------

- More bugfixes in ccp_util.IPv4Obj()
- IPv4Obj should mostly be stable and reliable now
- Added solid unit test coverage for IPv4Obj()

<h2>Version: 1.1.21</h2>, Released: 2014-12-03
-------------------------------------

- Major bugfixes in IPv4Obj, convert results from ordinal_list() from a python list to a python tuple

<h2>Version: 1.1.20</h2>, Released: 2014-11-16
-------------------------------------

- Remove numpydoc

<h2>Version: 1.1.19</h2>, Released: 2014-11-16
-------------------------------------

- Fix for Read the Docs publication

<h2>Version: 1.1.18</h2>, Released: 2014-11-15
-------------------------------------

- Doc reformating
- remove duplicated ccp_util.IPv4Obj method

<h2>Version: 1.1.17</h2>, Released: 2014-11-13
-------------------------------------

- More doc reformating
- add recursion for ASA group-objects on object-groups

<h2>Version: 1.1.16</h2>, Released: 2014-11-13
-------------------------------------

- Reformat docs
- improve ASAConfigList()

<h2>Version: 1.1.15</h2>, Released: 2014-11-12
-------------------------------------

- Add gt and lt comparision methods to ccp_util.IPv4Obj()
- consolidate test scripts into one shell script

<h2>Version: 1.1.14</h2>, Released: 2014-11-11
-------------------------------------

- Fix Python3 breakage in 1.1.13

<h2>Version: 1.1.13</h2>, Released: 2014-11-11
-------------------------------------

- Fix github issues #10 and #11
- Improve Cisco ASA parsing support

<h2>Version: 1.1.12</h2>, Released: 2014-09-19
-------------------------------------

- Enhance support for ccp_util.IPv4Obj, add Cisco ASA parsing in models_asa

<h2>Version: 1.1.11</h2>, Released: 2014-09-18
-------------------------------------

- Fix Github Issue #9

<h2>Version: 1.1.10</h2>, Released: 2014-09-05
-------------------------------------

- Enhance AAA parsing in models_cisco

<h2>Version: 1.1.9</h2>, Released: 2014-09-04
------------------------------------

- Enhance AAA parsing in models_cisco

<h2>Version: 1.1.8</h2>, Released: 2014-09-03
------------------------------------

- Add initial models_cisco support for parsing basic AAA configuration

<h2>Version: 1.1.7</h2>, Released: 2014-09-02
------------------------------------

- Fix TravisCI failures

<h2>Version: 1.1.6</h2>, Released: 2014-09-02
------------------------------------

- Replace ipaddr.IPv4Network with ccp_util.IPv4Obj for more consistency
- Started adding unittests for models_cisco functionality
- Added local_py/ipaddress.py

<h2>Version: 1.1.5</h2>, Released: 2014-08-29
------------------------------------

- Add IOS Interface object functions in models_cisco to parse port number, interface type, etc
- Added the "Huge Ugly Warning" to models_cisco
- I also removed an unnecessary isinstance() in ccp_abc to improve performance.

<h2>Version: 1.1.4</h2>, Released: 2014-08-18
------------------------------------

- Major speed improvement when parsing large configurations (~45% faster than some previous CiscoConfParse versions)

<h2>Version: 1.1.3</h2>, Released: 2014-07-29
------------------------------------

- Fix is_switchport parsing

<h2>Version: 1.1.2</h2>, Released: 2014-05-15
------------------------------------

- Fix Python3 packaging (related to missing PEP366 compliance), more relative ipaddr imports

<h2>Version: 1.1.1</h2>, Released: 2014-05-15
------------------------------------

- Fix Python3 breakage due to xrange

<h2>Version: 1.1.0</h2>, Released: 2014-05-14
------------------------------------

- Improve parsing speed
- Simplify debugging logs.

<h2>Version: 1.0.7</h2>, Released: 2014-05-07
------------------------------------

- Add build automation improvements
- Modify default value for ipv4_network_object()

<h2>Version: 1.0.6</h2>, Released: 2014-05-06
------------------------------------

- Improve docs

<h2>Version: 1.0.5</h2>, Released: 2014-05-06
------------------------------------

- Improve docs

<h2>Version: 1.0.4</h2>, Released: 2014-05-04
------------------------------------

- Add new find_objects_w_child() and find_objects_wo_child() methods
- Add more documentation.

<h2>Version: 1.0.3</h2>, Released: 2014-05-03
------------------------------------

- Removed all examples in README.rst, and expanded those in the web documentation
- More non-trivial doc updates

<h2>Version: 1.0.2</h2>, Released: 2014-05-02
------------------------------------

- Even more documentation improvements
- Changed default value of IOSCfgLine.re_search / re_match from None to "".

<h2>Version: 1.0.1</h2>, Released: 2014-05-01
------------------------------------

- More documentation improvements
- Fix problem with experimental IOSCfgLine factory feature.

<h2>Version: 1.0.0</h2>, Released: 2014-04-30
------------------------------------

- Significant documentation overhaul
- Add documentation of new IOSCfgLine methods introduced in 0.9.10, as well as making the documentation more friendly to mobile devices
- substitute the sphinx_bootstrap_theme instead of the sphinxdoc theme
- Add line highlights in code examples which hopefully make complex examples more clear.

<h2>Version: 0.9.35</h2>, Released: 2014-04-30
-------------------------------------

- Update docstrings with more examples
- Improve doc Makefile

<h2>Version: 0.9.34</h2>, Released: 2014-04-29
-------------------------------------

- Update IOSCfgLine objects with a recursive delete, which will automatically delete children if the parent is deleted
- First steps toward a long-overdue documentation update
- A lot more is left to do.

<h2>Version: 0.9.33</h2>, Released: 2014-04-25
-------------------------------------

- Add unit test for banner parsing coverage

<h2>Version: 0.9.32</h2>, Released: 2014-04-22
-------------------------------------

- Fix banner parent-child relationships for Github Issue #4
- Improve parsing speed with pre-compiled regex in _mark_banner()
- Update example in README.rst
- Add new ignore_rgx option to the re_sub() line-object method.

<h2>Version: 0.9.31</h2>, Released: 2014-04-15
-------------------------------------

- Fix DBGFLAG issue in CiscoConfParse() for Github Issue #5

<h2>Version: 0.9.30</h2>, Released: 2014-04-04
-------------------------------------

- Add ignore_blank_lines option in CiscoConfParse() for Github Issue #3

<h2>Version: 0.9.29</h2>, Released: 2014-04-04
-------------------------------------

- Fix typo in CiscoConfParse()

<h2>Version: 0.9.28</h2>, Released: 2014-04-03
-------------------------------------

- Added new linesplit_rgx option in CiscoConfParse() to help user who filed Github Issue #2
- no defaults were changed
- Added Python 3.4 in .travis.yml in hopes of testing against Python 3.4

<h2>Version: 0.9.27</h2>, Released: 2014-03-26
-------------------------------------

- Added a new append_line() method to ciscoconfparse.

<h2>Version: 0.9.26</h2>, Released: 2014-03-19
-------------------------------------

- Finally caved and left my copy of ipaddr that's modified to work with python3 in ciscoconfparse/ipaddr.py, where Travis can find it

<h2>Version: 0.9.25</h2>, Released: 2014-03-19
-------------------------------------

- Improve speed in find_blocks(), as requested by Github Issue #1
- Minor change to improve Travis CI builds

<h2>Version: 0.9.24</h2>, Released: 2014-03-13
-------------------------------------

- Fix broken Travis CI builds (because of where I moved the ipaddr module)
- Added new functionality in models_cisco (still alpha code at this point)

<h2>Version: 0.9.23</h2>, Released: 2014-03-05
-------------------------------------

- Modify ipv4_addr_object default value in models_cisco
- move ipaddr module to a local folder

<h2>Version: 0.9.22</h2>, Released: 2014-02-28
-------------------------------------

- Add PIM interface support in models_cisco (still alpha at this point)

<h2>Version: 0.9.21</h2>, Released: 2014-02-26
-------------------------------------

- Fix Python3.2 build (note to self..
- u'' isn't supported until Python3.3).

<h2>Version: 0.9.20</h2>, Released: 2014-02-26
-------------------------------------

- Updated README with other Cisco IOS configuration resources
- Fixed problems in models_cisco
- improved / added docstrings
- Improve build workflow.

<h2>Version: 0.9.19</h2>, Released: 2014-02-17
-------------------------------------

- Fixed Python3 build issue in 0.9.18

<h2>Version: 0.9.18</h2>, Released: 2014-02-17
-------------------------------------

- Updated README.rst
- Added new IOSCfgLine.lineage() & CiscoConfParse.lineage() methods (experimental at this point)
- Added IOSCfgLine.all_children
- "President's Day holiday release"

<h2>Version: 0.9.17</h2>, Released: 2014-02-15
-------------------------------------

- Updated README.rst, add MANIFEST.in and requirements.txt
- Several new object-oriented methods added.

<h2>Version: 0.9.16</h2>, Released: 2014-02-12
-------------------------------------

- Fix bug in ccp_abc.insert_before() and insert_after()
- Made updates to README.rst
- Ripped out linenum references in various insert methods

<h2>Version: 0.9.15</h2>, Released: 2014-02-10
-------------------------------------

- Updated README.rst with inline example

<h2>Version: 0.9.14</h2>, Released: 2014-02-09
-------------------------------------

- Support for Travis CI
- Fix Travis CI build failures on Python3.3 (due to how __hash__() is computed).

<h2>Version: 0.9.13</h2>, Released: 2014-02-09
-------------------------------------

- Fixed Python3 compatibility, which broke a few builds ago
- Including ipaddr-py (patched for Python3) until versions of Python3 typically include it (right now, Debian 7.3 has Python3.2 without ipaddr-py)

<h2>Version: 0.9.12</h2>, Released: 2014-02-08
-------------------------------------

- Fixed bug in ccp_abc.py
- reworked comment detection
- performance improvements

<h2>Version: 0.9.11</h2>, Released: 2014-02-04
-------------------------------------

- Bugfixes

<h2>Version: 0.9.10</h2>, Released: 2014-02-03
-------------------------------------

- Bugfixes and more performance improvements
- Doubled number of unit tests
- Added alpha-quality code in another module.

<h2>Version: 0.9.9</h2>, Released: 2014-01-31
------------------------------------

- Major insert() / append() performance improvements
- Add optional interface-aware config line factory objects
- Add abstract base classes
- Add atomic options to insert_before(), insert_after(), etc...

<h2>Version: 0.9.8</h2>, Released: 2014-01-24
------------------------------------

- Remove debugging info

<h2>Version: 0.9.7</h2>, Released: 2014-01-24
------------------------------------

- Major rewrite, removed support for old python versions
- Ripped out inefficient code I wrote as a python newbie, added more idiomatic structures in various places
- Also added support for inserting and deleting lines via insert_before(), insert_after(), and insert_after_child()

<h2>Version: 0.9.6</h2>, Released: 2014-01-06
------------------------------------

- Update copyright to 2014
- Rewrite unit tests

<h2>Version: 0.9.5</h2>, Released: 2013-12-31
------------------------------------

- Add replace_lines() function, enhance unit tests, added an exactmatch option on _find_line_OBJ()
- Updated code copyright to include 2014

<h2>Version: 0.9.4</h2>, Released: 2013-08-14
------------------------------------

- Add Python3 compliance
- other minor tweaks

<h2>Version: 0.9.3</h2>, Released: 2013-05-11
------------------------------------

- Added methods to IOSCfgLine: __eq__(), __hash__(), __lt__(), __gt__(), as well as simplifying several other methods
- Misc code maintenance...

<h2>Version: 0.9.2</h2>, Released: 2013-05-09
------------------------------------

- Add find_children_w_parents() method..
- tidy up unit-tests

<h2>Version: 0.9.1</h2>, Released: 2012-12-31
------------------------------------

- Improve docs with numpydoc and intersphinx links
- Add more examples / doctests
- Renamed internal CiscoConfParse methods with a leading _ to make Sphinx documentation more intuitive...

<h2>Version: 0.9.0</h2>, Released: 2012-12-30
------------------------------------

- Add RST documentation into the archives and fix more build issues

<h2>Version: 0.8.6</h2>, Released: 2012-12-30
------------------------------------

- Fix packaging problems introduced when I switched to a native mercurial repository (examples/* and configs/* were not automatically packaged in the .egg / .tar.gz anymore...)

<h2>Version: 0.8.5</h2>, Released: 2012-12-29
------------------------------------

- Added custom comment delimiters that were in the 0.8.3a private build
- Converted the unicode backslash to a true unicode instance.

<h2>Version: 0.8.4</h2>, Released: 2012-12-29
------------------------------------

- Add doctests, code maintenance, and more documentation fixes
- Improved examples/req_cfgspec_all_diff.py and examples/req_cfgspec_excl_diff.py.

<h2>Version: 0.8.3</h2>, Released: 2009-10-16
------------------------------------

- Documentation updates
- PEP8 formatting

<h2>Version: 0.8.2</h2>, Released: 2009-08-08
------------------------------------

- Fixed a fatal crash in find_blocks()

<h2>Version: 0.8.1</h2>, Released: 2009-07-19
------------------------------------

- Code reorganization
- Fixed a bad RuntimeError
- Promoted to production-quality at this point

<h2>Version: 0.8.0</h2>, Released: 2007-10-11
------------------------------------

- Removed residual internal debugging from the CiscoPassword class
- Added an 'ignore_ws' options to all public methods, except req_cfgspec_excl_diff
- this option will make the method's matches ignore whitespace differences (useful in some CatOS configurations)
- After much deliberation, I have removed the explicit 'False' return values for methods that do not match
- instead I am returning an empty list (which will test False)
- Apologies for breaking any existing code, but I decided against leaving beta with this behavior
- Removed all sys.exit(0) statements in favor of raising a RuntimeError.

<h2>Version: 0.7.5</h2>, Released: 2007-08-04
------------------------------------

- Fixed a bug in the parse() method, which was associating grandchildren as children of the grandparent
- Added unit tests.

<h2>Version: 0.7.0</h2>, Released: 2007-08-03
------------------------------------

- Added an optional parameter to the find_lines(), find_children(), find_all_children(), and find_blocks() methods
- This parameter will allow the user to specify whether he wants an "exact" match or a normal regex match
- Also fixed a bug that broke parsing of configs with an indented line at the very end.

<h2>Version: 0.6.8</h2>, Released: 2007-08-02
------------------------------------

- Ported fixes to the CiscoPassword class from the cisco_decrypt package
- Notably, there were crashes when it was called with certain unencrypted passwords.

<h2>Version: 0.6.7</h2>, Released: 2007-08-01
------------------------------------

- Fixed bug where some methods didn't return False when no diffs were found

<h2>Version: 0.6.6</h2>, Released: 2007-07-30
------------------------------------

- Added password decryption options to the command-line help menu
- Modified all diff functions to return False if no diffs are found

<h2>Version: 0.6.5</h2>, Released: 2007-07-28
------------------------------------

- Fixed another CiscoPassword bug
- Added warning if CiscoPassword decryption fails
- Added command-line functionality for improved interoperability with other languages (and shell-usage if you like).

<h2>Version: 0.6.1</h2>, Released: 2007-07-26
------------------------------------

- Cosmetic restructuring of code

<h2>Version: 0.6.0</h2>, Released: 2007-07-21
------------------------------------

- Revised APIs
- Existing APIs should be stable now
