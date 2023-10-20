r""" ccp_util.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2023      David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019-2020 David Michael Pennington at ThousandEyes
     Copyright (C) 2014-2019 David Michael Pennington at Samsung Data Services

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""

##############################################################################
# Disable SonarCloud warnings in this file
#   - S1192: Define a constant instead of duplicating this literal
#   - S1313: Disable alerts on magic IPv4 / IPv6 addresses
#   - S5843: Avoid regex complexity
#   - S5852: Slow regex are security-sensitive
#   - S6395: Unwrap this unnecessarily grouped regex subpattern.
##############################################################################
#pragma warning disable S1192
#pragma warning disable S1313
#pragma warning disable S5843
#pragma warning disable S5852
#pragma warning disable S6395

from operator import attrgetter
from functools import wraps
import locale
import socket
import time
import copy
import sys
import re
import os

from collections.abc import MutableSequence, Sequence
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from ipaddress import collapse_addresses as ipaddr_collapse_addresses
from ipaddress import AddressValueError

from dns.exception import DNSException
from dns.resolver import Resolver
from dns import reversename, query, zone

from deprecated import deprecated

from loguru import logger

from ciscoconfparse.protocol_values import ASA_TCP_PORTS, ASA_UDP_PORTS
from ciscoconfparse.errors import InvalidParameters, InvalidMember, MismatchedType
from ciscoconfparse.errors import InvalidShellVariableMapping
from ciscoconfparse.errors import PythonOptimizeException
from ciscoconfparse.errors import DynamicAddressException
from ciscoconfparse.errors import ListItemMissingAttribute
from ciscoconfparse.errors import ListItemTypeError
from ciscoconfparse.errors import InvalidCiscoInterface
from ciscoconfparse.errors import DNSLookupError
import ciscoconfparse

# Maximum ipv4 as an integer
IPV4_MAXINT = 4294967295
# Maximum ipv6 as an integer
IPV6_MAXINT = 340282366920938463463374607431768211455
IPV4_MAXSTR_LEN = 31  # String length with periods, slash, and netmask
IPV6_MAXSTR_LEN = 39 + 4  # String length with colons, slash and masklen

IPV4_MAX_PREFIXLEN = 32
IPV6_MAX_PREFIXLEN = 128


_IPV6_REGEX_ELEMENTS = r"[0-9a-fA-F]{1,4}"
_CISCO_RANGE_ATOM_STR = r"""\d+\s*\-*\s*\d*"""
_CISCO_RANGE_STR = r"""^(?P<intf_prefix>[a-zA-Z\s]*)(?P<slot_prefix>[\d\/]*\d+\/)*(?P<range_text>(\s*{})*)$""".format(
    _CISCO_RANGE_ATOM_STR
)
_RGX_CISCO_RANGE = re.compile(_CISCO_RANGE_STR)

####################### Begin IPv6 #############################
_IPV6_REGEX_STR = r"""(?!:::\S+?$)       # Negative Lookahead for 3 colons
 (?P<addr>                               # Begin a group named 'addr'
 (?P<opt1>{0}(?::{0}){{7}})              # no double colons, option 1
|(?P<opt2>(?:{0}:){{1}}(?::{0}){{1,6}})  # match fe80::1
|(?P<opt3>(?:{0}:){{2}}(?::{0}){{1,5}})  # match fe80:a::1
|(?P<opt4>(?:{0}:){{3}}(?::{0}){{1,4}})  # match fe80:a:b::1
|(?P<opt5>(?:{0}:){{4}}(?::{0}){{1,3}})  # match fe80:a:b:c::1
|(?P<opt6>(?:{0}:){{5}}(?::{0}){{1,2}})  # match fe80:a:b:c:d::1
|(?P<opt7>(?:{0}:){{6}}(?::{0}){{1,1}})  # match fe80:a:b:c:d:e::1
|(?P<opt8>:(?::{0}){{1,7}})              # ipv6 with leading double colons
|(?P<opt9>(?:{0}:){{1,7}}:)              # ipv6 with trailing double colons
|(?P<opt10>(?:::))                       # ipv6 bare double colons (default route)
)([/\s](?P<masklen>\d+))*                # match 'masklen' and end 'addr' group
""".format(_IPV6_REGEX_ELEMENTS)

_IPV6_REGEX_STR_COMPRESSED1 = r"""(?!:::\S+?$)(?P<addr1>(?P<opt1_1>{0}(?::{0}){{7}})|(?P<opt1_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt1_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt1_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt1_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt1_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt1_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt1_8>:(?::{0}){{1,7}})|(?P<opt1_9>(?:{0}:){{1,7}}:)|(?P<opt1_10>(?:::)))""".format(_IPV6_REGEX_ELEMENTS)

_IPV6_REGEX_STR_COMPRESSED2 = r"""(?!:::\S+?$)(?P<addr2>(?P<opt2_1>{0}(?::{0}){{7}})|(?P<opt2_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt2_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt2_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt2_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt2_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt2_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt2_8>:(?::{0}){{1,7}})|(?P<opt2_9>(?:{0}:){{1,7}}:)|(?P<opt2_10>(?:::)))""".format(_IPV6_REGEX_ELEMENTS)

_IPV6_REGEX_STR_COMPRESSED3 = r"""(?!:::\S+?$)(?P<addr3>(?P<opt3_1>{0}(?::{0}){{7}})|(?P<opt3_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt3_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt3_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt3_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt3_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt3_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt3_8>:(?::{0}){{1,7}})|(?P<opt3_9>(?:{0}:){{1,7}}:)|(?P<opt3_10>(?:::)))""".format(_IPV6_REGEX_ELEMENTS)

_RGX_IPV6ADDR = re.compile(_IPV6_REGEX_STR, re.VERBOSE)
####################### End IPv6 #############################

####################### Begin IPv4 #############################
_IPV4_REGEX_STR = r"^(?P<addr>\d+\.\d+\.\d+\.\d+)"
_RGX_IPV4ADDR = re.compile(_IPV4_REGEX_STR)
_RGX_IPV4ADDR_WITH_MASK = re.compile(
    r"""
     (?:
       ^(?P<v4addr_nomask>\d+\.\d+\.\d+\.\d+)$
      |(?:^
         (?:(?P<v4addr_netmask>\d+\.\d+\.\d+\.\d+))(\s+|\/)(?:(?P<netmask>\d+\.\d+\.\d+\.\d+))
       $)
      |^(?:\s*(?P<v4addr_prefixlen>\d+\.\d+\.\d+\.\d+)(?:\/(?P<masklen>\d+))\s*)$
    )
    """,
    re.VERBOSE,
)
####################### End IPv4 #############################


class UnsupportedFeatureWarning(SyntaxWarning):
    pass


class PythonOptimizeCheck(object):
    """
    Check if we're running under "python -O ...".  The -O option removes
    all `assert` statements at runtime.  ciscoconfparse depends heavily on
    `assert` and running ciscoconfparse under python -O is a really bad idea.

    __debug__ is True unless run with `python -O ...`.  __debug__ is False
    under `python -O ...`.

    Also throw an error if PYTHONOPTIMIZE is set in the windows or unix shell.

    This class should be run in <module_name_dir>/__init__.py.

    This condition is not unique to ciscoconfparse.

    Simple usage (in __init__.py):
    ------------------------------

    # Handle PYTHONOPTIMIZE problems...
    from ciscoconfparse.ccp_util import PythonOptimizeCheck
    _ = PythonOptimizeCheck()


    """
    @logger.catch(reraise=True)
    def __init__(self):

        self.PYTHONOPTIMIZE_env_value = os.environ.get("PYTHONOPTIMIZE", None)

        error = "__no_error__"
        try:
            # PYTHONOPTIMIZE is not supported...  in the linux shell
            # disable it with `unset PYTHONOPTIMIZE`
            if isinstance(self.PYTHONOPTIMIZE_env_value, str) and self.PYTHONOPTIMIZE_env_value.strip()!="":
                # This condition explicitly allows PYTHONOPTIMIZE="", which
                # is not a problem.
                error = "Your environment has PYTHONOPTIMIZE set.  ciscoconfparse doesn't support running under PYTHONOPTIMIZE."
            # PYTHONOPTIMIZE is not supported...  in the linux shell
            # disable it with `unset PYTHONOPTIMIZE`
            elif self.PYTHONOPTIMIZE_env_value is not None:
                error = "Your environment has PYTHONOPTIMIZE set.  ciscoconfparse doesn't support running under PYTHONOPTIMIZE."
            # Throw an error if we're running under `python -O`.  `python -O` is not supported
            # We should keep the __debug__ check for `-O` at the end, otherwise it
            # masks identifying problems with PYTHONOPTIMIZE set in the shell...
            elif __debug__ is False:
                # Running under 'python -O'
                error = "You're using `python -O`. Please don't.  ciscoconfparse doesn't support `python -O`"

            else:
                # whew...
                pass

        except Exception as exception_info:
            print("exception_info", str(exception_info))
            raise RuntimeError("Something bad happened in PYTHONOPTIMIZE checks.  Please report this problem as a ciscoconfparse bug")

        if error != "__no_error__":
            raise PythonOptimizeException(error)

def run_this_posix_command(cmd, timeout=None, shell=False, cwd=None, encoding=locale.getpreferredencoding(), env=None):
    """
    Run this POSIX command using subprocess.run().
    """

    if isinstance(env, dict):
        for key, value in env.items:
            if isinstance(key, str) and isinstance(value, (str, int, float)):
                pass  # noqa
            else:
                error = f"The ENV {key}: {value} {type(value)} mapping entry is invalid."
                raise ValueError(error)
    elif env is None:
        pass          # noqa
    else:
        error = "`env` must be None or a dict of variable names / values."
        logger.critical(error)
        raise InvalidShellVariableMapping(error)

    if not isinstance(cmd, str):
        error = f"'{cmd}' must be a string"
        logger.critical(error)

    if shell is True:
        cmdparts = cmd
    else:
        cmdparts = shlex.split(cmd)

    output_namedtuple = run(
        cmdparts, timeout=timeout, capture_output=True, shell=shell, cwd=cwd,
        encoding=encoding
    )
    (return_code, stdout, stderr) = (output_namedtuple.returncode, output_namedtuple.stdout,
        output_namedtuple.stderr)

    if return_code > 0:
        error = f"'{cmd}' failed: --> {stdout} <-- / --> {stderr} <--"
        logger.critical(error)

    return return_code, stdout, stderr



@logger.catch(reraise=True)
def ccp_logger_control(
    sink=sys.stderr,
    action="",
    enqueue=True,
    level="DEBUG",
    read_only=False,
    colorize=True,
    active_handlers=None,
    debug=0,
):
    """
    A simple function to handle logging... Enable / Disable all
    ciscoconfparse logging here... also see Github issue #211.

    Example
    -------
    """

    msg = f"ccp_logger_control() was called with sink='{sink}', action='{action}', enqueue={enqueue}, level='{level}', read_only={read_only}, colorize={colorize}, active_handlers={active_handlers}, debug={debug}"
    if debug > 0:
        logger.info(msg)

    if not isinstance(action, str):
        raise ValueError

    if action not in set({"remove", "add", "disable", "enable",}):
        error = f"{action} is invalid."
        logger.critical(error)
        raise ValueError(error)

    if active_handlers is None:
        active_handlers = []

    package_name = "ciscoconfparse"

    if read_only is True:
        if debug > 0:
            print(f"    Setting loguru enqueue=False, because read_only={read_only}")
        enqueue = False

    if action == "remove":
        # Require an explicit loguru handler_id to remove...
        if isinstance(active_handlers, list):
            for handler_id in active_handlers:
                if not isinstance(handler_id, int):
                    raise ValueError
                logger.remove(handler_id)
        else:
            raise ValueError()
        return True

    elif action == "disable":
        # Administratively disable this loguru logger
        logger.disable(package_name)
        return True

    elif action == "enable":
        # Administratively enable this loguru logger
        logger.enable(package_name)
        return True

    elif action == "add":

        if debug > 0:
            print(f"    Adding loguru handler with enqueue={enqueue}, because read_only={read_only}")
        handler_id = logger.add(
            sink=sink,
            diagnose=True,
            backtrace=True,
            # https://github.com/mpenning/ciscoconfparse/issues/215
            enqueue=enqueue,
            serialize=False,
            catch=True,
            # rotation="00:00",
            # retention="1 day",
            # compression="zip",
            colorize=True,
            level="DEBUG",
        )
        logger.enable(package_name)
        active_handlers.append(handler_id)
        return active_handlers

    else:
        raise NotImplementedError(f"action='{action}' is an unsupported logger action")

@logger.catch(reraise=True)
def configure_loguru(
    sink=sys.stderr,
    action="",
    # rotation="midnight",
    # retention="1 month",
    # compression="zip",
    level="DEBUG",
    read_only=False,
    colorize=True,
    active_handlers=None,
    debug=0,
):
    """
    configure_loguru()
    """
    if not isinstance(action, str):
        raise ValueError

    assert action in ('remove', 'add', 'enable', 'disable', '',)
    # assert isinstance(rotation, str)
    # assert isinstance(retention, str)
    # assert isinstance(compression, str)
    # assert compression == "zip"
    if not isinstance(level, str):
        raise ValueError

    if not isinstance(colorize, bool):
        raise ValueError

    if not isinstance(debug, int) or (debug < 0) or (5 < debug):
        raise ValueError

    if active_handlers is None:
        active_handlers = []

    if not isinstance(active_handlers, list):
        raise ValueError()

    # logger_control() was imported above...
    #    Remove the default loguru logger to stderr (handler_id==0)...
    for handler_id in active_handlers:
        if isinstance(handler_id, int):
            if debug > 0:
                print(f"Disabling loguru handler: {handler_id}")
            ccp_logger_control(action="remove", read_only=read_only, active_handlers=[handler_id])
        else:
            raise ValueError(f"handler_id must be an integer -->{handler_id}<--")

    # Add log to STDOUT
    if debug > 0:
        print(f"Calling ccp_logger_control(action='add', read_only={read_only})")

    active_loguru_handlers = ccp_logger_control(
        sink=sys.stdout,
        action="add",
        level="DEBUG",
        # rotation='midnight',   # ALE barks about the rotation keyword...
        # retention="1 month",
        # compression=compression,
        read_only=read_only,
        colorize=colorize
    )

    if debug > 0:
        print(f"added loguru handler_id -->{active_loguru_handlers}<--")
    ccp_logger_control(action="enable", read_only=read_only, active_handlers=active_handlers)
    if debug > 0:
        print(f"    enabled loguru with handlers -->{active_loguru_handlers}<--")
    return active_loguru_handlers



@logger.catch(reraise=True)
def as_text_list(object_list):
    """
    This is a helper-function to convert a list of configuration objects into
    a list of text config lines.

    Examples
    --------

    >>> from ciscoconfparse.ccp_util import as_text_list
    >>> from ciscoconfparse import CiscoConfParse
    >>>
    >>> config = [
    ... 'interface GigabitEthernet1/13',
    ... '  ip address 192.0.2.1/30',
    ... '  vrf member ThisRestrictedVrf',
    ... '  no ip redirects',
    ... '  no ipv6 redirects',
    @logger.catch(reraise=True)
    ... ]
    >>> parse = CiscoConfParse(config)
    >>> interface_object = parse.find_objects("^interface")[0]
    >>> interface_config_objects = interface_object.all_children
    >>> interface_config_objects
    [<IOSCfgLine # 1 '  ip address 192.0.2.1/30' (parent is # 0)>, <IOSCfgLine # 2 '  vrf member ThisRestrictedVrf' (parent is # 0)>, <IOSCfgLine # 3 '  no ip redirects' (parent is # 0)>, <IOSCfgLine # 4 '  no ipv6 redirects' (parent is # 0)>]
    >>>
    >>> as_text_list(interface_config_objects)
    ['  ip address 192.0.2.1/30', '  vrf member ThisRestrictedVrf', '  no ip redirects', '  no ipv6 redirects']
    >>>

    """
    if not isinstance(object_list, Sequence):
        raise ValueError

    for obj in object_list:
        if not isinstance(obj.linenum, int):
            raise ValueError

        if not isinstance(obj.text, str):
            raise ValueError

    # return [ii.text for ii in object_list]
    return list(map(attrgetter("text"), object_list))


@logger.catch(reraise=True)
def junos_unsupported(func):
    """A function wrapper to warn junos users of unsupported features"""

    @logger.catch(reraise=True)
    def wrapper(*args, **kwargs):
        warn = f"syntax='junos' does not fully support config modifications such as .{func.__name__}(); see Github Issue #185.  https://github.com/mpenning/ciscoconfparse/issues/185"
        syntax = kwargs.get("syntax", None)
        if len(args) >= 1:
            if isinstance(args[0], ciscoconfparse.ConfigList):
                syntax = args[0].syntax
            else:
                # print("TYPE", type(args[0]))
                syntax = args[0].confobj.syntax
        if syntax == "junos":
            logger.warning(warn, UnsupportedFeatureWarning)
        func(*args, **kwargs)

    return wrapper


@logger.catch(reraise=True)
def log_function_call(function=None, *args, **kwargs):
    """A wrapper; this decorator uses loguru to log function calls.

    Example
    -------

    @log_function_call
    def testme(*args, **kwargs):
        pass

    """

    @logger.catch(reraise=True)
    def logging_decorator(ff):
        @wraps(ff)
        def wrapped_logging(*args, **kwargs):
            if True:
                if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
                    # Called as @log_function_call
                    logger.info("Type 1 log_function_call: %s()" % (ff.__qualname__))

                else:
                    logger.info(
                        "Type 2 log_function_call: %s(%s, %s)"
                        % (ff.__qualname__, args, kwargs)
                    )

            logger.info(
                f"Type 3 log_function_call: {ff.__qualname__}({args}, {kwargs})"
            )
            return ff(*args, **kwargs)

        return wrapped_logging

    if function is not None:
        logger.info("Type 4 log_function_call: %s()" % (function.__qualname__))
        return logging_decorator(function)

    logger.info("Type 5 log_function_call: %s()" % (function.__qualname__))
    return logging_decorator


def enforce_valid_types(var, var_types=None, error_str=None):
    assert isinstance(var_types, tuple)
    if not isinstance(var, var_types):
        raise ValueError(error_str)


@logger.catch(reraise=True)
def fix_repeated_words(cmd="", word=""):
    """Fix repeated words in the beginning of commands... Example 'no no logging 1.2.3.4' will be returned as 'logging 1.2.3.4' (both 'no' words are removed)."""
    assert isinstance(cmd, str) and len(cmd) > 0
    assert isinstance(word, str) and len(word) > 0
    while True:
        # look at the command and fix the repeated words in it...
        rgx = rf"^(?P<indent>\s*){word.strip()}\s+{word.strip()}\s+(?P<remaining_cmd>\S.+)$"
        mm = re.search(rgx, cmd)
        if mm is not None:
            # We found a repeated word in the command...
            indent = mm.group('indent')
            remaining_cmd = mm.group('remaining_cmd')
            cmd = f"{indent}{remaining_cmd}"
        else:
            break
    return cmd


class __ccp_re__(object):
    """
    A wrapper around python's re.  This is an experimental object... it may
    disappear at any time as long as this message exists.

    self.regex = rf'{regex}'
    self.compiled = re.compile(self.regex, flags=flags)
    self.group = group
    self.match_type = match_type
    self.target_str = None
    self.search_result = None
    self.attempted_search = False

    Parameters
    ----------
    regex : str
        A string containing the regex string to be matched.  Default: r"".  This method is hard-coded to *always* use a python raw-string.
    compiled: re.Pattern
        This is a compiled regex pattern - `re.compiled(self.regex, flags=flags)`.
    groups: dict
        A dict keyed by the integer match group, or the named regex capture group.  The values in this dict


    Examples
    --------

    >>> from ciscoconfparse.ccp_util import ccp_re
    >>> ## Parse from an integer...

    """

    @logger.catch(reraise=True)
    def __init__(self, regex_str=r"", target_str=None, groups=None, flags=0, debug=0):
        if not isinstance(regex_str, str):
            raise ValueError

        if not isinstance(flags, int):
            raise ValueError

        if not isinstance(debug, int):
            raise ValueError


        if isinstance(regex_str, str):
            self.regex_str = regex_str
            self.compiled = re.compile(self.regex, flags=flags)
        else:
            raise ValueError

        self.attempted_search = False
        if isinstance(target_str, str):
            self.target_str = target_str
            self.s(self.target_str)
        else:
            self.target_str = target_str

        self.groups = groups
        self.search_result = None

    # do NOT wrap with @logger.catch(...)
    def __repr__(self):
        return f"""ccp_re({self.regex}, {self.target_str})"""

    # do NOT wrap with @logger.catch(...)
    def __str__(self):
        return f"""ccp_re({self.regex}, {self.target_str})"""

    # do NOT wrap with @logger.catch(...)
    @property
    def regex(self):
        return r"""%s""" % self.regex_str

    # do NOT wrap with @logger.catch(...)
    @regex.setter
    def regex(self, regex_str):
        if not isinstance(regex_str, str):
            raise ValueError

        self.regex_str = regex_str
        self.compiled = re.compile(regex_str)
        self.attempted_search = False


    # do NOT wrap with @logger.catch(...)
    def s(self, target_str):
        assert self.attempted_search is False
        if not isinstance(target_str, str):
            raise ValueError

        self.attempted_search = True
        self.search_result = self.compiled.search(target_str)
        if isinstance(self.search_result, re.Match):
            match_groups = self.search_result.groups()
            if len(match_groups) > 0:
                return match_groups
            else:
                # Return the whole string if there are no match groups
                return target_str
        else:
            return None

    # do NOT wrap with @logger.catch(...)
    @property
    def result(self):
        raise NotImplementedError()

    # do NOT wrap with @logger.catch(...)
    @property
    def captured(self):
        rv_groups = list()
        rv_groupdict = dict()

        if (self.attempted_search is True) and (self.search_result is None):
            error = (
                ".search(r'%s') was attempted but the regex ('%s') did not capture anything"
                % (self.target_str, self.regex)
            )
            logger.warning(error)

        elif (self.attempted_search is True) and (
            isinstance(self.search_result, re.Match) is True
        ):

            # rv_groups should be a list of capture group
            rv_groups = list(self.search_result.groups())
            # rv_groupdict should be a dictionary of named capture groups...
            # if there are any named capture groups...
            rv_groupdict = self.search_result.groupdict()

            if (self.groups != {}) and isinstance(self.groups, dict):

                # Cast types of the numerical regex match groups...
                for idx, value in enumerate(rv_groups):
                    # Lookup the match_type in the self.groups dictionary. regex
                    # capture groups are indexed starting at 1, so we need to
                    # offset the enumerate() idx value...
                    match_type = self.groups.get(idx + 1, None)
                    if match_type is not None:
                        rv_groups[idx] = match_type(value)

                # Cast types of the named regex match groups...
                for re_name, value in rv_groupdict.items():
                    match_type = self.groups.get(re_name, None)
                    if match_type is not None:
                        rv_groupdict[re_name] = match_type(value)

        elif self.attempted_search is False:
            error = ".search(r'%s') was NOT attempted yet." % (self.target_str)
            logger.warning(error)

        return rv_groups, rv_groupdict


# do NOT wrap with @logger.catch(...)
def _get_ipv4(val="", strict=False, stdlib=False, debug=0):
    """Return the requested IPv4 object to the caller.  This method heavily depends on IPv4Obj()"""
    if not isinstance(val, (str, int)):
        raise ValueError

    if not isinstance(strict, bool):
        raise ValueError

    if not isinstance(stdlib, bool):
        raise ValueError

    if not isinstance(debug, int):
        raise ValueError


    try:
        # Test val in stdlib and raise ipaddress.AddressValueError()
        # if there's a problem...
        IPv4Network(val, strict=False)

        obj = IPv4Obj(val)
        if stdlib is False:
            return obj
        else:
            if obj.prefixlen == IPV4_MAX_PREFIXLEN:
                # Return IPv6Address()
                if not isinstance(obj.ip, IPv4Address):
                    raise ValueError

                return obj.ip
            else:
                # Return IPv6Network()
                if not isinstance(obj.network, IPv4Network):
                    raise ValueError

                return obj.network
    except BaseException:
        raise AddressValueError("_get_ipv4(val='%s')" % (val))


# do NOT wrap with @logger.catch(...)
def _get_ipv6(val="", strict=False, stdlib=False, debug=0):
    """Return the requested IPv6 object to the caller.  This method heavily depends on IPv6Obj()"""
    if not isinstance(val, (str, int)):
        raise ValueError

    if not isinstance(strict, bool):
        raise ValueError

    if not isinstance(stdlib, bool):
        raise ValueError

    if not isinstance(debug, int):
        raise ValueError


    try:
        # Test val in stdlib and raise ipaddress.AddressValueError()
        # if there's a problem...
        IPv6Network(val, strict=False)

        obj = IPv6Obj(val)
        if stdlib is False:
            return obj
        else:
            if obj.prefixlen == IPV6_MAX_PREFIXLEN:
                # Return IPv6Address()
                if not isinstance(obj.ip, IPv6Address):
                    raise ValueError

                return obj.ip
            else:
                # Return IPv6Network()
                if not isinstance(obj.network, IPv6Network):
                    raise ValueError

                return obj.network

    except BaseException:
        raise AddressValueError("_get_ipv6(val='%s')" % (val))


# do NOT wrap with @logger.catch(...)
def ip_factory(val="", stdlib=False, mode="auto_detect", debug=0):
    """
    Accept an IPv4 or IPv6 address / (mask or masklength).  Return an appropriate IPv4 or IPv6 object

    Set stdlib=True if you only want python's stdlib IP objects.

    Throw an error if addr cannot be parsed as a valid IPv4 or IPv6 object.
    """

    if not isinstance(val, (str, int)):
        raise ValueError

    assert mode in {"auto_detect", "ipv4", "ipv6"}
    if not isinstance(stdlib, bool):
        raise ValueError

    if not isinstance(debug, int):
        raise ValueError


    obj = None
    if mode == "auto_detect":

        if isinstance(val, str) and (":" in val):
            obj = _get_ipv6(val=val, stdlib=stdlib, debug=debug)

        elif isinstance(val, str) and not (":" in val):
            obj = _get_ipv4(val=val, stdlib=stdlib, debug=debug)

        elif isinstance(val, int):
            # Do not try to make ip version assumptions for integer inputs...
            error_msg = "ip_factory(val=%s, mode='auto_detect') does not support integer inputs" % val
            raise NotImplementedError(error_msg)

        if obj is not None:
            return obj
        else:
            error_str = "Cannot auto-detect ip='%s'" % val
            raise AddressValueError(error_str)

    elif mode == "ipv4":
        try:
            obj = _get_ipv4(val=val, stdlib=stdlib, debug=debug)
            return obj
        except BaseException:
            error_str = "Cannot parse '%s' as ipv4" % val
            raise AddressValueError(error_str)

    elif mode == "ipv6":
        try:
            obj = _get_ipv6(val=val, stdlib=stdlib, debug=debug)
            return obj
        except BaseException:
            error_str = "Cannot parse '%s' as ipv6" % val
            raise AddressValueError(error_str)

    else:
        error_str = "Cannot parse '%s' as ipv4 or ipv6" % val
        raise AddressValueError(error_str)


@logger.catch(reraise=True)
def collapse_addresses(network_list):
    """
    This is a ciscoconfparse proxy for ipaddress.collapse_addresses()

    It attempts to summarize network_list into the closest network(s)
    containing prefixes in `network_list`.

    Return an iterator of the collapsed IPv4Network or IPv6Network objects.
    addresses is an iterator of IPv4Network or IPv6Network objects. A
    TypeError is raised if addresses contains mixed version objects.
    """
    if not isinstance(network_list, Sequence):
        raise ValueError

    @logger.catch(reraise=True)
    def ip_net(arg):
        if isinstance(arg, IPv4Obj):
            return arg.network
        elif isinstance(arg, IPv4Network):
            return arg
        elif isinstance(arg, IPv6Obj):
            return arg.network
        elif isinstance(arg, IPv6Network):
            return arg
        else:
            raise ValueError("collapse_addresses() isn't sure how to handle %s" % arg)

    return ipaddr_collapse_addresses([ip_net(ii) for ii in network_list])


# Build a wrapper around ipaddress classes to mimic the behavior of network
# interfaces (such as persisting host-bits when the intf masklen changes) and
# add custom @properties
class IPv4Obj(object):

    # This method is on IPv4Obj().  @logger.catch() breaks the __init__() method.
    # Use 'nosec' to disable default linter security flags about using 0.0.0.1
    def __init__(self, v4addr_prefixlen=f"0.0.0.1/{IPV4_MAX_PREFIXLEN}", strict=False, debug=0): # nosec
        """An object to represent IPv4 addresses and IPv4 networks.

        When :class:`~ccp_util.IPv4Obj` objects are compared or sorted, network numbers are sorted lower to higher.  If network numbers are the same, shorter masks are lower than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses..  Comparisons between :class:`~ccp_util.IPv4Obj` instances was chosen so it's easy to find the longest-match for a given prefix (see examples below).

        This object emulates the behavior of ipaddr.IPv4Network (in Python2) where host-bits were retained in the IPv4Network() object.  :class:`ipaddress.IPv4Network` in Python3 does not retain host-bits; the desire to retain host-bits in both Python2 and Python3 ip network objects was the genesis of this API.

        Parameters
        ----------
        v4addr_prefixlen : str or int
            A string (or integer) containing an IPv4 address, and optionally a netmask or masklength.  Integers are also accepted and the masklength of the integer is assumed to be 32-bits.  The following address/netmask formats are supported: "10.1.1.1/24", "10.1.1.1 255.255.255.0", "10.1.1.1/255.255.255.0"
        strict: bool
            When `strict` is True, the value of `v4addr_prefixlen` must not have host-bits set.  The default value is False.


        Examples
        --------

        >>> from ciscoconfparse.ccp_util import IPv4Obj
        >>> ## Parse from an integer...
        >>> net = IPv4Obj(2886729984)
        >>> net
        <IPv4Obj 172.16.1.0/32>
        >>> net.prefixlen = 24
        >>> net
        <IPv4Obj 172.16.1.0/24>
        >>> ## Parse from an string...
        >>> net = IPv4Obj('172.16.1.0/24')
        >>> net
        <IPv4Obj 172.16.1.0/24>
        >>> net.ip
        IPv4Address('172.16.1.0')
        >>> net.ip + 1
        IPv4Address('172.16.1.1')
        >>> str(net.ip+1)
        '172.16.1.1'
        >>> net.network
        IPv4Network('172.16.1.0/24')
        >>> net.network_object
        IPv4Network('172.16.1.0/24')
        >>> str(net.network_object)
        '172.16.1.0/24'
        >>> net.prefixlen
        24
        >>> net.network_object.iterhosts()
        <generator object iterhosts at 0x7f00bfcce730>
        >>>
        >>> # Example of finding the longest-match IPv4 route for an addr...
        >>> prefix_list = ['0.0.0.0/0', '4.0.0.0/8', '2.0.0.0/7', '4.0.0.0/16', '2.0.0.0/32']
        >>> rt_table = sorted([IPv4Obj(ii) for ii in prefix_list], reverse=True)
        >>> addr = IPv4Obj('4.0.1.1')
        >>> for route in rt_table:
        ...     if addr in route:
        ...         break
        ...
        >>> # The longest match is contained in route
        >>> route
        <IPv4Obj 4.0.0.0/16>
        >>>


        Attributes
        ----------
        as_binary_tuple : :py:class:`tuple`
            The address as a tuple of zero-padded binary strings
        as_cidr_addr : str
            Return a string representing the IPv4 host and netmask of this object in cidr notation.  Example - '172.16.0.1/24'
        as_cidr_net : str
            Return a string representing the IPv4 network and netmask of this object in cidr notation.  Example - '172.16.5.0/24'
        as_decimal : int
            The ip address as a decimal integer
        as_decimal_network : int
            The network address as a decimal integer
        as_hex_tuple : tuple
            The address as a tuple of zero-padded 8-bit hex strings
        as_zeropadded : str
            Return a zero-padded string of the ip address (example: '10.1.1.1' returns '010.001.001.001')
        as_zeropadded_network : str
            Return a zero-padded string of the ip network (example: '10.1.1.1' returns '010.001.001.000')
        broadcast : str
            An IPv4Address object representing the broadcast address
        get_regex : str
            Returns the regex string used for an IPv4 Address
        exploded : str
            Returns the IPv4 Address object as a string.  The string representation is in dotted decimal notation. Leading zeroes are never included in the representation.
        hostmask : :class:`ipaddress.IPv4Address`
            A :class:`ipaddress.IPv4Address` representing the hostmask
        ip : :class:`ipaddress.IPv4Address`
            Returns an :class:`ipaddress.IPv4Address` with the host address of this object
        ip_object  : :class:`ipaddress.IPv4Address`
            Returns an :class:`ipaddress.IPv4Address` with the host address of this object
        is_multicast : bool
            Return a boolean True if this object represents a multicast address; otherwise return False.
        is_private : bool
            Return a boolean True if this object represents a private IPv4 address; otherwise return False.
        is_reserved : bool
            Return a boolean True if this object represents a reserved IPv4 address; otherwise return False.
        netmask : :class:`ipaddress.IPv4Address`
            An :class:`ipaddress.IPv4Address` object containing the netmask
        network : :class:`ipaddress.IPv4Network`
            Returns an :class:`ipaddress.IPv4Network` with the network of this object
        network_offset : int
            Returns the integer difference between host number and network number.  This must be less than `numhosts`
        network_object : :class:`ipaddress.IPv4Network`
            Returns an :class:`ipaddress.IPv4Network` with the network of this object
        numhosts : int
            An integer representing the number of host addresses contained in the network
        packed : str
            Returns the IPv4 object as packed hex bytes
        prefixlen : int
            An python setter/getter method which return an integer representing the length of the netmask
        prefixlength : int
            An integer representing the length of the netmask
        inverse_netmask : :class:`ipaddress.IPv4Address`
            A :class:`ipaddress.IPv4Address` representing the hostmask.  .hostmask and .inverse_netmask return the same values
        version : int
            Returns an integer representing the IP version of this object.  Only 4 or 6 are valid results
        """
        if debug > 0:
            logger.info(f"IPv4Obj(v4addr_prefixlen='{v4addr_prefixlen}', strict={strict}, debug={debug}) was called")

        try:
            assert isinstance(v4addr_prefixlen, (str, int, IPv4Obj))
        except AssertionError as eee:
            raise AddressValueError(
                f"Could not parse '{v4addr_prefixlen}' (type: {type(v4addr_prefixlen)}) into an IPv4 Address. {eee}"
            )
        except BaseException as eee:
            raise AddressValueError(
                f"Could not parse '{v4addr_prefixlen}' (type: {type(v4addr_prefixlen)}) into an IPv4 Address. {eee}"
            )

        self.v4addr_prefixlen = v4addr_prefixlen
        self.dna = "IPv4Obj"
        self.ip_object = None
        self.network_object = None
        self.strict = strict
        self.debug = debug
        self.params_dict = {}

        if isinstance(v4addr_prefixlen, str):

            tmp = re.split(r"\s+", v4addr_prefixlen.strip())
            if len(tmp)==2:
                v4addr_prefixlen = "/".join(tmp)
            elif len(tmp)==1:
                v4addr_prefixlen = tmp[0]
            # anything else should be handled by the following regex...

            v4_str_rgx = _RGX_IPV4ADDR_WITH_MASK.search(v4addr_prefixlen.strip())
            if v4_str_rgx is not None:
                pp = v4_str_rgx.groupdict()
                try:
                    # Use 'nosec' to disable default linter security flags about using 0.0.0.1
                    ipv4 = pp.get("v4addr_nomask", None) or pp.get("v4addr_netmask", None) or pp.get("v4addr_prefixlen", None) or "0.0.0.1" # nosec
                except DynamicAddressException as eee:
                    raise ValueError(str(eee))

            elif "dhcp" in v4addr_prefixlen.strip().lower():
                raise DynamicAddressException("Cannot parse address from a DHCP string.")

            else:
                raise AddressValueError(
                    f"Could not parse '{v4addr_prefixlen}' {type(v4addr_prefixlen)} into an IPv4 Address"
                )

            self.ip_object = IPv4Address(ipv4)
            if isinstance(pp["masklen"], str):
                netstr = ipv4 + "/" + pp["masklen"]
            elif isinstance(pp["netmask"], str):
                netstr = ipv4 + "/" + pp["netmask"]
            else:
                netstr = ipv4+"/32"
            self.network_object = IPv4Network(netstr, strict=False)

        elif isinstance(v4addr_prefixlen, int):
            assert 0 <= v4addr_prefixlen <= IPV4_MAXINT
            self.ip_object = IPv4Address(v4addr_prefixlen)
            self.network_object = IPv4Network(v4addr_prefixlen, strict=False)

        elif isinstance(v4addr_prefixlen, IPv4Obj):
            self.ip_object = IPv4Address(v4addr_prefixlen.ip)
            self.network_object = IPv4Network(v4addr_prefixlen.as_cidr_net, strict=False)

        else:
            raise AddressValueError(
                f"Could not parse '{v4addr_prefixlen}' ({type(v4addr_prefixlen)}) into an IPv4 Address"
            )


    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def _ipv4_params_dict_DEPERCATED(self, arg, debug=0):
        """
        Parse out important IPv4 parameters from arg.  This method must run to
        completion for IPv4 address parsing to work correctly.
        """
        if not isinstance(arg, (str, int, IPv4Obj)):
            raise ValueError

        if isinstance(arg, str):
            try:
                mm = _RGX_IPV4ADDR_WITH_MASK.search(arg)
            except TypeError:
                raise AddressValueError(
                    f"_ipv4_params_dict() doesn't understand how to parse {arg}"
                )
            except BaseException as eee:
                raise AddressValueError(
                    f"_ipv4_params_dict() doesn't understand how to parse {arg}"
                )

            error_msg = f"_ipv4_params_dict() couldn't parse '{arg}'"
            assert mm is not None, error_msg

            mm_result = mm.groupdict()
            addr = (
                # Use 'nosec' to disable default linter security flags about using 0.0.0.1
                mm_result["v4addr_nomask"] or mm_result["v4addr_netmask"] or mm_result["v4addr_prefixlen"] or "0.0.0.1" # nosec
            )
            ## Normalize if we get zero-padded strings, i.e. 172.001.001.001
            assert re.search(r"^\d+\.\d+.\d+\.\d+", addr)
            addr = ".".join([str(int(ii)) for ii in addr.split(".")])

            netmask = mm_result["netmask"]

            masklen = int(mm_result.get("masklen", None) or IPV4_MAX_PREFIXLEN)

            if netmask is not None:
                ip_arg_str = f"{addr}/{netmask}"
            elif masklen is not None:
                ip_arg_str = f"{addr}/{masklen}"
            else:
                raise AddressValueError()

        elif isinstance(arg, int):
            addr = str(IPv4Address(arg))
            netmask = "255.255.255.255"
            masklen = 32
            ip_arg_str = f"{addr}/{masklen}"

        elif isinstance(arg, IPv4Obj):
            addr = str(arg.ip)
            netmask = str(arg.netmask)
            masklen = arg.masklen
            ip_arg_str = f"{addr}/{masklen}"

        else:
            raise AddressValueError("IPv4Obj(arg='%s') is an unknown argument type" % (arg))

        assert 0 <= masklen <= IPV4_MAX_PREFIXLEN
        params_dict = {
            'ipv4_addr': addr,
            'ip_version': 4,
            'ip_arg_str': ip_arg_str,
            'netmask': netmask,
            'masklen': masklen,
        }

        return params_dict

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __repr__(self):
        if not isinstance(self.prefixlen, int):
            raise ValueError

        return f"""<IPv4Obj {str(self.ip_object)}/{self.prefixlen}>"""

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __eq__(self, val):
        try:
            # Code to fix Github issue #180
            for obj in [self, val]:
                for attr_name in ["as_decimal", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except AssertionError:
                        return False

            # Compare objects numerically...
            if self.as_decimal == val.as_decimal and self.prefixlen == val.prefixlen:
                return True
            return False
        except AttributeError as eee:
            errmsg = f"'{self.__repr__()}' cannot compare itself to '{val}': {eee}"
            raise AttributeError(errmsg)
        except BaseException as eee:
            errmsg = f"'{self.__repr__()}' cannot compare itself to '{val}': {eee}"
            raise AttributeError(errmsg)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __ne__(self, val):
        return not self.__eq__(val)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __gt__(self, val):
        try:
            for obj in [self, val]:
                for attr_name in ["as_decimal", "as_decimal_network", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except (AssertionError):
                        error_str = f"Cannot compare {self} with '{type(obj)}'"
                        raise AssertionError(error_str)

            val_prefixlen = int(getattr(val, "prefixlen"))
            self_prefixlen = int(getattr(self, "prefixlen"))
            val_ndec = int(getattr(val, "as_decimal_network"))
            self_ndec = int(getattr(self, "as_decimal_network"))
            val_dec = int(getattr(val, "as_decimal"))
            self_dec = int(getattr(self, "as_decimal"))

            if self_ndec == val_ndec and self_prefixlen == val_prefixlen:
                return self_dec > val_dec

            # for the same network, longer prefixlens sort "higher" than shorter prefixlens
            elif self_ndec == val_ndec:
                return self_prefixlen > val_prefixlen

            else:
                return self_ndec > val_ndec

        except BaseException:
            errmsg = f"{self.__repr__()} cannot compare itself to '{val}'"
            raise ValueError(errmsg)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __lt__(self, val):
        try:
            for obj in [self, val]:
                for attr_name in ["as_decimal", "as_decimal_network", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except (AssertionError):
                        error_str = f"Cannot compare {self} with '{type(obj)}'"
                        raise AssertionError(error_str)
                    except BaseException:
                        error_str = f"Cannot compare {self} with '{type(obj)}'"
                        raise AssertionError(error_str)

            val_prefixlen = int(getattr(val, "prefixlen"))
            self_prefixlen = int(getattr(self, "prefixlen"))
            val_ndec = int(getattr(val, "as_decimal_network"))
            self_ndec = int(getattr(self, "as_decimal_network"))
            val_dec = int(getattr(val, "as_decimal"))
            self_dec = int(getattr(self, "as_decimal"))

            if self_ndec == val_ndec and self_prefixlen == val_prefixlen:
                return self_dec < val_dec

            # for the same network, longer prefixlens sort "higher" than shorter prefixlens
            elif self_ndec == val_ndec:
                return self_prefixlen < val_prefixlen

            else:
                return self_ndec < val_ndec

        except Exception:
            errmsg = f"{self.__repr__()} cannot compare itself to '{val}'"
            logger.error(errmsg)
            raise ValueError(errmsg)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __int__(self):
        """Return this object as an integer"""
        if getattr(self, "as_decimal", None) is not None:
            return self.as_decimal
        else:
            return False

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __index__(self):
        """Return this object as an integer (used for hex() and bin() operations)"""
        if getattr(self, "as_decimal", None) is not None:
            return self.as_decimal
        else:
            return False

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __add__(self, val):
        """Add an integer to IPv4Obj() and return an IPv4Obj()"""
        if not isinstance(val, int):
            raise ValueError(f"Cannot add type: '{type(val)}' to IPv4Obj()")

        orig_prefixlen = self.prefixlen
        total = self.as_decimal + val
        assert total <= IPV4_MAXINT, "Max IPv4 integer exceeded"
        assert total >= 0, "Min IPv4 integer exceeded"
        retval = IPv4Obj(total)
        retval.prefixlen = orig_prefixlen
        return retval

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __sub__(self, val):
        """Subtract an integer from IPv4Obj() and return an IPv4Obj()"""
        if not isinstance(val, int):
            raise ValueError(f"Cannot subtract type: '{type(val)}' from {self}")

        orig_prefixlen = self.prefixlen
        total = self.as_decimal - val
        assert total < IPV4_MAXINT, "Max IPv4 integer exceeded"
        assert total >= 0, "Min IPv4 integer exceeded"
        retval = IPv4Obj(total)
        retval.prefixlen = orig_prefixlen
        return retval

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __contains__(self, val):
        # Used for "foo in bar"... python calls bar.__contains__(foo)
        try:
            if self.network_object.prefixlen == 0:
                return True
            elif self.network_object.prefixlen > val.network_object.prefixlen:
                # obvious shortcut... if this object's mask is longer than
                #    val, this object cannot contain val
                return False
            else:
                # return (val.network in self.network)
                #
                ## Last used: 2020-07-12... version 1.5.6
                # return (self.network <= val.network) and (
                #    self.broadcast >= val.broadcast
                # )
                return (self.as_decimal_network <= val.as_decimal_network) and (self.as_decimal_broadcast >= val.as_decimal_broadcast) and (self.prefixlen <= val.prefixlen)

        except ValueError as eee:
            raise ValueError(
                "Could not check whether '{}' is contained in '{}': {}".format(
                    val, self, str(eee)
                )
            )
        except BaseException as eee:
            raise ValueError(
                "Could not check whether '{}' is contained in '{}': {}".format(
                    val, self, str(eee)
                )
            )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __hash__(self):
        # Python3 needs __hash__()
        return hash(str(self.ip_object)) + hash(str(self.prefixlen))

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __iter__(self):
        return self.network_object.__iter__()

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def __next__(self):
        ## For Python3 iteration...
        return self.network_object.__next__()

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def next(self):
        ## For Python2 iteration...
        return self.network_object.__next__()

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def _version(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return self.version

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def _prefixlen(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return self.prefixlen

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def _max_prefixlen(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return IPV4_MAX_PREFIXLEN

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @staticmethod
    def get_regex():
        return _IPV4_REGEX_STR

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def _ip(self):
        """Returns the address as an integer.  This property exists for compatibility with ipaddress.IPv4Address() in stdlib"""
        return int(self.ip_object)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def ip(self):
        """Returns the address as an :class:`ipaddress.IPv4Address` object."""
        return self.ip_object

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def netmask(self):
        """Returns the network mask as an :class:`ipaddress.IPv4Address` object."""
        return self.network_object.netmask

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def masklen(self):
        """Returns the length of the network mask as an integer."""
        return int(self.network_object.prefixlen)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @masklen.setter
    def masklen(self, arg):
        """masklen setter method"""
        self.network_object = IPv4Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def masklength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @masklength.setter
    def masklength(self, arg):
        """masklen setter method"""
        self.network_object = IPv4Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def prefixlen(self):
        """Returns the length of the network mask as an integer."""
        return int(self.network_object.prefixlen)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @prefixlen.setter
    def prefixlen(self, arg):
        """prefixlen setter method"""
        self.network_object = IPv4Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def prefixlength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @prefixlength.setter
    def prefixlength(self, arg):
        """prefixlength setter method"""
        self.network_object = IPv4Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def exploded(self):
        """Returns the IPv4 Address object as a string.  The string representation is in dotted decimal notation. Leading zeroes are never included in the representation."""
        return self.ip_object.exploded

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def packed(self):
        """Returns the IPv4 object as packed hex bytes"""
        return self.ip_object.packed

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def broadcast(self):
        """Returns the broadcast address as an :class:`ipaddress.IPv4Address` object."""
        if sys.version_info[0] < 3:
            return self.network_object.broadcast
        else:
            return self.network_object.broadcast_address

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def network(self):
        """Returns an :class:`ipaddress.IPv4Network` object, which represents this network."""
        if sys.version_info[0] < 3:
            return self.network_object.network
        else:
            ## The ipaddress module returns an "IPAddress" object in Python3...
            return IPv4Network(f"{self.network_object.compressed}")

    # @property
    # def as_decimal_network(self):
    #    """Returns an integer calculated from the network address..."""
    #    num_strings = str(self.network).split(".")
    #    num_strings.reverse()  # reverse the order
    #    return sum(
    #        [int(num, 16) * (65536 ** idx) for idx, num in enumerate(num_strings)]
    #    )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def hostmask(self):
        """Returns the host mask as an :class:`ipaddress.IPv4Address` object."""
        return self.network_object.hostmask

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def max_int(self):
        """Return the maximum size of an IPv4 Address object as an integer"""
        return IPV4_MAXINT

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def inverse_netmask(self):
        """Returns the host mask as an :class:`ipaddress.IPv4Address` object."""
        return self.network_object.hostmask

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def version(self):
        """Returns the IP version of the object as an integer.  i.e. 4"""
        return 4

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def network_offset(self):
        """Returns the integer difference between host number and network number.  This must be less than `numhosts`"""
        offset = self.as_decimal - self.as_decimal_network
        assert offset <= self.numhosts
        return offset

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @network_offset.setter
    def network_offset(self, arg):
        """
        Accept an integer network_offset and modify this IPv4Obj() to be 'arg' integer offset from the subnet.

        Throw an error if the network_offset would exceed the existing subnet boundary.

        Example
        -------
        >>> addr = IPv6Obj("192.0.2.1/24")
        >>> addr.network_offset = 20
        >>> addr
        <IPv6Obj 192.0.2.20/24>
        >>>
        """
        if isinstance(arg, (int, str)):
            arg = int(arg)
            # get the max offset for this subnet...
            max_offset = self.as_decimal_broadcast - self.as_decimal_network
            if arg <= max_offset:
                self.ip_object = IPv4Address(self.as_decimal_network + arg)
            else:
                raise AddressValueError(f"{self}.network_offset({arg=}) exceeds the boundaries of '{self.as_cidr_net}'")
        else:
            raise NotImplementedError

    # On IPv4Obj()
    @property
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if self.prefixlength <= 30:
            return 2 ** (IPV4_MAX_PREFIXLEN - self.network_object.prefixlen) - 2
        elif self.prefixlength == 31:
            # special case... /31 subnet has no broadcast address
            return 2
        elif self.prefixlength == 32:
            return 1
        else:
            # We (obviously) should never hit this...
            raise NotImplementedError

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_decimal(self):
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.ip).split(".")
        num_strings.reverse()  # reverse the order
        return sum(int(num) * (256**idx) for idx, num in enumerate(num_strings))

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_decimal_network(self):
        """Returns the integer value of the IP network as a decimal integer; explicitly, if this object represents 1.1.1.5/24, 'as_decimal_network' returns the integer value of 1.1.1.0/24"""
        num_strings = str(self.network).split("/")[0].split(".")
        num_strings.reverse()  # reverse the order
        return sum(int(num) * (256**idx) for idx, num in enumerate(num_strings))

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_decimal_broadcast(self):
        """Returns the integer value of the IP broadcast as a decimal integer; explicitly, if this object represents 1.1.1.5/24, 'as_decimal_broadcast' returns the integer value of 1.1.1.255"""
        broadcast_offset = 2 ** (IPV4_MAX_PREFIXLEN - self.network_object.prefixlen) - 1
        return self.as_decimal_network + broadcast_offset

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_int(self):
        """Returns the IP address as a decimal integer"""
        return self.as_decimal

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_zeropadded(self):
        """Returns the IP address as a zero-padded string (useful when sorting in a text-file)"""
        num_strings = str(self.ip).split(".")
        return ".".join([f"{int(num):03}" for num in num_strings])

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_zeropadded_network(self):
        """Returns the IP network as a zero-padded string (useful when sorting in a text-file)"""
        num_strings = self.as_cidr_net.split("/")[0].split(".")
        return (
            ".".join([f"{int(num):03}" for num in num_strings])
            + "/" + str(self.prefixlen)
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_hex(self):
        """Returns the IP address as a hex string"""
        return hex(self)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_binary_tuple(self):
        """Returns the IP address as a tuple of zero-padded binary strings"""
        return tuple(f"{int(num):08b}" for num in str(self.ip).split("."))

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_hex_tuple(self):
        """Returns the IP address as a tuple of zero-padded hex strings"""
        return tuple(f"{int(num):02x}" for num in str(self.ip).split("."))

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_cidr_addr(self):
        """Returns a string with the address in CIDR notation"""
        return str(self.ip) + "/" + str(self.prefixlen)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def as_cidr_net(self):
        """Returns a string with the network in CIDR notation"""
        if sys.version_info[0] < 3:
            return str(self.network) + "/" + str(self.prefixlen)
        else:
            return str(self.network)

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def is_multicast(self):
        """Returns a boolean for whether this is a multicast address"""
        return self.network_object.is_multicast

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def is_private(self):
        """Returns a boolean for whether this is a private address"""
        return self.network_object.is_private

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    @property
    def is_reserved(self):
        """Returns a boolean for whether this is a reserved address"""
        return self.network_object.is_reserved


# Build a wrapper around ipaddress classes to mimic the behavior of network
# interfaces (such as persisting host-bits when the intf masklen changes) and
# add custom @properties
class IPv6Obj(object):

    # This method is on IPv6Obj().  @logger.catch() breaks the __init__() method.
    def __init__(self, v6addr_prefixlen=f"::1/{IPV6_MAX_PREFIXLEN}", strict=False, debug=0):
        """An object to represent IPv6 addresses and IPv6 networks.

        When :class:`~ccp_util.IPv6Obj` objects are compared or sorted, network numbers are sorted lower to higher.  If network numbers are the same, shorter masks are lower than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses.  Comparisons between :class:`~ccp_util.IPv6Obj` instances was chosen so it's easy to find the longest-match for a given prefix.

        This object emulates the behavior of ipaddr.IPv6Network() (in Python2) where host-bits were retained in the IPv6Network() object.  :class:`ipaddress.IPv6Network` in Python3 does not retain host-bits; the desire to retain host-bits in both Python2 and Python3 ip network objects was the genesis of this API.

        Parameters
        ----------
        v6addr_prefixlen : str or int
            A string containing an IPv6 address, and optionally a netmask or masklength.  Integers are also accepted; the mask is assumed to be 128 bits if an integer is provided. The following address/netmask formats are supported: "2001::dead:beef", "2001::dead:beef/64",
        strict : bool
            When `strict` is True, the value of `v6addr_prefixlen` must not have host-bits set.  The default value is False.

        Examples
        --------

        >>> from ciscoconfparse.ccp_util import IPv6Obj
        >>> net = IPv6Obj(42540488161975842760550356429036175087)
        >>> net
        <IPv6Obj 2001::dead:beef/64>
        >>> net = IPv6Obj("2001::dead:beef/64")
        >>> net
        <IPv6Obj 2001::dead:beef/64>
        >>>

        Attributes
        ----------
        network : :class:`ipaddress.IPv6Network`
            Returns an :class:`ipaddress.IPv6Network` with the network of this object
        network_object : :class:`ipaddress.IPv6Network`
            Returns an :class:`ipaddress.IPv6Network` with the network of this object
        ip_object  : :class:`ipaddress.IPv6Address`
            Returns an :class:`ipaddress.IPv6Address` with the host address of this object
        ip : :class:`ipaddress.IPv6Address`
            Returns an :class:`ipaddress.IPv6Address` with the host address of this object
        as_binary_tuple : tuple
            The ipv6 address as a tuple of zero-padded binary strings
        as_decimal : int
            The ipv6 address as a decimal integer
        as_decimal_network : int
            The network address as a decimal integer
        as_hex_tuple : tuple
            The ipv6 address as a tuple of zero-padded 8-bit hex strings
        get_regex : str
            Returns the regex string used for an IPv6 Address
        netmask : :class:`ipaddress.IPv6Address`
            An :class:`ipaddress.IPv6Address` object containing the netmask
        network_offset : int
            Returns the integer difference between host number and network number.  This must be less than `numhosts`
        numhosts : int
            An integer representing the number of host addresses contained in the network
        prefixlen : int
            An integer representing the length of the netmask
        broadcast: raises `NotImplementedError`; IPv6 doesn't use broadcast addresses
        hostmask : :class:`ipaddress.IPv6Address`
            An :class:`ipaddress.IPv6Address` representing the hostmask
        numhosts : int
            An integer representing the number of hosts contained in the network

        """

        if debug > 0:
            logger.info(f"IPv6Obj(v6addr_prefixlen='{v6addr_prefixlen}', strict={strict}, debug={debug}) was called")

        self.v6addr_prefixlen = v6addr_prefixlen
        self.dna = "IPv6Obj"
        self.ip_object = None
        self.network_object = None
        self.strict = strict
        self.debug = debug


        if isinstance(v6addr_prefixlen, str):
            assert len(v6addr_prefixlen) <= IPV6_MAXSTR_LEN

            tmp = re.split(r"\s+", v6addr_prefixlen.strip())
            if len(tmp)==2:
                v6addr_prefixlen = "/".join(tmp)
            elif len(tmp)==1:
                v6addr_prefixlen = tmp[0]
            else:
                raise NotImplementedError(v6addr_prefixlen.strip())

            v6_str_rgx = _RGX_IPV6ADDR.search(v6addr_prefixlen.strip())
            # Example 'pp'
            #     pp = {'addr': '2b00:cd80:14:10::1', 'opt1': None, 'opt2': None, 'opt3': None, 'opt4': None, 'opt5': '2b00:cd80:14:10::1', 'opt6': None, 'opt7': None, 'opt8': None, 'opt9': None, 'opt10': None, 'masklen': '64'}
            pp = v6_str_rgx.groupdict()
            for key in ["addr", "opt1", "opt2", "opt3", "opt4", "opt5", "opt6", "opt7", "opt8", "opt9", "opt10",]:
                ipv6 = pp[key]
                if ipv6 is not None:
                    break
            else:
                ipv6 = "::1"
            assert ipv6 is not None

            self.ip_object = IPv6Address(ipv6)
            if isinstance(pp["masklen"], str):
                netstr = ipv6 + "/" + pp["masklen"]
            # FIXME - this probably should be removed...
            #elif isinstance(pp["netmask"], str):
            #    netstr = ipv6 + "/" + pp["netmask"]
            else:
                netstr = ipv6+"/128"
            self.network_object = IPv6Network(netstr, strict=False)

        elif isinstance(v6addr_prefixlen, int):
            assert 0 <= v6addr_prefixlen <= IPV6_MAXINT
            self.ip_object = IPv6Address(v6addr_prefixlen)
            self.network_object = IPv6Network(v6addr_prefixlen, strict=False)

        elif isinstance(v6addr_prefixlen, IPv6Obj):
            self.ip_object = IPv6Address(v6addr_prefixlen.ip)
            self.network_object = IPv6Network(v6addr_prefixlen.as_cidr_net, strict=False)

        else:
            raise AddressValueError(
                "Could not parse '{}' (type: {}) into an IPv6 Address".format(
                    v6addr_prefixlen, type(v6addr_prefixlen)
                )
            )

    # On IPv6Obj()
    def _ipv6_params_dict_DEPRECATED(self, arg, debug=0):
        """
        Parse out important IPv6 parameters from arg.  This method must run to
        completion for IPv6 address parsing to work correctly.
        """
        if not isinstance(arg, (str, int, IPv6Obj,)):
            raise ValueError

        if isinstance(arg, str):
            try:
                mm = _RGX_IPV6ADDR.search(arg)

            except TypeError:
                raise AddressValueError(
                    f"_ipv6_params_dict() doesn't know how to parse {arg}"
                )
            except BaseException:
                raise AddressValueError(
                    f"_ipv6_params_dict() doesn't know how to parse {arg}"
                )


            ERROR = f"_ipv6_params_dict() couldn't parse '{arg}'"
            assert mm is not None, ERROR

            mm_result = mm.groupdict()
            try:
                addr = mm_result["addr"]

            except BaseException:
                addr = "::1"

            try:
                masklen = int(mm_result['masklen'])
            except BaseException:
                masklen = IPV6_MAX_PREFIXLEN

            if not (isinstance(masklen, int) and masklen <= 128):
                raise ValueError

            # If we have to derive the netmask as a long hex string,
            # calculate the netmask from the masklen as follows...
            netmask_int = (2**128 - 1) - (2**(128 - masklen) - 1)
            netmask = str(IPv6Address(netmask_int))

        elif isinstance(arg, int):
            # Assume this arg int() represents an IPv6 host-address
            addr = str(IPv6Address(arg))
            netmask = 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'
            masklen = 128

        elif isinstance(arg, IPv6Obj):
            addr = str(arg.ip)
            netmask = str(arg.netmask)
            masklen = int(arg.masklen)

        else:
            raise AddressValueError("IPv6Obj(arg='%s')" % (arg))

        assert 0 <= masklen <= IPV6_MAX_PREFIXLEN

        params_dict = {
            'ipv6_addr': addr,
            'ip_version': 6,
            'ip_arg_str': str(addr) + "/" + str(masklen),
            'netmask': netmask,
            'masklen': masklen,
        }

        if params_dict.get('masklen', None) is not None:
            ip_arg_str = f"{addr}/{masklen}"
            params_dict['ip_arg_str'] = ip_arg_str
        else:
            raise AddressValueError("IPv6Obj(arg='%s')" % (arg))

        return params_dict

    # On IPv6Obj()
    def __repr__(self):
        # Detect IPv4_mapped IPv6 addresses...
        if self.is_ipv4_mapped:
            return """<IPv6Obj ::ffff:{}/{}>""".format(
                str(self.ip.ipv4_mapped), self.prefixlen
            )
        else:
            return f"""<IPv6Obj {str(self.ip)}/{self.prefixlen}>"""

    # On IPv6Obj()
    def __eq__(self, val):
        try:
            for obj in [self, val]:
                for attr_name in ["as_decimal", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except AssertionError:
                        return False

            # Compare objects numerically...
            if self.as_decimal == val.as_decimal and self.prefixlen == val.prefixlen:
                return True
            return False
        except BaseException as e:
            errmsg = "'{}' cannot compare itself to '{}': {}".format(
                self.__repr__(), val, e
            )
            raise ValueError(errmsg)

    # On IPv6Obj()
    def __ne__(self, val):
        return not self.__eq__(val)

    # On IPv6Obj()
    def __gt__(self, val):
        try:
            for obj in [self, val]:
                for attr_name in ["as_decimal", "as_decimal_network", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except (AssertionError):
                        error_str = "Cannot compare {} with '{}'".format(
                            self, type(obj)
                        )
                        raise AssertionError(error_str)

            val_prefixlen = int(getattr(val, "prefixlen"))
            self_prefixlen = int(getattr(self, "prefixlen"))
            val_ndec = int(getattr(val, "as_decimal_network"))
            self_ndec = int(getattr(self, "as_decimal_network"))
            val_dec = int(getattr(val, "as_decimal"))
            self_dec = int(getattr(self, "as_decimal"))

            if self_ndec == val_ndec and self_prefixlen == val_prefixlen:
                return self_dec > val_dec

            # for the same network, longer prefixlens sort "higher" than shorter prefixlens
            elif self_ndec == val_ndec:
                return self_prefixlen > val_prefixlen

            else:
                return self_ndec > val_ndec

        except BaseException:
            errmsg = f"{self.__repr__()} cannot compare itself to '{val}'"
            raise ValueError(errmsg)

    # On IPv6Obj()
    def __lt__(self, val):
        try:
            for obj in [self, val]:
                for attr_name in ["as_decimal", "prefixlen"]:
                    try:
                        assert getattr(obj, attr_name, None) is not None
                    except (AssertionError):
                        error_str = "Cannot compare {} with '{}'".format(
                            self, type(obj)
                        )
                        raise AssertionError(error_str)

            val_prefixlen = int(getattr(val, "prefixlen"))
            self_prefixlen = int(getattr(self, "prefixlen"))
            val_ndec = int(getattr(val, "as_decimal_network"))
            self_ndec = int(getattr(self, "as_decimal_network"))
            val_dec = int(getattr(val, "as_decimal"))
            self_dec = int(getattr(self, "as_decimal"))

            if self_ndec == val_ndec and self_prefixlen == val_prefixlen:
                return self_dec < val_dec

            # for the same network, longer prefixlens sort "higher" than shorter prefixlens
            elif self_ndec == val_ndec:
                return self_prefixlen < val_prefixlen

            else:
                return self_ndec < val_ndec

        except BaseException:
            errmsg = f"{self.__repr__()} cannot compare itself to '{val}'"
            raise ValueError(errmsg)

    # On IPv6Obj()
    def __int__(self):
        """Return this object as an integer"""
        if getattr(self, "as_decimal", None) is not None:
            return self.as_decimal
        else:
            return False

    # On IPv6Obj()
    def __index__(self):
        """Return this object as an integer (used for hex() and bin() operations)"""
        if getattr(self, "as_decimal", None) is not None:
            return self.as_decimal
        else:
            return False

    # On IPv6Obj()
    def __add__(self, val):
        """Add an integer to IPv6Obj() and return an IPv6Obj()"""
        if not isinstance(val, int):
            raise ValueError("Cannot add type: '{}' to {}".format(type(val), self))

        orig_prefixlen = self.prefixlen
        total = self.as_decimal + val
        assert total <= IPV6_MAXINT, "Max IPv6 integer exceeded"
        assert total >= 0, "Min IPv6 integer exceeded"
        retval = IPv6Obj(total)
        retval.prefixlen = orig_prefixlen
        return retval

    # On IPv6Obj()
    def __sub__(self, val):
        """Subtract an integer from IPv6Obj() and return an IPv6Obj()"""
        if not isinstance(val, int):
            raise ValueError("Cannot subtract type: '{}' from {}".format(type(val), self))

        orig_prefixlen = self.prefixlen
        total = self.as_decimal - val
        assert total < IPV6_MAXINT, "Max IPv6 integer exceeded"
        assert total >= 0, "Min IPv6 integer exceeded"
        retval = IPv6Obj(total)
        retval.prefixlen = orig_prefixlen
        return retval

    # On IPv6Obj()
    def __contains__(self, val):
        # Used for "foo in bar"... python calls bar.__contains__(foo)
        try:
            if self.network_object.prefixlen == 0:
                return True
            elif self.network_object.prefixlen > val.network_object.prefixlen:
                # obvious shortcut... if this object's mask is longer than
                #    val, this object cannot contain val
                return False
            else:
                # NOTE: We cannot use the same algorithm as IPv4Obj.__contains__() because IPv6Obj doesn't have .broadcast
                # return (val.network in self.network)
                #
                ## Last used: 2020-07-12... version 1.5.6
                # return (self.network <= val.network) and (
                #    (self.as_decimal + self.numhosts - 1)
                #    >= (val.as_decimal + val.numhosts - 1)
                # )
                return (self.as_decimal_network <= val.as_decimal_network) and (
                    (self.as_decimal_network + self.numhosts - 1)
                    >= (val.as_decimal_network + val.numhosts - 1)
                )

        except (BaseException) as e:
            raise ValueError(
                "Could not check whether '{}' is contained in '{}': {}".format(
                    val, self, e
                )
            )

    # On IPv6Obj()
    def __hash__(self):
        # Python3 needs __hash__()
        return hash(str(self.ip_object)) + hash(str(self.prefixlen))

    # On IPv6Obj()
    def __iter__(self):
        return self.network_object.__iter__()

    # On IPv6Obj()
    def __next__(self):
        ## For Python3 iteration...
        return self.network_object.__next__()

    # On IPv6Obj()
    def next(self):
        ## For Python2 iteration...
        return self.network_object.__next__()

    # On IPv6Obj()
    @staticmethod
    def get_regex():
        return _IPV6_REGEX_STR

    # On IPv6Obj()
    @property
    def _version(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return self.version

    # On IPv6Obj()
    @property
    def _prefixlen(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return self.prefixlen

    # On IPv6Obj()
    @property
    def _max_prefixlen(self):
        """
        Fix github issue #203... build a `_prefixlen` attribute...
        """
        return IPV6_MAX_PREFIXLEN

    # On IPv6Obj()
    @property
    def is_ipv4_mapped(self):
        # ref RFC 4291 -  Section 2.5.5.2
        #     https://datatracker.ietf.org/doc/html/rfc4291#section-2.5.5.2
        #
        # ref RFC 5156 - Section 2.2 IPv4 mapped addresses
        #     https://datatracker.ietf.org/doc/html/rfc5156#section-2.2
        #
        # if self.ip in IPv6Network("::ffff:0:0/96", strict=False):
        if IPv6Network("::ffff:0:0/96").__contains__(self.ip):
            return True
        return False

    # On IPv6Obj()
    @property
    def _ip(self):
        """Returns the address as an integer.  This property exists for compatibility with ipaddress.IPv6Address() in stdlib"""
        return int(self.ip_object)

    # On IPv6Obj()
    @property
    def ip(self):
        """Returns the address as an :class:`ipaddress.IPv6Address` object."""
        return self.ip_object

    # On IPv6Obj()
    @property
    def netmask(self):
        """Returns the network mask as an :class:`ipaddress.IPv6Address` object."""
        return self.network_object.netmask

    # On IPv6Obj()
    @property
    def masklen(self):
        """Returns the length of the network mask as an integer."""
        return int(self.network_object.prefixlen)

    # On IPv6Obj()
    @masklen.setter
    def masklen(self, arg):
        """masklen setter method"""
        self.network_object = IPv6Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # On IPv6Obj()
    @property
    def masklength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    # On IPv6Obj()
    @masklength.setter
    def masklength(self, arg):
        """masklength setter method"""
        self.network_object = IPv6Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # On IPv6Obj()
    @property
    def prefixlen(self):
        """Returns the length of the network mask as an integer."""
        return int(self.network_object.prefixlen)

    # On IPv6Obj()
    @prefixlen.setter
    def prefixlen(self, arg):
        """prefixlen setter method"""
        self.network_object = IPv6Network(
            f"{str(self.ip_object)}/{arg}", strict=False
        )

    # On IPv6Obj()
    @property
    def prefixlength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    # On IPv6Obj()
    @property
    def compressed(self):
        """Returns the IPv6 Network object in compressed form"""
        return self.network_object.compressed

    # On IPv6Obj()
    @property
    def exploded(self):
        """Returns the IPv6 Address object in exploded form"""
        return self.ip_object.exploded

    # On IPv6Obj()
    @property
    def packed(self):
        """Returns the IPv6 object as packed hex bytes"""
        return self.ip_object.packed

    # On IPv6Obj()
    @property
    def broadcast(self):
        raise NotImplementedError("IPv6 does not use broadcast")

    # On IPv6Obj()
    @property
    def network(self):
        """Returns an :class:`ipaddress.IPv6Network` object, which represents this network."""
        ## The ipaddress module returns an "IPAddress" object in Python3...
        return IPv6Network(f"{self.network_object.compressed}")

    # On IPv6Obj()
    @property
    def as_decimal_network(self):
        """Returns the integer value of the IP network as a decimal integer; explicitly, if this object represents 2b00:cd80:14:10::1/64, 'as_decimal_network' returns the integer value of 2b00:cd80:14:10::0/64"""
        num_strings = str(self.network.exploded).split("/")[0].split(":")
        num_strings.reverse()  # reverse the order
        return sum(
            int(num, 16) * (65536**idx) for idx, num in enumerate(num_strings)
        )

    # do NOT wrap with @logger.catch(...)
    # On IPv6Obj()
    @property
    def as_decimal_broadcast(self):
        """IPv6 does not support broadcast addresses.  Use 'as_decimal_network_maxint' if you want the integer value that would otherwise be an IPv6 broadcast."""
        raise NotImplementedError("IPv6 does not support broadcast addresses.  Use 'as_decimal_network_maxint' if you want the integer value that would otherwise be an IPv6 broadcast.")

    # do NOT wrap with @logger.catch(...)
    # On IPv6Obj()
    @property
    def as_decimal_network_maxint(self):
        """Returns the integer value of the maximum value of an IPv6 subnet as a decimal integer; explicitly, if this object represents 2b00:cd80:14:10::0/64, 'as_decimal_network_maxint' returns the integer value of 2b00:cd80:14:10:ffff:ffff:ffff:ffff"""
        network_maxint_offset = 2 ** (IPV6_MAX_PREFIXLEN - self.network_object.prefixlen) - 1
        return self.as_decimal_network + network_maxint_offset

    # On IPv6Obj()
    @property
    def hostmask(self):
        """Returns the host mask as an :class:`ipaddress.IPv6Address` object."""
        return self.network_object.hostmask

    # On IPv6Obj()
    @property
    def max_int(self):
        """Return the maximum size of an IPv6 Address object as an integer"""
        return IPV6_MAXINT

    # On IPv6Obj()
    @property
    def inverse_netmask(self):
        """Returns the host mask as an :class:`ipaddress.IPv6Address` object."""
        return self.network_object.hostmask

    # On IPv6Obj()
    @property
    def version(self):
        """Returns the IP version of the object as an integer.  i.e. 6"""
        return 6

    # do NOT wrap with @logger.catch(...)
    # On IPv6Obj()
    @property
    def network_offset(self):
        """Returns the integer difference between host number and network number.  This must be less than `numhosts`"""
        offset = self.as_decimal - self.as_decimal_network
        assert offset <= self.numhosts
        return offset

    # do NOT wrap with @logger.catch(...)
    # On IPv6Obj()
    @network_offset.setter
    def network_offset(self, arg):
        """
        Accept an integer network_offset and modify this IPv6Obj() to be 'arg' integer offset from the subnet.

        Throw an error if the network_offset would exceed the existing subnet boundary.

        Example
        -------
        >>> addr = IPv6Obj("2b00:cd80:14:10::1/64")
        >>> addr.network_offset = 20
        >>> addr
        <IPv6Obj 2b00:cd80:14:10::20/64>
        >>>
        """
        if isinstance(arg, (int, str)):
            arg = int(arg)
            # get the max offset for this subnet...
            max_offset = self.as_decimal_network_maxint - self.as_decimal_network
            if arg <= max_offset:
                self.ip_object = IPv6Address(self.as_decimal_network + arg)
            else:
                raise AddressValueError(f"{self}.network_offset({arg=}) exceeds the boundaries of '{self.as_cidr_net}'")
        else:
            raise NotImplementedError


    # On IPv6Obj()
    @property
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if self.prefixlength <= 126:
            return 2 ** (IPV6_MAX_PREFIXLEN - self.network_object.prefixlen) - 2
        elif self.prefixlength == 127:
            # special case... /127 subnet has no broadcast address
            return 2
        elif self.prefixlength == 128:
            return 1
        else:
            # We (obviously) should never hit this...
            raise NotImplementedError

    # On IPv6Obj()
    @property
    def as_decimal(self):
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.ip.exploded).split(":")
        num_strings.reverse()  # reverse the order
        return sum(
            int(num, 16) * (65536**idx) for idx, num in enumerate(num_strings)
        )

    # On IPv6Obj()
    def as_int(self):
        """Returns the IP address as a decimal integer"""
        return self.as_decimal

    # On IPv6Obj()
    @property
    def as_binary_tuple(self):
        """Returns the IPv6 address as a tuple of zero-padded 16-bit binary strings"""
        result_list = [f"{int(ii, 16):016b}" for ii in self.as_hex_tuple]
        return tuple(result_list)

    # On IPv6Obj()
    @property
    def as_hex(self):
        """Returns the IP address as a hex string"""
        return hex(self)

    # On IPv6Obj()
    @property
    def as_hex_tuple(self):
        """Returns the IPv6 address as a tuple of zero-padded 16-bit hex strings"""
        result_list = str(self.ip.exploded).split(":")
        return tuple(result_list)

    # On IPv6Obj()
    @property
    def as_cidr_addr(self):
        """Returns a string with the address in CIDR notation"""
        return str(self.ip) + "/" + str(self.prefixlen)

    # On IPv6Obj()
    @property
    def as_cidr_net(self):
        """Returns a string with the network in CIDR notation"""
        if sys.version_info[0] < 3:
            return str(self.network) + "/" + str(self.prefixlen)
        else:
            return str(self.network)

    # On IPv6Obj()
    @property
    def is_multicast(self):
        """Returns a boolean for whether this is a multicast address"""
        return self.network_object.is_multicast

    # On IPv6Obj()
    @property
    def is_private(self):
        """Returns a boolean for whether this is a private address"""
        return self.network_object.is_private

    # On IPv6Obj()
    @property
    def is_reserved(self):
        """Returns a boolean for whether this is a reserved address"""
        return self.network_object.is_reserved

    # On IPv6Obj()
    @property
    def is_link_local(self):
        """Returns a boolean for whether this is an IPv6 link-local address"""
        return self.network_object.is_link_local

    # On IPv6Obj()
    @property
    def is_site_local(self):
        """Returns a boolean for whether this is an IPv6 site-local address"""
        return self.network_object.is_site_local

    # On IPv6Obj()
    @property
    def is_unspecified(self):
        """Returns a boolean for whether this address is not otherwise
        classified"""
        return self.network_object.is_unspecified

    # On IPv6Obj()
    @property
    def teredo(self):
        return self.network_object.teredo

    # On IPv6Obj()
    @property
    def sixtofour(self):
        return self.network_object.sixtofour


class L4Object(object):
    """Object for Transport-layer protocols; the object ensures that logical operators (such as le, gt, eq, and ne) are parsed correctly, as well as mapping service names to port numbers

    Examples
    --------
    >>> from ciscoconfparse.ccp_util import L4Object
    >>> obj = L4Object(protocol="tcp", port_spec="range ssh smtp", syntax="asa")
    >>> obj
    <L4Object tcp ports: 22-25>
    >>> obj.protocol
    'tcp'
    >>> 25 in obj.port_list
    True
    >>>
    """

    def __init__(self, protocol="", port_spec="", syntax=""):
        self.protocol = protocol
        self.port_list = list()
        self.syntax = syntax

        try:
            port_spec = port_spec.strip()
        except BaseException as eee:
            error = f"{eee} while stripping whitespace from `port_spec`."
            logger.error(error)
            raise ValueError(error)

        if syntax == "asa":
            if protocol == "tcp":
                ports = ASA_TCP_PORTS
            elif protocol == "udp":
                ports = ASA_UDP_PORTS
            else:
                raise NotImplementedError(
                    "'{0}' is not supported: '{0}'".format(protocol)
                )
        else:
            raise NotImplementedError(f"This syntax is unknown: '{syntax}'")

        if "eq " in port_spec.strip():
            port_tmp = re.split(r"\s+", port_spec)[-1].strip()
            eq_port = int(ports.get(port_tmp, port_tmp))
            assert 1 <= eq_port <= 65535
            self.port_list = [eq_port]
        elif re.search(r"^\S+$", port_spec.strip()):
            # Technically, 'eq ' is optional...
            eq_port = int(ports.get(port_spec.strip(), port_spec.strip()))
            assert 1 <= eq_port <= 65535
            self.port_list = [eq_port]
        elif "range " in port_spec.strip():
            port_tmp = re.split(r"\s+", port_spec)[1:]
            low_port = int(ports.get(port_tmp[0], port_tmp[0]))
            high_port = int(ports.get(port_tmp[1], port_tmp[1]))
            assert low_port <= high_port
            self.port_list = sorted(range(low_port, high_port + 1))
        elif "lt " in port_spec.strip():
            port_tmp = re.split(r"\s+", port_spec)[-1]
            high_port = int(ports.get(port_tmp, port_tmp))
            assert 65536 >= high_port >= 2
            self.port_list = sorted(range(1, high_port))
        elif "gt " in port_spec.strip():
            port_tmp = re.split(r"\s+", port_spec)[-1]
            low_port = int(ports.get(port_tmp, port_tmp))
            assert 0 < low_port < 65535
            self.port_list = sorted(range(low_port + 1, 65536))
        elif "neq " in port_spec.strip():
            port_str = re.split(r"\s+", port_spec)[-1]
            tmp = set(range(1, 65536))
            tmp.remove(int(port_str))
            self.port_list = sorted(tmp)
        else:
            raise NotImplementedError(
                f"This port_spec is unknown: '{port_spec}'"
            )

    def __eq__(self, val):
        if (self.protocol == val.protocol) and (self.port_list == val.port_list):
            return True
        return False

    def __repr__(self):
        crobj = CiscoRange()
        crobj._list = self.port_list
        return f"<L4Object {self.protocol} ports: {crobj.compressed_str}>"


class DNSResponse(object):
    """A universal DNS Response object

    Parameters
    ----------
    query_type : str
        A string containing the DNS record type to lookup
    result_str : str
        A string containing the DNS Response
    input_str : str
        The DNS query string
    duration : float
        The query duration in seconds

    Attributes
    ----------
    query_type : str
        A string containing the DNS record type to lookup
    result_str : str
        A string containing the DNS Response
    input_str : str
        The DNS query string
    has_error : bool
        Indicates the query resulted in an error when True
    error_str : str
        The error returned by dnspython
    duration : float
        The query duration in seconds
    preference : int
        The MX record's preference (default: -1)

    Returns
    -------
    A :class:`~ccp_util.DNSResponse` instance"""

    def __init__(self, query_type="", result_str="", input_str="", duration=0.0):
        self.query_type = query_type
        self.result_str = result_str
        self.input_str = input_str
        self.duration = duration  # Query duration in seconds

        self.has_error = False
        self.error_str = ""
        self.preference = -1  # MX Preference

    def __str__(self):
        return self.result_str

    def __repr__(self):
        if not self.has_error:
            return '<DNSResponse "{}" result_str="{}">'.format(
                self.query_type, self.result_str
            )
        else:
            return '<DNSResponse "{}" error="{}">'.format(
                self.query_type, self.error_str
            )


@logger.catch(reraise=True)
def dns_query(input_str="", query_type="", server="", timeout=2.0):
    """A unified IPv4 & IPv6 DNS lookup interface; this is essentially just a wrapper around dnspython's API.  When you query a PTR record, you can use an IPv4 or IPv6 address (which will automatically be converted into an in-addr.arpa name.  This wrapper only supports a subset of DNS records: 'A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', and 'TXT'

    Paremeters
    ----------
    input_str : str
        A string containing the DNS record to lookup
    query_type : str
        A string containing the DNS record type (SOA not supported)
    server : str
        A string containing the fqdn or IP address of the dns server
    timeout : float
        DNS lookup timeout duration (default: 2.0 seconds)

    Returns
    -------
    A set([]) of :class:`~ccp_util.DNSResponse` instances.  Refer to the DNSResponse object in these docs for more information.

    Examples
    --------
    >>> from ciscoconfparse.ccp_util import dns_query
    >>> dns_query('www.pennington.net', "A", "4.2.2.2", timeout=0.5)
    {<DNSResponse "A" result_str="65.19.187.2">}
    >>> response_set = dns_query('www.pennington.net', 'A', '4.2.2.2')
    >>> aa = response_set.pop()
    >>> aa.result_str
    '65.19.187.2'
    >>> aa.error_str
    ''
    >>>
    """

    valid_records = {"A", "AAAA", "AXFR", "CNAME", "MX", "NS", "PTR", "TXT"}
    query_type = query_type.upper()
    assert query_type in valid_records
    assert server != ""
    assert float(timeout) > 0
    assert input_str != ""
    # input = input_str.strip()
    retval = set()
    rr = Resolver()
    rr.server = [socket.gethostbyname(server)]
    rr.timeout = float(timeout)
    rr.lifetime = float(timeout)
    start = time.time()
    if (query_type == "A") or (query_type == "AAAA"):
        try:
            answer = query(input_str, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    duration=duration,
                    input_str=input_str,
                    result_str=str(result.address),
                )
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
        except BaseException as eee:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = eee
            retval.add(response)

    elif query_type == "AXFR":
        """This is a hack: return text of zone transfer, instead of axfr objs"""
        _zone = zone.from_xfr(query.xfr(server, input_str, lifetime=timeout))
        return [_zone[node].to_text(node) for node in _zone.nodes.keys()]
    elif query_type == "CNAME":
        try:
            answer = rr.query(input_str, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    duration=duration,
                    input_str=input_str,
                    result_str=str(result.target),
                )
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
        except BaseException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
    elif query_type == "MX":
        try:
            answer = rr.query(input_str, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    input_str=input_str,
                    result_str=str(result.target),
                )
                response.preference = int(result.preference)
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
        except BaseException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
    elif query_type == "NS":
        try:
            answer = rr.query(input_str, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    duration=duration,
                    input_str=input_str,
                    result_str=str(result.target),
                )
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
        except BaseException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
    elif query_type == "PTR":

        try:
            IPv4Address(input_str)
            is_valid_v4 = True
        except BaseException:
            is_valid_v4 = False

        try:
            IPv6Address(input_str)
            is_valid_v6 = True
        except BaseException:
            is_valid_v6 = False

        if (is_valid_v4 is True) or (is_valid_v6 is True):
            inaddr = reversename.from_address(input_str)
        elif "in-addr.arpa" in input_str.lower():
            inaddr = input_str
        else:
            raise ValueError(f'Cannot query PTR record for "{input_str}"')

        try:
            answer = rr.query(inaddr, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    duration=duration,
                    input_str=inaddr,
                    result_str=str(result.target),
                )
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
    elif query_type == "TXT":
        try:
            answer = rr.query(input_str, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(
                    query_type=query_type,
                    duration=duration,
                    input_str=inaddr,
                    result_str=str(result.strings),
                )
                retval.add(response)
        except DNSException as e:
            duration = time.time() - start
            response = DNSResponse(
                input_str=input_str, duration=duration, query_type=query_type
            )
            response.has_error = True
            response.error_str = e
            retval.add(response)
    return retval


@logger.catch(reraise=True)
@deprecated(reason="dns_lookup() is obsolete; use dns_query() instead.  dns_lookup() will be removed", version='1.7.0')
def dns_lookup(input_str, timeout=3, server="", record_type="A"):
    """Perform a simple DNS lookup, return results in a dictionary"""
    if not isinstance(input_str, str):
        raise ValueError

    if not isinstance(timeout, (int, float)):
        error = f"An integer is required for `timeout`; not {timeout} {type(timeout)}"
        logger.error(error)
        raise DNSTimeoutError(error)

    if not isinstance(server, str):
        error = f"An string is required for `server`; not {server} {type(server)}"
        logger.error(error)
        raise DNSTimeoutError(error)

    if not isinstance(record_type, str):
        error = f"An string is required for `record_type`; not {record_type} {type(record_type)}."
        logger.error(error)
        raise DNSTimeoutError(error)


    rr = Resolver()
    rr.timeout = float(timeout)
    rr.lifetime = float(timeout)
    if server != "":
        rr.nameservers = [server]
    # dns_session = rr.resolve(input_str, record_type)
    dns_session = rr.query(input_str, record_type)
    responses = list()
    for rdata in dns_session:
        responses.append(str(rdata))

    """
    from dns import resolver
    rr = resolver.Resolver()
    rr.nameservers = ['8.8.8.8']
    rr.timeout = 2.0
    foo = rr.resolve('cisco.com', 'A')
    for rdata in foo:
        print("ADDR", rdata)
    """

    try:
        return {
            "record_type": record_type,
            "addrs": responses,
            "error": "",
            "name": input_str,
        }
    except DNSException as e:
        return {
            "record_type": record_type,
            "addrs": [],
            "error": repr(e),
            "name": input_str,
        }


@logger.catch(reraise=True)
@deprecated(reason="dns6_lookup() is obsolete; use dns_query() instead.  dns6_lookup() will be removed", version='1.7.0')
def dns6_lookup(input_str, timeout=3, server=""):
    """Perform a simple DNS lookup, return results in a dictionary"""
    rr = Resolver()
    rr.timeout = float(timeout)
    rr.lifetime = float(timeout)
    if server:
        rr.nameservers = [server]
    try:
        records = rr.query(input_str, "AAAA")
        return {
            "addrs": [ii.address for ii in records],
            "error": "",
            "name": input_str,
        }
    except DNSException as e:
        return {
            "addrs": [],
            "error": repr(e),
            "name": input_str,
        }


_REVERSE_DNS_REGEX = re.compile(r"^\s*\d+\.\d+\.\d+\.\d+\s*$")


@logger.catch(reraise=True)
def check_valid_ipaddress(input_addr=None):
    """
    Accept an input string with an IPv4 or IPv6 address. If the address is
    valid, return a tuple of:
    (input_addr, ipaddr_family)

    Throw an error if the address is not valid.
    """
    if not isinstance(input_addr, str):
        raise ValueError

    input_addr = input_addr.strip()
    ipaddr_family = 0
    try:
        IPv4Obj(input_addr)
        ipaddr_family = 4
    except BaseException:
        raise ValueError(input_addr)

    if ipaddr_family == 0:
        try:
            IPv6Obj(input_addr)
            ipaddr_family = 6
        except BaseException:
            raise ValueError(input_addr)

    error = "FATAL: '{0}' is not a valid IPv4 or IPv6 address.".format(input_addr)
    assert (ipaddr_family == 4 or ipaddr_family == 6), error
    return (input_addr, ipaddr_family)


@logger.catch(reraise=True)
@deprecated(reason="reverse_dns_lookup() is obsolete; use dns_query() instead.  reverse_dns_lookup() will be removed", version='1.7.0')
def reverse_dns_lookup(input_str, timeout=3.0, server="4.2.2.2", proto="udp"):
    """Perform a simple reverse DNS lookup on an IPv4 or IPv6 address; return results in a python dictionary"""
    if not isinstance(proto, str) and (proto=="udp" or proto=="tcp"):
        raise ValueError

    if not isinstance(float(timeout), float) and float(timeout) > 0.0:
        raise ValueError


    addr, addr_family = check_valid_ipaddress(input_str)
    assert addr_family==4 or addr_family==6

    if proto!="tcp" and proto!="udp":
        raise ValueError()

    raw_result = dns_query(input_str, query_type="PTR", server=server, timeout=timeout)
    if not isinstance(raw_result, set):
        raise ValueError

    assert len(raw_result)>=1
    tmp = raw_result.pop()
    if not isinstance(tmp, DNSResponse):
        raise ValueError


    if tmp.has_error is True:
        retval = {'addrs': [input_str], 'error': str(tmp.error_str), 'name': tmp.result_str}
    else:
        retval = {'addrs': [input_str], 'error': '', 'name': tmp.result_str}
    return retval


class CiscoInterface(object):
    interface_name = None
    interface_dict = None
    debug = None
    initialized = False
    _list = []
    _prefix = None
    _digit_separator = None
    _slot = None
    _card = None
    _port = None
    _subinterface = None
    _channel = None

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __init__(self, interface_name=None, interface_dict=None, debug=False):
        """
        Parse a string `interface_name` like "Serial4/1/2.9:5", (containing slot, card, port, subinterface, and channel) into its typical Cisco IOS components:
        - prefix: 'Serial'
        - number: '4/1/2'
        - slot: 4
        - card: 1
        - port: 2
        - subinterface: 9
        - channel: 5

        When comparing two CiscoInterface() instances, the most explicit comparison is with `CiscoInterface().sort_list`
        """
        if isinstance(interface_name, str):
            if debug is True:
                logger.info(f"CiscoInterface(interface_name='{interface_name}') was called")
        elif isinstance(interface_dict, dict):
            if debug is True:
                logger.info(f"CiscoInterface(interface_dict='{interface_dict}') was called")
        elif interface_name is not None:
            error = f"interface_name must be a string, not {type(interface_name)}."
            logger.critical(error)
            raise InvalidCiscoInterface(error)
        elif interface_dict is not None:
            error = f"interface_dict must be a dict, not {type(interface_dict)}."
            logger.critical(error)
            raise InvalidCiscoInterface(error)
        else:
            error = f"Could not create a CiscoInterface() instance"
            logger.critical(error)
            raise InvalidCiscoInterface(error)


        if isinstance(interface_name, str):
            if "," in interface_name:
                error = f"interface_name: {interface_name} must not contain a comma"
                logger.critical(error)
                raise InvalidCiscoInterface(error)
        elif isinstance(interface_dict, dict):
            self.update_internal_state(intf_dict=interface_dict)
        elif interface_name is not None:
            error = f"interface_name must be a string, not {interface_name}."
            logger.critical(error)
            raise InvalidCiscoInterface(error)
        else:
            error = f"Could not create a CiscoInterface() instance"
            logger.critical(error)
            raise InvalidCiscoInterface(error)

        self.interface_name = interface_name
        self.interface_dict = interface_dict
        self.debug = debug

        if isinstance(interface_name, str):
            intf_dict = self.parse_single_interface(interface_name, debug=debug)
            if debug is True:
                logger.success(f"    CiscoInterface().check_interface_dict({interface_dict}) succeeded")
                logger.debug(f"    Calling CiscoInterface().update_internal_state({interface_dict})")
            self.update_internal_state(intf_dict=intf_dict)
            if debug is True:
                logger.success(f"    CiscoInterface().update_internal_state({interface_dict}) succeeded")
        elif isinstance(interface_dict, dict):
            if debug is True:
                logger.info(f"CiscoInterface(interface_dict={interface_dict}) was called")
            if self.check_interface_dict(interface_dict) is True:
                if debug is True:
                    logger.success(f"    CiscoInterface().check_interface_dict({interface_dict}) succeeded")
                    logger.debug(f"    Calling CiscoInterface().update_internal_state({interface_dict})")
                self.update_internal_state(intf_dict=interface_dict, debug=debug)
                if debug is True:
                    logger.success(f"    CiscoInterface().update_internal_state({interface_dict}) succeeded")
            else:
                error = f"The interface dict check of {interface_dict} failed"
                logger.error(error)
                raise InvalidParameters(error)
        else:
            error = f"InvalidParameters: interface_name: {interface_name}, interface_dict: {interface_dict}"
            logger.critical(error)
            raise InvalidParameters(error)

        self.initialized = True

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def update_sort_list(self):
        "Return the sort_list"
        retval = []
        for ii in [self.slot, self.card, self.port, self.subinterface, self.channel]:
            if isinstance(ii, (str, int)):
                retval.append(int(ii))
            elif ii is None:
                retval.append(None)
            else:
                raise ValueError(f"{ii}")
        return retval

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def update_internal_state(self, intf_dict=None, debug=False):
        "Rewrite the state of this object; call this when any digit changes."
        ######################################################################
        # Always individual pieces
        ######################################################################
        _prefix = intf_dict["prefix"]
        _digit_separator = intf_dict["digit_separator"]
        _slot = intf_dict["slot"]
        _card = intf_dict["card"]
        _port = intf_dict["port"]
        _subinterface = intf_dict["subinterface"]
        _channel = intf_dict["channel"]
        self.prefix = _prefix.strip()
        self.digit_separator = _digit_separator
        self.slot = _slot
        self.card = _card
        self.port = _port
        self.subinterface = _subinterface
        self.channel = _channel

        ######################################################################
        # Always update sort_list
        ######################################################################
        if debug is True:
            logger.info("    CiscoInterface().update_internal_state() is calling CiscoInterface().update_sort_list()")
        self.update_sort_list()

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def parse_single_interface(self, interface_name=None, debug=False):
        """
        Parse a string `interface_name` like "Serial4/1/2.9:5", (containing slot, card, port, subinterface, and channel) into its typical Cisco IOS components:
        - prefix: 'Serial'
        - number: '4/1/2'
        - slot: 4
        - card: 1
        - port: 2
        - subinterface: 9
        - channel: 5

        When comparing two CiscoInterface() instances, the most explicit comparison is with `CiscoInterface().sort_list`
        """
        if debug is True:
            logger.info(f"Calling CiscoRange().parse_single_interface(interface_name='{interface_name}', debug={debug})")
        if isinstance(interface_name, str):
            self.interface_name = interface_name
            if "," in interface_name:
                error = f"interface_name: {interface_name} must not contain a comma"
                logger.critical(error)
                raise InvalidCiscoInterface(error)
        else:
            error = f"interface_name: {interface_name} must be a string."
            logger.critical(error)
            raise InvalidCiscoInterface(error)

        re_intf_short = re.search(r"^(?P<prefix>[a-zA-Z\-\s]*)(?P<port_subinterface_channel>[\d\:\.^\-^a-z^A-Z^\s]+)$", interface_name.strip())
        re_intf_long = re.search(r"^(?P<prefix>[a-zA-Z\-\s]*)(?P<slot_card_port_subinterface_channel>[\d\:\.\/^\-^a-z^A-Z^\s]+)$", interface_name.strip())
        re_any = re.search(r".*", interface_name.strip())
        if isinstance(re_intf_short, re.Match):

            intf_short = self.parse_intf_short(re_intf_short=re_intf_short)

            _prefix = intf_short["prefix"]
            if False:
                _slot_card_port_subinterface_channel = intf_short["slot_card_port_subinterface_channel"]
            _sep1 = intf_short["sep1"]
            _sep2 = intf_short["sep1"]
            _slot = intf_short["slot"]
            _card = intf_short["card"]
            _port = intf_short["port"]
            _digit_separator = intf_short["digit_separator"]
            _subinterface = intf_short["subinterface"]
            _channel = intf_short["channel"]

        elif isinstance(re_intf_long, re.Match):

            intf_long = self.parse_intf_long(re_intf_long=re_intf_long)

            _prefix = intf_long["prefix"]
            if False:
                _slot_card_port_subinterface_channel = intf_long["slot_card_port_subinterface_channel"]
            _sep1 = intf_long["sep1"]
            _sep2 = intf_long["sep1"]
            _slot = intf_long["slot"]
            _card = intf_long["card"]
            _port = intf_long["port"]
            _digit_separator = intf_long["digit_separator"]
            _subinterface = intf_long["subinterface"]
            _channel = intf_long["channel"]

        elif re_any is not None:
            error = f"The interface_name: string '{interface_name.strip()}' could not be parsed."
            logger.critical(error)
            raise InvalidCiscoInterface(error)
        else:
            error = f"The interface_name: string '{interface_name.strip()}' could not be parsed."
            logger.critical(error)
            raise InvalidCiscoInterface(error)

        if debug is True:
            logger.info(f"    CiscoRange().parse_single_interface() parse completed")

        retval = {}
        retval["prefix"] = _prefix
        retval["digit_separator"] = _digit_separator
        retval["slot"] = _slot
        retval["card"] = _card
        retval["port"] = _port
        retval["subinterface"] = _subinterface
        retval["channel"] = _channel
        if debug is True:
            logger.debug(f"    CiscoRange().parse_single_interface(): `_prefix = '{_prefix}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_digit_separator = '{_digit_separator}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_slot = '{_slot}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_card = '{_card}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_port = '{_port}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_subinterface = '{_subinterface}'`")
            logger.debug(f"    CiscoRange().parse_single_interface(): `_channel = '{_channel}'`")

        if debug is True:
            logger.success(f"CiscoRange().parse_single_interface() returned {retval}")
        return retval

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def check_interface_dict(self, interface_dict):
        _prefix = interface_dict["prefix"]
        _sep1 = interface_dict.get("sep1", None)
        _sep2 = interface_dict.get("sep1", None)
        _slot = interface_dict["slot"]
        _card = interface_dict["card"]
        _port = interface_dict["port"]
        _digit_separator = interface_dict["digit_separator"]
        _subinterface = interface_dict["subinterface"]
        _channel = interface_dict["channel"]

        if len(interface_dict.keys()) != 7:
            error = f"CiscoInterface() `interface_dict`: must have exactly 7 dictionary keys, but {len(interface_dict.keys())} were found."
            logger.error(error)
            raise ValueError(error)

        for attr_name in set(interface_dict.keys()):
            if not attr_name in {"prefix", "slot", "card", "port", "digit_separator", "subinterface", "channel"}:
                error = f"'{attr_name}' is not a valid `attribute_dict` key"
                logger.critical(error)
                raise KeyError(error)

        return True

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def parse_intf_short(self, re_intf_short=None, debug=False):
        """Parse the short interface regex match group and return a dict of all the interface components."""

        if not isinstance(re_intf_short, re.Match):
            error = f"re_intf_short: {re_intf_short} must be a regex match group"
            logger.critical(error)
            raise ValueError(error)

        groupdict_intf_short = re_intf_short.groupdict()
        re_port_short = re.search(r"^\D*(?P<port>\d+)", groupdict_intf_short["port_subinterface_channel"])
        groupdict_port_short = re_port_short.groupdict()

        _prefix = groupdict_intf_short.get("prefix", '').strip()
        _slot_card_port_subinterface_channel = groupdict_intf_short["port_subinterface_channel"]
        _sep1 = None
        _sep2 = None
        _slot = None
        _card = None
        _port = groupdict_port_short["port"]
        _digit_separator = _sep1
        _number = f"{_port}"
        _number_list = [None, None, _port]

        re_subinterface = re.search(rf"\.(?P<subinterface>\d+)", _slot_card_port_subinterface_channel)
        if isinstance(re_subinterface, re.Match):
            _subinterface = int(re_subinterface.groupdict()["subinterface"])
        else:
            _subinterface = None

        re_channel = re.search(r"\:(?P<channel>\d+)", _slot_card_port_subinterface_channel)
        if isinstance(re_channel, re.Match):
            _channel = int(re_channel.groupdict()["channel"])
        else:
            _channel = None

        _sort_list = [_slot, _card, _port, _subinterface, _channel]

        return {
            "prefix": _prefix,
            "sep1": _sep1,
            "sep2": _sep2,
            "card": _card,
            "slot": _slot,
            "port": _port,
            "digit_separator": _digit_separator,
            "subinterface": _subinterface,
            "channel": _channel,
        }

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def parse_intf_long(self, re_intf_long=None, debug=False):
        """Parse the long interface regex match group and return a dict of all the interface components."""
        groupdict_intf_long = re_intf_long.groupdict()
        _prefix = groupdict_intf_long.get("prefix", '').strip()
        re_slot_card_port = re.search(
            r"^(?P<slot>\d+)(?P<sep1>[^\:^\.^\-^\s^\d^a-z^A-Z])?(?P<card>\d+)?(?P<sep2>[^\:^\.^\-^\s^\d^a-z^A-Z])?(?P<port>\d+)?",
            groupdict_intf_long["slot_card_port_subinterface_channel"]
        )
        if isinstance(re_slot_card_port, re.Match):
            groupdict_slot_card_port = re_slot_card_port.groupdict()
            if groupdict_intf_long["slot_card_port_subinterface_channel"] is not None:
                _slot_card_port_subinterface_channel = groupdict_intf_long["slot_card_port_subinterface_channel"]
                _prefix = groupdict_intf_long["prefix"]
                _sep1 = groupdict_slot_card_port["sep1"]
                _sep2 = groupdict_slot_card_port["sep1"]
                _slot = groupdict_slot_card_port["slot"]
                _card = groupdict_slot_card_port["card"]
                _port = groupdict_slot_card_port["port"]

                # Handle Ethernet1/48, where 48 is initially assigned to
                #     _card (should be port)
                if isinstance(_slot, str) and isinstance(_card, str) and _port is None:
                    # Swap _card and _port
                    _port = _card
                    _card = None

                if isinstance(_slot, str):
                    _slot = int(_slot)
                if isinstance(_card, str):
                    _card = int(_card)
                if isinstance(_port, str):
                    _port = int(_port)

                if debug is True:
                    logger.debug(f"    CiscoRange().parse_single_interface(): {groupdict_slot_card_port}")
                if isinstance(_sep1, str) and _sep1 == _sep2:
                    _digit_separator = _sep1
                    if debug is True:
                        logger.debug(f"    CiscoRange().parse_single_interface(): `_digit_separator` = '{_digit_separator}'`")
                elif isinstance(_sep1, str):
                    _digit_separator = _sep1
                    if debug is True:
                        logger.debug(f"    CiscoRange().parse_single_interface(): `_digit_separator` = '{_digit_separator}'`")
                elif _sep1 is None and _sep2 is None and isinstance(_slot, str):
                    _digit_separator = None
                    if debug is True:
                        logger.debug(f"    CiscoRange().parse_single_interface(): `_digit_separator` = '{_digit_separator}'`")
                elif _sep1 is None and _slot is None and _card is None:
                    _digit_separator = None
                    if debug is True:
                        logger.debug(f"    CiscoRange().parse_single_interface(): `_digit_separator` = '{_digit_separator}'")
                else:
                    error = f"CiscoInterface() found a digit_separator inconsistency"
                    logger.critical(error)
                    raise ValueError(error)


                re_subinterface = re.search(rf"\.(?P<subinterface>\d+)", _slot_card_port_subinterface_channel)
                if isinstance(re_subinterface, re.Match):
                    _subinterface = int(re_subinterface.groupdict()["subinterface"])
                else:
                    _subinterface = None

                re_channel = re.search(r"\:(?P<channel>\d+)", _slot_card_port_subinterface_channel)
                if isinstance(re_channel, re.Match):
                    _channel = int(re_channel.groupdict()["channel"])
                else:
                    _channel = None

                _sort_list = [_slot, _card, _port, _subinterface, _channel]


            else:
                error = "The key named slot_card_port_subinterface_channel must not be None."
                logger.critical(error)
                raise ValueError(error)
        else:
            error = "The regex referred to by `re_card_slot_port` did not find a match."
            logger.critical(error)
            raise InvalidCiscoInterface(error)

        if debug is True:
            logger.success(f"    CiscoRange().parse_single_interface() success")

        return {
            "prefix": _prefix,
            "digit_separator": _digit_separator,
            "sep1": _sep1,
            "sep2": _sep2,
            "card": _card,
            "slot": _slot,
            "port": _port,
            "subinterface": _subinterface,
            "channel": _channel,
        }

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def from_dict(self, attribute_dict):
        obj = CiscoInterface("Ethernet1")
        obj.prefix = attribute_dict["prefix"]
        obj.digit_separator = attribute_dict["digit_separator"]
        obj.slot = attribute_dict["slot"]
        obj.card = attribute_dict["card"]
        obj.port = attribute_dict["port"]
        obj.subinterface = attribute_dict["subinterface"]
        obj.channel = attribute_dict["channel"]
        return obj

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def as_dict(self):
        return {
            "prefix": self.prefix,
            "digit_separator": self.digit_separator,
            "card": self.card,
            "slot": self.slot,
            "port": self.port,
            "subinterface": self.subinterface,
            "channel": self.channel,
        }

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        try:
            ##   try / except is usually faster than isinstance();
            ##   whenever I change self.__hash__(), I *must* change this...
            # FIXME
            return self.prefix == other.prefix and self.sort_list == other.sort_list
        except Exception:
            return False

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __gt__(self, other):
        # Ref: http://stackoverflow.com/a/7152796/667301
        if self.sort_list > other.sort_list:
            return True
        return False

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __lt__(self, other):
        # Ref: http://stackoverflow.com/a/7152796/667301
        if self.sort_list < other.sort_list:
            return True
        return False

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __hash__(self):
        """Build a unique (and sortable) identifier based solely on slot / card / port / subinterface / channel numbers for the object instance"""
        # I am using __hash__() in __gt__() and __lt__()
        return sum([(idx + 1)**ii for idx, ii in enumerate(self.sort_list) if isinstance(ii, int)])

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def render_as_string(self):
        if self.subinterface is None and self.channel is None:
            return f"""{self.prefix}{self.number}"""
        elif isinstance(self.subinterface, int) and self.channel is None:
            return f"""{self.prefix}{self.number}.{self.subinterface}"""
        elif self.subinterface is None and isinstance(self.channel, int):
            return f"""{self.prefix}{self.number}:{self.channel}"""
        else:
            return f"""{self.prefix}{self.number}.{self.subinterface}:{self.channel}"""

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __str__(self):
        return self.render_as_string()

    # This method is on CiscoInterface()
    @logger.catch(reraise=True)
    def __repr__(self):
        return f"""<CiscoInterface {self.__str__()}>"""

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def prefix(self):
        "Return 'Serial' if self.interface_name is 'Serial 2/1/8.3:6' and return '' if there is no interface prefix"
        return self._prefix

    # This method is on CiscoInterface()
    @prefix.setter
    @logger.catch(reraise=True)
    def prefix(self, value):
        if isinstance(value, str):
            self._prefix = value.strip()
        else:
            error = f"CiscoInterface().prefix must be a string, not {value} ({type(value)})"
            logger.error(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=False)
    def number(self):
        "Return '2/1/8' if self.interface_name is 'Serial 2/1/8.3:6'"

        if self.initialized is True:
            # Shortcut invalid interface configurations...
            if self.slot is None and self.card is None and self.port is None:
                error = f"Could not parse into _number: _slot: {self._slot} _card: {self._card} _port: {self._port} _digit_separator: {self.digit_separator}"
                logger.error(error)
                # Use sys.exit(1) here to avoid infinite recursion during
                #     pathological errors such as a dash in an interface range
                logger.critical(f"Forced python sys.exit() from `CiscoInterface(interface_name='{self.interface_name}').number`.  Manually calling sys.exit(99) on this failure to avoid infinite recursion during what should be a `raise ValueError()`; the infinite recursion might be a bug in a third-party library.")
                sys.exit(99)

            # Fix regex port parsing problems... relocate _slot and _card, as-required
            if self._slot is None and self._card is None and isinstance(self._port, (int, str)):
                self._number = f"{self._port}"
            elif isinstance(self._slot, (int, str)) and self._card is None and isinstance(self._port, (int, str)):
                self._number = f"{self._slot}{self.digit_separator}{self._port}"
            elif isinstance(self._slot, (int, str)) and isinstance(self._card, (int, str)) and isinstance(self._port, (int, str)):
                self._number = f"{self._slot}{self.digit_separator}{self._card}{self.digit_separator}{self._port}"
            else:
                error = f"Could not parse into _number: _slot: {self._slot} _card: {self._card} _port: {self._port} _digit_separator: {self.digit_separator}"
                logger.critical(error)
                raise ValueError(error)
        else:
            self._number = "__UNINITIALIZED_NUMBER_ATTRIBUTE__"
        return self._number

    # This method is on CiscoInterface()
    @number.setter
    @logger.catch(reraise=True)
    def number(self, value):
        self._number = value

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def number_list(self):
        "Return the number_list"
        retval = []
        for ii in [self._slot, self._card, self._port]:
            if isinstance(ii, (str, int)):
                retval.append(int(ii))
            elif ii is None:
                retval.append(None)
            else:
                raise ValueError(f"{ii}")
        return retval

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def digit_separator(self):
        "Return '/' if self.interface_name is 'Serial 2/1/8.3:6' and return None if there is no separator"
        return self._digit_separator

    # This method is on CiscoInterface()
    @digit_separator.setter
    @logger.catch(reraise=True)
    def digit_separator(self, value):
        if isinstance(value, str):
            self._digit_separator = value
        elif self.slot is not None or self.card is not None:
            error = f"Could not set _digit_separator: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)
        elif self.slot is None and self.card is None:
            if self.debug is True:
                logger.debug("Ignoring _digit_separator when there is no slot or card.")
        else:
            error = "Found an unsupported value for `CiscoInterface().digit_separator`."
            logger.error(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def slot_card_port_subinterface_channel(self):
        ""
        if isinstance(self.digit_separator, str) and isinstance(self.slot, (int, str)) and isinstance(self.card, (int, str)) and isinstance(self.port, (int, str)) and isinstance(self.subinterface, (int, str)) and isinstance(self.channel, (int, str)):
            return f"{self.slot}{self.digit_separator}{self.card}{self.digit_separator}{self.port}.{self.subinterface}:{self.channel}"
        elif isinstance(self.digit_separator, str) and isinstance(self.slot, (int, str)) and isinstance(self.card, (int, str)) and isinstance(self.port, (int, str)) and isinstance(self.subinterface, (int, str)) and self.channel is None:
            return f"{self.slot}{self.digit_separator}{self.card}{self.digit_separator}{self.port}.{self.subinterface}"
        elif isinstance(self.digit_separator, str) and isinstance(self.slot, (int, str)) and isinstance(self.card, (int, str)) and isinstance(self.port, (int, str)) and self.subinterface is None and self.channel is None:
            return f"{self.slot}{self.digit_separator}{self.card}{self.digit_separator}{self.port}"
        elif isinstance(self.digit_separator, str) and isinstance(self.slot, (int, str)) and self.card is None and isinstance(self.port, (int, str)) and self.subinterface is None and self.channel is None:
            return f"{self.slot}{self.digit_separator}{self.port}"
        elif self.slot is None and self.card is None and isinstance(self.port, (int, str)) and self.subinterface is None and self.channel is None:
            return f"{self.port}"
        else:
            error = "Could not construct a return value for CiscoInterface().slot_card_port_subinterface_channel.  digit_separator: {self.digit_separator} sort_list: {self.sort_list}"
            logger.error(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def slot(self):
        "Return 2 if self.interface_name is 'Serial 2/1/8.3:6' and return None if there is no slot"
        if self._slot is None:
            return None
        else:
            return int(self._slot)

    # This method is on CiscoInterface()
    @slot.setter
    @logger.catch(reraise=True)
    def slot(self, value):
        if isinstance(value, (int, str)):
            self._slot = int(value)
        elif value is None:
            self._slot = value
        else:
            error = f"Could not set _slot: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def card(self):
        "Return 1 if self.interface_name is 'Serial 2/1/8.3:6' and return None if there is no card"
        if self._card is None:
            return self._card
        else:
            return int(self._card)

    # This method is on CiscoInterface()
    @card.setter
    @logger.catch(reraise=True)
    def card(self, value):
        if isinstance(value, (int, str)):
            self._card = int(value)
        elif value is None:
            self._card = value
        else:
            error = f"Could not set _card: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def port(self):
        "Return 8 if self.interface_name is 'Serial 2/1/8.3:6' and raise a ValueError if there is no port"
        if self._port is None:
            return None
        else:
            return int(self._port)

    # This method is on CiscoInterface()
    @port.setter
    @logger.catch(reraise=True)
    def port(self, value):
        if isinstance(value, (int, str)):
            self._port = int(value)
        elif value is None:
            self._port = value
        else:
            error = f"Could not set _card: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def subinterface(self):
        "Return 3 if self.interface_name is 'Serial 2/1/8.3:6' and return None if there is no subinterface"
        return self._subinterface

    # This method is on CiscoInterface()
    @subinterface.setter
    @logger.catch(reraise=True)
    def subinterface(self, value):
        if isinstance(value, (int, str)):
            self._subinterface = int(value)
        elif value is None:
            self._subinterface = value
        else:
            error = f"Could not set _subinterface: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def channel(self):
        "Return 6 if self.interface_name is 'Serial 2/1/8.3:6 and return None if there is no channel'"
        return self._channel

    # This method is on CiscoInterface()
    @channel.setter
    @logger.catch(reraise=True)
    def channel(self, value):
        if isinstance(value, (int, str)):
            self._channel = int(value)
        elif value is None:
            self._channel = value
        else:
            error = f"Could not set _channel: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoInterface()
    @property
    @logger.catch(reraise=True)
    def sort_list(self):
        "Return the sort_list"
        return self.update_sort_list()

    # This method is on CiscoInterface()
    @sort_list.setter
    @logger.catch(reraise=True)
    def sort_list(self, value):
        if isinstance(value, list):
            self._sort_list = value
        else:
            error = f"Could not set _sort_list: {value} {type(value)}"
            logger.critical(error)
            raise ValueError(error)

class CiscoRange(MutableSequence):
    """Explode Cisco ranges into a list of explicit items... examples below...

    Examples
    --------

    >>> from ciscoconfparse.ccp_util import CiscoRange
    >>> CiscoRange('1-3,5,9-11,13')
    <CiscoRange 1-3,5,9-11,13>
    >>> for ii in CiscoRange('Eth2/1-3,5,9-10'):
    ...     print(ii)
    ...
    Eth2/1
    Eth2/2
    Eth2/3
    Eth2/5
    Eth2/9
    Eth2/10
    >>> CiscoRange('Eth2/1-3,7')
    <CiscoRange Eth2/1-3,7>
    >>> CiscoRange(text="")
    <CiscoRange []>
    """

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __init__(self, text="", result_type=str, default_iter_attr='port', reverse=False, debug=False):
        super().__init__()

        # Ensure that result_type is in the set of valid_result_types...
        valid_result_types = {str, None}
        if not result_type in valid_result_types:
            error = f'CiscoRange(text="{text}", result_type={result_type}) [text: {type(text)}] is not a valid result_type.  Choose from {valid_result_types}'
            logger.critical(error)
            raise ValueError(error)


        if debug is True:
            logger.info(f"CiscoRange(text='{text}', debug=True) [text: {type(text)}] was called.")
            logger.info(f"CiscoRange() for --> text: {text} <--")

        self.text = text
        self.result_type = result_type
        self.default_iter_attr = default_iter_attr
        self.reverse = reverse
        self.begin_obj = None
        self.this_obj = None
        self.iterate_attribute = None
        self._list = self.parse_text_list(text, debug=debug)
        self.range_str = ""

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def parse_text_list(self, text, debug=False):
        range_str = ""
        expanded_interfaces = []
        if ",," in text:
            error = f"-->{text}<-- is an invalid range; double-commas are not allowed"
            logger.error(error)
            raise ValueError(error)
        csv_parts = text.split(",")
        for idx, _csv_part in enumerate(csv_parts):

            if debug is True:
                logger.info(f"    CiscoRange() idx: {idx} for --> _csv_part: {_csv_part} <--")

            ##############################################################
            # Build base instances of begin_obj and this_obj
            ##############################################################
            if idx == 0:
            #if True:
                # Set the begin_obj...
                begin_obj = CiscoInterface(_csv_part.split("-")[0], debug=debug)
                self.begin_obj = begin_obj
                self.this_obj = copy.deepcopy(begin_obj)
                intf_dict = begin_obj.as_dict()

            ##############################################################
            # this_obj will also be modified in the large per
            #     attribute if-clauses, below
            ##############################################################
            self.this_obj = copy.deepcopy(begin_obj)

            ##############################################################
            # Walk all possible attributes to find which target_attribute
            #     we're iterating on...
            ##############################################################
            iterate_attribute = None
            for potential_iter_attr in ['channel', 'subinterface', 'port', 'card', 'slot']:
                if isinstance(getattr(begin_obj, potential_iter_attr), int):
                    self.iterate_attribute = potential_iter_attr
                    break

            if self.iterate_attribute is None:
                if debug is True:
                    logger.warning(f"CiscoRange() set `iterate_attribute` to the default of {self.default_iter_attr}")
                self.iterate_attribute = self.default_iter_attr

            if idx > 0:
                if self.iterate_attribute == 'channel' and isinstance(begin_obj.channel, int):
                    self.this_obj.channel = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug).channel
                elif self.iterate_attribute == 'subinterface' and isinstance(begin_obj.subinterface, int):
                    self.this_obj.subinterface = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug).subinterface
                elif self.iterate_attribute == 'port' and isinstance(begin_obj.port, int):
                    self.this_obj.port = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug).port
                elif self.iterate_attribute == 'card' and isinstance(begin_obj.card, int):
                    self.this_obj.card = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug).card
                elif self.iterate_attribute == 'slot' and isinstance(begin_obj.card, int):
                    self.this_obj.slot = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug).slot
                else:
                    raise NotImplementedError()

            ##################################################################
            #
            # Handle attribute incrementing below
            #
            # Walk backwards in .sort_list to find the most-specific value
            #
            ##################################################################
            if debug is True:
                logger.info(f"    CiscoRange(text={text}, debug=True) _csv_part: {_csv_part}")
                logger.info(f"    CiscoRange(text={text}, debug=True)     iterate_attribute: {self.iterate_attribute}")
                logger.debug(f"    CiscoRange(text={text}, debug=True)     begin_obj: {begin_obj}{os.linesep}")
                logger.debug(f"    CiscoRange(text={text}, debug=True)     this_obj: {self.this_obj}")

            # Set the end_ordinal... keep this separate from begin_obj logic...
            if self.iterate_attribute is None:
                raise ValueError()
            if "-" in _csv_part:
                if len(_csv_part.split("-")) == 2:
                    # Append a whole range of interfaces...
                    obj = CiscoInterface(_csv_part.split("-")[0].strip(), debug=debug)
                    begin_ordinal = getattr(obj, self.iterate_attribute)
                    end_ordinal = int(_csv_part.split("-")[1].strip())
                    if debug is True:
                        logger.info(f"CiscoRange(text={text}, debug=True) : end_ordinal={end_ordinal}")
                else:
                    error = f"Could not divide {_csv_part} into interface components"
                    logger.error(error)
                    raise ValueError(error)
            else:
                end_ordinal = None
                if debug is True:
                    logger.info(f"CiscoRange(text={text}, debug=True) : end_ordinal={end_ordinal}")

            if debug is True:
                logger.debug(f"    CiscoRange(text={text}, debug=True) [begin_obj: {type(self.begin_obj)}]    end_ordinal: {end_ordinal}")

            if self.iterate_attribute == 'channel' and isinstance(begin_obj.channel, int):
                ##############################################################
                # Handle incrementing channel numbers
                ##############################################################
                if end_ordinal is not None:
                    iter_dict = self.this_obj.as_dict()
                    for ii in range(begin_ordinal, end_ordinal+1):
                        if debug is True:
                            logger.debug(f"    idx: {idx} at point01,     set channel: {ii}")
                        iter_dict["channel"] = ii
                        # Use deepcopy to avoid problems with the same object
                        #     instance appended multiple times
                        if debug is True:
                            logger.info(f"    idx: {idx} at point02, Appending {self.this_obj}{os.linesep}")
                        expanded_interfaces.append(self.this_obj.update_internal_state(iter_dict))
                        continue
                else:
                    # Append a single interface
                    if debug is True:
                        logger.info(f"    idx: {idx} at point03, Appending {self.this_obj}{os.linesep}")
                    expanded_interfaces.append(copy.deepcopy(self.this_obj))
                    continue
            elif self.iterate_attribute == 'subinterface' and isinstance(begin_obj.subinterface, int):
                ##############################################################
                # Handle incrementing subinterface numbers
                ##############################################################
                if end_ordinal is not None:
                    iter_dict = self.this_obj.as_dict()
                    for ii in range(begin_ordinal, end_ordinal+1):
                        if debug is True:
                            logger.debug(f"    idx: {idx} at point04,     set subinterface: {ii}")
                        iter_dict["subinterface"] = ii
                        # Use deepcopy to avoid problems with the same object
                        #     instance appended multiple times
                        if debug is True:
                            logger.info(f"    idx: {idx} at point05, Appending {self.this_obj}{os.linesep}")
                        expanded_interfaces.append(self.this_obj.from_dict(iter_dict))
                        continue
                else:
                    # Append a single interface
                    if debug is True:
                        logger.info(f"    idx: {idx} at point06, Appending {self.this_obj}{os.linesep}")
                    expanded_interfaces.append(self.this_obj)
                    continue
            elif self.iterate_attribute == 'port' and isinstance(begin_obj.port, int):
                ##############################################################
                # Handle incrementing port numbers
                ##############################################################
                if end_ordinal is not None:
                    iter_dict = self.this_obj.as_dict()
                    for ii in range(begin_ordinal, end_ordinal+1):
                        if debug is True:
                            logger.debug(f"    idx: {idx} at point07,     set subinterface: {ii}")
                        iter_dict["port"] = ii
                        # Use deepcopy to avoid problems with the same object
                        #     instance appended multiple times
                        if debug is True:
                            logger.info(f"    idx: {idx} at point08, Appending {self.this_obj}{os.linesep}")
                        expanded_interfaces.append(self.this_obj.from_dict(iter_dict))
                        continue
                else:
                    # Append a single interface
                    if debug is True:
                        logger.info(f"    idx: {idx} at point09, Appending {self.this_obj}{os.linesep}")
                    expanded_interfaces.append(self.this_obj)
                    continue

            elif self.iterate_attribute == 'card' and isinstance(begin_obj.card, int):
                ##############################################################
                # Handle incrementing port numbers
                ##############################################################
                if end_ordinal is not None:
                    iter_dict = self.this_obj.as_dict()
                    for ii in range(begin_ordinal, end_ordinal+1):
                        if debug is True:
                            logger.debug(f"    idx: {idx} at point10,     set subinterface: {ii}")
                        iter_dict["card"] = ii
                        # Use deepcopy to avoid problems with the same object
                        #     instance appended multiple times
                        if debug is True:
                            logger.info(f"    idx: {idx} at point11, Appending {self.this_obj}{os.linesep}")
                        expanded_interfaces.append(self.this_obj.from_dict(iter_dict))
                        continue
                else:
                    # Append a single interface
                    if debug is True:
                        logger.info(f"    idx: {idx} at point12, Appending {self.this_obj}{os.linesep}")
                    expanded_interfaces.append(self.this_obj)
                    continue

            elif self.iterate_attribute == 'slot' and isinstance(begin_obj.slot, int):
                ##############################################################
                # Handle incrementing port numbers
                ##############################################################
                if end_ordinal is not None:
                    iter_dict = self.this_obj.as_dict()
                    for ii in range(begin_ordinal, end_ordinal+1):
                        if debug is True:
                            logger.debug(f"    idx: {idx} at point13,     set subinterface: {ii}")
                        iter_dict["slot"] = ii
                        # Use deepcopy to avoid problems with the same object
                        #     instance appended multiple times
                        if debug is True:
                            logger.info(f"    idx: {idx} at point14, Appending {self.this_obj}{os.linesep}")
                        expanded_interfaces.append(self.this_obj.from_dict(iter_dict))
                        continue
                else:
                    # Append a single interface
                    if debug is True:
                        logger.info(f"    idx: {idx} at point15, Appending {self.this_obj}{os.linesep}")
                    expanded_interfaces.append(self.this_obj)
                    continue

            else:
                error = f"Cannot determine CiscoRange().iterate_attribute.  We thought it was --> {self.iterate_attribute} <--"
                logger.critical(error)
                raise ValueError(error)

        ######################################################################
        # Sort _expanded_interfaces...
        ######################################################################
        if not isinstance(self.text, str):
            error = f'CiscoRange(text="{self.text}") must be a string representation of a CiscoRange(), such as "Ethernet1,4-7,12"; the received text argument was {type(self.text)} instead of a string'
            logger.error(error)
            raise ValueError(error)
        # De-deplicate _expanded_interfaces...
        _expanded_interfaces = expanded_interfaces
        _expanded_interfaces = list(set(_expanded_interfaces))
        retval = sorted(_expanded_interfaces, key=lambda x: x.sort_list, reverse=self.reverse)
        if debug is True:
            logger.info(f"CiscoRange(text='{self.text}', debug=True) [begin_obj: {type(self.begin_obj)}] returning: {retval}")
        return retval

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __repr__(self):
        return f"""<CiscoRange {self.__str__()}>"""

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __len__(self):
        return len(self._list)

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __getitem__(self, ii):
        max_list_index = len(self._list) - 1
        if ii > max_list_index:
            error = f"CiscoRange() attempted to access CiscoRange()._list[{ii}], but the max list index is {max_list_index}"
            logger.critical(error)
            raise IndexError(error)
        else:
            return self._list[ii]

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __delitem__(self, ii):
        max_list_index = len(self._list) - 1
        if ii > max_list_index:
            error = f"CiscoRange() attempted to access CiscoRange()._list[{ii}], but the max list index is {max_list_index}"
            logger.critical(error)
            raise IndexError(error)
        else:
            del self._list[ii]

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __setitem__(self, ii, val):
        max_list_index = len(self._list) - 1
        if ii > max_list_index:
            error = f"CiscoRange() attempted to access CiscoRange()._list[{ii}], but the max list index is {max_list_index}"
            logger.critical(error)
            raise IndexError(error)
        else:
            return self._list[ii]

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def insert(self, ii, val):
        # Insert at the end of the list with new_last_list_idx = len(self._list)
        new_last_list_idx = len(self._list)
        self._list.insert(new_last_list_idx, val)
        return self

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def __str__(self):
        return "[" + str(", ".join([str(ii) for ii in self._list])) + "]"

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def remove(self, arg):
        length_before = len(self._list)
        list_before = copy.deepcopy(self._list)
        # Try removing some common result types...
        for result_type in [None, str, int, float]:
            if result_type is None:
                new_list = [ii for ii in list_before if ii != arg]
            else:
                new_list = [ii for ii in list_before if result_type(ii) != arg]
            if len(new_list) < length_before:
                self._list = new_list
                break
        arg_type = type(arg)
        if len(new_list) == length_before:
            if arg_type is not type(self._list[0]):
                # Do a simple type check to see if typing is the problem...
                raise MismatchedType(arg)
            else:
                # Otherwise, flag the problem as an invalid member...
                raise InvalidMember(arg)
        return self


    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def as_list(self, result_type=str):
        """Return a list of sorted components; an empty string is automatically rejected.  This method is tricky to test due to the requirement for the `.sort_list` attribute on all elements; avoid using the ordered nature of `as_list` and use `as_set`."""
        yy_list = copy.deepcopy(self._list)
        for ii in self._list:
            if isinstance(ii, str) and ii == "":
                # Reject an empty string...
                continue
            if getattr(ii, "sort_list", None) is not None:
                # Require the .sort_list attribute...
                yy_list.append(ii)

        self._list = yy_list
        try:
            # Disable linter qa checks on this embedded list syntax...
            retval = sorted(set(self._list), reverse=self.reverse) # noqa
            if result_type is None:
                return retval
            elif result_type is str:
                return [str(ii) for ii in retval]
            elif result_type is int:
                return [int(ii) for ii in retval]
            else:
                error = f"CiscoRange().as_list(result_type={result_type}) is not valid.  Choose from {[None, int, str]}.  result_type: None will return CiscoInterface() objects."
                logger.critical(error)
                raise ValueError(error)
        except AttributeError as eee:
            error = f"`sorted(self._list, reverse={self.reverse})` tried to access an attribute that does not exist on the objects being sorted: {eee}"
            logger.error(error)
            raise ListItemMissingAttribute(error)
        except Exception as eee:
            logger.critical(eee)
            raise ValueError(eee)

    # This method is on CiscoRange()
    @logger.catch(reraise=True)
    def as_set(self, result_type=str):
        """Return an unsorted set({}) components.  Use this method instead of `.as_list` whenever possible to avoid the requirement for elements needing a `.sort_list` attribute."""
        retval = set(self._list)
        if result_type is None:
            return retval
        elif result_type is str:
            return set([str(ii) for ii in retval])
        elif result_type is int:
            return set([int(ii) for ii in retval])
        else:
            error = f"CiscoRange().as_list(result_type={result_type}) is not valid.  Choose from {[None, int, str]}.  result_type: None will return CiscoInterface() objects."
            logger.critical(error)
            raise ValueError(error)

    # This method is on CiscoRange()
    ## Github issue #125
    @logger.catch(reraise=True)
    def as_compressed_str(self, debug=False):
        """
        Return a text string with a compressed csv of values

        >>> from ciscoconfparse.ccp_util import CiscoRange
        >>> range_obj = CiscoRange('1,3,5,6,7')
        >>> range_obj.compressed_str
        '1,3,5-7'
        >>>
        """
        retval = list()
        if False:
            prefix_str = self.line_prefix.strip() + self.slot_prefix.strip()

        # Build a magic attribute dict so we can intelligently prepend slot/card/port/etc...
        magic_string = "3141592653591892234109876543212345678"
        this_obj = CiscoInterface(self.text.split(",")[0])
        magic_dict = this_obj.as_dict()
        for attr_name in ("channel", "subinterface", "port", "card", "slot",):
            if magic_dict[attr_name] is not None:
                if attr_name == self.iterate_attribute:
                    magic_dict[attr_name] = int(magic_string)
                    break
        if debug is True:
            logger.info(f"CiscoRange() calling CiscoInterface(interface_dict={magic_dict}).as_compressed_str()")
        obj = CiscoInterface(interface_dict=magic_dict, debug=debug)
        if debug is True:
            logger.success(f"    CiscoRange() call to CiscoInterface().as_compressed_str() with `interface_dict` parameter succeeded")
        prefix_str = str(obj).replace(magic_string, "")
        prefix_str_len = len(prefix_str)

        # Build a list of the relevant string iteration pieces...
        input_str = []
        for idx, component in enumerate(self.as_list()):
            input_str.append(getattr(CiscoInterface(component), self.iterate_attribute))


        if len(input_str) == 0:  # Special case, handle empty list
            return ""

        # source - https://stackoverflow.com/a/51227915/667301
        input_str = sorted(list(set(input_str)))
        range_list = [input_str[0]]
        for ii in range(len(input_str)):
            if ii + 1 < len(input_str) and ii - 1 > -1:
                if (input_str[ii] - input_str[ii - 1] == 1) and (
                    input_str[ii + 1] - input_str[ii] == 1
                ):
                    if range_list[-1] != "-":
                        range_list += ["-"]
                else:
                    range_list += [input_str[ii]]
        if len(input_str) > 1:
            range_list += [input_str[len(input_str) - 1]]

        # Build the return value from range_list...
        retval = prefix_str + str(range_list[0])
        for ii in range(1, len(range_list)):
            if str(type(range_list[ii])) != str(type(range_list[ii - 1])):
                retval += str(range_list[ii])
            else:
                retval += "," + str(range_list[ii])

        return retval


##############################################################################
# Restore SonarCloud warnings in this file
##############################################################################
#pragma warning restore S1192
#pragma warning restore S1313
#pragma warning restore S5843
#pragma warning restore S5852
#pragma warning restore S6395
