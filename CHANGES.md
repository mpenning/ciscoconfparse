## Version: GIT HEAD

- Released: Not released
- Summary:
    - Insert something here

## Version: 1.7.16

- Released: 2023-02-13
- Summary:
    - Add initial support for `CiscoConfParse()` object instance support in `HDiff()`
    - Add `HDiff()` documentation
    - Convert `diff_word` and `diff_side` `HDiff()` attributes to `HDiff()` getter / setter methods
    - Improve `BaseCfgLine()` initialization
    - Improve `BaseCfgLine()` attribute handling: `.text`, `.indent`
    - Remove loop in `testValues_find_children()` to simplify test flow.
    - Add `ccp_util.fix_repeated_words()`
    - Change `allow_enqueue` parameter to `enqueue` in `ccp_logger_control()`.  `allow_enqueue` is not a valid `loguru` parameter name.


## Version: 1.7.15

- Released: 2023-02-10
- Summary:
    - Streamline `_bootstrap_from_text()` code.
    - Extract common code into `_build_banner_re_ios()` (for nxos and ios)
    - Extract common object init code from `CiscoConfParse()._bootstrap_obj_init_foo()` (where foo = asa, ios, nxos and junos) into `_build_cfgobj_from_text()`.
    - Remove the unused `output_format` parameter from `HDiff()`
    - Add `HDiff()` docstrings

## Version: 1.7.14

- Released: 2023-02-06
- Summary:
    - Allow `CiscoConfParse()` to parse an empty configuration command list i.e. `CiscoConfParse([])`; remove the `ValueError()` raised on parsing an empty config.
    - Re-implement and simplify `CiscoConfParse().sync_diff()` with `HDiff()`.
    - Rename variables in `HDiff().compress_dict_diffs()`.
    - Rename dict_line to line and add the command indent rename dict_line to line and add the command indent rename dict_line to line and add the command indent in `CiscoConfParse().sync_diff()`
    - Add 'parents' to `HDiff()` diff dicts and add parent line output in `sync_diff()`
    - Expand `CiscoConfParse()` test coverage for reading files from disk

## Version: 1.7.13

- Released: 2023-01-31
- Summary:
    - Fix `CiscoConfParse().read_config_file()` recursive call in `read_config_file()`.
    - Fix `CiscoConfParse().read_config_file()` missing `open()` in `read_config_file()`.
    - Fix file-open test escapes associated with github issue #262.

## Version: 1.7.12

