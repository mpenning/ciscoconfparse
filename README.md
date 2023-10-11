ciscoconfparse
==============

[![Github unittest workflow][4]][5]
[![SonarCloud][51]][52] [![SonarCloud Maintainability Rating][53]][54] [![SonarCloud Lines of Code][55]][56] [![SonarCloud Code Smells][57]][58]
[![Snyk Package Health][37]][38] [![CodeFactor Code Health][43]][44] [![Codacy Code Health][46]][47]
[![git commits][41]][42] [![Version][2]][3] [![Downloads][6]][7] [![License][8]][9]


Introduction: What is ciscoconfparse?
-------------------------------------

Short answer: ciscoconfparse is a [Python][10] library
that helps you quickly answer questions like these about your
Cisco configurations:

- What interfaces are shutdown?
- Which interfaces are in trunk mode?
- What address and subnet mask is assigned to each interface?
- Which interfaces are missing a critical command?
- Is this configuration missing a standard config line?

It can help you:

- Audit existing router / switch / firewall / wlc configurations
- Modify existing configurations
- Build new configurations

Speaking generally, the library examines an IOS-style config and breaks
it into a set of linked parent / child relationships. You can perform
complex queries about these relationships.

[![Cisco IOS config: Parent / child][11]][11]

Usage
-----

The following code will parse a configuration stored in
\'exampleswitch.conf\' and select interfaces that are shutdown.

```python
from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

for intf_obj in parse.find_objects_w_child('^interface', '^\s+shutdown'):
    print("Shutdown: " + intf_obj.text)
```

The next example will find the IP address assigned to interfaces.

```python
from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

for intf_obj in parse.find_objects('^interface'):

    intf_name = intf_obj.re_match_typed('^interface\s+(\S.+?)$')

    # Search children of all interfaces for a regex match and return
    # the value matched in regex match group 1.  If there is no match,
    # return a default value: ''
    intf_ip_addr = intf_obj.re_match_iter_typed(
        r'ip\saddress\s(\d+\.\d+\.\d+\.\d+)\s', result_type=str,
        group=1, default='')
    print("{0}: {1}".format(intf_name, intf_ip_addr))
```

Are there private copies of CiscoConfParse()?
---------------------------------------------

Yes.  [Cisco Systems][27] maintains their own copy of `CiscoConfParse()`. The terms of the GPLv3
license allow this as long as they don't distribute their modified private copy in
binary form.  Also refer to this [GPLv3 License primer / GPLv3 101][45].  Officially, [modified
copies of CiscoConfParse source-code must also be licensed as GPLv3][45].

