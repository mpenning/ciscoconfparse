r""" ccp_util.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021-2022 David Michael Pennington
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

from operator import attrgetter
from functools import wraps
import socket
import time
import sys
import re
import os

from collections.abc import MutableSequence
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from ipaddress import collapse_addresses as ipaddr_collapse_addresses
from ipaddress import AddressValueError


from dns.exception import DNSException
from dns.resolver import Resolver
from dns import reversename, query, zone

from deprecat import deprecat

from loguru import logger

from ciscoconfparse.protocol_values import ASA_TCP_PORTS, ASA_UDP_PORTS
from ciscoconfparse.errors import PythonOptimizeException
import ciscoconfparse


# Maximum ipv4 as an integer
IPV4_MAXINT = 4294967295
# Maximum ipv6 as an integer
IPV6_MAXINT = 340282366920938463463374607431768211455
IPV4_MAXSTR_LEN = 31  # String length with periods, slash, and netmask
IPV6_MAXSTR_LEN = 39 + 4  # String length with colons, slash and masklen

IPV4_MAX_PREFIXLEN = 32
IPV6_MAX_PREFIXLEN = 128


_CISCO_RANGE_ATOM_STR = r"""\d+\s*\-*\s*\d*"""
_CISCO_RANGE_STR = r"""^(?P<line_prefix>[a-zA-Z\s]*)(?P<slot_prefix>[\d\/]*\d+\/)*(?P<range_text>(\s*{})*)$""".format(
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
|(?P<opt8>:(?::{0}){{1,7}})              # leading double colons
|(?P<opt9>(?:{0}:){{1,7}}:)              # trailing double colons
|(?P<opt10>(?:::))                       # bare double colons (default route)
)([/\s](?P<masklen>\d+))*                # match 'masklen' and end 'addr' group
""".format(
    r"[0-9a-fA-F]{1,4}"
)

_IPV6_REGEX_STR_COMPRESSED1 = r"""(?!:::\S+?$)(?P<addr1>(?P<opt1_1>{0}(?::{0}){{7}})|(?P<opt1_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt1_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt1_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt1_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt1_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt1_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt1_8>:(?::{0}){{1,7}})|(?P<opt1_9>(?:{0}:){{1,7}}:)|(?P<opt1_10>(?:::)))""".format(
    r"[0-9a-fA-F]{1,4}"
)

_IPV6_REGEX_STR_COMPRESSED2 = r"""(?!:::\S+?$)(?P<addr2>(?P<opt2_1>{0}(?::{0}){{7}})|(?P<opt2_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt2_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt2_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt2_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt2_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt2_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt2_8>:(?::{0}){{1,7}})|(?P<opt2_9>(?:{0}:){{1,7}}:)|(?P<opt2_10>(?:::)))""".format(
    r"[0-9a-fA-F]{1,4}"
)

_IPV6_REGEX_STR_COMPRESSED3 = r"""(?!:::\S+?$)(?P<addr3>(?P<opt3_1>{0}(?::{0}){{7}})|(?P<opt3_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt3_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt3_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt3_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt3_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt3_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt3_8>:(?::{0}){{1,7}})|(?P<opt3_9>(?:{0}:){{1,7}}:)|(?P<opt3_10>(?:::)))""".format(
    r"[0-9a-fA-F]{1,4}"
)

_RGX_IPV6ADDR = re.compile(_IPV6_REGEX_STR, re.VERBOSE)
####################### End IPv6 #############################

