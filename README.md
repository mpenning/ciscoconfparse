ciscoconfparse
==============

[![Github unittest workflow][4]][5] [![Code Health][37]][38] [![git commits][41]][42] [![Repo Code Grade][43]][44]  [![Version][2]][3] [![Downloads][6]][7] [![License][8]][9]


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

Is this a tool, or is it artwork?
---------------------------------

That depends on who you ask.  Many companies use CiscoConfParse as part of their
network engineering toolbox; others regard it as a form of artwork.

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

- The latest copy of the docs are [archived on the web][15]
- There is also a [CiscoConfParse Tutorial][16]

Editing the Package
-------------------

-   `git clone https://github.com/mpenning/ciscoconfparse`
-   `cd ciscoconfparse`
-   `git checkout -b develop`
-   Add / modify / delete on the `develop` branch
-   `make test`
-   If tests run clean, `git commit` all the pending changes on the `develop` branch
-   (as required) Edit the version number in [pyproject.toml][12]
-   `git checkout main`
-   `git merge develop`
-   `make test`
-   `make repo-push`
-   `make pypi`

Pre-requisites
--------------

[The ciscoconfparse python package][3] requires Python versions 3.7+ (note: Python version 3.7.0 has a bug - ref [Github issue \#117][18], but version 3.7.1 works); the OS should not matter.

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

Unit-Tests
----------

The project\'s [test workflow][1] checks ciscoconfparse on Python versions 3.7 and higher, as well as a [pypy JIT][22] executable.

Click the image below for details; the current build status is: [![Github unittest status][4]][5]

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

- Copyright (C) 2021-2023 David Michael Pennington
- Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems (post-acquisition: Cisco acquired ThousandEyes)
- Copyright (C) 2019 David Michael Pennington at ThousandEyes
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