Dear [Cisco Systems][27]: please consider porting your improvements back into
the [`github ciscoconfparse repo`](https://github.com/mpenning/ciscoconfparse).

Dependencies
------------

- [Python 3](https://python.org/)
- [passlib](https://github.com/glic3rinu/passlib)
- [toml](https://github.com/uiri/toml)
- [dnspython](https://github.com/rthalley/dnspython)
- [loguru](https://github.com/Delgan/loguru)
- [deprecated](https://github.com/tantale/deprecated)

What if we don\'t use Cisco IOS?
--------------------------------

Don\'t let that stop you.

As of CiscoConfParse 1.2.4, you can parse [brace-delimited configurations][13] into a Cisco IOS style (see [Github Issue \#17][14]), which means that CiscoConfParse can parse these configurations:

- Juniper Networks Junos
- Palo Alto Networks Firewall configurations
- F5 Networks configurations

CiscoConfParse also handles anything that has a Cisco IOS style of configuration, which includes:

- Cisco IOS, Cisco Nexus, Cisco IOS-XR, Cisco IOS-XE, Aironet OS, Cisco ASA, Cisco CatOS
- Arista EOS
- Brocade
- HP Switches
- Force 10 Switches
- Dell PowerConnect Switches
- Extreme Networks
- Enterasys
- Screenos

Docs
----

- Blogs
  - Kirk Byers published [a ciscoconfparse blog piece](https://pynet.twb-tech.com/blog/parsing-configurations-w-ciscoconfparse.html)
  - Henry Ölsner published [a ciscoconfparse blog piece](https://codingnetworker.com/2016/06/parse-cisco-ios-configuration-ciscoconfparse/)
- The latest copy of the docs are [archived on the web][15]
- There is also a [CiscoConfParse Tutorial][16]

Installation and Downloads
--------------------------

-   Use `poetry` for Python3.x\... :

        python -m pip install ciscoconfparse

If you\'re interested in the source, you can always pull from the [github repo][17]:

- Download from [the github repo][17]: :

        git clone git://github.com/mpenning/ciscoconfparse
        cd ciscoconfparse/
        python -m pip install .

Github Star History
-------------------

[![Github Star History Chart][40]][40]

Interesting Users (and some downstream projects)
------------------------------------------------

The following are featured [CiscoConfParse](https://github.com/mpenning/ciscoconfparse/) users / projects:

- [salt](https://github.com/saltstack/salt)
- [suzieq](https://github.com/netenglabs/suzieq):  SuzieQ collects, normalizes, and stores timestamped data that is otherwise only available to engineers by logging into each device, providing a rich data lake that can be queried and leveraged for next generation monitoring and alerting
- [netwalk](https://github.com/icovada/netwalk): Python library to discover, parse, analyze and change Cisco switched networks
- [netlint](https://github.com/Kircheneer/netlint)
- [cisco_switchport_auditor](https://github.com/corvese/cisco_switchport_auditor): Parses Cisco switch configuration into Switch & Interface objects to access configuration details of the aforementioned in a programatic manner. Works with SSH, RESTCONF, or with running/start-up config files.
- [nipper-ng](https://github.com/arpitn30/nipper-ng): a network security analyzer
- [pynipper-ng](https://github.com/syn-4ck/pynipper-ng): a network security analyzer
- [build_fabric](https://github.com/sjhloco/build_fabric): Build a declarative Cisco NXOS leaf and spine fabric using Ansible
- [junos-ansible](https://github.com/yzguy/junos-ansible)
- [faddr](https://github.com/kido5217/faddr)
- [NetOpsNornir](https://github.com/wangcongxing/NetOpsNornir/)
- [adala](https://github.com/blindhog/adala): Extract useful information about your Cisco network
- [xlina](https://github.com/blindhog/xlina):
  - organize_acls.py: Extract and organize access-list configurations and organizes associated objects and object-groups.
  - organize_anyconnect.py: Extract and organize Anyconnect profiles and associated group policies, auth servers, access-lists, etc
  - organize_static_nats.py: Extract and organize static nat configurations and associated objects and object-groups
  - organize_auto_nat.py: Extract and organize auto nat configurations with associated objects
  - organize_crypto_maps.py: Extract and organize crypto map configurations and associated access-lists, transform-sets, tunnel-groups, etc
- [Catalyst_2_Meraki_Config_Checker](https://github.com/fadysharobeem/Catalyst_2_Meraki_Config_Checker): Check the Cisco Catalyst configuration text file and verify if they are supported by the Meraki MS platform.
- [parse_nxos_config](https://github.com/ocptech/parse_nxos_config): Generates an Excel file with the information gathered from running-config file from Cisco NXOS
- [Nornir3_CDP_map](https://github.com/nouse4it/Nornir3_CDP_map): Set interface descriptions by looking at the hostname of its CDP neighbor
- [devicebanner](https://github.com/labeveryday/devicebanner/): Update the banner message of the day on network devices
- [iosconfigslicer](https://github.com/imanassypov/iosconfigslicer): Simple script to slice Cisco configuration file, and replicate sections of the config via SSH to another device
- [ciscocfg](https://github.com/Mareel-io/ciscocfg): a simple RPCd for ciscoconfparse
- [confParser](https://github.com/yshornikov/confParser/): SSH with paramiko, and dump information about your configs into sqllite3 / Excel
- [parse_config](https://github.com/Sergey-Link/parse_config/): Dump information about your Vlans / VRFs to excel
- Finally, _[Cisco Systems](https://cisco.com/) Product Engineering and Advanced Services_

Other Useful Network Management Projects
----------------------------------------

- [netbox](https://github.com/netbox-community/netbox/): NetBox is the source of truth for everything on your network, from physical components like power systems and cabling to virtual assets like IP addresses and VLANs
  - [ntc-netbox-plugin-onboarding](https://github.com/networktocode/ntc-netbox-plugin-onboarding): A plugin for NetBox to easily onboard new devices.
- [nautobot](https://github.com/nautobot/nautobot): Network Source of Truth & Network Automation Platform.
- [nornir](https://github.com/nornir-automation/nornir): Network Automation via Plugins - A pluggable multi-threaded framework with inventory management to help operate collections of devices
- [network-importer](https://github.com/networktocode/network-importer/): The network importer is a tool/library to analyze and/or synchronize an existing network with a Network Source of Truth (SOT), it's designed to be idempotent and by default it's only showing the difference between the running network and the remote SOT.
- [nuts](https://github.com/network-unit-testing-system/nuts): NUTS defines a desired network state and checks it against a real network using pytest and nornir.
- [jerikan](https://vincent.bernat.ch/en/blog/2021-network-jerikan-ansible):
- [nettowel](https://github.com/InfrastructureAsCode-ch/nettowel/): Collection of useful network automation functions
- [napalm-panos](https://github.com/napalm-automation-community/napalm-panos)
- [assessment-cmds](https://github.com/blindhog/assessment-cmds/): Useful show commands to check your Cisco router's health
- [learn-to-cloud](https://github.com/labeveryday/learn-to-cloud): Primer for Cloud-computing fundamentals

What is the pythonic way of handling script credentials?
--------------------------------------------------------

1. Never hard-code credentials
2. Use [python-dotenv](https://github.com/theskumar/python-dotenv)

Are you releasing licensing besides GPLv3?
------------------------------------------

It is a [work in progress](https://github.com/mpenning/ciscoconfparse/issues/270)

Is this a tool, or is it artwork?
---------------------------------

That depends on who you ask.  Many companies use CiscoConfParse as part of their
network engineering toolbox; others regard it as a form of artwork.

Pre-requisites
--------------

[The ciscoconfparse python package][3] requires Python versions 3.7+ (note: Python version 3.7.0 has a bug - ref [Github issue \#117][18], but version 3.7.1 works); the OS should not matter.



Other Resources
---------------

- [Dive into Python3](http://www.diveintopython3.net/) is a good way to learn Python
- [Team CYMRU][30] has a [Secure IOS Template][29], which is especially useful for external-facing routers / switches
- [Cisco\'s Guide to hardening IOS devices][31]
- [Center for Internet Security Benchmarks][32] (An email address, cookies, and javascript are required)

Bug Tracker and Support
-----------------------

- Please report any suggestions, bug reports, or annoyances with a [github bug report][24].
- If you\'re having problems with general python issues, consider searching for a solution on [Stack Overflow][33].  If you can\'t find a solution for your problem or need more help, you can [ask on Stack Overflow][34] or [reddit/r/Python][39].
- If you\'re having problems with your Cisco devices, you can contact:
  - [Cisco TAC][28]
  - [reddit/r/Cisco][35]
  - [reddit/r/networking][36]
  - [NetworkEngineering.se][23]

Unit-Tests and Development
--------------------------

The project\'s [test workflow][1] checks ciscoconfparse on Python versions 3.7 and higher, as well as a [pypy JIT][22] executable.

Caveats:

- At this point, [CiscoConfParse][3] does NOT adhere to [Semantic Versioning][49]
- Although we added [commitizen][48] as a dev dependency, we are NOT enforcing commit rules (such as [Conventional Commits][50]) yet.

Click the image below for details; the current build status is: [![Github unittest status][4]][5]

Editing the Package
-------------------

-   `git clone https://github.com/mpenning/ciscoconfparse`
-   `cd ciscoconfparse`
-   `git checkout -b develop`
-   Add / modify / delete on the `develop` branch
-   `make test`
-   If tests run clean, `git commit` all the pending changes on the `develop` branch
-   If you plan to publish this as an official version rev, edit the version number in [pyproject.toml][12].  In the future, we want to integrate `commitizen` to manage versioning.
-   `git checkout main`
-   `git merge develop`
-   `make test`
-   `git push origin main`
-   `make pypi`

Sphinx Documentation
--------------------

Building the ciscoconfparse documentation tarball comes down to this one wierd trick:

- `cd sphinx-doc/`
- `pip install -r ./requirements.txt;  # install Sphinx dependencies`
- `pip install -r ../requirements.txt; # install ccp dependencies`
- `make html`

License and Copyright
---------------------

[ciscoconfparse][3] is licensed [GPLv3][21]

- Copyright (C) 2022-2023 David Michael Pennington
- Copyright (C) 2022 David Michael Pennington at WellSky
- Copyright (C) 2022 David Michael Pennington
- Copyright (C) 2019-2021 David Michael Pennington at Cisco Systems / ThousandEyes
- Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
- Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corp
- Copyright (C) 2007-2011 David Michael Pennington

The word \"Cisco\" is a registered trademark of [Cisco Systems][27].

Author
------

[ciscoconfparse][3] was written by [David Michael Pennington][25] (mike \[\~at\~\] pennington \[.dot.\] net).


  [1]: https://github.com/mpenning/ciscoconfparse/blob/main/.github/workflows/tests.yml
  [2]: https://img.shields.io/pypi/v/ciscoconfparse.svg
  [3]: https://pypi.python.org/pypi/ciscoconfparse/
  [4]: https://github.com/mpenning/ciscoconfparse/actions/workflows/tests.yml/badge.svg
  [5]: https://github.com/mpenning/ciscoconfparse/actions/workflows/tests.yml
  [6]: https://pepy.tech/badge/ciscoconfparse
  [7]: https://pepy.tech/project/ciscoconfparse
  [8]: http://img.shields.io/badge/license-GPLv3-blue.svg
  [9]: https://www.gnu.org/copyleft/gpl.html
  [10]: https://www.python.org
  [11]: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
  [12]: https://github.com/mpenning/ciscoconfparse/blob/main/pyproject.toml
  [13]: https://github.com/mpenning/ciscoconfparse/blob/master/configs/sample_01.junos
  [14]: https://github.com/mpenning/ciscoconfparse/issues/17
  [15]: http://www.pennington.net/py/ciscoconfparse/
  [16]: http://pennington.net/tutorial/ciscoconfparse/ccp_tutorial.html
  [17]: https://github.com/mpenning/ciscoconfparse
  [18]: https://github.com/mpenning/ciscoconfparse/issues/117
  [19]: https://github.com/mpenning/ciscoconfparse/issues/13
  [20]: https://github.com/CrackerJackMack/
  [21]: http://www.gnu.org/licenses/gpl-3.0.html
  [22]: https://pypy.org
  [23]: https://networkengineering.stackexchange.com/
  [24]: https://github.com/mpenning/ciscoconfparse/issues/new/choose
  [25]: https://github.com/mpenning
  [26]: https://github.com/muir
  [27]: https://www.cisco.com/
  [28]: https://www.cisco.com/go/support
  [29]: https://www.cymru.com/Documents/secure-ios-template.html
  [30]: https://team-cymru.com/company/
  [31]: http://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html
  [32]: https://learn.cisecurity.org/benchmarks
  [33]: https://stackoverflow.com
  [34]: http://stackoverflow.com/questions/ask
  [35]: https://www.reddit.com/r/Cisco/
  [36]: https://www.reddit.com/r/networking
  [37]: https://snyk.io/advisor/python/ciscoconfparse/badge.svg
  [38]: https://snyk.io/advisor/python/ciscoconfparse
  [39]: https://www.reddit.com/r/Python/
  [40]: https://api.star-history.com/svg?repos=mpenning/ciscoconfparse&type=Date
  [41]: https://img.shields.io/github/commit-activity/m/mpenning/ciscoconfparse
  [42]: https://img.shields.io/github/commit-activity/m/mpenning/ciscoconfparse
  [43]: https://www.codefactor.io/Content/badges/B.svg
  [44]: https://www.codefactor.io/repository/github/mpenning/ciscoconfparse/
  [45]: https://fossa.com/blog/open-source-software-licenses-101-gpl-v3/
  [46]: https://app.codacy.com/project/badge/Grade/4774ebb0292d4e1d9dc30bf263d9df14
  [47]: https://app.codacy.com/gh/mpenning/ciscoconfparse/dashboard
  [48]: https://commitizen-tools.github.io/commitizen/
  [49]: https://semver.org/
  [50]: https://www.conventionalcommits.org/en/v1.0.0/
  [51]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse&metric=alert_status
  [52]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse
  [53]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse&metric=sqale_rating
  [54]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse
  [55]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse&metric=ncloc
  [56]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse
  [57]: https://sonarcloud.io/api/project_badges/measure?project=mpenning_ciscoconfparse&metric=code_smells
  [58]: https://sonarcloud.io/summary/new_code?id=mpenning_ciscoconfparse
