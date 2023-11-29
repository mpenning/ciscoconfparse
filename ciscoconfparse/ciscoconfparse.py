"""
ciscoconfparse.py - Parse, Query, Build, and Modify IOS-style configs.

Copyright (C) 2022-2023 David Michael Pennington
Copyright (C) 2022 David Michael Pennington at WellSky
Copyright (C) 2022 David Michael Pennington
Copyright (C) 2019-2021 David Michael Pennington at Cisco Systems / ThousandEyes
Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corp
Copyright (C) 2007-2011 David Michael Pennington


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
mike [~at~] pennington [.dot.] net
"""

from collections.abc import MutableSequence, Sequence
from functools import partial
from operator import is_not
import inspect
import pathlib
import locale
import time
import copy
import sys
import re
import os


from deprecated import deprecated
from loguru import logger
import hier_config
import yaml
import toml

from ciscoconfparse.models_cisco import IOSHostnameLine, IOSRouteLine
from ciscoconfparse.models_cisco import IOSIntfLine
from ciscoconfparse.models_cisco import IOSAccessLine, IOSIntfGlobal
from ciscoconfparse.models_cisco import IOSAaaLoginAuthenticationLine
from ciscoconfparse.models_cisco import IOSAaaEnableAuthenticationLine
from ciscoconfparse.models_cisco import IOSAaaCommandsAuthorizationLine
from ciscoconfparse.models_cisco import IOSAaaConsoleAuthorizationLine
from ciscoconfparse.models_cisco import IOSAaaCommandsAccountingLine
from ciscoconfparse.models_cisco import IOSAaaExecAccountingLine
from ciscoconfparse.models_cisco import IOSAaaGroupServerLine
from ciscoconfparse.models_cisco import IOSCfgLine

from ciscoconfparse.models_nxos import NXOSHostnameLine, NXOSRouteLine
from ciscoconfparse.models_nxos import NXOSAccessLine, NXOSIntfGlobal
from ciscoconfparse.models_nxos import NXOSAaaLoginAuthenticationLine
from ciscoconfparse.models_nxos import NXOSAaaEnableAuthenticationLine
from ciscoconfparse.models_nxos import NXOSAaaCommandsAuthorizationLine
from ciscoconfparse.models_nxos import NXOSAaaConsoleAuthorizationLine
from ciscoconfparse.models_nxos import NXOSAaaCommandsAccountingLine
from ciscoconfparse.models_nxos import NXOSAaaExecAccountingLine
from ciscoconfparse.models_nxos import NXOSCfgLine, NXOSIntfLine
from ciscoconfparse.models_nxos import NXOSAaaGroupServerLine
from ciscoconfparse.models_nxos import NXOSvPCLine

from ciscoconfparse.models_iosxr import IOSXRCfgLine, IOSXRIntfLine

from ciscoconfparse.models_asa import ASAObjGroupNetwork
from ciscoconfparse.models_asa import ASAObjGroupService
from ciscoconfparse.models_asa import ASAHostnameLine
from ciscoconfparse.models_asa import ASAObjNetwork
from ciscoconfparse.models_asa import ASAObjService
from ciscoconfparse.models_asa import ASAIntfGlobal
from ciscoconfparse.models_asa import ASAIntfLine
from ciscoconfparse.models_asa import ASACfgLine
from ciscoconfparse.models_asa import ASAName
from ciscoconfparse.models_asa import ASAAclLine

# from ciscoconfparse.models_junos import JunosIntfLine
from ciscoconfparse.models_junos import JunosCfgLine

from ciscoconfparse.ccp_abc import BaseCfgLine

from ciscoconfparse.ccp_util import fix_repeated_words
from ciscoconfparse.ccp_util import enforce_valid_types
from ciscoconfparse.ccp_util import junos_unsupported
from ciscoconfparse.ccp_util import configure_loguru

from ciscoconfparse.errors import InvalidParameters
from ciscoconfparse.errors import RequirementFailure

# Not using ccp_re yet... still a work in progress
# from ciscoconfparse.ccp_util import ccp_re

ALL_IOS_FACTORY_CLASSES = [
    IOSIntfLine,
    IOSRouteLine,
    IOSAccessLine,
    IOSAaaLoginAuthenticationLine,
    IOSAaaEnableAuthenticationLine,
    IOSAaaCommandsAuthorizationLine,
    IOSAaaConsoleAuthorizationLine,
    IOSAaaCommandsAccountingLine,
    IOSAaaExecAccountingLine,
    IOSAaaGroupServerLine,
    IOSHostnameLine,
    IOSIntfGlobal,
    IOSCfgLine,        # IOSCfgLine MUST be last
]
ALL_NXOS_FACTORY_CLASSES = [
    NXOSIntfLine,
    NXOSRouteLine,
    NXOSAccessLine,
    NXOSAaaLoginAuthenticationLine,
    NXOSAaaEnableAuthenticationLine,
    NXOSAaaCommandsAuthorizationLine,
    NXOSAaaConsoleAuthorizationLine,
    NXOSAaaCommandsAccountingLine,
    NXOSAaaExecAccountingLine,
    NXOSAaaGroupServerLine,
    NXOSvPCLine,
    NXOSHostnameLine,
    NXOSIntfGlobal,
    NXOSCfgLine,        # NXOSCfgLine MUST be last
]
ALL_IOSXR_FACTORY_CLASSES = [
    IOSXRIntfLine,
    IOSXRCfgLine,
]
ALL_ASA_FACTORY_CLASSES = [
    ASAIntfLine,
    ASAName,
    ASAObjNetwork,
    ASAObjService,
    ASAObjGroupNetwork,
    ASAObjGroupService,
    ASAIntfGlobal,
    ASAHostnameLine,
    ASAAclLine,
    ASACfgLine,        # ASACfgLine MUST be last
]
ALL_JUNOS_FACTORY_CLASSES = [
    ##########################################################################
    # JunosIntfLine is rather broken; JunosCfgLine should be enough
    ##########################################################################
    # JunosIntfLine,
    JunosCfgLine,      # JunosCfgLine MUST be last
]

# Indexing into CFGLINE is normally faster than serial if-statements...
CFGLINE = {
    "ios": IOSCfgLine,
    "nxos": NXOSCfgLine,
    "iosxr": IOSXRCfgLine,
    "asa": ASACfgLine,
    "junos": JunosCfgLine,
}

ALL_VALID_SYNTAX = (
    "ios",
    "nxos",
    "iosxr",
    "asa",
    "junos",
)

ALL_BRACE_SYNTAX = {
    "junos",
}


@logger.catch(reraise=True)
def get_version_number():
    """Read the version number from 'pyproject.toml', or use version 0.0.0 in odd circumstances."""
    # Docstring props: http://stackoverflow.com/a/1523456/667301
    # version: if-else below fixes Github issue #123

    version = "0.0.0"  # version read failed

    pyproject_toml_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../pyproject.toml",
    )
    if os.path.isfile(pyproject_toml_path):
        # Retrieve the version number from pyproject.toml...
        toml_values = {}
        with open(pyproject_toml_path, encoding=ENCODING) as fh:
            toml_values = toml.loads(fh.read())
            version = toml_values["tool"]["poetry"].get("version", -1.0)

        if not isinstance(version, str):
            raise ValueError("The version parameter must be a string.")

    else:
        # This is required for importing from a zipfile... Github issue #123
        version = "0.0.0"  # __version__ read failed

    return version


ENCODING = None
ACTIVE_LOGURU_HANDLERS = None
__author_email__ = r"mike /at\ pennington [dot] net"
__author__ = f"David Michael Pennington <{__author_email__}>"
__copyright__ = f'2007-{time.strftime("%Y")}, {__author__}'
__license__ = "GPLv3"
__status__ = "Production"
__version__ = None


@logger.catch(reraise=True)
def initialize_globals():
    """Initialize ciscoconfparse global dunder-variables and a couple others."""
    global ENCODING
    #global ACTIVE_LOGURU_HANDLERS
    global __author_email__
    global __author__
    global __copyright__
    global __license__
    global __status__
    global __version__

    ENCODING = locale.getpreferredencoding()

    __author_email__ = r"mike /at\ pennington [dot] net"
    __author__ = f"David Michael Pennington <{__author_email__}>"
    __copyright__ = f'2007-{time.strftime("%Y")}, {__author__}'
    __license__ = "GPLv3"
    __status__ = "Production"
    try:
        __version__ = get_version_number()
    except BaseException as eee:
        __version__ = "0.0.0"
        error = f"{eee}: could not determine the ciscoconfparse version via get_version_number()."
        logger.critical(error)
        raise ValueError(error)

    # These are all the 'dunder variables' required...
    globals_dict = {
        "__author_email__": __author_email__,
        "__author__": __author__,
        "__copyright__": __copyright__,
        "__license__": __license__,
        "__status__": __status__,
        "__version__": __version__,
    }
    return globals_dict


@logger.catch(reraise=True)
def initialize_ciscoconfparse(read_only=False, debug=0):
    """Initialize ciscoconfparse global variables and configure logging."""
    globals_dict = initialize_globals()
    for key, value in globals_dict.items():
        # Example, this will set __version__ to content of 'value'
        #     from -> https://stackoverflow.com/a/3972978/667301
        globals()[key] = value

    # Re-configure loguru... not a perfect solution, but this should be good enough
    #     Ref Github Issue #281
    if globals_dict.get("ACTIVE_LOGURU_HANDLERS", None) is None:
        active_loguru_handlers = configure_loguru(read_only=read_only, active_handlers=None, debug=debug)
    else:
        active_loguru_handlers = configure_loguru(read_only=read_only, active_handlers=globals_dict["ACTIVE_LOGURU_HANDLERS"], debug=debug)

    globals()["ACTIVE_LOGURU_HANDLERS"] = active_loguru_handlers

    if debug > 0 and read_only is True:
        logger.info("DISABLED loguru enqueue parameter because read_only=True.")

    return globals_dict, active_loguru_handlers


# ALL ciscoconfparse global variables initizalization happens here...
_, ACTIVE_LOGURU_HANDLERS = initialize_ciscoconfparse()


@logger.catch(reraise=True)
def parse_line_braces(line_txt=None, comment_delimiter=None) -> tuple:
    """Internal helper-method for brace-delimited configs (typically JunOS, syntax='junos')."""
    # Removed config parameter assertions in 1.7.2...

    retval = ()

    enforce_valid_types(line_txt, (str,), "line_txt parameter must be a string.")
    enforce_valid_types(
        comment_delimiter, (str,), "comment_delimiter parameter must be a string."
    )
    if len(comment_delimiter) > 1:
        raise ValueError("len(comment_delimiter) must be one.")

    child_indent = 0
    this_line_indent = 0

    junos_re_str = r"""^
    (?:\s*
        (?P<braces_close_left>\})*(?P<line1>.*?)(?P<braces_open_right>\{)*;*
        |(?P<line2>[^\{\}]*?)(?P<braces_open_left>\{)(?P<condition2>.*?)(?P<braces_close_right>\});*\s*
        |(?P<line3>[^\{\}]*?);*\s*
    )\s*$
    """
    brace_re = re.compile(junos_re_str, re.VERBOSE)
    comment_re = re.compile(
        r"^\s*(?P<delimiter>[{0}]+)(?P<comment>[^{0}]*)$".format(
            re.escape(comment_delimiter)
        )
    )

    brace_match = brace_re.search(line_txt.strip())
    comment_match = comment_re.search(line_txt.strip())

    if isinstance(comment_match, re.Match):
        results = comment_match.groupdict()
        delimiter = results.get("delimiter", "")
        comment = results.get("comment", "")
        retval = (
            this_line_indent,
            child_indent,
            delimiter + comment
        )

    elif isinstance(brace_match, re.Match):
        results = brace_match.groupdict()

        # } line1 { foo bar this } {
        braces_close_left = bool(results.get("braces_close_left", ""))
        braces_open_right = bool(results.get("braces_open_right", ""))

        # line2
        braces_open_left = bool(results.get("braces_open_left", ""))
        braces_close_right = bool(results.get("braces_close_right", ""))

        # line3
        line1_str = results.get("line1", "")
        line2_str = results.get("line2", "")

        if braces_close_left and braces_open_right:
            # Based off line1
            #     } elseif { bar baz } {
            this_line_indent -= 1
            child_indent += 0
            line1 = results.get("line1", None)
            retval = (this_line_indent, child_indent, line1)

        elif bool(line1_str) and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     address 1.1.1.1
            this_line_indent -= 0
            child_indent += 0
            _line1 = results.get("line1", "").strip()
            # Strip empty braces here
            line1 = re.sub(r"\s*\{\s*\}\s*", "", _line1)
            retval = (this_line_indent, child_indent, line1)

        elif (line1_str == "") and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     return empty string
            this_line_indent -= 0
            child_indent += 0
            retval = (this_line_indent, child_indent, "")

        elif braces_open_left and braces_close_right:
            # Based off line2
            #    this { bar baz }
            this_line_indent -= 0
            child_indent += 0
            _line2 = results.get("line2", None) or ""
            condition = results.get("condition2", None) or ""
            if condition.strip() == "":
                line2 = _line2
            else:
                line2 = _line2 + " {" + condition + " }"
            retval = (this_line_indent, child_indent, line2)

        elif braces_close_left:
            # Based off line1
            #   }
            this_line_indent -= 1
            child_indent -= 1
            retval = (this_line_indent, child_indent, "")

        elif braces_open_right:
            # Based off line1
            #   this that foo {
            this_line_indent -= 0
            child_indent += 1
            line = results.get("line1", None) or ""
            retval = (this_line_indent, child_indent, line)

        elif (line2_str != "") and (line2_str is not None):
            this_line_indent += 0
            child_indent += 0
            retval = (this_line_indent, child_indent, "")

        else:
            error = f'Cannot parse `{line_txt}`'
            logger.error(error)
            raise ValueError(error)

    else:
        error = f'Cannot parse `{line_txt}`'
        logger.error(error)
        raise ValueError(error)

    return retval


# This method was on ConfigList()
@logger.catch(reraise=True)
def cfgobj_from_text(
    text_list, txt, idx, syntax=None, comment_delimiter=None, factory=None
):
    """Build cfgobj from configuration text syntax, and factory inputs."""

    if not isinstance(txt, str):
        error = f"cfgobj_from_text(txt=`{txt}`) must be a string"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(idx, int):
        error = f"cfgobj_from_text(idx=`{idx}`) must be an int"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiter, str):
        error = f"cfgobj_from_text(comment_delimiter=`{comment_delimiter}`) must be a string"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(factory, bool):
        error = f"cfgobj_from_text(factory=`{factory}`) must be a boolean"
        logger.error(error)
        raise InvalidParameters(error)

    # if not factory is **faster** than factory is False
    if syntax in ALL_VALID_SYNTAX and not factory:
        obj = CFGLINE[syntax](
            all_lines=text_list,
            line=txt,
            comment_delimiter=comment_delimiter,
        )
        if isinstance(obj, BaseCfgLine):
            obj.linenum = idx
        else:
            error = f"{CFGLINE[syntax]}(txt=`{txt}`) must return an instance of BaseCfgLine(), but it returned {obj}"
            logger.error(error)
            raise ValueError(error)

    # if factory is **faster** than if factory is True
    elif syntax in ALL_VALID_SYNTAX and factory:
        obj = config_line_factory(
            all_lines=text_list,
            line=txt,
            comment_delimiter=comment_delimiter,
            syntax=syntax,
        )
        if isinstance(obj, BaseCfgLine):
            obj.linenum = idx
        else:
            error = f"config_line_factory(line=`{txt}`) must return an instance of BaseCfgLine(), but it returned {obj}"
            logger.error(error)
            raise ValueError(error)

    else:
        err_txt = (
            f"Cannot classify config list item `{txt}` into a proper configuration object line"
        )
        logger.error(err_txt)
        raise ValueError(err_txt)

    return obj