- Released: 2023-01-31
- Summary:
    - Fix `CiscoConfParse().read_config_file()` argument name test escape (ref github issue #262)

## Version: 1.7.11

- Released: 2023-01-28
- Summary:
    - Improve file `open()` error handling.  NOTE: `FileNotFoundError()` is now raised for invalid file paths.
    - Improve edge case handling for Cisco IOS banner delimiters.
    - Remove `_validate_ConfigObjs()` and improve logic in `CiscoConfParse().__init__()`.
    - Revert back to using `read_config_file()` if the config is stored in a file.

## Version: 1.7.9

- Released: 2023-01-28
- Summary:
    - Fix unit tests to work with version 1.7.8+

## Version: 1.7.8

- Released: 2023-01-28
- Summary:
    - Streamline `CiscoConfParse().__init__()` logic and delegate `__init__()` tasks to dedicated methods.
    - Validate that `CiscoConfParse().ConfigObjs` is None or instance of `collections.abc.Sequence()`
    - Convert all checks for `collections.abc.Iterator` to `collections.abc.Sequence`; ref github issue #256
    - Add more error conditions and explicit errors in ciscoconfparse/ciscoconfparse.py
    - Implement `read_config_file()` logic
    - Add more unit tests


## Version: 1.7.7

- Released: 2023-01-27
- Summary:
    - Replace `assert isinstance()`, as requested in github issue #256
    - Remove test `ping` code from `Makefile`
    - Small code reorganization in `class CiscoConfParse()`

## Version: 1.7.6

- Released: 2023-01-25
- Summary:
    - Reorganize Makefile, pyproject.toml and requirements.txt to minimize end-user package upgrades

## Version: 1.7.5

- Released: 2023-01-22
- Summary:
    - Move non-essential packages to requirements-dev.txt (github issue #258)


## Version: 1.7.4

- Released: 2023-01-22
- Summary:
    - Reorganize pyproject.toml for github issue #258 (as suggested by @verbosemode)

## Version: 1.7.3

- Released: 2023-01-21
- Summary:
    - Edit in documentation style fixes recommended by `pydocstyle -e --convention=numpy <filename>`.
    - Convert some of the assertions that validated `CiscoConfParse()` method parameters and variables into if-statements for more idiomatic python.
    - Convert some of the clunky-python-syntax into more idiomatic python.
    - Rip out all `terraform` parsing attempts.

## Version: 1.7.2

- Released: 2023-01-20
- Summary:
    - Update for [CVE-2022-40898](https://nvd.nist.gov/vuln/detail/CVE-2022-40898) in the python `wheel <= 0.38.0` package.
      - [github issue #257](https://github.com/mpenning/ciscoconfparse/issues/257) reported this issue.
      - Modified `requirements.txt` to manually upgrade `python`'s default `wheel` version to a patched version of `wheel`.
    - Move documentation package dependencies to `sphinx-doc/requirements.txt`
    - Add documentation build instructions to `README.md`

## Version: 1.7.1

- Released: 2023-01-18
- Summary:
    - Improve config parsing code
    - Make ConfigList() more stable

## Version: 1.7.0

- Released: 2023-01-02
- Summary:
    - Add deprecat dependency
    - Add more Makefile targets
    - Makefile will successfully ping to internet or fail
    - Update Makefile to delete poetry.lock file
    - Correct 'make ping' logic and other tricky Makefile syntax


## Version: 1.6.53

- Released: 2022-11-18
- Summary:
    - Reformat pyproject.toml to be most compatible with 'pip install'
    - Several internal project-level optimizations...
    - git changes committed on 2022-11-09... somehow 1.6.53 wasn't pushed to pypi on 9-Nov-2022.  It was pushed to pypi on 18-Nov-2022

## Version: 1.6.52

- Released: 2022-11-09
- Summary:
    - Fix Github Issue #254

## Version: 1.6.51

- Released: 2022-10-21
- Summary:
    - Add user and project parameters to dev_tools/git_helper.py.  Modify the Makefile accordingly
    - Fix `.delete(recurse=True)` implementation (see Github Issue #253)
    - Fix incorrect debug level check in _bootstrap_from_text()
    - Add more debug logs... however, many methods still lack debug messages

## Version: 1.6.50

- Released: 2022-10-21
- Summary:
    - Modify .github/workflows/tests.yml with improved yml
    - Enhance CiscoConfParse().__repr__() string output
    - Minor package documentation tweaks

## Version: 1.6.49

- Released: 2022-10-21
- Summary:
    - Adjust string strip() conditions on config lines in ``assign_parent_to_closing_braces()``

## Version: 1.6.48

- Released: 2022-10-21
- Summary:
    - Add code to catch misconfigurations such as parsing a string instead of a list in `ciscoconfparse.ConfigList(``)`
    - Avoid problems with reading empty lines (see Github Issue #251)

## Version: 1.6.47

- Released: 2022-10-17
- Summary:
    - Add repo version management into the Makefile ('make bump-version-patch' / 'make bump-version-minor')
    - Add repo version management to 'dev_tools/git_helper.py'
    - Revise README_git_workflow.md to include more rebase and merge details

## Version: 1.6.46

- Released: 2022-10-15
- Summary:
    - Reorganize reverse_dns_lookup() in ciscoconfparse/ccp_util.py

## Version: 1.6.45

- Released: 2022-10-15
- Summary:
    - Reorganize ciscoconfparse initialization

## Version: 1.6.44

- Released: 2022-10-14
- Summary:
    - Merge [Github PR #244](https://github.com/mpenning/ciscoconfparse/pull/244) Fix functionality of delete_children_matching

## Version: 1.6.43

- Released: 2022-10-14
- Summary:
    - Fixes [Github issue #250](https://github.com/mpenning/ciscoconfparse/issues/250) Change all logger.catch() decorators to use reraise=True

## Version: 1.6.42

- Released: 2022-10-04
- Summary:
    - Add `CHANGES.md` and deprecate `CHANGES`
    - Fixes [Github issue #249](https://github.com/mpenning/ciscoconfparse/issues/249) [Bug]: ciscoconfparse.get_config_lines TypeError: open() argument after ** must be a mapping, not method
    - Fixes [Github issue #248](https://github.com/mpenning/ciscoconfparse/issues/248)
    - Modify [nxos test cases](https://github.com/mpenning/ciscoconfparse/commit/cbe0f489ce98029457d7632667a63330b4d34244)
    - Formally deprecate and remove references to Python3.6 support (Python3.6 went EOL on 2021-12-23 -> https://endoflife.date/python)

## Version: [`1.6.41`](https://pypi.org/project/ciscoconfparse/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/")
- Released: 2022-00-00
- Summary:
    - Add `CHANGES.md` and deprecate `CHANGES`
    - Require at least Python3.6
    - Add `HDiff()` which fixes [Github issue #184](https://github.com/mpenning/ciscoconfparse/issues/184)
    - Modify `uncfgtext`.  Deprecate `add_uncfgtext()`
    - Add a dedicated bootstrap method (`_bootstrap_obj_init_junos()`) for parsing `syntax==junos`
    - Add `JunosCfgLine()`
    - Add `ciscoconfparse/models_iosxr.py` which is mostly broken (but this also comes with the caveat of an 'unsupported feature').  Ref   - [Github issue #235](https://github.com/mpenning/ciscoconfparse/issues/235)
    - Restore `tests/test_CiscoConfParse.py` to proper functionality.  See [git commit hash `840b11ce334f0b7120bbfc90d2d83fbdc5ed1bd1`](https://github.com/mpenning/ciscoconfparse/commit/840b11ce334f0b7120bbfc90d2d83fbdc5ed1bd1)
    - Add deprecation notices on `sync_diff()`, `req_cfgspec_excl_diff()` and `req_cfgspec_all_diff()`
    - Remove `NXOSConfigList()` and `ASAConfigList()` which were dead code and unused
    - Change `ignore_blank_lines` behavior for [Github Issue #229](https://github.com/mpenning/ciscoconfparse/issues/229).  Now blank line  s are **always allowed** in banners or macros regardless of what `ignore_blank_lines` is set to.
    - Modify `tests/runtests.sh` for simplicity and consistency.
    - Add test coverage for "parsing F5 configs as ios", "parsing F5 configs as junos"
    - Rename loop variables that overlapped scope with other code sections
    - Remove other dead / unreachable code


## Version: [`1.6.40`](https://pypi.org/project/ciscoconfparse/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/")
- Released: 2022-03-09
- Summary:
    - Fix various git merge conflicts

## Version: `l.6.38`
- Released: 2022-03-04
- Summary:
    - Internal adjustments on previous commit

## Version: `l.6.37`
- Released: 2022-03-04
- Summary:
    - Rename 'master' branch to 'main'
    - Add config diff infrastructure (preparing to make heavy changes to diffs)

## Version: `l.6.36`
- Released: 2022-02-20
- Summary:
    - Cosmetic changes to `dns_query()`

## Version: `l.6.35`
- Released: 2022-02-19
- Summary:
    - Fix problems with `ip_factory()`

## Version: [`1.6.34`](https://pypi.org/project/ciscoconfparse/1.6.34/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.34/")
- Released: 2022-02-16
- Summary:
    - Add `_ip` property to `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.6.33`](https://pypi.org/project/ciscoconfparse/1.6.33/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.33/")
- Released: 2022-02-16
- Summary:
    - Commit changes from develop to `master`

## Version: [`1.6.32`](https://pypi.org/project/ciscoconfparse/1.6.32/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.32/")
- Released: 2022-02-16
- Summary:
    - Add support for IPv4 Mapped IPv6 Addresses

## Version: [`1.6.31`](https://pypi.org/project/ciscoconfparse/1.6.31/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.31/")
- Released: 2022-02-06
- Summary:
    - Improve `CiscoConfParse().__init__()` Rip out redundant code

## Version: [`1.6.30`](https://pypi.org/project/ciscoconfparse/1.6.30/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.30/")
- Released: 2022-02-04
- Summary:
    - Fix `BaseCfgLine().has_child_with()` method

## Version: [`1.6.29`](https://pypi.org/project/ciscoconfparse/1.6.29/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.29/")
- Released: 2022-01-29
- Summary:
    - Re-organize / cleanup `IPv4Obj()`, `IPv6Obj()`

## Version: [`1.6.28`](https://pypi.org/project/ciscoconfparse/1.6.28/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.28/")
- Released: 2022-01-28
- Summary:
    - Make `ip_factory()` more resilient

## Version: [`1.6.27`](https://pypi.org/project/ciscoconfparse/1.6.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.27/")
- Released: 2022-01-28
- Summary:
    - Make `ip_factory()` more resilient

## Version: [`1.6.26`](https://pypi.org/project/ciscoconfparse/1.6.26/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.26/")
- Released: 2022-01-26
- Summary:
    - Fix issue raised in [github `PR` #219](https://github.com/mpenning/ciscoconfparse/pull/219)

## Version: [`1.6.25`](https://pypi.org/project/ciscoconfparse/1.6.25/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.25/")
- Released: 2022-01-26
- Summary:
    - Remove old 'ipaddr' module requirement from Python2.7 days

## Version: [`1.6.24`](https://pypi.org/project/ciscoconfparse/1.6.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.24/")
- Released: 2022-01-25
- Summary:
    - Update `CHANGES` to match most recent github version

## Version: [`1.6.21`](https://pypi.org/project/ciscoconfparse/1.6.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.21/")
- Released: 2022-01-12
- Summary:
    - Commit with `ccp_logger_control` feature incompete

## Version: [`1.6.20`](https://pypi.org/project/ciscoconfparse/1.6.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.20/")
- Released: 2022-01-11
- Summary:
    - Code cleanup

## Version: [`1.6.19`](https://pypi.org/project/ciscoconfparse/1.6.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.19/")
- Released: 2022-01-09
- Summary:
    - Fix IPv6 bug in `ip_factory()`

## Version: [`1.6.18`](https://pypi.org/project/ciscoconfparse/1.6.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.18/")
- Released: 2022-01-09
- Summary:
    - Fix failed py36 test

## Version: [`1.6.17`](https://pypi.org/project/ciscoconfparse/1.6.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.17/")
- Released: 2022-01-09
- Summary:
    - Enhance `regex_groups` on `find_object_branches`

## Version: [`1.6.16`](https://pypi.org/project/ciscoconfparse/1.6.16/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.16/")
- Released: 2022-01-07
- Summary:
    - Add regex match group support to `find_object_branches`

## Version: [`1.6.15`](https://pypi.org/project/ciscoconfparse/1.6.15/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.15/")
- Released: 2022-01-05
- Summary:
    - Fix several problems in version `1.6.14`

## Version: `1.6.14`
- Released: 2022-01-01
- Summary:
    - Ensure masklen and prefix are int objects for `IPv4Obj()` and `IPv6Obj()` network mask length

## Version: [`1.6.13`](https://pypi.org/project/ciscoconfparse/1.6.13/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.13/")
- Released: 2021-12-31
- Summary:
    - Add `ccp_util.ip_factory()`

## Version: [`1.6.12`](https://pypi.org/project/ciscoconfparse/1.6.12/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.12/")
- Released: 2021-12-20
- Summary:
    - Replace `map()` calls with equivalent list-comprehensions

## Version: [`1.6.11`](https://pypi.org/project/ciscoconfparse/1.6.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.11/")
- Released: 2021-12-12
- Summary:
    - Update `IPv4Obj()` and `IPv6Obj()` docs

## Version: [`1.6.10`](https://pypi.org/project/ciscoconfparse/1.6.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.10/")
- Released: 2021-12-08
- Summary:
    - Improve style and readability

## Version: [`1.6.9`](https://pypi.org/project/ciscoconfparse/1.6.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.9/")
- Released: 2021-12-06
- Summary:
    - Small tweak

## Version: [`1.6.8`](https://pypi.org/project/ciscoconfparse/1.6.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.8/")
- Released: 2021-12-03
- Summary:
    - Reorganize build infra and ccp data structures
    - Fix [Github issue #214](https://github.com/mpenning/ciscoconfparse/issues/214)
    - Fix for issue documented in [Github `PR` #217](https://github.com/mpenning/ciscoconfparse/pull/217) .

## Version: [`1.6.7`](https://pypi.org/project/ciscoconfparse/1.6.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.7/")
- Released: 2021-11-22
- Summary:
    - Misc updates

## Version: [`1.6.6`](https://pypi.org/project/ciscoconfparse/1.6.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.6/")
- Released: 2021-11-18
- Summary:
    - Build poetry infra

## Version: `1.6.5`
- Released: 2021-11-18
- Summary:
    - Deprecate setuptools

## Version: [`1.6.4`](https://pypi.org/project/ciscoconfparse/1.6.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.4/")
- Released: 2021-11-11
- Summary:
    - Rename loguru.logger's `logger_id` to `handler_id`

## Version: [`1.6.3`](https://pypi.org/project/ciscoconfparse/1.6.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.3/")
- Released: 2021-11-11
- Summary:
    - Add an explicit `logger_id` parameter to ensure only intended loguru loggers are removed...

## Version: [`1.6.2`](https://pypi.org/project/ciscoconfparse/1.6.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.2/")
- Released: 2021-11-11
- Summary:
    - Enhance `ccp_logger_control()`
    - Added a "disable" and "enable" command to `ccp_logger_control()`

## Version: [`1.6.1`](https://pypi.org/project/ciscoconfparse/1.6.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.1/")
- Released: 2021-11-11
- Summary:
    - Add `ccp_logger_control()`
    - See [Github issue #211](https://github.com/mpenning/ciscoconfparse/issues/211) .

## Version: [`1.6.0`](https://pypi.org/project/ciscoconfparse/1.6.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.6.0/")
- Released: 2021-11-08
- Summary:
    - Fix race-condition for `CiscoConfParse` kwarg in `IOSConfigList`, `NXOSConfigList`, and `ASAConfigList`
    - Add explicit configuration file encoding with default encoding from python's locale module
    - Add tests to catch breakage similar to [Github Issue #209](https://github.com/mpenning/ciscoconfparse/issues/209)
    - Remove colorama dependency.

## Version: [`1.5.51`](https://pypi.org/project/ciscoconfparse/1.5.51/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.51/")
- Released: 2021-11-01
- Summary:
    - Config `insert()s` are broken See [Github issue #209](https://github.com/mpenning/ciscoconfparse/issues/209)
    - New release with modified copyrights

## Version: [`1.5.50`](https://pypi.org/project/ciscoconfparse/1.5.50/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.50/")
- Released: 2021-10-08
- Summary:
    - Config `insert()s` are broken See [Github issue #209](https://github.com/mpenning/ciscoconfparse/issues/209)
    - `NOTE` `MODIFIED` RELEASE
    - Update copyrights, fix [Github issue #208](https://github.com/mpenning/ciscoconfparse/issues/208)
    - Also see https://stackoverflow.com/q/21064581/667301 as an alternative to deleting the original pypi package data

## Version: [`1.5.49`](https://pypi.org/project/ciscoconfparse/1.5.49/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.49/")
- Released: 2021-10-08
- Summary:
    - Config `insert()s` are broken See [Github issue #209](https://github.com/mpenning/ciscoconfparse/issues/209) Fix typos and syntax

## Version: [`1.5.48`](https://pypi.org/project/ciscoconfparse/1.5.48/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.48/")
- Released: 2021-10-07
- Summary:
    - Config `insert()s` are broken See [Github issue #209](https://github.com/mpenning/ciscoconfparse/issues/209) Changes to `insert_before()` and `insert_after()`, update Copyrights

## Version: `1.5.47`
- Released: 2021-09-15
- Summary:
    - Expose a proxy function to call `ipaddress.collapse_addresses()`

## Version: [`1.5.46`](https://pypi.org/project/ciscoconfparse/1.5.46/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.46/")
- Released: 2021-07-17
- Summary:
    - More logging work..
    - Prepare for debugging overhaul.

## Version: [`1.5.45`](https://pypi.org/project/ciscoconfparse/1.5.45/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.45/")
- Released: 2021-07-17
- Summary:
    - Refine error logging in `setup.py`

## Version: `1.5.44`
- Released: 2021-07-17
- Summary:
    - Fix `get_metadata()` returned value in `setup.py`

## Version: `1.5.37`
- Released: 2021-07-17
- Summary:
    - Rework `version.json` to `metadata.json`

## Version: [`1.5.36`](https://pypi.org/project/ciscoconfparse/1.5.36/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.36/")
- Released: 2021-07-11
- Summary:
    - Rework git remote (i.e. origin) logic

## Version: [`1.5.35`](https://pypi.org/project/ciscoconfparse/1.5.35/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.35/")
- Released: 2021-07-11
- Summary:
    - Fix git tags in `Makefile`
    - Deprecate py2.7 support

## Version: [`1.5.30`](https://pypi.org/project/ciscoconfparse/1.5.30/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.30/")
- Released: 2021-03-01
- Summary:
    - Add a helper-function: `as_text_list()`
    - Improve performance of `.delete()`

## Version: [`1.5.29`](https://pypi.org/project/ciscoconfparse/1.5.29/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.29/")
- Released: 2021-01-28
- Summary:
    - Fix `__int__()` and `__index__()` on `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.5.28`](https://pypi.org/project/ciscoconfparse/1.5.28/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.28/")
- Released: 2021-01-23
- Summary:
    - Enhance `ccp_util.CiscoRange()` to parse a wider variety of string inputs

## Version: [`1.5.27`](https://pypi.org/project/ciscoconfparse/1.5.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.27/")
- Released: 2021-01-23
- Summary:
    - Remove slow code from `ccp_util.CiscoRange()`

## Version: [`1.5.26`](https://pypi.org/project/ciscoconfparse/1.5.26/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.26/")
- Released: 2021-01-23
- Summary:
    - Make `ccp_util.L4Object().__repr__()` more friendly

## Version: [`1.5.25`](https://pypi.org/project/ciscoconfparse/1.5.25/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.25/")
- Released: 2021-01-23
- Summary:
    - Fix Github Issue `#195`, merge github `PR` `#194`, fix multiple unreported bugs in `ccp_util.L4Object()`

## Version: [`1.5.24`](https://pypi.org/project/ciscoconfparse/1.5.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.24/")
- Released: 2021-01-06
- Summary:
    - Fix [Github Issue #178](https://github.com/mpenning/ciscoconfparse/issues/178)

## Version: [`1.5.23`](https://pypi.org/project/ciscoconfparse/1.5.23/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.23/")
- Released: 2021-01-05
- Summary:
    - Prevent `find_object_branches()` from using `None`

## Version: [`1.5.22`](https://pypi.org/project/ciscoconfparse/1.5.22/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.22/")
- Released: 2020-11-27
- Summary:
    - Fix [Github issue #186](https://github.com/mpenning/ciscoconfparse/issues/186) (replace variables named input)

## Version: [`1.5.21`](https://pypi.org/project/ciscoconfparse/1.5.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.21/")
- Released: 2020-11-27
- Summary:
    - Fix [Github issue #187](https://github.com/mpenning/ciscoconfparse/issues/187)

## Version: [`1.5.20`](https://pypi.org/project/ciscoconfparse/1.5.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.20/")
- Released: 2020-11-27
- Summary:
    - Fix [Github issue #185](https://github.com/mpenning/ciscoconfparse/issues/185)

## Version: [`1.5.19`](https://pypi.org/project/ciscoconfparse/1.5.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.19/")
- Released: 2020-07-22
- Summary:
    - Add `__ne__()` support to `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.5.18`](https://pypi.org/project/ciscoconfparse/1.5.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.18/")
- Released: 2020-07-21
- Summary:
    - Fix Github issue `#180` `IPv4Obj()` and `IPv6Obj()` cannot use logical compare ops with certain Python objects

## Version: [`1.5.17`](https://pypi.org/project/ciscoconfparse/1.5.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.17/")
- Released: 2020-07-11
- Summary:
    - Fix Python `2.7` packaging

## Version: `1.5.7`
- Released: 2020-07-11
- Summary:
    - Revise `IPv4Obj()` & `IPv6Obj()` `__lt__()`, `__gt__()`, and `__contains__()` methods (impacts sorting behavior)
    - Reformatted documentation to latest numpydoc format
    - Add version number as json data instead of raw text...

## Version: [`1.5.6`](https://pypi.org/project/ciscoconfparse/1.5.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.6/")
- Released: 2020-06-27
- Summary:
    - Improve `find_object_branches()` speed
    - Reformat with `black`

## Version: [`1.5.5`](https://pypi.org/project/ciscoconfparse/1.5.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.5/")
- Released: 2020-06-12
- Summary:
    - Beta-test new function: `find_object_branches()`

## Version: [`1.5.4`](https://pypi.org/project/ciscoconfparse/1.5.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.4/")
- Released: 2020-04-12
- Summary:
    - Modify `IPv4Obj().__add__()` and `IPv6Obj().__add__()` (and `__sub__())` methods return `IPv4Obj()/IPv6Obj()` objects
    - Add support for `int()`, `bin()` and `hex()` on the `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.5.3`](https://pypi.org/project/ciscoconfparse/1.5.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.3/")
- Released: 2020-04-12
- Summary:
    - Fix `IPv6Obj().packed` and `IPv6Obj().exploded`
    - Add `IPv4Obj().packed` and `IPv4Obj().exploded`

## Version: [`1.5.2`](https://pypi.org/project/ciscoconfparse/1.5.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.2/")
- Released: 2020-04-12
- Summary:
    - Add `__add__()` and `__sub__()` to `IPv4Obj()` and `IPv6Obj()`
    - Remove use of `IPv6Obj().broadcast` in `IPv6Obj().__contains__()`

## Version: [`1.5.1`](https://pypi.org/project/ciscoconfparse/1.5.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.1/")
- Released: 2020-02-23
- Summary:
    - Remove embedded junos debugging

## Version: [`1.5.0`](https://pypi.org/project/ciscoconfparse/1.5.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.5.0/")
- Released: 2020-02-23
- Summary:
    - Complete rewrite of junos parser (fix [Github issue #70](https://github.com/mpenning/ciscoconfparse/issues/70) )
    - Deprecate support for Python `3.4`

## Version: [`1.4.11`](https://pypi.org/project/ciscoconfparse/1.4.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.11/")
- Released: 2019-12-05
- Summary:
    - Github issue `#170` Explicitly `close()` open filehandles

## Version: [`1.4.10`](https://pypi.org/project/ciscoconfparse/1.4.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.10/")
- Released: 2019-11-25
- Summary:
    - Integrate [Github issue #169](https://github.com/mpenning/ciscoconfparse/issues/169) , add support for parsing pathlib.Path objects which contain a configuration

## Version: [`1.4.9`](https://pypi.org/project/ciscoconfparse/1.4.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.9/")
- Released: 2019-11-22
- Summary:
    - Add `.as_cidr_net` and `.as_cidr_addr` on `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.4.8`](https://pypi.org/project/ciscoconfparse/1.4.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.8/")
- Released: 2019-11-21
- Summary:
    - Merge [Github `PR` #168](https://github.com/mpenning/ciscoconfparse/pull/168)
    - Rename `in_portchannel` and `is_portchannel`

## Version: [`1.4.7`](https://pypi.org/project/ciscoconfparse/1.4.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.7/")
- Released: 2019-09-10
- Summary:
    - Add support for `NXOS` vrf with dhcp helper-address

## Version: [`1.4.6`](https://pypi.org/project/ciscoconfparse/1.4.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.6/")
- Released: 2019-09-10
- Summary:
    - Add support for `NXOS` dhcp helper-address (w/ factory=True)

## Version: [`1.4.5`](https://pypi.org/project/ciscoconfparse/1.4.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.5/")
- Released: 2019-09-07
- Summary:
    - Add support for `NXOS` in `find_interface_objects()`

## Version: [`1.4.4`](https://pypi.org/project/ciscoconfparse/1.4.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.4/")
- Released: 2019-09-07
- Summary:
    - Fix Github issue `#162` and [Github issue #164](https://github.com/mpenning/ciscoconfparse/issues/164)

## Version: [`1.4.3`](https://pypi.org/project/ciscoconfparse/1.4.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.3/")
- Released: 2019-08-14
- Summary:
    - Fix [Github issue #160](https://github.com/mpenning/ciscoconfparse/issues/160)
    - Add parser for various `NXOS` features

## Version: [`1.4.2`](https://pypi.org/project/ciscoconfparse/1.4.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.2/")
- Released: 2019-07-28
- Summary:
    - Fix [Github issue #141](https://github.com/mpenning/ciscoconfparse/issues/141)
    - `NOTE` This will break parsing helper-addresses under factory=True
    - If you use this feature, please migrate your scripts to the new format

## Version: [`1.4.1`](https://pypi.org/project/ciscoconfparse/1.4.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.1/")
- Released: 2019-07-28
- Summary:
    - Implement `re_search_children()` directly on the `CiscoConfParse()` object

## Version: [`1.4.0`](https://pypi.org/project/ciscoconfparse/1.4.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.4.0/")
- Released: 2019-07-27
- Summary:
    - Fix [Github issue #158](https://github.com/mpenning/ciscoconfparse/issues/158) , `*KEYWORD` `CHANGE` `WARNING:*` some methods formrely used a keyword called `all_children`
    - The new syntax is 'recurse' (ref: [Github issue #159](https://github.com/mpenning/ciscoconfparse/issues/159) )

## Version: [`1.3.43`](https://pypi.org/project/ciscoconfparse/1.3.43/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.43/")
- Released: 2019-07-05
- Summary:
    - Attempt to fix [Github issue #154](https://github.com/mpenning/ciscoconfparse/issues/154)

## Version: [`1.3.42`](https://pypi.org/project/ciscoconfparse/1.3.42/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.42/")
- Released: 2019-06-27
- Summary:
    - Fix [Github issue #153](https://github.com/mpenning/ciscoconfparse/issues/153)

## Version: [`1.3.41`](https://pypi.org/project/ciscoconfparse/1.3.41/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.41/")
- Released: 2019-06-27
- Summary:
    - [RELEASE BROKEN] `HSRP` timers now return a float (used to return int)
    - `NXOS` support for `HSRP` (Github issue `#152)`

## Version: [`1.3.40`](https://pypi.org/project/ciscoconfparse/1.3.40/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.40/")
- Released: 2019-06-20
- Summary:
    - Update version handling
    - Github issue `#122`
    - Update sphinx documentation

## Version: [`1.3.39`](https://pypi.org/project/ciscoconfparse/1.3.39/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.39/")
- Released: 2019-05-27
- Summary:
    - Allow `re_match_iter_typed()` to use default=True

## Version: [`1.3.38`](https://pypi.org/project/ciscoconfparse/1.3.38/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.38/")
- Released: 2019-05-27
- Summary:
    - Add `CiscoConfParse().re_match_iter_typed()`

## Version: [`1.3.37`](https://pypi.org/project/ciscoconfparse/1.3.37/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.37/")
- Released: 2019-05-12
- Summary:
    - Take a step further towards full Python 3 compat (Github issue `#98)`

## Version: [`1.3.36`](https://pypi.org/project/ciscoconfparse/1.3.36/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.36/")
- Released: 2019-04-22
- Summary:
    - Refine Junos parsing (Github issue `#142)`

## Version: [`1.3.35`](https://pypi.org/project/ciscoconfparse/1.3.35/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.35/")
- Released: 2019-04-20
- Summary:
    - Refine `IOS` macro parsing (Github issue `#144)`

## Version: [`1.3.34`](https://pypi.org/project/ciscoconfparse/1.3.34/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.34/")
- Released: 2019-04-19
- Summary:
    - Add support for `IOS` macros (Github issue `#143)`

## Version: [`1.3.33`](https://pypi.org/project/ciscoconfparse/1.3.33/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.33/")
- Released: 2019-04-07
- Summary:
    - Merge [Github `PR` #140](https://github.com/mpenning/ciscoconfparse/pull/140) `(delete_lines()` bug)

## Version: [`1.3.32`](https://pypi.org/project/ciscoconfparse/1.3.32/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.32/")
- Released: 2019-03-17
- Summary:
    - Fix [Github issue #135](https://github.com/mpenning/ciscoconfparse/issues/135)

## Version: [`1.3.31`](https://pypi.org/project/ciscoconfparse/1.3.31/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.31/")
- Released: 2019-03-16
- Summary:
    - Fix Github issues `#131`, `132`, `133`, `134`

## Version: [`1.3.30`](https://pypi.org/project/ciscoconfparse/1.3.30/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.30/")
- Released: 2019-02-18
- Summary:
    - Fix bugs related to Python3 (Github issue `#117)`

## Version: [`1.3.29`](https://pypi.org/project/ciscoconfparse/1.3.29/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.29/")
- Released: 2019-02-07
- Summary:
    - Add `IP` helper-address parsing in `models_cisco.py`

## Version: [`1.3.28`](https://pypi.org/project/ciscoconfparse/1.3.28/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.28/")
- Released: 2019-02-06
- Summary:
    - Revert universal wheel packages (universal=0)

## Version: [`1.3.27`](https://pypi.org/project/ciscoconfparse/1.3.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.27/")
- Released: 2019-01-26
- Summary:
    - Build universal wheel packages

## Version: [`1.3.26`](https://pypi.org/project/ciscoconfparse/1.3.26/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.26/")
- Released: 2019-01-26
- Summary:
    - Build improvements ref Github issue `#127`, `#128`

## Version: [`1.3.25`](https://pypi.org/project/ciscoconfparse/1.3.25/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.25/")
- Released: 2019-01-23
- Summary:
    - Another swing at [Github issue #127](https://github.com/mpenning/ciscoconfparse/issues/127)

## Version: [`1.3.24`](https://pypi.org/project/ciscoconfparse/1.3.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.24/")
- Released: 2019-01-23
- Summary:
    - Rollback fix for [Github issue #127](https://github.com/mpenning/ciscoconfparse/issues/127)

## Version: [`1.3.23`](https://pypi.org/project/ciscoconfparse/1.3.23/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.23/")
- Released: 2019-01-23
- Summary:
    - Attempt to fix [Github issue #127](https://github.com/mpenning/ciscoconfparse/issues/127)

## Version: [`1.3.22`](https://pypi.org/project/ciscoconfparse/1.3.22/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.22/")
- Released: 2018-12-16
- Summary:
    - Fix Github issue `#124-126` and [Github issue #110](https://github.com/mpenning/ciscoconfparse/issues/110)

## Version: [`1.3.21`](https://pypi.org/project/ciscoconfparse/1.3.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.21/")
- Released: 2018-12-16
- Summary:
    - Fix Github issue `#121` and [Github issue #123](https://github.com/mpenning/ciscoconfparse/issues/123)

## Version: [`1.3.20`](https://pypi.org/project/ciscoconfparse/1.3.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.20/")
- Released: 2018-07-02
- Summary:
    - Fix Github issue `#114` (Py3.5 requires different `open()` syntax)

## Version: [`1.3.19`](https://pypi.org/project/ciscoconfparse/1.3.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.19/")
- Released: 2018-06-23
- Summary:
    - Fix [Github issue #111](https://github.com/mpenning/ciscoconfparse/issues/111) (banner parsing broken in some cases)

## Version: [`1.3.18`](https://pypi.org/project/ciscoconfparse/1.3.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.18/")
- Released: 2018-06-09
- Summary:
    - Add * to MANIFEST.in

## Version: [`1.3.17`](https://pypi.org/project/ciscoconfparse/1.3.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.17/")
- Released: 2018-06-08
- Summary:
    - Attempt to resolve [Github issue #106](https://github.com/mpenning/ciscoconfparse/issues/106)

## Version: [`1.3.16`](https://pypi.org/project/ciscoconfparse/1.3.16/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.16/")
- Released: 2018-06-01
- Summary:
    - Add `dns_query()` zone transfer as text

## Version: [`1.3.15`](https://pypi.org/project/ciscoconfparse/1.3.15/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.15/")
- Released: 2018-04-21
- Summary:
    - Distrbution change

## Version: [`1.3.14`](https://pypi.org/project/ciscoconfparse/1.3.14/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.14/")
- Released: 2018-04-21
- Summary:
    - Attempt to fix unit tests

## Version: [`1.3.13`](https://pypi.org/project/ciscoconfparse/1.3.13/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.13/")
- Released: 2018-04-21
- Summary:
    - Fix Github issue `#103`, Python3 `ccp_util` imports

## Version: [`1.3.12`](https://pypi.org/project/ciscoconfparse/1.3.12/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.12/")
- Released: 2018-04-16
- Summary:
    - Upgrade comparison operations of `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.3.11`](https://pypi.org/project/ciscoconfparse/1.3.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.11/")
- Released: 2018-03-31
- Summary:
    - Fix [Github issue #101](https://github.com/mpenning/ciscoconfparse/issues/101)

## Version: [`1.3.10`](https://pypi.org/project/ciscoconfparse/1.3.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.10/")
- Released: 2018-03-04
- Summary:
    - Fix various bugs in `dns_query()`
    - Add a query duration to the `DNSResponse()` object

## Version: [`1.3.9`](https://pypi.org/project/ciscoconfparse/1.3.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.9/")
- Released: 2018-03-03
- Summary:
    - Build `dns_query()` responses on a universal `DNSResponse()` object

## Version: [`1.3.8`](https://pypi.org/project/ciscoconfparse/1.3.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.8/")
- Released: 2018-03-03
- Summary:
    - Fix Python3 packaging, [Github issue #98](https://github.com/mpenning/ciscoconfparse/issues/98)

## Version: `1.3.7`
- Released: 2018-03-03
- Summary:
    - [RELEASE BROKEN and removed from pypi]

## Version: `1.3.6`
- Released: 2018-02-13
- Summary:
    - [RELEASE BROKEN and removed from pypi]

## Version: `1.3.5`
- Released: 2018-02-13
- Summary:
    - [RELEASE BROKEN and removed from pypi]

## Version: `1.3.4`
- Released: 2018-02-13
- Summary:
    - [RELEASE BROKEN and removed from pypi]

## Version: `1.3.3`
- Released: 2018-02-13
- Summary:
    - [RELEASE BROKEN and removed from pypi]

## Version: `1.3.2`
- Released: 2018-02-10
- Summary:
    - Add `all_children` flag to `re_match_iter_typed()` [RELEASE BROKEN]

## Version: [`1.3.1`](https://pypi.org/project/ciscoconfparse/1.3.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.3.1/")
- Released: 2018-01-29
- Summary:
    - Raise DynamicErrorException on ipv4 dhcp interfaces

## Version: [`1.2.55`](https://pypi.org/project/ciscoconfparse/1.2.55/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.55/")
- Released: 2018-01-25
- Summary:
    - Add manual speed and duplex to `models_nxos.py`

## Version: [`1.2.54`](https://pypi.org/project/ciscoconfparse/1.2.54/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.54/")
- Released: 2018-01-25
- Summary:
    - Add manual speed and duplex to `models_cisco.py`

## Version: [`1.2.53`](https://pypi.org/project/ciscoconfparse/1.2.53/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.53/")
- Released: 2018-01-25
- Summary:
    - Attempt to fix [Github issue #49](https://github.com/mpenning/ciscoconfparse/issues/49)

## Version: [`1.2.52`](https://pypi.org/project/ciscoconfparse/1.2.52/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.52/")
- Released: 2018-01-25
- Summary:
    - Alpha-quality nxos factory parser (ref: [Github issue #71](https://github.com/mpenning/ciscoconfparse/issues/71) )

## Version: [`1.2.51`](https://pypi.org/project/ciscoconfparse/1.2.51/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.51/")
- Released: 2018-01-24
- Summary:
    - Fix packaging problem

## Version: [`1.2.50`](https://pypi.org/project/ciscoconfparse/1.2.50/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.50/")
- Released: 2018-01-24
- Summary:
    - Throw a `ValueError` on ipv4 dhcp factory interfaces

## Version: [`1.2.49`](https://pypi.org/project/ciscoconfparse/1.2.49/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.49/")
- Released: 2017-07-23
- Summary:
    - Fix doctest breakage

## Version: `1.2.48`
- Released: 2017-07-23
- Summary:
    - Fix [Github issue #82](https://github.com/mpenning/ciscoconfparse/issues/82)

## Version: [`1.2.47`](https://pypi.org/project/ciscoconfparse/1.2.47/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.47/")
- Released: 2017-03-05
- Summary:
    - Fix Github issue `#75`, Github issue `#76`, [Github issue #77](https://github.com/mpenning/ciscoconfparse/issues/77)

## Version: [`1.2.46`](https://pypi.org/project/ciscoconfparse/1.2.46/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.46/")
- Released: 2017-01-09
- Summary:
    - Normalize zero-padded `IP` address string inputs to `IPv4Obj()`

## Version: [`1.2.45`](https://pypi.org/project/ciscoconfparse/1.2.45/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.45/")
- Released: 2017-01-05
- Summary:
    - Add zero-padded `ccp_util.IPv4Obj()` strings, improve `IPv4Obj()` and `IPv6Obj()`

## Version: [`1.2.44`](https://pypi.org/project/ciscoconfparse/1.2.44/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.44/")
- Released: 2016-11-25
- Summary:
    - Improve parsing speed for the factory=True parser

## Version: [`1.2.43`](https://pypi.org/project/ciscoconfparse/1.2.43/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.43/")
- Released: 2016-11-25
- Summary:
    - Fix [Github issue #63](https://github.com/mpenning/ciscoconfparse/issues/63) , add a new function: `find_objects_w_all_children()`

## Version: [`1.2.42`](https://pypi.org/project/ciscoconfparse/1.2.42/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.42/")
- Released: 2016-11-24
- Summary:
    - Fix [Github issue #62](https://github.com/mpenning/ciscoconfparse/issues/62) , add a new object called `CiscoRange()`

## Version: [`1.2.41`](https://pypi.org/project/ciscoconfparse/1.2.41/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.41/")
- Released: 2016-11-24
- Summary:
    - Fix Github issue `#51`, Github issue `#53`, Github issue `#57`, Githbu issue `#64`, [Github issue #65](https://github.com/mpenning/ciscoconfparse/issues/65)

## Version: [`1.2.40`](https://pypi.org/project/ciscoconfparse/1.2.40/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.40/")
- Released: 2016-04-30
- Summary:
    - Fix Github issue `#44` (Could not parse 'ipv6 router ospf `6')`
    - Modify default value for `access_vlan`
    - Add new `is_portchannel` property
    - Update copyright dates
    - Remove `OSX` from test matrix

## Version: [`1.2.39`](https://pypi.org/project/ciscoconfparse/1.2.39/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.39/")
- Released: 2015-10-27
- Summary:
    - Fix TravisCI breakage

## Version: [`1.2.38`](https://pypi.org/project/ciscoconfparse/1.2.38/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.38/")
- Released: 2015-10-27
- Summary:
    - Integrate `PR` `#48`, which fixes [github issue #47](https://github.com/mpenning/ciscoconfparse/issues/47)

## Version: [`1.2.37`](https://pypi.org/project/ciscoconfparse/1.2.37/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.37/")
- Released: 2015-07-06
- Summary:
    - Fix [Github issue #37](https://github.com/mpenning/ciscoconfparse/issues/37) `(sync_diff()` includes double negatives)

## Version: [`1.2.36`](https://pypi.org/project/ciscoconfparse/1.2.36/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.36/")
- Released: 2015-07-06
- Summary:
    - Add `dns6_lookup()`, add tutorial

## Version: [`1.2.35`](https://pypi.org/project/ciscoconfparse/1.2.35/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.35/")
- Released: 2015-07-03
- Summary:
    - Fix issue with ipv6 route parsing

## Version: [`1.2.34`](https://pypi.org/project/ciscoconfparse/1.2.34/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.34/")
- Released: 2015-07-03
- Summary:
    - Add support for ipv6 static routes in `models_cisco` (Github issue `#34)`

## Version: [`1.2.33`](https://pypi.org/project/ciscoconfparse/1.2.33/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.33/")
- Released: 2015-07-02
- Summary:
    - Expand coverage of icmp and standard ACLs in `models_asa`

## Version: [`1.2.32`](https://pypi.org/project/ciscoconfparse/1.2.32/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.32/")
- Released: 2015-07-01
- Summary:
    - Add `find_objects_dna()`

## Version: [`1.2.31`](https://pypi.org/project/ciscoconfparse/1.2.31/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.31/")
- Released: 2015-06-29
- Summary:
    - Fix [Github issue #39](https://github.com/mpenning/ciscoconfparse/issues/39) (not parsing Junos comments correctly)

## Version: [`1.2.30`](https://pypi.org/project/ciscoconfparse/1.2.30/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.30/")
- Released: 2015-06-27
- Summary:
    - Enhance banner delimiter parsing

## Version: [`1.2.29`](https://pypi.org/project/ciscoconfparse/1.2.29/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.29/")
- Released: 2015-06-27
- Summary:
    - Add `dns_lookup` and `reverse_dns_lookup` in `ccp_util`

## Version: [`1.2.28`](https://pypi.org/project/ciscoconfparse/1.2.28/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.28/")
- Released: 2015-06-27
- Summary:
    - Fix build problem

## Version: [`1.2.27`](https://pypi.org/project/ciscoconfparse/1.2.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.27/")
- Released: 2015-06-27
- Summary:
    - Termcolor `->` colorama

## Version: [`1.2.27`](https://pypi.org/project/ciscoconfparse/1.2.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.27/")
- Released: 2015-06-27
- Summary:
    - Forgot to check in some updates...

## Version: [`1.2.26`](https://pypi.org/project/ciscoconfparse/1.2.26/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.26/")
- Released: 2015-06-27
- Summary:
    - Update debugging code

## Version: [`1.2.25`](https://pypi.org/project/ciscoconfparse/1.2.25/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.25/")
- Released: 2015-06-23
- Summary:
    - Modest ASAObjGroupNetwork speed improvements

## Version: [`1.2.24`](https://pypi.org/project/ciscoconfparse/1.2.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.24/")
- Released: 2015-06-22
- Summary:
    - Fix Github issue `#41`, improve `IPv4Obj()` docs

## Version: [`1.2.23`](https://pypi.org/project/ciscoconfparse/1.2.23/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.23/")
- Released: 2015-06-19
- Summary:
    - Improve `IPv4Obj()` parsing speed

## Version: [`1.2.22`](https://pypi.org/project/ciscoconfparse/1.2.22/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.22/")
- Released: 2015-06-18
- Summary:
    - Improve ASAAclLine Log level parsing support

## Version: [`1.2.21`](https://pypi.org/project/ciscoconfparse/1.2.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.21/")
- Released: 2015-06-16
- Summary:
    - Initial support for ASAAclLine parsing, partial commit for [Github Issue #29](https://github.com/mpenning/ciscoconfparse/issues/29)

## Version: [`1.2.20`](https://pypi.org/project/ciscoconfparse/1.2.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.20/")
- Released: 2015-06-11
- Summary:
    - Increase `ASA` config parse speed (when parsed with factory=True)

## Version: [`1.2.19`](https://pypi.org/project/ciscoconfparse/1.2.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.19/")
- Released: 2015-04-18
- Summary:
    - Fix Github issue `#33` Unicode path support, Github issue `#36` Banner delimiter issues, [Github issue #37](https://github.com/mpenning/ciscoconfparse/issues/37) `delete()` broke in some situations

## Version: [`1.2.18`](https://pypi.org/project/ciscoconfparse/1.2.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.18/")
- Released: 2015-04-08
- Summary:
    - Fix Github issue `#32` (ccp + py34 + windows broken).

## Version: [`1.2.17`](https://pypi.org/project/ciscoconfparse/1.2.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.17/")
- Released: 2015-04-06
- Summary:
    - Fix [Github issue #31](https://github.com/mpenning/ciscoconfparse/issues/31)
    - First steps towards `IPv6Obj()` support.

## Version: [`1.2.16`](https://pypi.org/project/ciscoconfparse/1.2.16/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.16/")
- Released: 2015-04-01
- Summary:
    - Improve ip route detection in `models_cisco`, as requested by [Github issue #30](https://github.com/mpenning/ciscoconfparse/issues/30)
    - Convert more unit tests to native py.test format

## Version: [`1.2.15`](https://pypi.org/project/ciscoconfparse/1.2.15/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.15/")
- Released: 2015-03-22
- Summary:
    - Implement feature requested by [Github issue #28](https://github.com/mpenning/ciscoconfparse/issues/28) (Cisco `ASA` standby addrs), improve `sync_diff()` / fix bugs, add .geneology / `.geneology_text` features

## Version: [`1.2.14`](https://pypi.org/project/ciscoconfparse/1.2.14/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.14/")
- Released: 2015-03-07
- Summary:
    - Enhance config modification speed as documented in [Github issue #26](https://github.com/mpenning/ciscoconfparse/issues/26)
    - Implement `find_interface_objects()` as documented in [Github issue #27](https://github.com/mpenning/ciscoconfparse/issues/27)
    - Improved unit test coverage

## Version: [`1.2.13`](https://pypi.org/project/ciscoconfparse/1.2.13/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.13/")
- Released: 2015-03-01
- Summary:
    - Fix Github issue `#25:` Python3 bites me again

## Version: [`1.2.12`](https://pypi.org/project/ciscoconfparse/1.2.12/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.12/")
- Released: 2015-03-01
- Summary:
    - Fix [Github issue #24](https://github.com/mpenning/ciscoconfparse/issues/24) : recursive dependencies in `setup.py` and `ciscoconfparse/__init__.py`

## Version: [`1.2.11`](https://pypi.org/project/ciscoconfparse/1.2.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.11/")
- Released: 2015-03-01
- Summary:
    - Converted unit-tests to py.test
    - Fix Github issue `#23` (banner detection bug), add `sync_diff()` feature from [Github issue #22](https://github.com/mpenning/ciscoconfparse/issues/22) , improve `setup.py` script
    - `NOTE:` going forward, `sync_diff()` will deprecate use of `req_cfgspec_excl_diff()`

## Version: [`1.2.10`](https://pypi.org/project/ciscoconfparse/1.2.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.10/")
- Released: 2015-02-10
- Summary:
    - Fix Github issue `#21` in `find_all_children()`, update unit tests to detect [github issue #21](https://github.com/mpenning/ciscoconfparse/issues/21) , add new-style example in examples/

## Version: [`1.2.9`](https://pypi.org/project/ciscoconfparse/1.2.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.9/")
- Released: 2015-02-02
- Summary:
    - Reduce package size, enhance generator support

## Version: [`1.2.8`](https://pypi.org/project/ciscoconfparse/1.2.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.8/")
- Released: 2015-01-29
- Summary:
    - Add support for iterating over a generator (CiscoConfParse input, ref [Github issue #19](https://github.com/mpenning/ciscoconfparse/issues/19) )

## Version: [`1.2.7`](https://pypi.org/project/ciscoconfparse/1.2.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.7/")
- Released: 2015-01-26
- Summary:
    - Fix `README`, again
    - Pypi and github don't act the same way.

## Version: [`1.2.6`](https://pypi.org/project/ciscoconfparse/1.2.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.6/")
- Released: 2015-01-26
- Summary:
    - Fix `README`, because it looks awful on pypi (they don't allow twitter embedding)

## Version: [`1.2.5`](https://pypi.org/project/ciscoconfparse/1.2.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.5/")
- Released: 2015-01-26
- Summary:
    - Add 'indent' and `auto_indent` options to `append_to_family()`

## Version: [`1.2.4`](https://pypi.org/project/ciscoconfparse/1.2.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.4/")
- Released: 2015-01-25
- Summary:
    - Fix `_unique_OBJ()` to work in Python2.6, which doesn't have set comprehensions

## Version: [`1.2.3`](https://pypi.org/project/ciscoconfparse/1.2.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.3/")
- Released: 2015-01-25
- Summary:
    - Add `find_objects_w_parents()`

## Version: [`1.2.2`](https://pypi.org/project/ciscoconfparse/1.2.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.2/")
- Released: 2015-01-25
- Summary:
    - Add support for parsing Junos as a Cisco-IOS-style configuration github issue `#17`, fixed github issue `#16` [Banners with comment characters in them are not parsed correctly], fixed [github issue #15](https://github.com/mpenning/ciscoconfparse/issues/15) `[CiscoConfParse.append('config_line_here')` is a null operation]

## Version: [`1.2.1`](https://pypi.org/project/ciscoconfparse/1.2.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.1/")
- Released: 2015-01-24
- Summary:
    - More parsing speed optimizations, particularly in banner parsing
    - Ripped out old, unused code

## Version: [`1.2.0`](https://pypi.org/project/ciscoconfparse/1.2.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.2.0/")
- Released: 2015-01-24
- Summary:
    - Major parser rewrite: streamline parser, less spaghetti code, add `ccp_abc.is_config_line`
    - This version *should* parse Cisco Nexus syntax now (but parse Cisco Nexus configs with `ignore_blank_lines=False)`
    - Implement enhancement in [github issue #6](https://github.com/mpenning/ciscoconfparse/issues/6)

## Version: [`1.1.24`](https://pypi.org/project/ciscoconfparse/1.1.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.24/")
- Released: 2015-01-23
- Summary:
    - Fix [github issue #13](https://github.com/mpenning/ciscoconfparse/issues/13) (ciscoconfparse did not parse correctly when `ignore_blank_lines=True)`
    - Some parent assignments were missed if blank lines were in the configuration

## Version: [`1.1.23`](https://pypi.org/project/ciscoconfparse/1.1.23/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.23/")
- Released: 2015-01-17
- Summary:
    - Update copyrights to `2015`, use list comprehension in `re_search_children()` to increase speed

## Version: [`1.1.22`](https://pypi.org/project/ciscoconfparse/1.1.22/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.22/")
- Released: 2014-12-04
- Summary:
    - More bugfixes in `ccp_util.IPv4Obj()`
    - `IPv4Obj()` should mostly be stable and reliable now
    - Added solid unit test coverage for `IPv4Obj()`

## Version: [`1.1.21`](https://pypi.org/project/ciscoconfparse/1.1.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.21/")
- Released: 2014-12-03
- Summary:
    - Major bugfixes in `IPv4Obj()`, convert results from `ordinal_list()` from a python list to a python tuple

## Version: [`1.1.20`](https://pypi.org/project/ciscoconfparse/1.1.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.20/")
- Released: 2014-11-16
- Summary:
    - Remove numpydoc

## Version: [`1.1.19`](https://pypi.org/project/ciscoconfparse/1.1.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.19/")
- Released: 2014-11-16
- Summary:
    - Fix for Read the Docs publication

## Version: [`1.1.18`](https://pypi.org/project/ciscoconfparse/1.1.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.18/")
- Released: 2014-11-15
- Summary:
    - Doc reformating
    - Remove duplicated `ccp_util.IPv4Obj` method

## Version: [`1.1.17`](https://pypi.org/project/ciscoconfparse/1.1.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.17/")
- Released: 2014-11-13
- Summary:
    - More doc reformating
    - Add recursion for `ASA` group-objects on object-groups

## Version: [`1.1.16`](https://pypi.org/project/ciscoconfparse/1.1.16/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.16/")
- Released: 2014-11-13
- Summary:
    - Reformat docs
    - Improve `ASAConfigList()`

## Version: [`1.1.15`](https://pypi.org/project/ciscoconfparse/1.1.15/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.15/")
- Released: 2014-11-12
- Summary:
    - Add gt and lt comparision methods to `ccp_util.IPv4Obj()`
    - Consolidate test scripts into one shell script

## Version: [`1.1.14`](https://pypi.org/project/ciscoconfparse/1.1.14/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.14/")
- Released: 2014-11-11
- Summary:
    - Fix Python3 breakage in `1.1.13`

## Version: [`1.1.13`](https://pypi.org/project/ciscoconfparse/1.1.13/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.13/")
- Released: 2014-11-11
- Summary:
    - Fix github issues `#10` and `#11`
    - Improve Cisco `ASA` parsing support

## Version: [`1.1.12`](https://pypi.org/project/ciscoconfparse/1.1.12/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.12/")
- Released: 2014-09-19
- Summary:
    - Enhance support for `ccp_util.IPv4Obj`, add Cisco `ASA` parsing in `models_asa`

## Version: [`1.1.11`](https://pypi.org/project/ciscoconfparse/1.1.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.11/")
- Released: 2014-09-18
- Summary:
    - Fix [Github Issue #9](https://github.com/mpenning/ciscoconfparse/issues/9)

## Version: [`1.1.10`](https://pypi.org/project/ciscoconfparse/1.1.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.10/")
- Released: 2014-09-05
- Summary:
    - Enhance `AAA` parsing in `models_cisco`

## Version: [`1.1.9`](https://pypi.org/project/ciscoconfparse/1.1.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.9/")
- Released: 2014-09-04
- Summary:
    - Enhance `AAA` parsing in `models_cisco`

## Version: [`1.1.8`](https://pypi.org/project/ciscoconfparse/1.1.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.8/")
- Released: 2014-09-03
- Summary:
    - Add initial `models_cisco` support for parsing basic `AAA` configuration

## Version: [`1.1.7`](https://pypi.org/project/ciscoconfparse/1.1.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.7/")
- Released: 2014-09-02
- Summary:
    - Fix TravisCI failures

## Version: `1.1.6`
- Released: 2014-09-02
- Summary:
    - Replace ipaddr.IPv4Network with `ccp_util.IPv4Obj` for more consistency
    - Started adding unittests for `models_cisco` functionality
    - Added `local_py/ipaddress.py`

## Version: [`1.1.5`](https://pypi.org/project/ciscoconfparse/1.1.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.5/")
- Released: 2014-08-29
- Summary:
    - Add `IOS` Interface object functions in `models_cisco` to parse port number, interface type, etc
    - Added the "Huge Ugly Warning" to `models_cisco`
    - I also removed an unnecessary `isinstance()` in `ccp_abc` to improve performance.

## Version: [`1.1.4`](https://pypi.org/project/ciscoconfparse/1.1.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.4/")
- Released: 2014-08-18
- Summary:
    - Major speed improvement when parsing large configurations `(~45%` faster than some previous `CiscoConfParse` versions)

## Version: [`1.1.3`](https://pypi.org/project/ciscoconfparse/1.1.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.3/")
- Released: 2014-07-29
- Summary:
    - Fix `is_switchport` parsing

## Version: [`1.1.2`](https://pypi.org/project/ciscoconfparse/1.1.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.2/")
- Released: 2014-05-15
- Summary:
    - Fix Python3 packaging (related to missing `PEP366` compliance), more relative `ipaddr` imports

## Version: [`1.1.1`](https://pypi.org/project/ciscoconfparse/1.1.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.1/")
- Released: 2014-05-15
- Summary:
    - Fix Python3 breakage due to xrange

## Version: [`1.1.0`](https://pypi.org/project/ciscoconfparse/1.1.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.1.0/")
- Released: 2014-05-14
- Summary:
    - Improve parsing speed
    - Simplify debugging logs.

## Version: [`1.0.7`](https://pypi.org/project/ciscoconfparse/1.0.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.7/")
- Released: 2014-05-07
- Summary:
    - Add build automation improvements
    - Modify default value for `ipv4_network_object()`

## Version: [`1.0.6`](https://pypi.org/project/ciscoconfparse/1.0.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.6/")
- Released: 2014-05-06
- Summary:
    - Improve docs

## Version: [`1.0.5`](https://pypi.org/project/ciscoconfparse/1.0.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.5/")
- Released: 2014-05-06
- Summary:
    - Improve docs

## Version: [`1.0.4`](https://pypi.org/project/ciscoconfparse/1.0.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.4/")
- Released: 2014-05-04
- Summary:
    - Add new `find_objects_w_child()` and `find_objects_wo_child()` methods
    - Add more documentation.

## Version: [`1.0.3`](https://pypi.org/project/ciscoconfparse/1.0.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.3/")
- Released: 2014-05-03
- Summary:
    - Removed all examples in `README.rst`, and expanded those in the web documentation
    - More non-trivial doc updates

## Version: [`1.0.2`](https://pypi.org/project/ciscoconfparse/1.0.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.2/")
- Released: 2014-05-02
- Summary:
    - Even more documentation improvements
    - Changed default value of `IOSCfgLine.re_search` / `re_match` from `None` to ``.

## Version: [`1.0.1`](https://pypi.org/project/ciscoconfparse/1.0.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.1/")
- Released: 2014-05-01
- Summary:
    - More documentation improvements
    - Fix problem with experimental `IOSCfgLine` factory feature.

## Version: [`1.0.0`](https://pypi.org/project/ciscoconfparse/1.0.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/1.0.0/")
- Released: 2014-04-30
- Summary:
    - Significant documentation overhaul
    - Add documentation of new `IOSCfgLine` methods introduced in `0.9.10`, as well as making the documentation more friendly to mobile devices
    - Substitute the `sphinx_bootstrap_theme` instead of the sphinxdoc theme
    - Add line highlights in code examples which hopefully make complex examples more clear.

## Version: [`0.9.35`](https://pypi.org/project/ciscoconfparse/0.9.35/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.35/")
- Released: 2014-04-30
- Summary:
    - Update docstrings with more examples
    - Improve doc `Makefile`

## Version: [`0.9.34`](https://pypi.org/project/ciscoconfparse/0.9.34/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.34/")
- Released: 2014-04-29
- Summary:
    - Update `IOSCfgLine` objects with a recursive delete, which will automatically delete children if the parent is deleted
    - First steps toward a long-overdue documentation update
    - A lot more is left to do.

## Version: [`0.9.33`](https://pypi.org/project/ciscoconfparse/0.9.33/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.33/")
- Released: 2014-04-25
- Summary:
    - Add unit test for banner parsing coverage

## Version: [`0.9.32`](https://pypi.org/project/ciscoconfparse/0.9.32/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.32/")
- Released: 2014-04-22
- Summary:
    - Fix banner parent-child relationships for [Github Issue #4](https://github.com/mpenning/ciscoconfparse/issues/4)
    - Improve parsing speed with pre-compiled regex in `_mark_banner()`
    - Update example in `README.rst`
    - Add new `ignore_rgx` option to the `re_sub()` line-object method.

## Version: [`0.9.31`](https://pypi.org/project/ciscoconfparse/0.9.31/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.31/")
- Released: 2014-04-15
- Summary:
    - Fix `DBGFLAG` issue in `CiscoConfParse()` for [Github Issue #5](https://github.com/mpenning/ciscoconfparse/issues/5)

## Version: [`0.9.30`](https://pypi.org/project/ciscoconfparse/0.9.30/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.30/")
- Released: 2014-04-04
- Summary:
    - Add `ignore_blank_lines` option in `CiscoConfParse()` for [Github Issue #3](https://github.com/mpenning/ciscoconfparse/issues/3)

## Version: [`0.9.29`](https://pypi.org/project/ciscoconfparse/0.9.29/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.29/")
- Released: 2014-04-04
- Summary:
    - Fix typo in `CiscoConfParse()`

## Version: [`0.9.28`](https://pypi.org/project/ciscoconfparse/0.9.28/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.28/")
- Released: 2014-04-03
- Summary:
    - Added new `linesplit_rgx` option in `CiscoConfParse()` to help user who filed [Github Issue #2](https://github.com/mpenning/ciscoconfparse/issues/2)
    - No defaults were changed
    - Added Python `3.4` in .travis.yml in hopes of testing against Python `3.4`

## Version: [`0.9.27`](https://pypi.org/project/ciscoconfparse/0.9.27/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.27/")
- Released: 2014-03-26
- Summary:
    - Added a new `append_line()` method to `ciscoconfparse`.

## Version: [`0.9.26`](https://pypi.org/project/ciscoconfparse/0.9.26/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.26/")
- Released: 2014-03-19
- Summary:
    - Finally caved and left my copy of `ipaddr` that's modified to work with python3 in `ciscoconfparse/ipaddr.py`, where Travis can find it

## Version: [`0.9.25`](https://pypi.org/project/ciscoconfparse/0.9.25/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.25/")
- Released: 2014-03-19
- Summary:
    - Improve speed in `find_blocks()`, as requested by [Github Issue #1](https://github.com/mpenning/ciscoconfparse/issues/1)
    - Minor change to improve Travis `CI` builds

## Version: [`0.9.24`](https://pypi.org/project/ciscoconfparse/0.9.24/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.24/")
- Released: 2014-03-13
- Summary:
    - Fix broken Travis `CI` builds (because of where I moved the `ipaddr` module)
    - Added new functionality in `models_cisco` (still alpha code at this point)

## Version: [`0.9.23`](https://pypi.org/project/ciscoconfparse/0.9.23/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.23/")
- Released: 2014-03-05
- Summary:
    - Modify `ipv4_addr_object` default value in `models_cisco`
    - Move `ipaddr` module to a local folder

## Version: [`0.9.22`](https://pypi.org/project/ciscoconfparse/0.9.22/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.22/")
- Released: 2014-02-28
- Summary:
    - Add `PIM` interface support in `models_cisco` (still alpha at this point)

## Version: [`0.9.21`](https://pypi.org/project/ciscoconfparse/0.9.21/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.21/")
- Released: 2014-02-26
- Summary:
    - Fix Python3.2 build (note to self..
    - `U'` isn't supported until Python3.3).

## Version: [`0.9.20`](https://pypi.org/project/ciscoconfparse/0.9.20/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.20/")
- Released: 2014-02-26
- Summary:
    - Updated `README` with other Cisco `IOS` configuration resources
    - Fixed problems in `models_cisco`
    - Improved / added docstrings
    - Improve build workflow.

## Version: [`0.9.19`](https://pypi.org/project/ciscoconfparse/0.9.19/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.19/")
- Released: 2014-02-17
- Summary:
    - Fixed Python3 build issue in `0.9.18`

## Version: [`0.9.18`](https://pypi.org/project/ciscoconfparse/0.9.18/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.18/")
- Released: 2014-02-17
- Summary:
    - Updated `README.rst`
    - Added new `IOSCfgLine.lineage()` & `CiscoConfParse.lineage()` methods (experimental at this point)
    - Added `IOSCfgLine.all_children`
    - "President's Day holiday release"

## Version: [`0.9.17`](https://pypi.org/project/ciscoconfparse/0.9.17/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.17/")
- Released: 2014-02-15
- Summary:
    - Updated `README.rst`, add MANIFEST.in and requirements.txt
    - Several new object-oriented methods added.

## Version: [`0.9.16`](https://pypi.org/project/ciscoconfparse/0.9.16/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.16/")
- Released: 2014-02-12
- Summary:
    - Fix bug in `ccp_abc.insert_before()` and `insert_after()`
    - Made updates to `README.rst`
    - Ripped out linenum references in various insert methods

## Version: [`0.9.15`](https://pypi.org/project/ciscoconfparse/0.9.15/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.15/")
- Released: 2014-02-10
- Summary:
    - Updated `README.rst` with inline example

## Version: [`0.9.14`](https://pypi.org/project/ciscoconfparse/0.9.14/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.14/")
- Released: 2014-02-09
- Summary:
    - Support for Travis `CI`
    - Fix Travis `CI` build failures on Python3.3 (due to how `__hash__()` is computed).

## Version: [`0.9.13`](https://pypi.org/project/ciscoconfparse/0.9.13/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.13/")
- Released: 2014-02-09
- Summary:
    - Fixed Python3 compatibility, which broke a few builds ago
    - Including ipaddr-py (patched for Python3) until versions of Python3 typically include it (right now, Debian `7.3` has Python3.2 without ipaddr-py)

## Version: [`0.9.12`](https://pypi.org/project/ciscoconfparse/0.9.12/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.12/")
- Released: 2014-02-08
- Summary:
    - Fixed bug in `ccp_abc.py`
    - Reworked comment detection
    - Performance improvements

## Version: [`0.9.11`](https://pypi.org/project/ciscoconfparse/0.9.11/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.11/")
- Released: 2014-02-04
- Summary:
    - Bugfixes

## Version: [`0.9.10`](https://pypi.org/project/ciscoconfparse/0.9.10/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.10/")
- Released: 2014-02-03
- Summary:
    - Bugfixes and more performance improvements
    - Doubled number of unit tests
    - Added alpha-quality code in another module.

## Version: [`0.9.9`](https://pypi.org/project/ciscoconfparse/0.9.9/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.9/")
- Released: 2014-01-31
- Summary:
    - Major `insert()` / `append()` performance improvements
    - Add optional interface-aware config line factory objects
    - Add abstract base classes
    - Add atomic options to `insert_before()`, `insert_after()`, etc...

## Version: [`0.9.8`](https://pypi.org/project/ciscoconfparse/0.9.8/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.8/")
- Released: 2014-01-24
- Summary:
    - Remove debugging info

## Version: [`0.9.7`](https://pypi.org/project/ciscoconfparse/0.9.7/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.7/")
- Released: 2014-01-24
- Summary:
    - Major rewrite, removed support for old python versions
    - Ripped out inefficient code I wrote as a python newbie, added more idiomatic structures in various places
    - Also added support for inserting and deleting lines via `insert_before()`, `insert_after()`, and `insert_after_child()`

## Version: [`0.9.6`](https://pypi.org/project/ciscoconfparse/0.9.6/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.6/")
- Released: 2014-01-06
- Summary:
    - Update copyright to `2014`
    - Rewrite unit tests

## Version: [`0.9.5`](https://pypi.org/project/ciscoconfparse/0.9.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.5/")
- Released: 2013-12-31
- Summary:
    - Add `replace_lines()` function, enhance unit tests, added an exactmatch option on `_find_line_OBJ()`
    - Updated code copyright to include `2014`

## Version: [`0.9.4`](https://pypi.org/project/ciscoconfparse/0.9.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.4/")
- Released: 2013-08-14
- Summary:
    - Add Python3 compliance
    - Other minor tweaks

## Version: [`0.9.3`](https://pypi.org/project/ciscoconfparse/0.9.3/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.3/")
- Released: 2013-05-11
- Summary:
    - Added methods to `IOSCfgLine:` `__eq__()`, `__hash__()`, `__lt__()`, `__gt__()`, as well as simplifying several other methods
    - Misc code maintenance...

## Version: [`0.9.2`](https://pypi.org/project/ciscoconfparse/0.9.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.2/")
- Released: 2013-05-09
- Summary:
    - Add `find_children_w_parents()` method..
    - Tidy up unit-tests

## Version: [`0.9.1`](https://pypi.org/project/ciscoconfparse/0.9.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.1/")
- Released: 2012-12-31
- Summary:
    - Improve docs with numpydoc and intersphinx links
    - Add more examples / doctests
    - Renamed internal `CiscoConfParse` methods with a leading _ to make Sphinx documentation more intuitive...

## Version: [`0.9.0`](https://pypi.org/project/ciscoconfparse/0.9.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.9.0/")
- Released: 2012-12-30
- Summary:
    - Add `RST` documentation into the archives and fix more build issues

## Version: `0.8.6`
- Released: 2012-12-30
- Summary:
    - Fix packaging problems introduced when I switched to a native mercurial repository (examples/* and configs/* were not automatically packaged in the .egg / .tar.gz anymore...)

## Version: [`0.8.5`](https://pypi.org/project/ciscoconfparse/0.8.5/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.8.5/")
- Released: 2012-12-29
- Summary:
    - Added custom comment delimiters that were in the 0.8.3a private build
    - Converted the unicode backslash to a true unicode instance.

## Version: [`0.8.4`](https://pypi.org/project/ciscoconfparse/0.8.4/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.8.4/")
- Released: 2012-12-29
- Summary:
    - Add doctests, code maintenance, and more documentation fixes
    - Improved `examples/req_cfgspec_all_diff.py` and `examples/req_cfgspec_excl_diff.py`.

## Version: `0.8.3`
- Released: 2009-10-16
- Summary:
    - Documentation updates
    - `PEP8` formatting

## Version: [`0.8.2`](https://pypi.org/project/ciscoconfparse/0.8.2/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.8.2/")
- Released: 2009-08-08
- Summary:
    - Fixed a fatal crash in `find_blocks()`

## Version: [`0.8.1`](https://pypi.org/project/ciscoconfparse/0.8.1/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.8.1/")
- Released: 2009-07-19
- Summary:
    - Code reorganization
    - Fixed a bad `RuntimeError`
    - Promoted to production-quality at this point

## Version: [`0.8.0`](https://pypi.org/project/ciscoconfparse/0.8.0/ "To download the package from pypi, visit https://pypi.org/project/ciscoconfparse/0.8.0/")
- Released: 2007-10-11
- Summary:
    - Removed residual internal debugging from the CiscoPassword class
    - Added an `ignore_ws` options to all public methods, except `req_cfgspec_excl_diff`
    - This option will make the method's matches ignore whitespace differences (useful in some CatOS configurations)
    - After much deliberation, I have removed the explicit `False` return values for methods that do not match
    - Instead I am returning an empty list (which will test False)
    - Apologies for breaking any existing code, but I decided against leaving beta with this behavior
    - Removed all `sys.exit(0)` statements in favor of raising a `RuntimeError`.

## Version: `0.7.5`
- Released: 2007-08-04
- Summary:
    - Fixed a bug in the `parse()` method, which was associating grandchildren as children of the grandparent
    - Added unit tests.

## Version: `0.7.0`
- Released: 2007-08-03
- Summary:
    - Added an optional parameter to the `find_lines()`, `find_children()`, `find_all_children()`, and `find_blocks()` methods
    - This parameter will allow the user to specify whether he wants an "exact" match or a normal regex match
    - Also fixed a bug that broke parsing of configs with an indented line at the very end.

## Version: `0.6.8`
- Released: 2007-08-02
- Summary:
    - Ported fixes to the CiscoPassword class from the `cisco_decrypt` package
    - Notably, there were crashes when it was called with certain unencrypted passwords.

## Version: `0.6.7`
- Released: 2007-08-01
- Summary:
    - Fixed bug where some methods didn't return `False` when no diffs were found

## Version: `0.6.6`
- Released: 2007-07-30
- Summary:
    - Added password decryption options to the command-line help menu
    - Modified all diff functions to return `False` if no diffs are found

## Version: `0.6.5`
- Released: 2007-07-28
- Summary:
    - Fixed another CiscoPassword bug
    - Added warning if CiscoPassword decryption fails
    - Added command-line functionality for improved interoperability with other languages (and shell-usage if you like).

## Version: `0.6.1`
- Released: 2007-07-26
- Summary:
    - Cosmetic restructuring of code

## Version: `0.6.0`
- Released: 2007-07-21
- Summary:
    - Revised APIs
    - Existing APIs should be stable now