####################### Begin IPv4 #############################
_IPV4_REGEX_STR = r"^(?P<addr>\d+\.\d+\.\d+\.\d+)"
_RGX_IPV4ADDR = re.compile(_IPV4_REGEX_STR)
_RGX_IPV4ADDR_NETMASK = re.compile(
    r"""
     (?:
       ^(?P<addr0>\d+\.\d+\.\d+\.\d+)$
      |(?:^
         (?:(?P<addr1>\d+\.\d+\.\d+\.\d+))(?:\s+|\/)(?:(?P<netmask>\d+\.\d+\.\d+\.\d+))
       $)
      |^(?:\s*(?P<addr2>\d+\.\d+\.\d+\.\d+)(?:\/(?P<masklen>\d+))\s*)$
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

@logger.catch(reraise=True)
def ccp_logger_control(
    sink=sys.stderr,
    action="",
    handler_id=None,
    allow_enqueue=True,
    # rotation="00:00",
    # retention="1 month",
    # compression="zip",
    level="DEBUG",
    colorize=True,
    debug=0,
):
    """
    A simple function to handle logging... Enable / Disable all
    ciscoconfparse logging here... also see Github issue #211.

    Example
    -------
    """

    msg = "ccp_logger_control() was called with sink='{}', action='{}', handler_id='{}', allow_enqueue={}, level='{}', colorize={}, debug={}".format(
        sink,
        action,
        handler_id,
        allow_enqueue,
        # rotation,
        # retention,
        # compression,
        level,
        colorize,
        debug,
    )
    if debug > 0:
        logger.info(msg)

    assert isinstance(action, str)
    assert action in ("remove", "add", "disable", "enable", "",)

    package_name = "ciscoconfparse"

    if action == "remove":
        # Require an explicit loguru handler_id to remove...
        assert isinstance(handler_id, int)

        logger.remove(handler_id)
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

        logger.add(
            sink=sink,
            diagnose=True,
            backtrace=True,
            # https://github.com/mpenning/ciscoconfparse/issues/215
            enqueue=allow_enqueue,
            serialize=False,
            catch=True,
            # rotation="00:00",
            # retention="1 day",
            # compression="zip",
            colorize=True,
            level="DEBUG",
        )
        logger.enable(package_name)
        return True

    elif action == "":
        raise ValueError(
            "action='' is not supported.  Please use a valid action keyword"
        )

    else:
        raise NotImplementedError(
            "action='%s' is an unsupported logger action" % action
        )


@logger.catch(reraise=True)
def configure_loguru(
    sink=sys.stderr,
    action="",
    # rotation="midnight",
    # retention="1 month",
    # compression="zip",
    level="DEBUG",
    colorize=True,
    debug=0,
):
    """
    configure_loguru()
    """
    assert isinstance(action, str)
    assert action in ('remove', 'add', 'enable', 'disable', '',)
    # assert isinstance(rotation, str)
    # assert isinstance(retention, str)
    # assert isinstance(compression, str)
    # assert compression == "zip"
    assert isinstance(level, str)
    assert isinstance(colorize, bool)
    assert isinstance(debug, int) and (0 <= debug <= 5)

    # logger_control() was imported above...
    #    Remove the default loguru logger to stderr (handler_id==0)...
    ccp_logger_control(action="remove", handler_id=0)

    # Add log to STDOUT
    ccp_logger_control(
        sink=sys.stdout,
        action="add",
        level="DEBUG",
        # rotation='midnight',   # ALE barks about the rotation keyword...
        # retention="1 month",
        # compression=compression,
        colorize=colorize
    )
    ccp_logger_control(action="enable")


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
    assert isinstance(object_list, (list, tuple,))
    for obj in object_list:
        assert isinstance(obj.linenum, int)
        assert isinstance(obj.text, str)
    # return [ii.text for ii in object_list]
    return list(map(attrgetter("text"), object_list))


@logger.catch(reraise=True)
def junos_unsupported(func):
    """A function wrapper to warn junos users of unsupported features"""

    @logger.catch(reraise=True)
    def wrapper(*args, **kwargs):
        warn = "syntax='junos' does not fully support config modifications such as .{}(); see Github Issue #185.  https://github.com/mpenning/ciscoconfparse/issues/185".format(
            func.__name__
        )
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



class __ccp_re__(object):
    """
    A wrapper around python's re.  This is an experimental object... it may
    disappear at any time as long as this message exists.

    self.regex = r'{}'.format(regex)
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
    def __init__(self, regex_str=r"", target_str=None, groups=None, flags=0,
        debug=0):
        assert isinstance(regex_str, str)
        assert isinstance(flags, int)
        assert isinstance(debug, int)

        if isinstance(regex_str, str):
            assert isinstance(regex_str, str)
            self.regex_str = regex_str
            self.compiled = re.compile(self.regex, flags=flags)

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
        assert isinstance(regex_str, str)
        self.regex_str = regex_str
        self.compiled = re.compile(regex_str)
        self.attempted_search = False


    # do NOT wrap with @logger.catch(...)
    def s(self, target_str):
        assert self.attempted_search is False
        assert isinstance(target_str, str)

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
    assert isinstance(val, str) or isinstance(val, int)
    assert isinstance(strict, bool)
    assert isinstance(stdlib, bool)
    assert isinstance(debug, int)

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
                assert isinstance(obj.ip, IPv4Address)
                return obj.ip
            else:
                # Return IPv6Network()
                assert isinstance(obj.network, IPv4Network)
                return obj.network
    except Exception as ee:
        raise AddressValueError("_get_ipv4(val='%s')" % (val))


# do NOT wrap with @logger.catch(...)
def _get_ipv6(val="", strict=False, stdlib=False, debug=0):
    """Return the requested IPv6 object to the caller.  This method heavily depends on IPv6Obj()"""
    assert isinstance(val, str) or isinstance(val, int)
    assert isinstance(strict, bool)
    assert isinstance(stdlib, bool)
    assert isinstance(debug, int)

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
                assert isinstance(obj.ip, IPv6Address)
                return obj.ip
            else:
                # Return IPv6Network()
                assert isinstance(obj.network, IPv6Network)
                return obj.network

    except Exception as ee:
        raise AddressValueError("_get_ipv6(val='%s')" % (val))

# do NOT wrap with @logger.catch(...)
def ip_factory(val="", stdlib=False, mode="auto_detect", debug=0):
    """
    Accept an IPv4 or IPv6 address / (mask or masklength).  Return an appropriate IPv4 or IPv6 object

    Set stdlib=True if you only want python's stdlib IP objects.

    Throw an error if addr cannot be parsed as a valid IPv4 or IPv6 object.
    """

    assert isinstance(val, str) or isinstance(val, int)
    assert mode in {"auto_detect", "ipv4", "ipv6"}
    assert isinstance(stdlib, bool)
    assert isinstance(debug, int)

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
        except:
            error_str = "Cannot parse '%s' as ipv4" % val
            raise AddressValueError(error_str)

    elif mode == "ipv6":
        try:
            obj = _get_ipv6(val=val, stdlib=stdlib, debug=debug)
            return obj
        except:
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
    assert isinstance(network_list, list) or isinstance(network_list, tuple)

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

    # This method is on IPv4Obj().  Do NOT add @logger.catch to __init__()...
    # that breaks it.
    def __init__(self, arg=f"127.0.0.1/{IPV4_MAX_PREFIXLEN}", strict=False, debug=0):
        """An object to represent IPv4 addresses and IPv4 networks.

        When :class:`~ccp_util.IPv4Obj` objects are compared or sorted, network numbers are sorted lower to higher.  If network numbers are the same, shorter masks are lower than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses..  Comparisons between :class:`~ccp_util.IPv4Obj` instances was chosen so it's easy to find the longest-match for a given prefix (see examples below).

        This object emulates the behavior of ipaddr.IPv4Network (in Python2) where host-bits were retained in the IPv4Network() object.  :class:`ipaddress.IPv4Network` in Python3 does not retain host-bits; the desire to retain host-bits in both Python2 and Python3 ip network objects was the genesis of this API.

        Parameters
        ----------
        arg : str or int
            A string (or integer) containing an IPv4 address, and optionally a netmask or masklength.  Integers are also accepted.  The following address/netmask formats are supported: "10.1.1.1/24", "10.1.1.1 255.255.255.0", "10.1.1.1/255.255.255.0"
        strict: bool
            When `strict` is True, the value of `arg` must not have host-bits set.  The default value is False.


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
        network_object : :class:`ipaddress.IPv4Network`
            Returns an :class:`ipaddress.IPv4Network` with the network of this object
        numhosts : int
            An integer representing the number of hosts contained in the network
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
            logger.info(f"IPv4Obj(arg='{arg}', strict={strict}, debug={debug}) was called")

        self.arg = arg
        self.dna = "IPv4Obj"
        self.ip_object = None
        self.network_object = None
        self.strict = strict
        self.debug = debug
        self.params_dict = {}

        # Build params_dict... this needs to work with any supported input...
        if isinstance(arg, str):
            params_dict = self._ipv4_params_dict(arg)
            self.params_dict = params_dict

        elif isinstance(arg, int):
            params_dict = self._ipv4_params_dict(arg)
            self.params_dict = params_dict

        elif isinstance(arg, IPv4Obj):
            params_dict = {
                'ipv4_addr': str(arg.ip),
                'ip_version': 4,
                'ip_arg_str': str(arg.ip)+"/"+str(arg.masklen),
                'netmask': str(arg.netmask),
                'masklen': str(arg.masklen),
            }
            self.params_dict = params_dict

        else:
            raise ValueError("type(%s) is not supported" % arg)


        if isinstance(arg, str):
            # Removing string length checks in 1.6.29... there are too many
            #    options such as IPv4Obj("111.111.111.111      255.255.255.255")
            # RECURSION
            #obj = _get_ipv4(arg, strict=strict)
            self.network_object = IPv4Network(params_dict['ip_arg_str'], strict=strict)
            self.ip_object = IPv4Address(params_dict['ipv4_addr'])
            return None

        elif isinstance(arg, int):
            assert 0 <= arg <= IPV4_MAXINT
            self.network_object = IPv4Network(arg, strict=strict)
            self.ip_object = IPv4Address(arg)
            return None

        elif isinstance(arg, IPv4Obj):
            ip_str = f"{str(arg.ip_object)}/{arg.prefixlen}"
            self.network_object = IPv4Network(ip_str, strict=False)
            self.ip_object = IPv4Address(str(arg.ip_object))
            return None

        elif isinstance(arg, IPv4Network):
            self.network_object = arg
            self.ip_object = IPv4Address(str(arg).split("/")[0])
            return None

        elif isinstance(arg, IPv4Address):
            self.network_object = IPv4Network(str(arg) + "/" + str(IPV4_MAX_PREFIXLEN))
            self.ip_object = IPv4Address(str(arg).split("/")[0])
            return None

        else:
            raise AddressValueError(
                "Could not parse '{}' (type: {}) into an IPv4 Address".format(
                    arg, type(arg)
                )
            )

    # do NOT wrap with @logger.catch(...)
    # On IPv4Obj()
    def _ipv4_params_dict(self, arg, debug=0):
        """
        Parse out important IPv4 parameters from arg.  This method must run to
        completion for IPv4 address parsing to work correctly.
        """
        assert isinstance(arg, str) or isinstance(arg, int) or isinstance(arg, IPv4Obj)

        if isinstance(arg, str):
            try:
                mm = _RGX_IPV4ADDR_NETMASK.search(arg)
            except TypeError:
                raise AddressValueError(
                    f"_ipv4_params_dict() doesn't understand how to parse {arg}"
                )

            error_msg = f"_ipv4_params_dict() couldn't parse '{arg}'"
            assert mm is not None, error_msg

            mm_result = mm.groupdict()
            addr = (
                mm_result["addr0"]
                or mm_result["addr1"]
                or mm_result["addr2"]
                or "127.0.0.1"
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
        assert isinstance(self.prefixlen, int)
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
        except AttributeError as e:
            errmsg = "'{}' cannot compare itself to '{}': {}".format(
                self.__repr__(), val, e
            )
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

        except Exception:
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
        assert isinstance(val, int), "Cannot add type: '{}' to {}".format(
            type(val), self
        )
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
        assert isinstance(val, int), "Cannot subtract type: '{}' from {}".format(
            type(val), self
        )
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
                return (self.as_decimal_network <= val.as_decimal_network) and (
                    (self.as_decimal_network + self.numhosts - 1)
                    >= (val.as_decimal_network + val.numhosts - 1)
                )

        except ValueError as e:
            raise ValueError(
                "Could not check whether '{}' is contained in '{}': {}".format(
                    val, self, e
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
    def netmask(self):
        return self.network_object.netmask

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
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if sys.version_info[0] < 3:
            return self.network_object.numhosts
        else:
            return 2 ** (IPV4_MAX_PREFIXLEN - self.network_object.prefixlen)

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
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.network).split("/")[0].split(".")
        num_strings.reverse()  # reverse the order
        return sum(int(num) * (256**idx) for idx, num in enumerate(num_strings))

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
            + "/"
            + str(self.prefixlen)
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

    # This method is on IPv6Obj().  Do NOT add @logger.catch to __init__()...
    # that breaks it.
    def __init__(self, arg=f"::1/{IPV6_MAX_PREFIXLEN}", strict=False, debug=0):
        """An object to represent IPv6 addresses and IPv6 networks.

        When :class:`~ccp_util.IPv6Obj` objects are compared or sorted, network numbers are sorted lower to higher.  If network numbers are the same, shorter masks are lower than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses.  Comparisons between :class:`~ccp_util.IPv6Obj` instances was chosen so it's easy to find the longest-match for a given prefix.

        This object emulates the behavior of ipaddr.IPv6Network() (in Python2) where host-bits were retained in the IPv6Network() object.  :class:`ipaddress.IPv6Network` in Python3 does not retain host-bits; the desire to retain host-bits in both Python2 and Python3 ip network objects was the genesis of this API.

        Parameters
        ----------
        arg : str or int
            A string containing an IPv6 address, and optionally a netmask or masklength.  Integers are also accepted. The following address/netmask formats are supported: "2001::dead:beef", "2001::dead:beef/64",
        strict : bool
            When `strict` is True, the value of `arg` must not have host-bits set.  The default value is False.

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
        prefixlen : int
            An integer representing the length of the netmask
        broadcast: raises `NotImplementedError`; IPv6 doesn't use broadcast addresses
        hostmask : :class:`ipaddress.IPv6Address`
            An :class:`ipaddress.IPv6Address` representing the hostmask
        numhosts : int
            An integer representing the number of hosts contained in the network

        """

        if debug > 0:
            logger.info(f"IPv6Obj(arg='{arg}', strict={strict}, debug={debug}) was called")

        self.arg = arg
        self.dna = "IPv6Obj"
        self.ip_object = None
        self.network_object = None
        self.strict = strict
        self.debug = debug
        self.params_dict = {}

        # Build params_dict... this needs to work with any supported input...
        if isinstance(arg, str) or isinstance(arg, int) or isinstance(arg, IPv6Obj):
            params_dict = self._ipv6_params_dict(arg)
            self.params_dict = params_dict

        if isinstance(arg, str):
            assert len(arg) <= IPV6_MAXSTR_LEN
            self.network_object = IPv6Network(params_dict['ip_arg_str'], strict=strict)
            self.ip_object = IPv6Address(params_dict['ipv6_addr'])
            return None

        elif isinstance(arg, int):
            assert 0 <= arg <= IPV6_MAXINT
            self.network_object = IPv6Network(arg, strict=strict)
            self.ip_object = IPv6Address(arg)
            return None

        elif isinstance(arg, IPv6Obj):
            ip_str = f"{str(arg.ip_object)}/{arg.prefixlen}"
            self.network_object = IPv6Network(ip_str, strict=False)
            self.ip_object = IPv6Address(str(arg.ip_object))
            return None

        elif isinstance(arg, IPv6Network):
            self.network_object = arg
            self.ip_object = IPv6Address(str(arg).split("/")[0])
            return None

        elif isinstance(arg, IPv6Address):
            self.network_object = IPv6Network(str(arg) + "/" + str(IPV6_MAX_PREFIXLEN))
            self.ip_object = IPv6Address(str(arg).split("/")[0])
            return None

        else:
            raise AddressValueError("IPv6Obj(arg='%s') is an unknown argument type" % (arg))

    # On IPv6Obj()
    def _ipv6_params_dict(self, arg, debug=0):
        """
        Parse out important IPv6 parameters from arg.  This method must run to
        completion for IPv6 address parsing to work correctly.
        """
        assert isinstance(arg, str) or isinstance(arg, int) or isinstance(arg, IPv6Obj)

        if isinstance(arg, str):
            try:
                mm = _RGX_IPV6ADDR.search(arg)

            except TypeError:
                raise AddressValueError(
                    f"_ipv6_params_dict() doesn't know how to parse {arg}"
                )


            ERROR = f"_ipv6_params_dict() couldn't parse '{arg}'"
            assert mm is not None, ERROR

            mm_result = mm.groupdict()
            try:
                addr = mm_result["addr"]

            except Exception as ee:
                addr = "::1"

            try:
                masklen = int(mm_result['masklen'])
            except Exception as ee:
                masklen = IPV6_MAX_PREFIXLEN

            assert isinstance(masklen, int) and masklen <= 128
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
        except (Exception) as e:
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

        except Exception:
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

        except Exception:
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
        assert isinstance(val, int), "Cannot add type: '{}' to {}".format(
            type(val), self
        )
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
        assert isinstance(val, int), "Cannot subtract type: '{}' from {}".format(
            type(val), self
        )
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

        except (Exception) as e:
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
        """Returns the IP network as a decimal integer"""
        num_strings = str(self.network.exploded).split("/")[0].split(":")
        num_strings.reverse()  # reverse the order
        return sum(
            int(num, 16) * (65536**idx) for idx, num in enumerate(num_strings)
        )

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

    # On IPv6Obj()
    @property
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if sys.version_info[0] < 3:
            return self.network_object.numhosts
        else:
            return 2 ** (IPV6_MAX_PREFIXLEN - self.network_object.prefixlen)

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
        except Exception:
            port_spec = port_spec

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
    elif query_type == "PTR":

        try:
            tmp = IPv4Address(input_str)
            is_valid_v4 = True
        except:
            is_valid_v4 = False

        try:
            tmp = IPv6Address(input_str)
            is_valid_v6 = True
        except:
            is_valid_v6 = False

        if (is_valid_v4 is True) or (is_valid_ipv6 is True):
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
@deprecat(reason="dns_lookup() is obsolete; use dns_query() instead.  dns_lookup() will be removed", version = '1.7.0')
def dns_lookup(input_str, timeout=3, server="", record_type="A"):
    """Perform a simple DNS lookup, return results in a dictionary"""
    assert isinstance(input_str, str)
    assert isinstance(timeout, int)
    assert isinstance(server, str)
    assert isinstance(record_type, str)

    rr = Resolver()
    rr.timeout = float(timeout)
    rr.lifetime = float(timeout)
    if server != "":
        rr.nameservers = [server]
    #dns_session = rr.resolve(input_str, record_type)
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
            #"addrs": [ii.address for ii in records],
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
@deprecat(reason="dns6_lookup() is obsolete; use dns_query() instead.  dns6_lookup() will be removed", version = '1.7.0')
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
    assert isinstance(input_addr, str)
    input_addr = input_addr.strip()
    ipaddr_family = 0
    try:
        assert IPv4Obj(input_addr)
        ipaddr_family = 4
    except Exception as _:
        pass

    if ipaddr_family == 0:
        try:
            assert IPv6Obj(input_addr)
            ipaddr_family = 6
        except Exception as _:
            pass

    error = "FATAL: '{0}' is not a valid IPv4 or IPv6 address.".format(input_addr)
    assert (ipaddr_family == 4 or ipaddr_family == 6), error
    return (input_addr, ipaddr_family)

@logger.catch(reraise=True)
@deprecat(reason="reverse_dns_lookup() is obsolete; use dns_query() instead.  reverse_dns_lookup() will be removed", version = '1.7.0')
def reverse_dns_lookup(input_str, timeout=3.0, server="4.2.2.2", proto="udp"):
    """Perform a simple reverse DNS lookup on an IPv4 or IPv6 address; return results in a python dictionary"""
    assert isinstance(proto, str) and (proto=="udp" or proto=="tcp")
    assert isinstance(float(timeout), float) and float(timeout) > 0.0

    addr, addr_family = check_valid_ipaddress(input_str)
    assert addr_family==4 or addr_family==6

    tcp_flag = None
    if proto=="tcp":
        tcp_flag = True
    elif proto=="udp":
        tcp_flag = False
    else:
        raise ValueError()

    raw_result = dns_query(input_str, query_type="PTR", server=server, timeout=timeout)
    assert isinstance(raw_result, set)
    assert len(raw_result)>=1
    tmp = raw_result.pop()
    assert isinstance(tmp, DNSResponse)

    if tmp.has_error is True:
        retval = {'addrs': [input_str], 'error': str(tmp.error_str), 'name': tmp.result_str}
    else:
        retval = {'addrs': [input_str], 'error': '', 'name': tmp.result_str}
    return retval


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
    >>> CiscoRange()
    <CiscoRange []>
    """

    def __init__(self, text="", result_type=str):
        super().__init__()
        self.text = text
        self.result_type = result_type
        if text:
            (
                self.line_prefix,
                self.slot_prefix,
                self.range_text,
            ) = self._parse_range_text()
            self._list = self._range()
        else:
            self.line_prefix = ""
            self.slot_prefix = ""
            self._list = list()

    def __repr__(self):
        if len(self._list) == 0:
            return """<CiscoRange []>"""
        else:
            return f"""<CiscoRange {self.compressed_str}>"""

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]

    def __setitem__(self, ii, val):
        return self._list[ii]

    def __str__(self):
        return self.__repr__()

    # Github issue #124
    def __eq__(self, other):
        assert hasattr(other, "line_prefix")
        self_prefix_str = self.line_prefix + self.slot_prefix
        other_prefix_str = other.line_prefix + other.slot_prefix
        cmp1 = self_prefix_str.lower() == other_prefix_str.lower()
        cmp2 = sorted(self._list) == sorted(other._list)
        return cmp1 and cmp2

    def insert(self, ii, val):
        ## Insert something at index ii
        for idx, obj in enumerate(CiscoRange(val, result_type=self.result_type)):
            self._list.insert(ii + idx, obj)

        # Prune out any duplicate entries, and sort...
        self._list = sorted(map(self.result_type, set(self._list)))
        return self

    def append(self, val):
        list_idx = len(self._list)
        self.insert(list_idx, val)
        return self

    def _normalize_and_split_text(self):
        """Split self.text on commas, then remove all common string prefixes in the list (except on the first element).  Return a 'normalized' list of strings with common_prefix removed except on the first element in the list (i.e. "Eth1/1,Eth1/4,Eth1/7" -> ["Eth1/1", "4", "7"])."""
        tmp = self.text.split(",")

        # Handle case of "Eth1/1,Eth1/5-7"... remove the common_prefix...
        common_prefix = os.path.commonprefix(tmp)

        # Ensure that we don't capture trailing digits into common_prefix
        mm = re.search(r"^(\D.*?)\d*$", common_prefix.strip())
        if mm is not None:
            common_prefix = mm.group(1)
            # Keep the common_prefix on the first element...
            _tmp = [tmp[0]]

            # Remove the common_prefix from all other list elements...
            for idx, ii in enumerate(tmp):
                if idx > 0:

                    # Unicode is the only type with .isnumeric()...
                    prefix_removed = ii[len(common_prefix) :]

                    if prefix_removed.isnumeric():
                        _tmp.append(prefix_removed)
                    elif re.search(r"^\d+\s*-\s*\d+$", prefix_removed.strip()):
                        _tmp.append(prefix_removed)
                    else:
                        ERROR = f"CiscoRange() couldn't parse '{self.text}'"
                        raise ValueError(ERROR)
            tmp = _tmp
        return tmp

    def _parse_range_text(self):
        tmp = self._normalize_and_split_text()

        mm = _RGX_CISCO_RANGE.search(tmp[0])

        ERROR = f"CiscoRange() couldn't parse '{self.text}'"
        assert mm is not None, ERROR

        mm_result = mm.groupdict()
        line_prefix = mm_result.get("line_prefix", "") or ""
        slot_prefix = mm_result.get("slot_prefix", "") or ""
        if len(tmp[1:]) > 1:
            range_text = mm_result["range_text"] + "," + ",".join(tmp[1:])
        elif len(tmp[1:]) == 1:
            range_text = mm_result["range_text"] + "," + tmp[1]
        elif len(tmp[1:]) == 0:
            range_text = mm_result["range_text"]
        return line_prefix, slot_prefix, range_text

    def _parse_dash_range(self, text):
        """Parse a dash Cisco range into a discrete list of items"""
        retval = set({})
        for range_atom in text.split(","):
            try:
                begin, end = range_atom.split("-")
            except ValueError:
                ## begin and end are the same number
                begin, end = range_atom, range_atom
            begin, end = int(begin.strip()), int(end.strip()) + 1
            assert begin > -1
            assert end > begin
            retval.update(range(begin, end))
        return sorted(list(retval))

    def _range(self):
        """Enumerate all values in the CiscoRange()"""

        def combine(arg):
            return self.line_prefix + self.slot_prefix + str(arg)

        return [
            self.result_type(ii)
            for ii in map(combine, self._parse_dash_range(self.range_text))
        ]

    def remove(self, arg):
        remove_obj = CiscoRange(arg)
        for ii in remove_obj:
            try:
                ## Remove arg, even if duplicated... Ref Github issue #126
                while True:
                    index = self.index(self.result_type(ii))
                    self.pop(index)
            except ValueError:
                pass
        return self

    @property
    def as_list(self):
        return self._list

    ## Github issue #125
    @property
    def compressed_str(self):
        """
        Return a text string with a compressed csv of values

        >>> from ciscoconfparse.ccp_util import CiscoRange
        >>> range_obj = CiscoRange('1,3,5,6,7')
        >>> range_obj.compressed_str
        '1,3,5-7'
        >>>
        """
        retval = list()
        prefix_str = self.line_prefix.strip() + self.slot_prefix.strip()
        prefix_str_len = len(prefix_str)

        # Build a list of integers (without prefix_str)
        input_str = list()
        for ii in self._list:
            # Removed try / except which is slower than sys.version_info
            unicode_ii = str(ii)

            # Removed this in version 1.5.27 because it's so slow...
            # trailing_digits = re.sub(r"^{0}(\d+)$".format(prefix_str), "\g<1>", unicode_ii)

            complete_len = len(unicode_ii)
            # Assign ii to the trailing number after prefix_str...
            #    this is much faster than regexp processing...
            trailing_digits_len = complete_len - prefix_str_len
            trailing_digits = unicode_ii[-1 * trailing_digits_len :]
            input_str.append(int(trailing_digits))

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
                        range_list = range_list
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