@logger.catch(reraise=True)
def build_space_tolerant_regex(linespec):
    r"""SEMI-PRIVATE: Accept a string, and return a string with all spaces replaced with '\s+'."""
    # Define backslash with manual Unicode...
    backslash = "\x5c"
    # escaped_space = "\\s+" (not a raw string)
    escaped_space = (backslash + backslash + "s+").translate("utf-8")

    enforce_valid_types(linespec, (str,), "linespec parameter must be a string.")
    if isinstance(linespec, str):
        linespec = re.sub(r"\s+", escaped_space, linespec)

    elif isinstance(linespec, Sequence):
        for idx, tmp in enumerate(linespec):
            # Ensure this list element is a string...
            if not isinstance(tmp, str):
                raise ValueError("tmp parameter must be a string.")
            linespec[idx] = re.sub(r"\s+", escaped_space, tmp)

    return linespec


@logger.catch(reraise=True)
def assign_parent_to_closing_braces(input_list=None, keep_blank_lines=False):
    """Accept a list of brace-delimited BaseCfgLine() objects; these objects should not already have a parent assigned.  Walk the list of BaseCfgLine() objects and assign the 'parent' attribute BaseCfgLine() objects to the closing config braces.  Return the list of objects (with the assigned 'parent' attributes).

    Closing Brace Assignment Example
    --------------------------------

    line number 1
    line number 2 {
        line number 3 {
            line number 4
            line number 5 {
                line number 6
                line number 7
                line number 8
            }            # Assign this closing-brace's parent as line 5
        }                # Assign this closing-brace's parent as line 3
    }                    # Assign this closing-brace's parent as line 2
    line number 11
    """
    if input_list is None:
        raise ValueError("Cannot modify.  The input_list is None")

    input_condition = isinstance(input_list, Sequence)
    if input_condition is True and len(input_list) > 0:
        opening_brace_objs = []
        for obj in input_list:
            if isinstance(obj, BaseCfgLine) and isinstance(obj.text, str):
                # These rstrip() are one of two fixes, intended to catch user error such as
                # the problems that the submitter of Github issue #251 had.
                # CiscoConfParse() could not read his configuration because he submitted
                # a multi-line string...
                #
                # This check will explicitly catch some problems like that...
                if len(obj.text.rstrip()) >= 1 and obj.text.rstrip()[-1] == "{":
                    opening_brace_objs.append(obj)

                elif len(obj.text.strip()) >= 1 and obj.text.strip()[0] == "}":
                    if len(opening_brace_objs) >= 1:
                        obj.parent = opening_brace_objs.pop()
                    else:
                        raise ValueError

    return input_list


# This method was copied from the same method in git commit below...
# https://raw.githubusercontent.com/mpenning/ciscoconfparse/bb3f77436023873da344377d3c839387f5131e7f/ciscoconfparse/ciscoconfparse.py
@logger.catch(reraise=True)
def convert_junos_to_ios(input_list=None, stop_width=4, comment_delimiter="!", debug=0):
    """Accept `input_list` containing a list of junos-brace-formatted-string config lines.  This method strips off semicolons / braces from the string lines in `input_list` and returns the lines in a new list where all lines are explicitly indented as IOS would (as if IOS understood braces)."""

    if not isinstance(input_list, list):
        error = "convert_junos_to_ios() `input_list` must be a non-empty python list"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(stop_width, int):
        error = "convert_junos_to_ios() `stop_width` must be an integer"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiter, str):
        error = "convert_junos_to_ios() `comment_delimiter` must be a string"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(debug, int):
        error = "convert_junos_to_ios() `debug` must be an integer"
        logger.error(error)
        raise InvalidParameters(error)

    # Note to self, I made this regex fairly junos-specific...
    input_condition_01 = isinstance(input_list, list) and len(input_list) > 0
    input_condition_02 = "{" not in set(comment_delimiter)
    input_condition_03 = "}" not in set(comment_delimiter)
    if not (input_condition_01 and input_condition_02 and input_condition_03):
        error = "convert_junos_to_ios() input conditions failed"
        logger.error(error)
        raise ValueError(error)

    lines = []
    offset = 0
    STOP_WIDTH = stop_width
    for idx, tmp in enumerate(input_list):
        if debug > 0:
            logger.debug(f"Parse line {idx + 1}:'{tmp.strip()}'")
        (this_line_indent, child_indent, line) = parse_line_braces(
            tmp.strip(), comment_delimiter=comment_delimiter
        )
        lines.append((" " * STOP_WIDTH * (offset + this_line_indent)) + line.strip())
        offset += child_indent

    return lines


class CiscoConfParse(object):
    """Parse Cisco IOS configurations and answer queries about the configs."""
    finished_config_parse = False
    debug = 0
    ConfigObjs = None
    syntax = "ios"
    comment_delimiter = "!"
    factory = False
    ignore_blank_lines = True
    encoding = locale.getpreferredencoding()
    read_only = False

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def __init__(
        self,
        config="",
        comment="!",
        debug=0,
        factory=False,
        linesplit_rgx=r"\r*\n+",
        ignore_blank_lines=True,
        syntax="ios",
        encoding=locale.getpreferredencoding(),
        read_only=False,
    ):
        """
        Initialize CiscoConfParse.

        Parameters
        ----------
        config : list or str
            A list of configuration statements, or a configuration file path to be parsed
        comment : str
            A comment delimiter.  This should only be changed when parsing non-Cisco IOS configurations, which do not use a !  as the comment delimiter.  ``comment`` defaults to '!'.  This value can hold multiple characters in case the config uses multiple characters for comment delimiters; however, the comment delimiters are always assumed to be one character wide
        debug : int
            ``debug`` defaults to 0, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug range goes from 0 (no debugging) to 5 (max debugging).  Debug output is not particularly friendly.
        factory : bool
            ``factory`` defaults to False; if set ``True``, it enables a beta-quality configuration line classifier.
        linesplit_rgx : str
            ``linesplit_rgx`` is used when parsing configuration files to find where new configuration lines are.  It is best to leave this as the default, unless you're working on a system that uses unusual line terminations (for instance something besides Unix, OSX, or Windows)
        ignore_blank_lines : bool
            ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration (ref: Github Issue #3), or you are parsing configurations which naturally have blank lines (such as Cisco Nexus configurations).
        syntax : str
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'iosxr', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).
        encoding : str
            A string holding the coding type.  Default is `locale.getpreferredencoding()`
        read_only : bool
            A bool indicating whether CiscoConfParse should execute read-only.



        Returns
        -------
        :class:`~ciscoconfparse.CiscoConfParse`

        Examples
        --------
        This example illustrates how to parse a simple Cisco IOS configuration
        with :class:`~ciscoconfparse.CiscoConfParse` into a variable called
        ``parse``.  This example also illustrates what the ``ConfigObjs``
        and ``ioscfg`` attributes contain.

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse
        <CiscoConfParse: 2 lines / syntax: ios / comment delimiter: '!' / factory: False>
        >>> parse.ConfigObjs
        <ConfigList, comment='!', conf=[<IOSCfgLine # 0 'logging trap debugging'>, <IOSCfgLine # 1 'logging 172.28.26.15'>]>
        >>> parse.ioscfg
        ['logging trap debugging', 'logging 172.28.26.15']
        >>>

        Attributes
        ----------
        comment_delimiter : str
            A string containing the comment-delimiter.  Default: "!"
        ConfigObjs : :class:`~ciscoconfparse.ConfigList`
            A custom list, which contains all parsed :class:`~models_cisco.IOSCfgLine` instances.
        debug : int
            An int to enable verbose config parsing debugs. Default 0.
        ioscfg : list
            A list of text configuration strings
        objs
            An alias for `ConfigObjs`
        openargs : dict
            Returns a dictionary of valid arguments for `open()` (these change based on the running python version).
        syntax : str
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'iosxr', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).

        """
        ######################################################################
        # Log a warning if parsing with `ignore_blank_lines=True` and
        #     `factory=False`, which is the default parsing config...
        ######################################################################
        if ignore_blank_lines is True and factory is False:
            logger.info("As of version 1.9.17 and later, `ignore_blank_lines=True` is only honored when `factory=True`")

        ######################################################################
        # Reconfigure loguru if read_only is True
        ######################################################################
        if read_only is True:
            active_loguru_handlers = configure_loguru(read_only=read_only, active_handlers=globals()["ACTIVE_LOGURU_HANDLERS"], debug=debug)
            globals()["ACTIVE_LOGURU_HANDLERS"] = active_loguru_handlers
            if debug > 0:
                logger.warning(f"Disabled loguru enqueue because read_only={read_only}")

        if not (isinstance(syntax, str) and (syntax in ALL_VALID_SYNTAX)):
            error = f"'{syntax}' is an unknown syntax"
            logger.error(error)
            raise ValueError(error)

        # all IOSCfgLine object instances...
        self.finished_config_parse = False
        self.debug = debug
        self.ConfigObjs = None
        self.syntax = syntax
        self.comment_delimiter = comment
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.encoding = encoding or ENCODING
        self.read_only = read_only

        if len(config) > 0:
            try:
                correct_element_types = []
                for ii in config:
                    # Check whether the elements are the correct types...
                    if isinstance(ii, (str, BaseCfgLine)):
                        correct_element_types.append(True)
                    else:
                        correct_element_types.append(False)

                elements_have_len = all(correct_element_types)
            except AttributeError:
                elements_have_len = False
            except TypeError:
                elements_have_len = False
        else:
            elements_have_len = None

        if elements_have_len is False:
            error = "All ConfigList elements must have a length()"
            logger.error(error)
            raise InvalidParameters(error)

        # Read the configuration lines and detect invalid inputs...
        # tmp_lines = self._get_ccp_lines(config=config, logger=logger)
        if isinstance(config, (str, pathlib.Path,)):
            if ignore_blank_lines is True and factory is False:
                tmp_lines = self.read_config_file(filepath=config, linesplit_rgx=r"\r*\n+")
            else:
                tmp_lines = self.read_config_file(filepath=config, linesplit_rgx=r"\r*\n")
        elif isinstance(config, Sequence):
            if ignore_blank_lines is True and factory is False:
                tmp_lines = [ii for ii in config if len(ii) != 0]
            else:
                tmp_lines = config
        else:
            error = f"Cannot read config from {config}"
            logger.critical(error)
            raise ValueError(error)

        # conditionally strip off junos-config braces and other syntax
        #     parsing issues...
        config_lines = self.handle_ccp_brace_syntax(tmp_lines=tmp_lines, syntax=syntax)
        if self.check_ccp_input_good(config=config_lines, logger=logger) is False:
            error = f"Cannot parse config=`{tmp_lines}`"
            logger.critical(error)
            raise ValueError(error)

        if self.debug > 0:
            logger.info("assigning self.ConfigObjs = ConfigList()")

        self.ConfigObjs = ConfigList(
            initlist=config_lines,
            comment_delimiter=comment,
            debug=debug,
            factory=factory,
            ignore_blank_lines=ignore_blank_lines,
            syntax=syntax,
            ccp_ref=self,
        )

        # IMPORTANT this MUST not be a lie :-)...
        self.finished_config_parse = True

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def handle_ccp_brace_syntax(self, tmp_lines=None, syntax=None):
        """Deal with brace-delimited syntax issues, such as conditionally discarding junos closing brace-lines."""

        if syntax not in ALL_VALID_SYNTAX:
            error = f"{syntax} parser factory is not yet enabled; use factory=False"
            logger.critical(error)
            raise InvalidParameters(error)

        if not isinstance(tmp_lines, (list, tuple)):
            error = f"handle_ccp_brace_syntax(tmp_lines={tmp_lines}) must not be None"
            logger.error(error)
            raise InvalidParameters(error)

        ######################################################################
        # Explicitly handle all brace-parsing factory syntax here...
        ######################################################################
        if syntax == "junos":
            config_lines = convert_junos_to_ios(tmp_lines, comment_delimiter="#")
        elif syntax in ALL_VALID_SYNTAX:
            config_lines = tmp_lines
        else:
            error = f"handle_ccp_brace_syntax(syntax=`{syntax}`) is not yet supported"
            logger.error(error)
            raise InvalidParameters(error)

        return config_lines

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def __repr__(self):
        """Return a string that represents this CiscoConfParse object instance.  The number of lines embedded in the string is calculated from the length of the ConfigObjs attribute."""
        if self.ConfigObjs is None:
            num_lines = 0
        elif isinstance(self.ConfigObjs, Sequence):
            num_lines = len(self.ConfigObjs)
        return (
            "<CiscoConfParse: %s lines / syntax: %s / comment delimiter: '%s' / factory: %s / ignore_blank_lines: %s / encoding: '%s'>"
            % (
                num_lines,
                self.syntax,
                self.comment_delimiter,
                self.factory,
                self.ignore_blank_lines,
                self.encoding,
            )
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def read_config_file(self, filepath=None, linesplit_rgx=r"\r*\n+"):
        """Read the config lines from the filepath.  Return the list of text configuration commands or raise an error."""

        if self.finished_config_parse is not False:
            raise RequirementFailure()

        valid_path_variable = False
        if filepath is None:
            error = "Filepath: None is invalid"
            logger.critical(error)
            raise FileNotFoundError(error)
        elif isinstance(filepath, (str, pathlib.Path,)):
            valid_path_variable = True

        if valid_path_variable and not os.path.exists(filepath):
            error = f"Filepath: {filepath} does not exist"
            logger.critical(error)
            raise FileNotFoundError(error)

        config_lines = None

        _encoding = self.openargs['encoding']
        if valid_path_variable is True and os.path.isfile(filepath) is True:
            # config string - assume a filename...
            if self.debug > 0:
                logger.debug(f"reading config from the filepath named '{filepath}'")

        elif valid_path_variable is True and os.path.isfile(filepath) is False:
            if self.debug > 0:
                logger.debug(f"filepath not found - '{filepath}'")
            try:
                _ = open(file=filepath, **self.openargs)
            except FileNotFoundError:
                error = f"""FATAL - Attempted to open(file='{filepath}', mode='r', encoding="{_encoding}"); the filepath named:"{filepath}" does not exist."""
                logger.critical(error)
                raise FileNotFoundError(error)

            except OSError:
                error = f"""FATAL - Attempted to open(file='{filepath}', mode='r', encoding="{_encoding}"); OSError opening "{filepath}"."""
                logger.critical(error)
                raise OSError(error)

            except BaseException:
                logger.critical(f"Cannot open {filepath}")
                raise BaseException

        else:
            error = f'Unexpected condition processing filepath: {filepath}'
            logger.critical(error)
            raise ValueError(error)

        # Read the file from disk and return the list of config statements...
        try:
            with open(file=filepath, **self.openargs) as fh:
                text = fh.read()
            rgx = re.compile(linesplit_rgx)
            config_lines = rgx.split(text)
            return config_lines

        except OSError:
            error = f"CiscoConfParse could not open() the filepath named '{filepath}'"
            logger.critical(error)
            raise OSError(error)

        except BaseException as eee:
            error = f"FATAL - {eee}"
            logger.critical(error)
            raise OSError(error) from eee

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def check_ccp_input_good(self, config=None, logger=None, linesplit_rgx=r"\r*\n+"):
        """The config parameter is a sequence of text config commands.  Return True or False based on whether the config can be parsed."""

        if self.finished_config_parse is not False:
            raise RequirementFailure()

        if isinstance(config, Sequence):
            # Here we assume that `config` is a list of text config lines...
            #
            # config list of text lines...
            if self.debug > 0:
                logger.debug(
                    f"parsing config stored in the config variable: `{config}`"
                )
            return True

        else:
            return False

    #########################################################################
    # This method is on CiscoConfParse()
    #      do NOT wrap this method in logger.catch() - github issue #249
    #########################################################################
    @property
    @logger.catch(reraise=True)
    def openargs(self):
        """Fix Py3.5 deprecation of universal newlines - Ref Github #114; also see https://softwareengineering.stackexchange.com/q/298677/23144."""
        if sys.version_info >= (
            3,
            6,
        ):
            retval = {"mode": "r", "newline": None, "encoding": self.encoding}
        else:
            retval = {"mode": "rU", "encoding": self.encoding}
        return retval

    # This method is on CiscoConfParse()
    @property
    @logger.catch(reraise=True)
    def ioscfg(self):
        """Return a list containing all text configuration statements."""
        # I keep ioscfg to emulate legacy ciscoconfparse behavior
        #
        # FYI: map / methodcaller is not significantly faster than a list
        #     comprehension, below...
        # See https://stackoverflow.com/a/51519942/667301
        # from operator import methodcaller
        # get_text_attr = methodcaller('text')
        # return list(map(get_text_attr, self.ConfigObjs))
        #
        return [ii.text for ii in self.ConfigObjs]

    # This method is on CiscoConfParse()
    @property
    @logger.catch(reraise=True)
    def objs(self):
        """CiscoConfParse().objs is an alias for the CiscoConfParse().ConfigObjs property; it returns a ConfigList() of config-line objects."""
        if self.ConfigObjs is None:
            error = (
                "ConfigObjs is set to None.  ConfigObjs should be a ConfigList() of configuration-line objects"
            )
            logger.error(error)
            raise ValueError(error)
        return self.ConfigObjs

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def atomic(self):
        """Use :func:`~ciscoconfparse.CiscoConfParse.atomic` to manually fix up ``ConfigObjs`` relationships after modifying a parsed configuration.  This method is slow; try to batch calls to :func:`~ciscoconfparse.CiscoConfParse.atomic()` if possible.

        Warnings
        --------
        If you modify a configuration after parsing it with :class:`~ciscoconfparse.CiscoConfParse`, you *must* call :func:`~ciscoconfparse.CiscoConfParse.commit` or :func:`~ciscoconfparse.CiscoConfParse.atomic` before searching the configuration again with methods such as :func:`~ciscoconfparse.CiscoConfParse.find_objects` or :func:`~ciscoconfparse.CiscoConfParse.find_lines`.  Failure to call :func:`~ciscoconfparse.CiscoConfParse.commit` or :func:`~ciscoconfparse.CiscoConfParse.atomic` on config modifications could lead to unexpected search results.

        See Also
        --------
        :func:`~ciscoconfparse.CiscoConfParse.commit`.
        """
        # self.ConfigObjs._bootstrap_from_text()
        self.ConfigObjs._list = self.ConfigObjs.bootstrap_obj_init_ng(self.ioscfg, debug=self.debug)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def commit(self):
        """Alias for calling the :func:`~ciscoconfparse.CiscoConfParse.atomic` method.  This method is slow; try to batch calls to :func:`~ciscoconfparse.CiscoConfParse.commit()` if possible.

        Warnings
        --------
        If you modify a configuration after parsing it with :class:`~ciscoconfparse.CiscoConfParse`, you *must* call :func:`~ciscoconfparse.CiscoConfParse.commit` or :func:`~ciscoconfparse.CiscoConfParse.atomic` before searching the configuration again with methods such as :func:`~ciscoconfparse.CiscoConfParse.find_objects` or :func:`~ciscoconfparse.CiscoConfParse.find_lines`.  Failure to call :func:`~ciscoconfparse.CiscoConfParse.commit` or :func:`~ciscoconfparse.CiscoConfParse.atomic` on config modifications could lead to unexpected search results.

        See Also
        --------
        :func:`~ciscoconfparse.CiscoConfParse.atomic`.
        """
        self.atomic()  # atomic() calls self.ConfigObjs.bootstrap_obj_init_ng

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_object_branches(
        self,
        branchspec=(),
        regex_flags=0,
        allow_none=True,
        regex_groups=False,
        debug=0,
    ):
        r"""Iterate over a tuple of regular expressions in `branchspec` and return matching objects in a list of lists (consider it similar to a table of matching config objects). `branchspec` expects to start at some ancestor and walk through the nested object hierarchy (with no limit on depth).

        Previous CiscoConfParse() methods only handled a single parent regex and single child regex (such as :func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child`).

        Transcend past one-level of parent-child relationship parsing to include multiple nested 'branches' of a single family (i.e. parents, children, grand-children, great-grand-children, etc).  The result of handling longer regex chains is that it flattens what would otherwise be nested loops in your scripts; this makes parsing heavily-nested configuratations like Juniper, Palo-Alto, and F5 much simpler.  Of course, there are plenty of applications for "flatter" config formats like IOS.

        Return a list of lists (of object 'branches') which are nested to the same depth required in `branchspec`.  However, unlike most other CiscoConfParse() methods, return an explicit `None` if there is no object match.  Returning `None` allows a single search over configs that may not be uniformly nested in every branch.

        Deprecation notice for the allow_none parameter
        -----------------------------------------------

        allow_none is deprecated and no longer a configuration option, as of version 1.6.16.
        Going forward, allow_none will always be considered True.

        Parameters
        ----------
        branchspec : tuple
            A tuple of python regular expressions to be matched.
        regex_flags :
            Chained regular expression flags, such as `re.IGNORECASE|re.MULTILINE`
        regex_groups : bool (default False)
            If True, return a tuple of re.Match groups instead of the matching configuration objects.
        debug : int
            Set debug > 0 for debug messages

        Returns
        -------
        list
            A list of lists of matching :class:`~ciscoconfparse.IOSCfgLine` objects

        Examples
        --------
        >>> from operator import attrgetter
        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     'ltm pool FOO {',
        ...     '  members {',
        ...     '    k8s-05.localdomain:8443 {',
        ...     '      address 192.0.2.5',
        ...     '      session monitor-enabled',
        ...     '      state up',
        ...     '    }',
        ...     '    k8s-06.localdomain:8443 {',
        ...     '      address 192.0.2.6',
        ...     '      session monitor-enabled',
        ...     '      state down',
        ...     '    }',
        ...     '  }',
        ...     '}',
        ...     'ltm pool BAR {',
        ...     '  members {',
        ...     '    k8s-07.localdomain:8443 {',
        ...     '      address 192.0.2.7',
        ...     '      session monitor-enabled',
        ...     '      state down',
        ...     '    }',
        ...     '  }',
        ...     '}',
        ...     ]
        >>> parse = CiscoConfParse(config=config, syntax='junos', comment='#')
        >>>
        >>> branchspec = (r'ltm\spool', r'members', r'\S+?:\d+', r'state\sup')
        >>> branches = parse.find_object_branches(branchspec=branchspec)
        >>>
        >>> # We found three branches
        >>> len(branches)
        3
        >>> # Each branch must match the length of branchspec
        >>> len(branches[0])
        4
        >>> # Print out one object 'branch'
        >>> branches[0]
        [<IOSCfgLine # 0 'ltm pool FOO'>, <IOSCfgLine # 1 '    members' (parent is # 0)>, <IOSCfgLine # 2 '        k8s-05.localdomain:8443' (parent is # 1)>, <IOSCfgLine # 5 '            state up' (parent is # 2)>]
        >>>
        >>> # Get the a list of text lines for this branch...
        >>> [ii.text for ii in branches[0]]
        ['ltm pool FOO', '    members', '        k8s-05.localdomain:8443', '            state up']
        >>>
        >>> # Get the config text of the root object of the branch...
        >>> branches[0][0].text
        'ltm pool FOO'
        >>>
        >>> # Note: `None` in branches[1][-1] because of no regex match
        >>> branches[1]
        [<IOSCfgLine # 0 'ltm pool FOO'>, <IOSCfgLine # 1 '    members' (parent is # 0)>, <IOSCfgLine # 6 '        k8s-06.localdomain:8443' (parent is # 1)>, None]
        >>>
        >>> branches[2]
        [<IOSCfgLine # 10 'ltm pool BAR'>, <IOSCfgLine # 11 '    members' (parent is # 10)>, <IOSCfgLine # 12 '        k8s-07.localdomain:8443' (parent is # 11)>, None]
        """
        # As of verion 1.6.16, allow_none is always True.  See the Deprecation
        # notice above...
        if allow_none is not True:
            warning = "The allow_none parameter is deprecated as of version 1.6.16.  Going forward, allow_none is always True."
            logger.warning(warning)
            allow_none = True

        if isinstance(branchspec, tuple):
            if debug > 1:
                message = f"{self.__class__.__name__}().find_object_branches(branchspec='{branchspec}') was called"
                logger.info(message)

            if branchspec == ():
                error = "find_object_branches(): branchspec must not be empty"
                logger.error(error)
                raise ValueError(error)

        else:
            error = "find_object_branches(): Please enclose the branchspec regular expressions in a Python tuple"
            logger.error(error)
            raise ValueError(error)

        @logger.catch(reraise=True)
        def list_matching_children(
            parent_obj,
            childspec,
            regex_flags,
            allow_none=True,
            debug=0,
        ):
            # I'm not using parent_obj.re_search_children() because
            # re_search_children() doesn't return None for no match...

            # FIXME: Insert debugging here...
            # print("PARENT "+str(parent_obj))

            # As of version 1.6.16, allow_none must always be True...
            if allow_none is not True:
                raise ValueError("allow_none parameter must always be True.")

            if debug > 1:
                msg = """Calling list_matching_children(
    parent_obj=%s,
    childspec=%s,
    regex_flags=%s,
    allow_none=%s,
    debug=%s,
    )""" % (
                    parent_obj,
                    childspec,
                    regex_flags,
                    allow_none,
                    debug,
                )
                logger.info(msg)

            # Get the child objects from parent objects
            if parent_obj is None:
                children = self._find_line_OBJ(
                    linespec=childspec,
                    exactmatch=False,
                )
            else:
                children = parent_obj.children

            # Find all child objects which match childspec...
            segment_list = [
                cobj
                for cobj in children
                if re.search(childspec, cobj.text, regex_flags)
            ]
            # Return [None] if no children matched...
            if len(segment_list) == 0:
                segment_list = [None]

            # FIXME: Insert debugging here...
            # print("    SEGMENTS "+str(segment_list))
            if debug > 1:
                logger.info(
                    "    list_matching_children() returns segment_list=%s"
                    % segment_list,
                )
            return segment_list

        branches = []
        # iterate over the regular expressions in branchspec
        for idx, childspec in enumerate(branchspec):
            # FIXME: Insert debugging here...
            # print("CHILDSPEC "+childspec)
            if idx == 0:
                # Get matching 'root' objects from the config
                next_kids = list_matching_children(
                    parent_obj=None,
                    childspec=childspec,
                    regex_flags=regex_flags,
                    allow_none=True,
                    debug=debug,
                )
                # Start growing branches from the segments we received...
                branches = [[kid] for kid in next_kids]

            else:
                new_branches = []
                for branch in branches:
                    # Extend existing branches into the new_branches
                    if branch[-1] is not None:
                        # Find children to extend the family branch...
                        next_kids = list_matching_children(
                            parent_obj=branch[-1],
                            childspec=childspec,
                            regex_flags=regex_flags,
                            allow_none=True,
                            debug=debug,
                        )

                        for kid in next_kids:
                            # Fork off a new branch and add each matching kid...
                            # Use copy.copy() for a "shallow copy" of branch:
                            #    https://realpython.com/copying-python-objects/
                            tmp = copy.copy(branch)
                            tmp.append(kid)
                            new_branches.append(tmp)
                    else:
                        branch.append(None)
                        new_branches.append(branch)

                # Ensure we have the most recent branches...
                branches = new_branches

        branches = new_branches

        # If regex_groups is True, assign regexp matches to the return matrix.
        if regex_groups is True:
            return_matrix = []
            # branchspec = (r"^interfaces", r"\s+(\S+)", r"\s+(unit\s+\d+)", r"family\s+(inet)", r"address\s+(\S+)")
            # for idx_matrix, row in enumerate(self.find_object_branches(branchspec)):
            for _, row in enumerate(branches):
                if not isinstance(row, Sequence):
                    raise RequirementFailure()

                # Before we check regex capture groups, allocate an "empty return_row"
                #   of the correct length...
                return_row = [(None,)] * len(branchspec)

                # Populate the return_row below...
                #     return_row will be appended to return_matrix...
                for idx, element in enumerate(row):
                    if element is None:
                        return_row[idx] = (None,)

                    else:
                        regex_result = re.search(branchspec[idx], element.text)
                        if regex_result is not None:
                            # Save all the regex capture groups in matched_capture...
                            matched_capture = regex_result.groups()
                            if len(matched_capture) == 0:
                                # If the branchspec groups() matches are a
                                # zero-length tuple, populate this return_row
                                # with the whole element's text
                                return_row[idx] = (element.text,)
                            else:
                                # In this case, we found regex capture groups
                                return_row[idx] = matched_capture
                        else:
                            # No regex capture groups b/c of no regex match...
                            return_row[idx] = (None,)

                return_matrix.append(return_row)

            branches = return_matrix

        # We could have lost or created an extra branch if these aren't the
        # same length
        return branches

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_interface_objects(self, intfspec, exactmatch=True):
        """Find all :class:`~cisco.IOSCfgLine` or :class:`~models_cisco.NXOSCfgLine` objects whose text is an abbreviation for ``intfspec`` and return the objects in a python list.

        Notes
        -----
        The configuration *must* be parsed with ``factory=True`` to use this method.

        Parameters
        ----------
        intfspec : str
            A string which is the abbreviation (or full name) of the interface.
        exactmatch : bool
            Defaults to True; when True, this option requires ``intfspec`` match the whole interface name and number.

        Returns
        -------
        list
            A list of matching :class:`~ciscoconfparse.IOSIntfLine` objects

        Examples
        --------
        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial1/1',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config, factory=True)
        >>>
        >>> parse.find_interface_objects('Se 1/0')
        [<IOSIntfLine # 1 'Serial1/0' info: '1.1.1.1/30'>]
        >>>

        """
        if self.factory is not True:
            err_text = "find_interface_objects() must be" " called with 'factory=True'"
            logger.error(err_text)
            raise ValueError(err_text)

        retval = list()
        if self.syntax not in ALL_BRACE_SYNTAX:
            if exactmatch is True:
                for obj in self.find_objects("^interface"):
                    if intfspec.lower() in obj.abbvs:
                        retval.append(obj)
                        break  # Only break if exactmatch is True
            else:
                err_text = "This method requires exactmatch set True"
                logger.error(err_text)
                raise NotImplementedError(err_text)
        # TODO: implement ASAConfigLine.abbvs and others
        else:
            err_text = "This method requires exactmatch set True"
            logger.error(err_text)
            raise NotImplementedError(err_text)

        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects_dna(self, dnaspec, exactmatch=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text matches ``dnaspec`` and return the :class:`~models_cisco.IOSCfgLine` objects in a python list.

        Notes
        -----
        :func:`~ciscoconfparse.CiscoConfParse.find_objects_dna` requires the configuration to be parsed with factory=True.

        Parameters
        ----------
        dnaspec : str
            A string or python regular expression, which should be matched.  This argument will be used to match dna attribute of the object
        exactmatch : bool
            Defaults to False.  When set True, this option requires ``dnaspec`` match the whole configuration line, instead of a portion of the configuration line.

        Returns
        -------
        list
            A list of matching :class:`~ciscoconfparse.IOSCfgLine` objects

        Examples
        --------
        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'hostname MyRouterHostname',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config, factory=True, syntax='ios')
        >>>
        >>> obj_list = parse.find_objects_dna(r'Hostname')
        >>> obj_list
        [<IOSHostnameLine # 1 'MyRouterHostname'>]
        >>>
        >>> # The IOSHostnameLine object has a hostname attribute
        >>> obj_list[0].hostname
        'MyRouterHostname'
        """
        if self.debug > 1:
            method_name = inspect.currentframe().f_code.co_name
            message = f"METHOD {self.__class__.__name__}().{method_name}(dnaspec='{dnaspec}') was called"
            logger.info(message)

        if self.ConfigObjs is None:
            # ConfigObjs should be a list, tuple or Sequence
            err_text = (
                "CiscoConfParse().ConfigObjs should be a list of "
                "config lines, but it's not initialized."
            )
            logger.error(err_text)
            raise ValueError(err_text)

        if self.factory is False:
            err_text = "find_objects_dna() must be called with 'factory=True'"
            logger.error(err_text)
            raise ValueError(err_text)

        if exactmatch is False:
            # Return objects whose text attribute matches linespec
            linespec_re = re.compile(dnaspec)

        elif exactmatch is True:
            # Return objects whose text attribute matches linespec exactly
            linespec_re = re.compile("^{}$".format(dnaspec))

        return list(
            filter(lambda obj: linespec_re.search(obj.dna), self.ConfigObjs),
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text matches ``linespec`` and return the :class:`~models_cisco.IOSCfgLine` objects in a python list.  :func:`~ciscoconfparse.CiscoConfParse.find_objects` is similar to :func:`~ciscoconfparse.CiscoConfParse.find_lines`; however, the former returns a list of :class:`~models_cisco.IOSCfgLine` objects, while the latter returns a list of text configuration statements.  Going forward, I strongly encourage people to start using :func:`~ciscoconfparse.CiscoConfParse.find_objects` instead of :func:`~ciscoconfparse.CiscoConfParse.find_lines`.

        Parameters
        ----------
        linespec : str
            A string or python regular expression, which should be matched
        exactmatch : bool
            Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.
        ignore_ws : bool
            boolean that controls whether whitespace is ignored.  Default is False.

        Returns
        -------
        list
            A list of matching :class:`~ciscoconfparse.IOSCfgLine` objects

        Examples
        --------
        This example illustrates the difference between
        :func:`~ciscoconfparse.CiscoConfParse.find_objects` and
        :func:`~ciscoconfparse.CiscoConfParse.find_lines`.
        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial1/1',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>>
        >>> parse.find_objects(r'^interface')
        [<IOSCfgLine # 1 'interface Serial1/0'>, <IOSCfgLine # 4 'interface Serial1/1'>]
        >>>
        >>> parse.find_lines(r'^interface')
        ['interface Serial1/0', 'interface Serial1/1']
        >>>

        """
        if self.debug > 0:
            logger.info(
                "find_objects('%s', exactmatch=%s) was called" % (linespec, exactmatch),
            )

        if ignore_ws:
            linespec = build_space_tolerant_regex(linespec)
        return self._find_line_OBJ(linespec, exactmatch)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """This method is the equivalent of a simple configuration grep (Case-sensitive).

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        exactmatch : bool
            Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.
        ignore_ws : bool
            boolean that controls whether whitespace is ignored.  Default is False.

        Returns
        -------
        list
            A list of matching configuration lines
        """
        if ignore_ws:
            linespec = build_space_tolerant_regex(linespec)

        if exactmatch is False:
            # Return the lines in self.ioscfg, which match linespec
            return list(filter(re.compile(linespec).search, self.ioscfg))
        else:
            # Return the lines in self.ioscfg, which match (exactly) linespec
            return list(
                filter(re.compile("^%s$" % linespec).search, self.ioscfg),
            )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects_w_child(self, parentspec, childspec, ignore_ws=False, recurse=False):
        """
        Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be
        returned.

        This is an alias for :func:`~ciscoconfparse.CiscoConfParse.find_parent_objects`

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects
        """
        return self.find_parent_objects(parentspec, childspec, ignore_ws=ignore_ws, recurse=recurse, escape_chars=False)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_parent_objects(
        self,
        parentspec,
        childspec=None,
        ignore_ws=False,
        recurse=False,
        escape_chars=False,
    ):
        """
        Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be
        returned.

        Parameters
        ----------
        parentspec : str or list
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)
        escape_chars : bool
            Set True if you want to escape characters before searching

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects

        Examples
        --------
        This example uses :func:`~ciscoconfparse.find_parent_objects()` to
        find all ports that are members of access vlan 300 in following
        config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/3
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/2
           interface FastEthernet0/3

        We do this by quering `find_objects_w_child()`; we set our
        parent as `^interface` and set the child as `switchport access
        vlan 300`.

        .. code-block:: python
           :emphasize-lines: 20

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet0/1',
           ...           ' switchport access vlan 532',
           ...           ' spanning-tree vlan 532 cost 3',
           ...           '!',
           ...           'interface FastEthernet0/2',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...           'interface FastEthernet0/3',
           ...           ' duplex full',
           ...           ' speed 100',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_parent_objects('^interface',
           ...     'switchport access vlan 300')
           ...
           [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
           >>>
        """
        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, str):
            pass
        elif isinstance(parentspec, (list, tuple)):
            if len(parentspec) > 1:
                _results = set()
                _parentspec = parentspec[0]
                for _childspec in parentspec[1:]:
                    _values = self.find_parent_objects(
                        _parentspec,
                        _childspec,
                        ignore_ws=ignore_ws,
                        recurse=recurse,
                        escape_chars=escape_chars
                    )
                    if len(_values) == 0:
                        ######################################################
                        # If any _childspec fails to match, we will hit this
                        # condition when that failure happens.
                        ######################################################
                        return []
                    else:
                        # Add the parent of this set of values
                        _ = [_results.add(ii) for ii in _values]
                # Sort the de-duplicated results
                return sorted(_results)
            else:
                error = f"`parentspec` {type(parentspec)} must be longer than one element."
                logger.error(error)
                raise InvalidParameters(error)
        else:
            error = f"Received unexpected `parentspec` {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)

        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ###################################################################
            # Escape regex to avoid embedded parenthesis problems
            ###################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        return list(
            filter(
                lambda x: x.re_search_children(childspec, recurse=recurse),
                self.find_objects(parentspec),
            ),
        )

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_objects_w_all_children(
        self,
        parentspec,
        childspec,
        ignore_ws=False,
        recurse=False,
    ):
        """Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match all elements
        in ``childspec``.  Only the parent :class:`~models_cisco.IOSCfgLine`
        objects will be returned.

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : list
            A list of text regular expressions to be matched among the children
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            Set True if you want to search all children (children, grand children, great grand children, etc...)

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects

        Examples
        --------
        This example uses :func:`~ciscoconfparse.find_objects_w_child()` to
        find all ports that are members of access vlan 300 in following
        config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/2
           interface FastEthernet0/3

        We do this by quering `find_objects_w_all_children()`; we set our
        parent as `^interface` and set the childspec as
        ['switchport access vlan 300', 'spanning-tree portfast'].

        .. code-block:: python
           :emphasize-lines: 19

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet0/1',
           ...           ' switchport access vlan 532',
           ...           ' spanning-tree vlan 532 cost 3',
           ...           '!',
           ...           'interface FastEthernet0/2',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...           'interface FastEthernet0/3',
           ...           ' duplex full',
           ...           ' speed 100',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_objects_w_all_children('^interface',
           ...     ['switchport access vlan 300', 'spanning-tree portfast'])
           ...
           [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
           >>>
        """

        # childspec must be an instance of collections.abc.Sequence()
        enforce_valid_types(
            childspec,
            (Sequence,),
            "childspec parameter must be an instance of collections.abc.Sequence().",
        )

        retval = []
        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            # childspec = map(build_space_tolerant_regex, childspec)
            childspec = [build_space_tolerant_regex(ii) for ii in childspec]

        for parentobj in self.find_objects(parentspec):
            results = set()
            for child_cfg in childspec:
                results.add(
                    bool(
                        parentobj.re_search_children(
                            child_cfg,
                            recurse=recurse,
                        ),
                    ),
                )
            if False in results:
                continue
            retval.append(parentobj)

        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_objects_w_missing_children(
        self,
        parentspec,
        childspec,
        ignore_ws=False,
    ):
        """Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children do not match
        all elements in ``childspec``.  Only the parent
        :class:`~models_cisco.IOSCfgLine` objects will be returned.

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : list
            A list of text regular expressions to be matched among the children
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching parent :class:`~models_cisco.IOSCfgLine` objects"""

        enforce_valid_types(
            childspec,
            (Sequence,),
            "childspec parameter must be an instance of collections.abc.Sequence().",
        )

        retval = []
        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            if isinstance(childspec, Sequence):
                childspec = [build_space_tolerant_regex(ii) for ii in childspec]

            else:
                err_txt = "Cannot call build_space_tolerant_regex()" " on childspec"
                raise ValueError(err_txt)

        for parentobj in self.find_objects(parentspec):
            results = set()
            for child_cfg in childspec:
                results.add(bool(parentobj.re_search_children(child_cfg)))
            if False in results:
                retval.append(parentobj)
            else:
                continue

        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_objects_wo_child(self, parentspec, childspec, ignore_ws=False, recurse=False):
        r"""Return a list of parent :class:`~models_cisco.IOSCfgLine` objects, which matched the ``parentspec`` and whose children did not match ``childspec``.  Only the parent :class:`~models_cisco.IOSCfgLine` objects will be returned.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching parent configuration lines
        """
        return self.find_parent_objects_wo_child(parentspec, childspec, ignore_ws=ignore_ws, recurse=recurse)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_parent_objects_wo_child(self, parentspec, childspec, ignore_ws=False, recurse=False, escape_chars=False):
        r"""Return a list of parent :class:`~models_cisco.IOSCfgLine` objects, which matched the ``parentspec`` and whose children did not match ``childspec``.  Only the parent :class:`~models_cisco.IOSCfgLine` objects will be returned.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

        Parameters
        ----------
        parentspec : str
            Text regular expression for the :class:`~models_cisco.IOSCfgLine` object to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        recurse : bool
            boolean that controls whether to recurse through children of children
        escape_chars : bool
            boolean that controls whether to escape characters before searching

        Returns
        -------
        list
            A list of matching parent configuration lines

        Examples
        --------
        This example finds all ports that are autonegotiating in the following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            spanning-tree vlan 532 cost 3
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
           !

        The following interfaces should be returned:

        .. code::

           interface FastEthernet0/1
           interface FastEthernet0/2

        We do this by quering `find_parent_objects_wo_child()`; we set our
        parent as `^interface` and set the child as `speed\s\d+` (a
        regular-expression which matches the word 'speed' followed by
        an integer).

        .. code-block:: python
           :emphasize-lines: 19

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet0/1',
           ...           ' switchport access vlan 532',
           ...           ' spanning-tree vlan 532 cost 3',
           ...           '!',
           ...           'interface FastEthernet0/2',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...           'interface FastEthernet0/3',
           ...           ' duplex full',
           ...           ' speed 100',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_parent_objects_wo_child(r'^interface', r'speed\s\d+')
           [<IOSCfgLine # 1 'interface FastEthernet0/1'>, <IOSCfgLine # 5 'interface FastEthernet0/2'>]
           >>>
        """

        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, (list, tuple)):
            ##################################################################
            # Catch unsupported parentspec type here
            ##################################################################
            error = f"find_parents_objects_wo_child() `parentspec` does not support a {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)
        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ###################################################################
            # Escape regex to avoid embedded parenthesis problems
            ###################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        return [
            obj
            for obj in self.find_objects(parentspec)
            if not obj.re_search_children(childspec, recurse=recurse)
        ]


    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_objects_w_parents(self, parentspec, childspec, ignore_ws=False):
        r"""Parse through the children of all parents matching parentspec,
        and return a list of child objects, which matched the childspec.

        This is just an alias for `find_child_objects()`

        Parameters
        ----------
        parentspec : str
            Text regular expression for the line to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching child objects
    """
        return self.find_child_objects(parentspec, childspec, ignore_ws=ignore_ws, recurse=False)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_child_objects(
            self,
            parentspec,
            childspec=None,
            ignore_ws=False,
            recurse=False,
            escape_chars=False
    ):
        r"""Parse through the children of all parents matching parentspec,
        and return a list of child objects, which matched the childspec.

        Parameters
        ----------
        parentspec : str or list
            Text regular expression for the line to be matched; this must match the parent's line
        childspec : str
            Text regular expression for the line to be matched; this must match the child's line
        ignore_ws : bool
            boolean that controls whether whitespace is ignored
        escape_chars : bool
            boolean that controls whether characters are escaped before searching

        Returns
        -------
        list
            A list of matching child objects

        Examples
        --------
        This example finds the object for "ge-0/0/0" under "interfaces" in the
        following config...

        .. code::

            interfaces
                ge-0/0/0
                    unit 0
                        family ethernet-switching
                            port-mode access
                            vlan
                                members VLAN_FOO
                ge-0/0/1
                    unit 0
                        family ethernet-switching
                            port-mode trunk
                            vlan
                                members all
                            native-vlan-id 1
                vlan
                    unit 0
                        family inet
                            address 172.16.15.5/22


        The following object should be returned:

        .. code::

            <IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>

        We do this by quering `find_child_objects()`; we set our
        parent as `^\s*interface` and set the child as
        `^\s+ge-0/0/1`.

        .. code-block:: python
           :emphasize-lines: 22,23

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['interfaces',
           ...           '    ge-0/0/0',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode access',
           ...           '                vlan',
           ...           '                    members VLAN_FOO',
           ...           '    ge-0/0/1',
           ...           '        unit 0',
           ...           '            family ethernet-switching',
           ...           '                port-mode trunk',
           ...           '                vlan',
           ...           '                    members all',
           ...           '                native-vlan-id 1',
           ...           '    vlan',
           ...           '        unit 0',
           ...           '            family inet',
           ...           '                address 172.16.15.5/22',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_child_objects('^\s*interfaces',
           ... r'\s+ge-0/0/1')
           [<IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>]
           >>>

        """
        if isinstance(parentspec, BaseCfgLine):
            parentspec = parentspec.text
        elif isinstance(parentspec, str):
            pass
        elif isinstance(parentspec, (list, tuple)):
            _parentspec_len = len(parentspec)
            if _parentspec_len > 1:
                _results = set()
                _parentspec = parentspec[0]
                for _idx, _childspec in enumerate(parentspec[1:]):
                    _values = self.find_child_objects(
                        _parentspec,
                        _childspec,
                        ignore_ws=ignore_ws,
                        recurse=recurse,
                        escape_chars=escape_chars
                    )
                    if len(_values) == 0:
                        ######################################################
                        # If any _childspec fails to match, we will hit this
                        # condition when that failure happens.
                        ######################################################
                        return []
                    elif _idx == _parentspec_len - 2:
                        ######################################################
                        # Add the matching last child of this set of values
                        # '_parentspec_len - 2' was used intentionally
                        ######################################################
                        _ = [_results.add(ii) for ii in _values]
                # Sort the de-duplicated results
                return sorted(_results)
            else:
                error = f"`parentspec` {type(parentspec)} must be longer than one element."
                logger.error(error)
                raise InvalidParameters(error)
        else:
            error = f"Received unexpected `parentspec` {type(parentspec)}"
            logger.error(error)
            raise InvalidParameters(error)

        if isinstance(childspec, BaseCfgLine):
            parentspec = childspec.text

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        if escape_chars is True:
            ######################################################################
            # Escape regex to avoid embedded parenthesis problems
            ######################################################################
            parentspec = re.escape(parentspec)
            childspec = re.escape(childspec)

        retval = set()
        parents = self.find_objects(parentspec)
        if recurse is False:
            for parent in parents:
                ##############################################################
                # If recurse is False, only search direct children
                ##############################################################
                for child in parent.children:
                    if child.re_match(rf"({childspec})", default=False):
                        retval.add(child)
        else:
            for parent in parents:
                ##############################################################
                # If recurse is True, search all children including children
                #    of the children
                ##############################################################
                for child in parent.all_children:
                    if child.re_match(rf"({childspec})", default=False):
                        retval.add(child)

        return sorted(retval)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def find_lineage(self, linespec, exactmatch=False):
        """
        Iterate through to the oldest ancestor of this object, and return
        a list of all ancestors / children in the direct line.  Cousins or
        aunts / uncles are *not* returned.  Note, all children
        of this object are returned.

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        exactmatch : bool
            Defaults to False; when True, this option requires ``linespec`` the whole line (not merely a portion of the line)

        Returns
        -------
        list
            A list of matching objects
        """
        tmp = self.find_objects(linespec, exactmatch=exactmatch)
        if len(tmp) > 1:
            err_txt = "linespec must be unique"
            logger.error(err_txt)
            raise ValueError(err_txt)

        return [obj.text for obj in tmp[0].lineage]

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def has_line_with(self, linespec):
        """Return True if `linespec` is contained in the configuration."""
        # https://stackoverflow.com/a/16097112/667301
        matching_conftext = list(
            filter(
                partial(is_not, None),
                [re.search(linespec, ii) for ii in self.ioscfg],
            ),
        )
        return bool(matching_conftext)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def delete_lines(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all :class:`~models_cisco.IOSCfgLine` objects whose text
        matches linespec, and delete the object"""
        objs = self.find_objects(linespec, exactmatch, ignore_ws)
        for obj in reversed(objs):
            # NOTE - 'del self.ConfigObjs...' was replaced in version 1.5.30
            #    with a simpler approach
            # del self.ConfigObjs[obj.linenum]
            obj.delete()

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def prepend_line(self, linespec):
        """Unconditionally insert an :class:`~models_cisco.IOSCfgLine` object
        for ``linespec`` (a text line) at the top of the configuration"""
        self.ConfigObjs.insert(0, linespec)
        return self.ConfigObjs[0]

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def append_line(self, linespec):
        """Unconditionally insert ``linespec`` (a text line) at the end of the
        configuration

        Parameters
        ----------
        linespec : str
            Text IOS configuration line

        Returns
        -------
        The parsed :class:`~models_cisco.IOSCfgLine` object instance

        """
        if isinstance(linespec, str) and linespec.strip() == "" and self.ignore_blank_lines is True:
            error = "Cannot insert a blank line if `ignore_blank_lines` is True"
            logger.error(error)
            raise InvalidParameters(error)
        elif isinstance(linespec, (int, str, float)):
            self.ConfigObjs.append(IOSCfgLine(str(linespec)))
        elif isinstance(linespec, IOSCfgLine):
            self.ConfigObjs.append(linespec)
        else:
            error = f"Cannot append {type(linespec)}"
            logger.critical(error)
            raise InvalidParameters(error)
        self.atomic()
        return self.ConfigObjs[-1]

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def replace_lines(
        self,
        linespec,
        replacestr,
        excludespec=None,
        exactmatch=False,
        atomic=False,
    ):
        """This method is a text search and replace (Case-sensitive).  You can
        optionally exclude lines from replacement by including a string (or
        compiled regular expression) in `excludespec`.

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        replacestr : str
            Text used to replace strings matching linespec
        excludespec : str
            Text regular expression used to reject lines, which would otherwise be replaced.  Default value of ``excludespec`` is None, which means nothing is excluded
        exactmatch : bool
            boolean that controls whether partial matches are valid
        atomic : bool
            boolean that controls whether the config is reparsed after replacement (default False)

        Returns
        -------
        list
            A list of changed configuration lines

        Examples
        --------
        This example finds statements with `EXTERNAL_CBWFQ` in following
        config, and replaces all matching lines (in-place) with `EXTERNAL_QOS`.
        For the purposes of this example, let's assume that we do *not* want
        to make changes to any descriptions on the policy.

        .. code::

           !
           policy-map EXTERNAL_CBWFQ
            description implement an EXTERNAL_CBWFQ policy
            class IP_PREC_HIGH
             priority percent 10
             police cir percent 10
               conform-action transmit
               exceed-action drop
            class IP_PREC_MEDIUM
             bandwidth percent 50
             queue-limit 100
            class class-default
             bandwidth percent 40
             queue-limit 100
           policy-map SHAPE_HEIR
            class ALL
             shape average 630000
             service-policy EXTERNAL_CBWFQ
           !

        We do this by calling `replace_lines(linespec='EXTERNAL_CBWFQ',
        replacestr='EXTERNAL_QOS', excludespec='description')`...

        .. code-block:: python
           :emphasize-lines: 23

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'policy-map EXTERNAL_CBWFQ',
           ...           ' description implement an EXTERNAL_CBWFQ policy',
           ...           ' class IP_PREC_HIGH',
           ...           '  priority percent 10',
           ...           '  police cir percent 10',
           ...           '    conform-action transmit',
           ...           '    exceed-action drop',
           ...           ' class IP_PREC_MEDIUM',
           ...           '  bandwidth percent 50',
           ...           '  queue-limit 100',
           ...           ' class class-default',
           ...           '  bandwidth percent 40',
           ...           '  queue-limit 100',
           ...           'policy-map SHAPE_HEIR',
           ...           ' class ALL',
           ...           '  shape average 630000',
           ...           '  service-policy EXTERNAL_CBWFQ',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.replace_lines('EXTERNAL_CBWFQ', 'EXTERNAL_QOS', 'description')
           ['policy-map EXTERNAL_QOS', '  service-policy EXTERNAL_QOS']
           >>>
           >>> # Now when we call `p.find_blocks('policy-map EXTERNAL_QOS')`, we get the
           >>> # changed configuration, which has the replacements except on the
           >>> # policy-map's description.
           >>> p.find_blocks('EXTERNAL_QOS')
           ['policy-map EXTERNAL_QOS', ' description implement an EXTERNAL_CBWFQ policy', ' class IP_PREC_HIGH', ' class IP_PREC_MEDIUM', ' class class-default', 'policy-map SHAPE_HEIR', ' class ALL', '  shape average 630000', '  service-policy EXTERNAL_QOS']
           >>>

        """
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        if excludespec:
            excludespec_re = re.compile(excludespec)

        for obj in self._find_line_OBJ(linespec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(obj.text):
                # Exclude replacements on lines which match excludespec
                continue
            retval.append(obj.re_sub(linespec, replacestr))

        if self.factory and atomic:
            self.ConfigObjs._list = self.ConfigObjs.bootstrap_obj_init_ng(self.ioscfg)

        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def replace_children(
        self,
        parentspec,
        childspec,
        replacestr,
        excludespec=None,
        exactmatch=False,
        atomic=False,
    ):
        r"""Replace lines matching `childspec` within the `parentspec`'s
        immediate children.

        Parameters
        ----------
        parentspec : str
            Text IOS configuration line
        childspec : str
            Text IOS configuration line, or regular expression
        replacestr : str
            Text IOS configuration, which should replace text matching ``childspec``.
        excludespec : str
            A regular expression, which indicates ``childspec`` lines which *must* be skipped.  If ``excludespec`` is None, no lines will be excluded.
        exactmatch : bool
            Defaults to False.  When set True, this option requires ``linespec`` match the whole configuration line, instead of a portion of the configuration line.

        Returns
        -------
        list
            A list of changed :class:`~models_cisco.IOSCfgLine` instances.

        Examples
        --------
        `replace_children()` just searches through a parent's child lines and
        replaces anything matching `childspec` with `replacestr`.  This method
        is one of my favorites for quick and dirty standardization efforts if
        you *know* the commands are already there (just set inconsistently).

        One very common use case is rewriting all vlan access numbers in a
        configuration.  The following example sets
        `storm-control broadcast level 0.5` on all GigabitEthernet ports.

        .. code-block:: python
           :emphasize-lines: 13

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface GigabitEthernet1/1',
           ...           ' description {I have a broken storm-control config}',
           ...           ' switchport',
           ...           ' switchport mode access',
           ...           ' switchport access vlan 50',
           ...           ' switchport nonegotiate',
           ...           ' storm-control broadcast level 0.2',
           ...           '!'
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.replace_children(r'^interface\sGigabit', r'broadcast\slevel\s\S+', 'broadcast level 0.5')
           [' storm-control broadcast level 0.5']
           >>>

        One thing to remember about the last example, you *cannot* use a
        regular expression in `replacestr`; just use a normal python string.
        """
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        childspec_re = re.compile(childspec)
        if excludespec:
            excludespec_re = re.compile(excludespec)
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in pobj.children:
                if excludespec and excludespec_re.search(cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif childspec_re.search(cobj.text):
                    retval.append(cobj.re_sub(childspec, replacestr))
                else:
                    pass

        if self.factory and atomic:
            self.ConfigObjs._list = self.ConfigObjs.bootstrap_obj_init_ng(self.ioscfg)
        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def replace_all_children(
        self,
        parentspec,
        childspec,
        replacestr,
        excludespec=None,
        exactmatch=False,
        atomic=False,
    ):
        """Replace lines matching `childspec` within all children (recursive) of lines whilch match `parentspec`"""
        retval = list()
        ## Since we are replacing text, we *must* operate on ConfigObjs
        childspec_re = re.compile(childspec)
        if excludespec:
            excludespec_re = re.compile(excludespec)
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and excludespec_re.search(pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in self._find_all_child_OBJ(pobj):
                if excludespec and excludespec_re.search(cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif childspec_re.search(cobj.text):
                    retval.append(cobj.re_sub(childspec, replacestr))
                else:
                    pass

        if self.factory and atomic:
            self.ConfigObjs._list = self.ConfigObjs.bootstrap_obj_init_ng(self.ioscfg)

        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def re_search_children(self, regexspec, recurse=False):
        """Use ``regexspec`` to search for root parents in the config with text matching regex.  If `recurse` is False, only root parent objects are returned.  A list of matching objects is returned.

        This method is very similar to :func:`~ciscoconfparse.CiscoConfParse.find_objects` (when `recurse` is True); however it was written in response to the use-case described in `Github Issue #156 <https://github.com/mpenning/ciscoconfparse/issues/156>`_.

        Parameters
        ----------
        regexspec : str
            A string or python regular expression, which should be matched.
        recurse : bool
            Set True if you want to search all objects, and not just the root parents

        Returns
        -------
        list
            A list of matching :class:`~models_cisco.IOSCfgLine` objects which matched.  If there is no match, an empty :py:func:`list` is returned.

        """
        ## I implemented this method in response to Github issue #156
        if recurse is False:
            # Only return the matching oldest ancestor objects...
            return [obj for obj in self.find_objects(regexspec) if (obj.parent is obj)]
        else:
            # Return any matching object
            return [obj for obj in self.find_objects(regexspec)]

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def re_match_iter_typed(
        self,
        regexspec,
        group=1,
        result_type=str,
        default="",
        untyped_default=False,
    ):
        r"""Use ``regexspec`` to search the root parents in the config
        and return the contents of the regular expression group, at the
        integer ``group`` index, cast as ``result_type``; if there is no
        match, ``default`` is returned.

        Note
        ----
        Only the first regex match is returned.

        Parameters
        ----------
        regexspec : str
            A string or python compiled regular expression, which should be matched.  This regular expression should contain parenthesis, which bound a match group.
        group : int
            An integer which specifies the desired regex group to be returned.  ``group`` defaults to 1.
        result_type : type
            A type (typically one of: ``str``, ``int``, ``float``, or :class:`~ccp_util.IPv4Obj`).         All returned values are cast as ``result_type``, which defaults to ``str``.
        default : any
            The default value to be returned, if there is no match.  The default is an empty string.
        untyped_default : bool
            Set True if you don't want the default value to be typed

        Returns
        -------
        ``result_type``
            The text matched by the regular expression group; if there is no match, ``default`` is returned.  All values are cast as ``result_type``.  The default result_type is `str`.


        Examples
        --------
        This example illustrates how you can use
        :func:`~ciscoconfparse.re_match_iter_typed` to get the
        first interface name listed in the config.

        >>> import re
        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial2/0',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse.re_match_iter_typed(r'interface\s(\S+)')
        'Serial1/0'
        >>>

        The following example retrieves the hostname from the configuration

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     '!',
        ...     'hostname DEN-EDGE-01',
        ...     '!',
        ...     'interface Serial1/0',
        ...     ' ip address 1.1.1.1 255.255.255.252',
        ...     '!',
        ...     'interface Serial2/0',
        ...     ' ip address 1.1.1.5 255.255.255.252',
        ...     '!',
        ...     ]
        >>> parse = CiscoConfParse(config=config)
        >>> parse.re_match_iter_typed(r'^hostname\s+(\S+)')
        'DEN-EDGE-01'
        >>>

        """
        ## iterate through root objects, and return the matching value
        ##  (cast as result_type) from the first object.text that matches regex

        # if (default is True):
        ## Not using self.re_match_iter_typed(default=True), because I want
        ##   to be sure I build the correct API for match=False
        ##
        ## Ref IOSIntfLine.has_dtp for an example of how to code around
        ##   this while I build the API
        #    raise NotImplementedError

        for cobj in self.ConfigObjs:
            # Only process parent objects at the root of the tree...
            if cobj.parent is not cobj:
                continue

            mm = re.search(regexspec, cobj.text)
            if mm is not None:
                return result_type(mm.group(group))
        ## Ref Github issue #121
        if untyped_default:
            return default
        else:
            return result_type(default)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _sequence_nonparent_lines(self, a_nonparent_objs, b_nonparent_objs):
        """Assume a_nonparent_objs is the existing config sequence, and
        b_nonparent_objs is the *desired* config sequence

        This method walks b_nonparent_objs, and orders a_nonparent_objs
        the same way (as much as possible)

        This method returns:

        - The reordered list of a_nonparent_objs
        - The reordered list of a_nonparent_lines
        - The reordered list of a_nonparent_linenums
        """
        a_parse = CiscoConfParse(config=[])  # A *new* parse for reordered a lines
        a_lines = list()
        a_linenums = list()

        ## Mark all a objects as not done
        for aobj in a_nonparent_objs:
            aobj.done = False

        for bobj in b_nonparent_objs:
            for aobj in a_nonparent_objs:
                if aobj.text == bobj.text:
                    aobj.done = True
                    a_parse.append_line(aobj.text)

        # Add any missing a_parent_objs + their children...
        for aobj in a_nonparent_objs:
            if aobj.done is False:
                aobj.done = True
                a_parse.append_line(aobj.text)

        a_parse.commit()

        a_nonparents_reordered = a_parse.ConfigObjs
        for aobj in a_nonparents_reordered:
            a_lines.append(aobj.text)
            a_linenums.append(aobj.linenum)

        return a_parse, a_lines, a_linenums

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _sequence_parent_lines(self, a_parent_objs, b_parent_objs):
        """Assume a_parent_objs is the existing config sequence, and
        b_parent_objs is the *desired* config sequence

        This method walks b_parent_objs, and orders a_parent_objs
        the same way (as much as possible)

        This method returns:

        - The reordered list of a_parent_objs
        - The reordered list of a_parent_lines
        - The reordered list of a_parent_linenums
        """
        a_parse = CiscoConfParse(config=[])  # A *new* parse for reordered a lines
        a_lines = list()
        a_linenums = list()

        ## Mark all a objects as not done
        for aobj in a_parent_objs:
            aobj.done = False
            for child in aobj.all_children:
                child.done = False

        ## Walk the b objects by parent, then child and reorder a objects
        for bobj in b_parent_objs:
            for aobj in a_parent_objs:
                if aobj.text == bobj.text:
                    aobj.done = True
                    a_parse.append_line(aobj.text)

                    # Append *matching* children to this aobj in the same order
                    for bchild in bobj.all_children:
                        for achild in aobj.all_children:
                            if achild.done:
                                continue
                            elif achild.geneology_text == bchild.geneology_text:
                                achild.done = True
                                a_parse.append_line(achild.text)

                    # Append *missing* children to this aobj...
                    for achild in aobj.all_children:
                        if achild.done is False:
                            achild.done = True
                            a_parse.append_line(achild.text)

        # Add any missing a_parent_objs + their children...
        for aobj in a_parent_objs:
            if aobj.done is False:
                aobj.done = True
                a_parse.append_line(aobj.text)
                for achild in aobj.all_children:
                    achild.done = True
                    a_parse.append_line(achild.text)

        a_parse.commit()

        a_parents_reordered = a_parse.ConfigObjs
        for aobj in a_parents_reordered:
            a_lines.append(aobj.text)
            a_linenums.append(aobj.linenum)

        return a_parse, a_lines, a_linenums

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def save_as(self, filepath):
        """Save a text copy of the configuration at ``filepath``; this
        method uses the OperatingSystem's native line separators (such as
        ``\\r\\n`` in Windows)."""
        try:
            with open(filepath, "w", encoding=self.encoding) as newconf:
                for line in self.ioscfg:
                    newconf.write(line + "\n")
            return True
        except BaseException as ee:
            logger.error(str(ee))
            raise ee

    ### The methods below are marked SEMI-PRIVATE because they return an object
    ###  or iterable of objects instead of the configuration text itself.

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _find_line_OBJ(self, linespec, exactmatch=False):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""

        if self.ConfigObjs is None:
            err = "ConfigObjs is None. self.ConfigObjs logic failed."
            raise ValueError(err)

        if self.debug >= 2:
            logger.debug(
                "Looking for match of linespec='%s', exactmatch=%s"
                % (linespec, exactmatch),
            )

        ## NOTE TO SELF: do not remove _find_line_OBJ(); used by Cisco employees
        if not exactmatch:
            # Return objects whose text attribute matches linespec
            linespec_re = re.compile(linespec)
        elif exactmatch:
            # Return objects whose text attribute matches linespec exactly
            linespec_re = re.compile("^%s$" % linespec)

        return list(
            filter(lambda obj: linespec_re.search(obj.text), self.ConfigObjs),
        )

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _find_all_child_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a single object and returns a list of
        decendants in all 'children' / 'grandchildren' / etc... after it.
        It should NOT return the children of siblings"""
        # sort the list, and get unique objects
        retval = set(lineobject.children)
        for candidate in lineobject.children:
            if candidate.has_children:
                for child in candidate.children:
                    retval.add(child)
        retval = sorted(retval)
        return retval

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _unique_OBJ(self, objectlist):
        """SEMI-PRIVATE: Returns a list of unique objects (i.e. with no
        duplicates).
        The returned value is sorted by configuration line number
        (lowest first)"""
        retval = set()
        for obj in objectlist:
            retval.add(obj)
        return sorted(retval)

    # This method is on CiscoConfParse()
    @ logger.catch(reraise=True)
    def _objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = []
        unconfdict = {}
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self._unique_OBJ(objectlist):
            if unconfdict.get(obj, None) == "DEFINED":
                retval.append(obj.uncfgtext)
            else:
                retval.append(obj.text)
        return retval


class Diff(object):

    @ logger.catch(reraise=True)
    def __init__(self, hostname=None, old_config=None, new_config=None, syntax='ios'):
        """
        Initialize Diff().

        Parameters
        ----------
        hostname : None
            An empty parameter, which seems to be optional for the diff backend
        old_config : str
            A string containing text configuration statements representing the most-recent config. Default value: `None`. If a filepath is provided, load the configuration from the file.
        new_config : str
            A string containing text configuration statements representing the desired config. Default value: `None`. If a filepath is provided, load the configuration from the file.
        syntax : str
            A string holding the configuration type.  Default: 'ios'.

        Returns
        -------
        :class:`~ciscoconfparse.Diff()`
        """

        ######################################################################
        # Handle hostname
        ######################################################################
        if hostname is not None:
            error = f"hostname='{hostname}' is not supported"
            logger.error(error)

        ######################################################################
        # Handle old_config
        ######################################################################
        if old_config is None:
            old_config = []
        elif isinstance(old_config, str) and len(old_config.splitlines()) == 1 and os.path.isfile(old_config):
            # load the old config from a file as a string...
            old_config = open(old_config).read()
        elif isinstance(old_config, str):
            pass
        elif isinstance(old_config, (list, tuple)):
            old_config = os.linesep.join(old_config)
        else:
            error = f"old_config {type(old_config)} must be a network configuration in a string, or a filepath to the configuration"
            logger.error(error)
            raise ValueError(error)

        ######################################################################
        # Handle new_config
        ######################################################################
        if new_config is None:
            new_config = []
        elif isinstance(new_config, str) and len(new_config.splitlines()) == 1 and os.path.isfile(new_config):
            # load the new config from a file as a list...
            new_config = open(new_config).read().splitlines()
        elif isinstance(new_config, str):
            pass
        elif isinstance(new_config, (list, tuple)):
            new_config = os.linesep.join(new_config)
        else:
            error = f"new_config {type(new_config)} must be a network configuration in a string, or a filepath to the configuration"
            logger.error(error)
            raise ValueError(error)

        ######################################################################
        # Handle syntax
        ######################################################################
        if syntax != 'ios':
            error = f"syntax='{syntax}' is not supported"
            logger.error(error)
            raise NotImplementedError(error)

        ###################################################################
        # For now, we will not use options_ios.yml... see
        #     https://github.com/netdevops/hier_config/blob/master/tests/fixtures/options_ios.yml
        ###################################################################
        # _ represents ios options as a dict... for now we use an empty
        # dict below...
        try:
            _ = yaml.load(open('./options_ios.yml'), Loader=yaml.SafeLoader)
        except FileNotFoundError:
            pass
        # For now, we use {} instead of `options_ios.yml`
        self.host = hier_config.Host('example_hostname', 'ios', {})

        # Old configuration
        self.host.load_running_config(old_config)
        # New configuration
        self.host.load_generated_config(new_config)

    @ logger.catch(reraise=True)
    def diff(self):
        """
        diff() returns the list of required configuration statements to go from the old_config to the new_config
        """
        retval = []
        diff_config = self.host.remediation_config()
        for obj in diff_config.all_children_sorted():
            retval.append(obj.cisco_style_text())
        return retval

    @ logger.catch(reraise=True)
    def rollback(self):
        """
        rollback() returns the list of required configuration statements to rollback from the new_config to the old_config
        """
        retval = []
        rollback_config = self.host.rollback_config()
        for obj in rollback_config.all_children_sorted():
            retval.append(obj.cisco_style_text())
        return retval


class ConfigList(MutableSequence):
    """A custom list to hold :class:`~ccp_abc.BaseCfgLine` objects.  Most people will never need to use this class directly."""
    CiscoConfParse = None
    ccp_ref = None
    comment_delimiter = None
    factory = None
    ignore_blank_lines = None
    syntax = None
    dna = "ConfigList"
    debug = None
    _list = []

    @ logger.catch(reraise=True)
    def __init__(
        self,
        initlist=None,
        comment_delimiter="!",
        debug=0,
        factory=False,
        ignore_blank_lines=True,
        # syntax="__undefined__",
        syntax="ios",
        **kwargs
    ):
        """Initialize the class.

        Parameters
        ----------
        initlist : list
            A list of parsed :class:`~models_cisco.IOSCfgLine` objects
        comment_delimiter : str
            A comment delimiter.  This should only be changed when parsing non-Cisco IOS configurations, which do not use a !  as the comment delimiter.  ``comment`` defaults to '!'
        debug : int
            ``debug`` defaults to 0, and should be kept that way unless you're working on a very tricky config parsing problem.  Debug output is not particularly friendly
        ignore_blank_lines : bool
            ``ignore_blank_lines`` defaults to True; when this is set True, ciscoconfparse ignores blank configuration lines.  You might want to set ``ignore_blank_lines`` to False if you intentionally use blank lines in your configuration (ref: Github Issue #3).

        Returns
        -------
        An instance of an :class:`~ciscoconfparse.ConfigList` object.

        """
        # data = kwargs.get('data', None)
        # comment_delimiter = kwargs.get('comment_delimiter', '!')
        # debug = kwargs.get('debug', False)
        # factory = kwargs.get('factory', False)
        # ignore_blank_lines = kwargs.get('ignore_blank_lines', True)
        # syntax = kwargs.get('syntax', 'ios')
        # CiscoConfParse = kwargs.get('CiscoConfParse', None)

        super().__init__()

        #######################################################################
        # Parse out CiscoConfParse and ccp_ref keywords...
        #     FIXME the CiscoConfParse attribute / parameter should go away
        #     use self.ccp_ref instead of self.CiscoConfParse
        #######################################################################

        # This assert is one of two fixes, intended to catch user error such as
        # the problems that the submitter of Github issue #251 had.
        # CiscoConfParse() could not read his configuration because he submitted
        # a multi-line string...
        #
        # This check will explicitly catch some problems like that...

        # IMPORTANT This check MUST come near the top of ConfigList()...
        if not isinstance(initlist, Sequence):
            raise ValueError

        if syntax not in ALL_VALID_SYNTAX:
            raise RequirementFailure()

        # NOTE a string is a invalid sequence... this guards against bad inputs
        if isinstance(initlist, str):
            error = f"ConfigList(initlist=f`{initlist}`) {type(initlist)} is not valid; `initlist` must be a valid Sequence."
            logger.critical(error)
            raise OSError(error)

        ciscoconfparse_kwarg_val = kwargs.get("CiscoConfParse", None)
        ccp_ref_kwarg_val = kwargs.get("ccp_ref", None)
        if ciscoconfparse_kwarg_val is not None:
            logger.warning(
                "The CiscoConfParse keyword will be deprecated soon.  Please use ccp_ref instead",
            )
        ccp_value = ccp_ref_kwarg_val or ciscoconfparse_kwarg_val

        self.CiscoConfParse = (
            ccp_value  # FIXME - CiscoConfParse attribute should go away soon
        )
        self.ccp_ref = ccp_value
        self.comment_delimiter = comment_delimiter
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.syntax = syntax
        self.dna = "ConfigList"
        self.debug = debug

        # Support input configuration as either a list or a generator instance
        #
        # as of python 3.9, getattr() below is slightly faster than
        #     isinstance(initlist, Sequence)
        self._list = self.bootstrap_obj_init_ng(initlist, debug=debug)

        # Removed this portion of __init__() in 1.7.16...
        if getattr(initlist, "__iter__", False) is not False:
            self._list = self.bootstrap_obj_init_ng(initlist)

        else:
            self._list = []

        if self.debug > 0:
            message = "Create ConfigList() with %i elements" % len(self._list)
            logger.info(message)

        ###
        ### Internal structures
        if syntax == "asa":
            self._RE_NAMES = re.compile(
                r"^\s*name\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)",
            )
            self._RE_OBJNET = re.compile(r"^\s*object-group\s+network\s+(\S+)")
            self._RE_OBJSVC = re.compile(r"^\s*object-group\s+service\s+(\S+)")
            self._RE_OBJACL = re.compile(r"^\s*access-list\s+(\S+)")
            self._network_cache = {}

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __repr__(self):
        return """<ConfigList, syntax='{}', comment='{}', conf={}>""".format(
            self.syntax,
            self.comment_delimiter,
            self._list,
        )

    @ logger.catch(reraise=True)
    def __iter__(self):
        return iter(self._list)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __lt__(self, other):
        return self._list < self.__cast(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __le__(self, other):
        return self._list < self.__cast(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __eq__(self, other):
        return self._list == self.__cast(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __gt__(self, other):
        return self._list > self.__cast(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __ge__(self, other):
        return self._list >= self.__cast(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __cast(self, other):
        return other._list if isinstance(other, ConfigList) else other

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __len__(self):
        return len(self._list)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __getitem__(self, ii):
        if isinstance(ii, slice):
            return self.__class__(self._list[ii])
        else:
            return self._list[ii]

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __setitem__(self, ii, val):
        self._list[ii] = val

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __delitem__(self, ii):
        del self._list[ii]
        #self._bootstrap_from_text()
        self._list = self.bootstrap_obj_init_ng(self.ioscfg, debug=self.debug)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __add__(self, other):
        if isinstance(other, ConfigList):
            return self.__class__(self._list + other._list)
        elif isinstance(other, type(self._list)):
            return self.__class__(self._list + other)
        return self.__class__(self._list + list(other))

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __radd__(self, other):
        if isinstance(other, ConfigList):
            return self.__class__(other._list + self._list)
        elif isinstance(other, type(self._list)):
            return self.__class__(other + self._list)
        return self.__class__(list(other) + self._list)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __iadd__(self, other):
        if isinstance(other, ConfigList):
            self._list += other._list
        elif isinstance(other, type(self._list)):
            self._list += other
        else:
            self._list += list(other)
        return self

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __mul__(self, val):
        return self.__class__(self._list * val)

    __rmul__ = __mul__

    @ logger.catch(reraise=True)
    def __imul__(self, val):
        self._list *= val
        return self

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_list"] = self.__dict__["_list"][:]
        return inst

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __str__(self):
        return self.__repr__()

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __enter__(self):
        # Add support for with statements...
        # FIXME: *with* statements dont work
        yield from self._list

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __exit__(self, *args, **kwargs):
        # FIXME: *with* statements dont work
        self._list[0].confobj.CiscoConfParse.atomic()

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def __getattribute__(self, arg):
        """Call arg on ConfigList() object, and if that fails, call arg from the ccp_ref attribute"""
        # Try a method call on ASAConfigList()

        # Rewrite self.CiscoConfParse to self.ccp_ref
        if arg == "CiscoConfParse":
            arg = "ccp_ref"

        try:
            return object.__getattribute__(self, arg)
        except BaseException:
            calling_function = inspect.stack()[1].function
            caller = inspect.getframeinfo(inspect.stack()[1][0])

            ccp_ref = object.__getattribute__(self, "ccp_ref")
            ccp_method = ccp_ref.__getattribute__(arg)
            message = """{2} doesn't have an attribute named "{3}". {0}() line {1} called `__getattribute__('{4}')`. CiscoConfParse() is making this work with duct tape in __getattribute__().""".format(
                calling_function, caller.lineno, ccp_ref, ccp_method, arg
            )
            logger.warning(message)
            return ccp_method

    # This method is on ConfigList()
    @ junos_unsupported
    @ logger.catch(reraise=True)
    def append(self, val):
        if self.debug >= 1:
            logger.debug("    ConfigList().append(val={}) was called.".format(val))

        self._list.append(val)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def pop(self, ii=-1):
        return self._list.pop(ii)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def remove(self, val):
        self._list.remove(val)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def clear(self):
        self._list.clear()

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def copy(self):
        return self.__class__(self)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def count(self, val):
        return self._list.count(val)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def index(self, val, *args):
        return self._list.index(val, *args)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def reverse(self):
        self._list.reverse()

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def sort(self, _unknown_arg, *args, **kwds):
        self._list.sort(*args, **kwds)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def extend(self, other):
        if isinstance(other, ConfigList):
            self._list.extend(other._list)
        else:
            self._list.extend(other)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def has_line_with(self, linespec):
        # https://stackoverflow.com/a/16097112/667301
        matching_conftext = list(
            filter(
                partial(is_not, None),
                [re.search(linespec, ii.text) for ii in self._list],
            ),
        )
        return bool(matching_conftext)

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def insert_before(self, exist_val=None, new_val=None, atomic=False):
        """
        Insert new_val before all occurances of exist_val.

        Parameters
        ----------
        exist_val : str
            An existing text value.  This may match multiple configuration entries.
        new_val : str
            A new value to be inserted in the configuration.
        atomic : bool
            A boolean that controls whether the config is reparsed after the insertion (default False)

        Returns
        -------
        list
            An ios-style configuration list (indented by stop_width for each configuration level).

        Examples
        --------

        >>> parse = CiscoConfParse(config=["a a", "b b", "c c", "b b"])
        >>> # Insert 'g' before any occurance of 'b'
        >>> retval = parse.insert_before("b b", "X X")
        >>> parse.commit()
        >>> parse.ioscfg
        ... ["a a", "X X", "b b", "c c", "X X", "b b"]
        >>>
        """

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        error = "FATAL CALL: in {} line {} {}(exist_val='{}', new_val='{}')".format(
            calling_filename,
            calling_lineno,
            calling_function,
            exist_val,
            new_val,
        )
        if isinstance(new_val, str) and new_val.strip() == "" and self.ignore_blank_lines is True:
            logger.warning(f"`new_val`=`{new_val}`")
            error = "Cannot insert a blank line if `ignore_blank_lines` is True"
            logger.error(error)
            raise InvalidParameters(error)

        # exist_val MUST be a string
        if isinstance(exist_val, str) is True and exist_val != "":
            pass

        # Matches "IOSCfgLine", "NXOSCfgLine" and "ASACfgLine"... (and others)
        elif isinstance(exist_val, BaseCfgLine):
            exist_val = exist_val.text

        else:
            logger.error(error)
            raise ValueError(error)

        # new_val MUST be a string
        if isinstance(new_val, str) is True:
            pass

        elif isinstance(new_val, BaseCfgLine):
            new_val = new_val.text

        else:
            logger.error(error)
            raise ValueError(error)

        if self.factory is False:
            new_obj = CFGLINE[self.syntax](
                all_lines=self._list,
                line=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.factory is True:
            new_obj = config_line_factory(
                all_lines=self._list,
                line=new_val,
                comment_delimiter=self.comment_delimiter,
                syntax=self.syntax,
            )

        else:
            logger.error(error)
            raise ValueError(error)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx
            for idx, list_obj in enumerate(self._list)
            if re.search(exist_val, list_obj.text)
        ]
        for idx in sorted(all_idx, reverse=True):
            # insert at idx - 0 implements 'insert_before()'...
            self._list.insert(idx, new_obj)

        if atomic:
            # Reparse the whole config as a text list
            #self._bootstrap_from_text()
            self._list = self.bootstrap_obj_init_ng(self.ioscfg)

        else:
            ## Just renumber lines...
            self.reassign_linenums()

    # This method is on ConfigList()
    @ junos_unsupported
    @ logger.catch(reraise=True)
    def insert_after(self, exist_val=None, new_val=None, atomic=False, new_val_indent=-1):
        """
        Insert new_val after all occurances of exist_val.

        Parameters
        ----------
        exist_val : str
            An existing configuration string value (used as the insertion reference point)
        new_val : str
            A new value to be inserted in the configuration.
        atomic : bool
            A boolean that controls whether the config is reparsed after the insertion (default False)
        new_val_indent : int
            The indent for new_val

        Returns
        -------
        list
            An ios-style configuration list (indented by stop_width for each configuration level).

        Examples
        --------

        >>> parse = CiscoConfParse(config=["a a", "b b", "c c", "b b"])
        >>> # Insert 'g' before any occurance of 'b'
        >>> retval = parse.ConfigObjs.insert_after("b b", "X X")
        >>> parse.commit()
        >>> parse.ioscfg
        ... ["a a", "b b", "X X", "c c", "b b", "X X"]
        >>>
        """

        #        inserted_object = False
        #        for obj in self.ccp_ref.find_objects(exist_val):
        #            logger.debug("Inserting '%s' after '%s'" % (new_val, exist_val))
        #            print("IDX", obj.index)
        #            obj.insert_after(new_val)
        #            inserted_object = True
        #        return inserted_object

        calling_fn_index = 1
        calling_filename = inspect.stack()[calling_fn_index].filename
        calling_function = inspect.stack()[calling_fn_index].function
        calling_lineno = inspect.stack()[calling_fn_index].lineno
        err_txt = "FATAL CALL: in {} line {} {}(exist_val='{}', new_val='{}')".format(
            calling_filename,
            calling_lineno,
            calling_function,
            exist_val,
            new_val,
        )
        if isinstance(new_val, str) and new_val.strip() == "" and self.ignore_blank_lines is True:
            logger.warning(f"`new_val`=`{new_val}`")
            error = "Cannot insert a blank line if `ignore_blank_lines` is True"
            logger.error(error)
            raise InvalidParameters(error)

        # exist_val MUST be a string
        if isinstance(exist_val, str) is True and exist_val != "":
            pass

        # Matches "IOSCfgLine", "NXOSCfgLine" and "ASACfgLine"... (and others)
        elif isinstance(exist_val, BaseCfgLine):
            exist_val = exist_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        # new_val MUST be a string or BaseCfgLine
        if isinstance(new_val, str) is True:
            pass

        elif isinstance(new_val, BaseCfgLine):
            new_val = new_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        if self.factory is False:
            new_obj = CFGLINE[self.syntax](
                all_lines=self._list,
                line=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.factory is True:
            new_obj = config_line_factory(
                all_lines=self._list,
                line=new_val,
                comment_delimiter=self.comment_delimiter,
                syntax=self.syntax,
            )

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx
            for idx, list_obj in enumerate(self._list)
            if re.search(exist_val, list_obj._text)
        ]
        for idx in sorted(all_idx, reverse=True):
            self._list.insert(idx + 1, new_obj)

        if atomic is True:
            # Reparse the whole config as a text list
            #self._bootstrap_from_text()
            self._list = self.bootstrap_obj_init_ng(self.ioscfg)
        else:
            ## Just renumber lines...
            self.reassign_linenums()

    # This method is on ConfigList()
    @ junos_unsupported
    @ logger.catch(reraise=True)
    def insert(self, ii, val):
        if not isinstance(ii, int):
            raise ValueError

        # Coerce a string into the appropriate object
        if getattr(val, "capitalize", False):
            if self.factory:
                obj = config_line_factory(
                    text=val,
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax,
                )

            elif self.factory is False:
                obj = CFGLINE[self.syntax](
                    text=val,
                    comment_delimiter=self.comment_delimiter,
                )

            else:
                err_txt = 'insert() cannot insert "{}"'.format(val)
                logger.error(err_txt)
                raise ValueError(err_txt)
        else:
            err_txt = 'insert() cannot insert "{}"'.format(val)
            logger.error(err_txt)
            raise ValueError(err_txt)

        ## Insert something at index ii
        self._list.insert(ii, obj)

        ## Just renumber lines...
        self.reassign_linenums()

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def config_hierarchy(self):
        """Walk this configuration and return the following tuple
        at each parent 'level': (list_of_parent_sibling_objs, list_of_nonparent_sibling_objs)

        """
        parent_siblings = []
        nonparent_siblings = []

        for obj in self.ccp_ref.find_objects(r"^\S+"):
            if obj.is_comment:
                continue
            elif len(obj.children) == 0:
                nonparent_siblings.append(obj)
            else:
                parent_siblings.append(obj)

        return parent_siblings, nonparent_siblings

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def _banner_mark_regex(self, regex):
        """
        Use the regex input parameter to identify all banner parent
        objects. Find banner object children and formally build references
        between banner parent / child objects.

        Set the blank_line_keep attribute for all banner parent / child objs
        Banner blank lines are automatically kept.
        """
        # Build a list of all banner parent objects...
        banner_objs = list(
            filter(lambda obj: regex.search(obj.text), self._list),
        )

        banner_re_str = r"^(?:(?P<btype>(?:set\s+)*banner\s\w+\s+)(?P<bchar>\S))"
        for parent in banner_objs:
            # blank_line_keep for Github Issue #229
            parent.blank_line_keep = True

            ## Parse out the banner type and delimiting banner character
            mm = re.search(banner_re_str, parent.text)
            if mm is not None:
                mm_results = mm.groupdict()
                (banner_lead, bannerdelimit) = (
                    mm_results["btype"].rstrip(),
                    mm_results["bchar"],
                )
            else:
                (banner_lead, bannerdelimit) = ("", None)

            if self.debug > 0:
                logger.debug("banner_lead = '{}'".format(banner_lead))
                logger.debug("bannerdelimit = '{}'".format(bannerdelimit))
                logger.debug(
                    "{} starts at line {}".format(
                        banner_lead,
                        parent.linenum,
                    ),
                )

            idx = parent.linenum
            while bannerdelimit is not None:
                ## Check whether the banner line has both begin and end delimter
                if idx == parent.linenum:
                    parts = parent.text.split(bannerdelimit)
                    if len(parts) > 2:
                        ## banner has both begin and end delimiter on one line
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead,
                                    parent.linenum,
                                ),
                            )
                        break

                ## Use code below to identify children of the banner line
                idx += 1
                try:
                    obj = self._list[idx]
                    if obj.text is None:
                        if self.debug > 0:
                            logger.warning(
                                "found empty text while parsing '{}' in the banner".format(
                                    obj
                                ),
                            )
                    elif bannerdelimit in obj.text.strip():
                        # Hit the bannerdelimit char... Exit banner parsing here...
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead,
                                    obj.linenum,
                                ),
                            )
                        # blank_line_keep for Github Issue #229
                        parent.children.append(obj)
                        parent.child_indent = 0
                        obj.parent = parent
                        break
                    else:
                        # all non-banner-parent lines should hit this condition
                        if self.debug > 0:
                            logger.debug("found banner child {}".format(obj))

                    # Commenting the following lines out; fix Github issue #115
                    # elif obj.is_comment and (obj.indent == 0):
                    #    break
                    parent.children.append(obj)
                    parent.child_indent = 0
                    obj.parent = parent
                    obj.blank_line_keep = True

                except IndexError:
                    break

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def _macro_mark_children(self, macro_parent_idx_list):
        """
        Set the blank_line_keep attribute for all banner parent / child objs.

        Macro blank lines are automatically kept.
        """
        # Mark macro children appropriately...
        for idx in macro_parent_idx_list:
            pobj = self._list[idx]
            # blank_line_keep for Github Issue #229
            pobj.blank_line_keep = True
            pobj.child_indent = 0

            # Walk the next configuration lines looking for the macro's children
            finished = False
            while not finished:
                idx += 1
                cobj = self._list[idx]
                # blank_line_keep for Github Issue #229
                cobj.blank_line_keep = True
                cobj.parent = pobj
                pobj.children.append(cobj)
                # If we hit the end of the macro, break out of the loop
                if cobj.text.rstrip() == "@":
                    finished = True

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def _maintain_bootstrap_parent_cache(self, parents_cache, indent, max_indent, is_config_line):
        ## Parent cache:
        ## Maintain indent vs max_indent in a family and
        ##     cache the parent until indent<max_indent
        parent = None
        if (indent < max_indent) and is_config_line:
            # walk parents and intelligently prune stale parents
            stale_parent_idxs = filter(
                lambda ii: ii >= indent,
                sorted(parents_cache.keys(), reverse=True),
            )

            # `del some_dict[key]` is the fastest way to delete keys
            #     See https://stackoverflow.com/a/3077179/667301
            for parent_idx in stale_parent_idxs:
                del parents_cache[parent_idx]
        else:
            ## As long as the child indent hasn't gone backwards,
            ##    we can use a cached parent
            parent = parents_cache.get(indent, None)

        return parents_cache, parent

    @ logger.catch(reraise=True)
    def _build_bootstrap_parent_child(self, retval, parents_cache, parent, idx, indent, obj, debug,):
        candidate_parent = None
        candidate_parent_idx = None
        ## If indented, walk backwards and find the parent...
        ## 1.  Assign parent to the child
        ## 2.  Assign child to the parent
        ## 3.  Assign parent's child_indent
        ## 4.  Maintain oldest_ancestor
        if (indent > 0) and (parent is not None):
            ## Add the line as a child (parent was cached)
            self._add_child_to_parent(retval, idx, indent, parent, obj)
        elif (indent > 0) and (parent is None):
            ## Walk backwards to find parent, and add the line as a child
            candidate_parent_idx = idx - 1
            while candidate_parent_idx >= 0:
                candidate_parent = retval[candidate_parent_idx]
                if (
                    candidate_parent.indent < indent
                ) and candidate_parent.is_config_line:
                    # We found the parent
                    parent = candidate_parent
                    parents_cache[indent] = parent  # Cache the parent
                    break
                else:
                    candidate_parent_idx -= 1

            ## Add the line as a child...
            self._add_child_to_parent(retval, idx, indent, parent, obj)

        else:
            if debug:
                logger.debug("    root obj assign: %s" % obj)

        return retval, parents_cache, parent

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def bootstrap_obj_init_ng(self, text_list=None, debug=0):
        """
        Accept a text list, and format into a list of *CfgLine() objects.

        This method returns a list of *CfgLine() objects.
        """
        if not isinstance(text_list, Sequence):
            raise ValueError

        if self.debug >= 1:
            logger.info("    ConfigList().bootstrap_obj_init_ng() was called.")

        retval = []
        idx = None
        syntax = self.syntax

        max_indent = 0
        macro_parent_idx_list = []
        # a dict of parents, indexed by int() child-indent...
        parent = None
        parents_cache = {}
        for idx, txt in enumerate(text_list):
            if self.debug >= 1:
                logger.debug("    bootstrap_obj_init_ng() adding text cmd: '%s' at idx %s" % (txt, idx,))
            if not isinstance(txt, str):
                raise ValueError

            # Assign a custom *CfgLine() based on factory...
            obj = cfgobj_from_text(
                text_list,
                txt=txt,
                idx=idx,
                syntax=syntax,
                comment_delimiter=self.comment_delimiter,
                factory=self.factory,
            )
            obj.confobj = self
            indent = obj.indent
            is_config_line = obj.is_config_line

            # list out macro parent line numbers...
            if txt[0:11] == "macro name " and syntax == "ios":
                macro_parent_idx_list.append(obj.linenum)

            parents_cache, parent = self._maintain_bootstrap_parent_cache(
                parents_cache, indent, max_indent, is_config_line
            )

            ## If indented, walk backwards and find the parent...
            ## 1.  Assign parent to the child
            ## 2.  Assign child to the parent
            ## 3.  Assign parent's child_indent
            ## 4.  Maintain oldest_ancestor
            retval, parents_cache, parent = self._build_bootstrap_parent_child(
                retval, parents_cache, parent, idx, indent, obj, debug,
            )

            ## Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent

            retval.append(obj)

        # Manually assign a parent on all closing braces
        self._list = assign_parent_to_closing_braces(input_list=retval)

        # Call _banner_mark_regex() to process banners in the returned obj
        # list.
        # Mark IOS banner begin and end config line objects...
        #
        # Build the banner_re regexp... at this point ios
        #    and nxos share the same method...
        if syntax not in ALL_BRACE_SYNTAX:
            banner_re = self._build_banner_re_ios()
            self._banner_mark_regex(banner_re)

            # We need to use a different method for macros than banners because
            #   macros don't specify a delimiter on their parent line, but
            #   banners call out a delimiter.
            self._macro_mark_children(macro_parent_idx_list)  # Process macros

        # change ignore_blank_lines behavior for Github Issue #229...
        #    Always allow a blank line if it's in a banner or macro...
        if self.ignore_blank_lines is True:
            retval = [
                obj
                for obj in self._list
                if obj.text.strip() != "" or obj.blank_line_keep is True
            ]
            self._list = retval

        return retval

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def _build_banner_re_ios(self):
        """Return a banner regexp for IOS (and at this point, NXOS)."""
        banner_str = {
            "login",
            "motd",
            "incoming",
            "exec",
            "telnet",
            "lcd",
        }
        banner_all = [r"^(set\s+)*banner\s+{}".format(ii) for ii in banner_str]
        banner_all.append(
            "aaa authentication fail-message",
        )  # Github issue #76
        banner_re = re.compile("|".join(banner_all))

        return banner_re

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def _add_child_to_parent(self, _list, idx, indent, parentobj, childobj):
        ## parentobj could be None when trying to add a child that should not
        ##    have a parent
        if parentobj is None:
            if self.debug >= 1:
                logger.debug("parentobj is None")
            return

        if self.debug >= 4:
            logger.debug(
                "Adding child '{}' to parent" " '{}'".format(childobj, parentobj),
            )
            logger.debug(
                "BEFORE parent.children - {}".format(
                    parentobj.children,
                ),
            )

        if childobj.is_comment and (_list[idx - 1].indent > indent):
            ## I *really* hate making this exception, but legacy
            ##   ciscoconfparse never marked a comment as a child
            ##   when the line immediately above it was indented more
            ##   than the comment line
            pass
        elif childobj.parent is childobj:
            # Child has not been assigned yet
            parentobj.children.append(childobj)
            childobj.parent = parentobj
            childobj.parent.child_indent = indent
        else:
            pass

        if self.debug > 0:
            # logger.debug("     AFTER parent.children - {0}"
            #    .format(parentobj.children))
            pass

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def iter_with_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if idx >= begin_index:
                yield obj

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def iter_no_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx >= begin_index) and (not obj.is_comment):
                yield obj

    # This method is on ConfigList()
    @ logger.catch(reraise=True)
    def reassign_linenums(self):
        # Call this after any insertion or deletion
        for idx, obj in enumerate(self._list):
            obj.linenum = idx

    # This method is on ConfigList()
    @ property
    @ logger.catch(reraise=True)
    def all_parents(self):
        return [obj for obj in self._list if obj.has_children]

    # This method is on ConfigList()
    @ property
    @ logger.catch(reraise=True)
    def last_index(self):
        return self.__len__() - 1

    ##########################################################################
    # Special syntax='asa' methods...
    ##########################################################################

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @ logger.catch(reraise=True)
    def names(self):
        """Return a dictionary of name to address mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        name_rgx = self._RE_NAMES
        for obj in self.ccp_ref.find_objects(name_rgx):
            addr = obj.re_match_typed(name_rgx, group=1, result_type=str)
            name = obj.re_match_typed(name_rgx, group=2, result_type=str)
            retval[name] = addr
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @ logger.catch(reraise=True)
    def object_group_network(self):
        """Return a dictionary of name to object-group network mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        obj_rgx = self._RE_OBJNET
        for obj in self.ccp_ref.find_objects(obj_rgx):
            name = obj.re_match_typed(obj_rgx, group=1, result_type=str)
            retval[name] = obj
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @ property
    @ logger.catch(reraise=True)
    def access_list(self):
        """Return a dictionary of ACL name to ACE (list) mappings"""
        if self.syntax != "asa":
            raise RequirementFailure()

        retval = {}
        for obj in self.ccp_ref.find_objects(self._RE_OBJACL):
            name = obj.re_match_typed(
                self._RE_OBJACL,
                group=1,
                result_type=str,
            )
            tmp = retval.get(name, [])
            tmp.append(obj)
            retval[name] = tmp
        return retval


#########################################################################3


class DiffObject(object):
    """This object should be used at every level of hierarchy"""

    @ logger.catch(reraise=True)
    def __init__(self, level, nonparents, parents):
        self.level = level
        self.nonparents = nonparents
        self.parents = parents

    @ logger.catch(reraise=True)
    def __repr__(self):
        return "<DiffObject level: {}>".format(self.level)


class CiscoPassword(object):
    @ logger.catch(reraise=True)
    def __init__(self, ep=""):
        self.ep = ep

    @ logger.catch(reraise=True)
    def decrypt(self, ep=""):
        """Cisco Type 7 password decryption.  Converted from perl code that was
        written by jbash [~at~] cisco.com; enhancements suggested by
        rucjain [~at~] cisco.com"""

        xlat = (
            0x64,
            0x73,
            0x66,
            0x64,
            0x3B,
            0x6B,
            0x66,
            0x6F,
            0x41,
            0x2C,
            0x2E,
            0x69,
            0x79,
            0x65,
            0x77,
            0x72,
            0x6B,
            0x6C,
            0x64,
            0x4A,
            0x4B,
            0x44,
            0x48,
            0x53,
            0x55,
            0x42,
            0x73,
            0x67,
            0x76,
            0x63,
            0x61,
            0x36,
            0x39,
            0x38,
            0x33,
            0x34,
            0x6E,
            0x63,
            0x78,
            0x76,
            0x39,
            0x38,
            0x37,
            0x33,
            0x32,
            0x35,
            0x34,
            0x6B,
            0x3B,
            0x66,
            0x67,
            0x38,
            0x37,
        )

        dp = ""
        regex = re.compile("^(..)(.+)")
        ep = ep or self.ep
        if not (len(ep) & 1):
            result = regex.search(ep)
            try:
                s, e = int(result.group(1)), result.group(2)
            except ValueError:
                # typically get a ValueError for int( result.group(1))) because
                # the method was called with an unencrypted password.  For now
                # SILENTLY bypass the error
                s, e = (0, "")
            for ii in range(0, len(e), 2):
                # int( blah, 16) assumes blah is base16... cool
                magic = int(re.search(".{%s}(..)" % ii, e).group(1), 16)
                # Wrap around after 53 chars...
                newchar = "%c" % (magic ^ int(xlat[int(s % 53)]))
                dp = dp + str(newchar)
                s = s + 1
        # if s > 53:
        #    logger.warning("password decryption failed.")
        return dp


@ logger.catch(reraise=True)
def config_line_factory(all_lines=None, line=None, comment_delimiter="!", syntax="ios", debug=0):
    """A factory method to assign a custom BaseCfgLine() subclass based on `all_lines`, `line`, `comment_delimiter`, and `syntax` parameters."""
    # Complicted & Buggy
    # classes = [j for (i,j) in globals().iteritems() if isinstance(j, TypeType) and issubclass(j, BaseCfgLine)]
    if not isinstance(all_lines, list):
        error = f"config_line_factory(all_lines=`{all_lines}`) must be a list, but we got {type(all_lines)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(line, str):
        error = f"config_line_factory(text=`{line}`) must be a string, but we got {type(line)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(comment_delimiter, str):
        error = f"config_line_factory(comment_delimiter=`{comment_delimiter}`) must be a string, but we got {type(comment_delimiter)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(syntax, str):
        error = f"config_line_factory(syntax=`{syntax}`) must be a string, but we got {type(syntax)}"
        logger.error(error)
        raise InvalidParameters(error)

    if not isinstance(debug, int):
        error = f"config_line_factory(debug=`{debug}`) must be an integer, but we got {type(debug)}"
        logger.error(error)
        raise InvalidParameters(error)

    if syntax not in ALL_VALID_SYNTAX:
        error = f"`{syntax}` is an unknown syntax"
        logger.error(error)
        raise ValueError(error)

    ##########################################################################
    # Select which list of factory classes will be used
    ##########################################################################
    factory_classes = None
    if syntax == "ios":
        factory_classes = ALL_IOS_FACTORY_CLASSES
    elif syntax == "nxos":
        factory_classes = ALL_NXOS_FACTORY_CLASSES
    elif syntax == "iosxr":
        factory_classes = ALL_IOSXR_FACTORY_CLASSES
    elif syntax == "asa":
        factory_classes = ALL_ASA_FACTORY_CLASSES
    elif syntax == "junos":
        factory_classes = ALL_JUNOS_FACTORY_CLASSES
    else:
        error = f"Cannot find a factory class list for syntax=`{syntax}`"
        logger.error(error)
        raise InvalidParameters(error)

    ##########################################################################
    # Walk all the classes and return the first class that
    # matches `.is_object_for(text)`.
    ##########################################################################
    try:
        for cls in factory_classes:
            if debug > 0:
                logger.debug(f"Consider config_line_factory() CLASS {cls}")
            if cls.is_object_for(all_lines=all_lines, line=line):
                basecfgline_subclass = cls(
                    all_lines=all_lines, line=line,
                    comment_delimiter=comment_delimiter,
                )  # instance of the proper subclass
                return basecfgline_subclass
    except ValueError:
        error = f"ciscoconfparse.py config_line_factory(all_lines={all_lines}, line=`{line}`, comment_delimiter=`{comment_delimiter}`, syntax=`{syntax}`) could not find a subclass of BaseCfgLine()"
        logger.error(error)
        raise ValueError(error)
    except Exception as eee:
        error = f"ciscoconfparse.py config_line_factory(all_lines={all_lines}, line=`{line}`, comment_delimiter=`{comment_delimiter}`, syntax=`{syntax}`): {eee}"

    if debug > 0:
        logger.debug("config_line_factory() is returning a default of IOSCfgLine()")
    return IOSCfgLine(all_lines=all_lines, line=line, comment_delimiter=comment_delimiter)


def parse_global_options():
    import optparse

    pp = optparse.OptionParser()
    pp.add_option(
        "-c",
        dest="config",
        help="Config file to be parsed",
        metavar="FILENAME",
    )
    pp.add_option(
        "-m",
        dest="method",
        help="Command for parsing",
        metavar="METHOD",
    )
    pp.add_option(
        "--a1",
        dest="arg1",
        help="Command's first argument",
        metavar="ARG",
    )
    pp.add_option(
        "--a2",
        dest="arg2",
        help="Command's second argument",
        metavar="ARG",
    )
    pp.add_option(
        "--a3",
        dest="arg3",
        help="Command's third argument",
        metavar="ARG",
    )
    (opts, args) = pp.parse_args()

    if opts.method == "find_lines":
        diff = CiscoConfParse(config=opts.config).find_lines(opts.arg1)
    elif opts.method == "find_children":
        diff = CiscoConfParse(config=opts.config).find_children(opts.arg1)
    elif opts.method == "find_all_children":
        diff = CiscoConfParse(config=opts.config).find_all_children(opts.arg1)
    elif opts.method == "find_blocks":
        diff = CiscoConfParse(config=opts.config).find_blocks(opts.arg1)
    elif opts.method == "find_parents_wo_child":
        diff = CiscoConfParse(config=opts.config).find_parents_wo_child(
            opts.arg1,
            opts.arg2,
        )
    elif opts.method == "req_cfgspec_excl_diff":
        diff = CiscoConfParse(config=opts.config).req_cfgspec_excl_diff(
            opts.arg1,
            opts.arg2,
            opts.arg3.split(","),
        )
    elif opts.method == "req_cfgspec_all_diff":
        diff = CiscoConfParse(config=opts.config).req_cfgspec_all_diff(
            opts.arg1.split(","),
        )
    elif opts.method == "decrypt":
        pp = CiscoPassword()
        print(pp.decrypt(opts.arg1))
        exit(1)
    elif opts.method == "help":
        print("Valid methods and their arguments:")
        print("   find_lines:             arg1=linespec")
        print("   find_children:          arg1=linespec")
        print("   find_all_children:      arg1=linespec")
        print("   find_blocks:            arg1=linespec")
        print("   find_parents_w_child:   arg1=parentspec  arg2=childspec")
        print("   find_parents_wo_child:  arg1=parentspec  arg2=childspec")
        print("   req_cfgspec_excl_diff:  arg1=linespec    arg2=uncfgspec   arg3=cfgspec")
        print("   req_cfgspec_all_diff:   arg1=cfgspec")
        print("   decrypt:                arg1=encrypted_passwd")
        exit(1)
    else:
        import doctest

        doctest.testmod()
        exit(0)

    if len(diff) > 0:
        for line in diff:
            print(line)
    else:
        opt_error = "ciscoconfparse was called with unknown parameters"
        logger.error(opt_error)
        raise RuntimeError(opt_error)


# TODO: Add unit tests below
if __name__ == "__main__":
    parse_global_options()
