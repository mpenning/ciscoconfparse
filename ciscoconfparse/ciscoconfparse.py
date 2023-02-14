"""
ciscoconfparse.py - Parse, Query, Build, and Modify IOS-style configs.

Copyright (C) 2022-2023 David Michael Pennington
Copyright (C) 2022 David Michael Pennington at WellSky
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
from datetime import datetime
from functools import partial
from operator import is_not
import warnings
import inspect
import pathlib
import locale
import time
import copy
import sys
import re
import os


from ciscoconfparse.models_cisco import IOSHostnameLine, IOSRouteLine
from ciscoconfparse.models_cisco import IOSIntfLine
from ciscoconfparse.models_cisco import IOSAccessLine, IOSIntfGlobal
from ciscoconfparse.models_cisco import IOSAaaLoginAuthenticationLine
from ciscoconfparse.models_cisco import IOSAaaEnableAuthenticationLine
from ciscoconfparse.models_cisco import IOSAaaCommandsAuthorizationLine
from ciscoconfparse.models_cisco import IOSAaaCommandsAccountingLine
from ciscoconfparse.models_cisco import IOSAaaExecAccountingLine
from ciscoconfparse.models_cisco import IOSAaaGroupServerLine
from ciscoconfparse.models_cisco import IOSCfgLine

from ciscoconfparse.models_nxos import NXOSHostnameLine, NXOSRouteLine
from ciscoconfparse.models_nxos import NXOSAccessLine, NXOSIntfGlobal
from ciscoconfparse.models_nxos import NXOSAaaLoginAuthenticationLine
from ciscoconfparse.models_nxos import NXOSAaaEnableAuthenticationLine
from ciscoconfparse.models_nxos import NXOSAaaCommandsAuthorizationLine
from ciscoconfparse.models_nxos import NXOSAaaCommandsAccountingLine
from ciscoconfparse.models_nxos import NXOSAaaExecAccountingLine
from ciscoconfparse.models_nxos import NXOSCfgLine, NXOSIntfLine
from ciscoconfparse.models_nxos import NXOSAaaGroupServerLine
from ciscoconfparse.models_nxos import NXOSvPCLine

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

from ciscoconfparse.models_junos import JunosCfgLine

from ciscoconfparse.ccp_abc import BaseCfgLine

from ciscoconfparse.ccp_util import fix_repeated_words
from ciscoconfparse.ccp_util import enforce_valid_types
from ciscoconfparse.ccp_util import junos_unsupported
from ciscoconfparse.ccp_util import configure_loguru
# Not using ccp_re yet... still a work in progress
# from ciscoconfparse.ccp_util import ccp_re

from deprecat import deprecat
from loguru import logger
import toml


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
        toml_values = dict()
        with open(pyproject_toml_path, encoding=ENCODING) as fh:
            toml_values = toml.loads(fh.read())
            version = toml_values["tool"]["poetry"].get("version", -1.0)

        if not isinstance(version, str):
            raise ValueError("The version parameter must be a string.")

    else:
        # This is required for importing from a zipfile... Github issue #123
        version = "0.0.0"  # __version__ read failed

    return version


def enforce_valid_types(var, var_types=None, error_str=None):
    assert isinstance(var_types, tuple)
    if not isinstance(var, var_types):
        raise ValueError(error_str)


@logger.catch(reraise=True)
def initialize_globals():
    """Initialize ciscoconfparse global dunder variables and a couple others."""
    global ALL_VALID_SYNTAX
    global ENCODING
    global __author_email__
    global __author__
    global __copyright__
    global __license__
    global __status__
    global __version__

    ENCODING = locale.getpreferredencoding()
    ALL_VALID_SYNTAX = (
        'ios',
        'nxos',
        'asa',
        'junos',
    )

    try:
        __author_email__ = r"mike /at\ pennington [dot] net"
        __author__ = "David Michael Pennington <{}>".format(__author_email__)
        __copyright__ = "2007-{}, {}".format(time.strftime("%Y"), __author__)
        __license__ = "GPLv3"
        __status__ = "Production"
        __version__ = get_version_number()

    except Exception as eee:
        raise ValueError(str(eee))

    finally:
        # These are all the 'dunder variables' required...
        globals_dict = {
            '__author_email__': __author_email__,
            '__author__': __author__,
            '__copyright__': __copyright__,
            '__license__': __license__,
            '__status__': __status__,
            '__version__': __version__,
        }
        return globals_dict


@logger.catch(reraise=True)
def initialize_ciscoconfparse():
    """Initialize ciscoconfparse global variables and configure logging."""
    configure_loguru()

    globals_dict = initialize_globals()
    for key, value in globals_dict.items():
        # Example, this will set __version__ to content of 'value'
        #     from -> https://stackoverflow.com/a/3972978/667301
        globals()[key] = value

    return globals_dict


# ALL ciscoconfparse global variables initizalization happens here...
initialize_ciscoconfparse()


@logger.catch(reraise=True)
def _parse_line_braces(line_txt=None, comment_delimiter=None) -> tuple:
    """Internal helper-method for brace-delimited configs (typically JunOS)."""
    # Removed config parameter assertions in 1.7.2...

    enforce_valid_types(line_txt, (str,),
        "line_txt parameter must be a string."
    )
    enforce_valid_types(comment_delimiter, (str,),
        "comment_delimiter parameter must be a string."
    )
    if len(comment_delimiter) > 1:
        raise ValueError("len(comment_delimiter) must be one.")

    syntax = "ios"
    child_indent = 0
    this_line_indent = 0

    junos_re_str = r"""^
    (?:\s*
        (?P<braces_close_left>\})*(?P<line1>.*?)(?P<braces_open_right>\{)*;*
        |(?P<line2>[^\{\}]*?)(?P<braces_open_left>\{)(?P<condition2>.*?)(?P<braces_close_right>\});*\s*
        |(?P<line3>[^\{\}]*?);*\s*
    )$
    """
    line_re = re.compile(junos_re_str, re.VERBOSE)
    comment_re = re.compile(r'^\s*(?P<delimiter>[{0}]+)(?P<comment>[^{0}]*)$'.format(re.escape(comment_delimiter)))

    mm = line_re.search(line_txt.strip())
    nn = comment_re.search(line_txt.strip())

    if nn is not None:
        results = nn.groupdict()
        return (this_line_indent, child_indent, results.get('delimiter', '') + results.get('comment', ''))

    elif mm is not None:
        results = mm.groupdict()

        # } line1 { foo bar this } {
        braces_close_left = bool(results.get('braces_close_left', ''))
        braces_open_right = bool(results.get('braces_open_right', ''))

        # line2
        braces_open_left = bool(results.get('braces_open_left', ''))
        braces_close_right = bool(results.get('braces_close_right', ''))

        # line3
        line1_str = results.get('line1', '')
        line2_str = results.get('line2', '')

        if braces_close_left and braces_open_right:
            # Based off line1
            #     } elseif { bar baz } {
            this_line_indent -= 1
            child_indent += 0
            retval = results.get('line1', None)
            return (this_line_indent, child_indent, retval)

        elif bool(line1_str) and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     address 1.1.1.1
            this_line_indent -= 0
            child_indent += 0
            retval = results.get('line1', '').strip()
            # Strip empty braces here
            retval = re.sub(r'\s*\{\s*\}\s*', '', retval)
            return (this_line_indent, child_indent, retval)

        elif (line1_str == '') and (braces_close_left is False) and (braces_open_right is False):
            # Based off line1:
            #     return empty string
            this_line_indent -= 0
            child_indent += 0
            return (this_line_indent, child_indent, '')

        elif braces_open_left and braces_close_right:
            # Based off line2
            #    this { bar baz }
            this_line_indent -= 0
            child_indent += 0
            line = results.get('line2', None) or ''
            condition = results.get('condition2', None) or ''
            if condition.strip() == '':
                retval = line
            else:
                retval = line + " {" + condition + " }"
            return (this_line_indent, child_indent, retval)

        elif braces_close_left:
            # Based off line1
            #   }
            this_line_indent -= 1
            child_indent -= 1
            return (this_line_indent, child_indent, '')

        elif braces_open_right:
            # Based off line1
            #   this that foo {
            this_line_indent -= 0
            child_indent += 1
            line = results.get('line1', None) or ''
            return (this_line_indent, child_indent, line)

        elif (line2_str != '') and (line2_str is not None):
            this_line_indent += 0
            child_indent += 0
            return (this_line_indent, child_indent, '')

        else:
            raise ValueError('Cannot parse {} match:"{}"'.format(
                syntax, line_txt))

    else:
        raise ValueError('Cannot parse {}:"{}"'.format(syntax, line_txt))

# This method was on ConfigList()
@logger.catch(reraise=True)
def _build_cfgobj_from_text(txt, idx, syntax=None, comment_delimiter=None, factory=None):
    """Build cfgobj from configuration text syntax, and factory inputs."""
    if factory is False:

        if syntax == "ios":
            obj = IOSCfgLine(txt, comment_delimiter)

        elif syntax == "nxos":
            obj = NXOSCfgLine(txt, comment_delimiter)

        elif syntax == "junos":
            obj = JunosCfgLine(txt, comment_delimiter)

        elif syntax == "asa":
            obj = ASACfgLine(
                text=txt,
                comment_delimiter=comment_delimiter,
            )

        else:
            raise ValueError

    elif syntax in ALL_VALID_SYNTAX:
        obj = ConfigLineFactory(
            txt,
            comment_delimiter,
            syntax=syntax,
        )

    else:
        err_txt = (
            "Cannot classify config list item '%s' "
            "into a proper configuration object line" % txt
        )
        logger.error(err_txt)
        raise ValueError(err_txt)

    obj.linenum = idx

    return obj

@logger.catch(reraise=True)
def build_space_tolerant_regex(linespec):
    r"""SEMI-PRIVATE: Accept a string, and return a string with all spaces replaced with '\s+'."""
    # Define backslash with manual Unicode...
    backslash = "\x5c"
    # escaped_space = "\\s+" (not a raw string)
    escaped_space = (backslash + backslash + "s+").translate("utf-8")

    enforce_valid_types(linespec, (str,),
        "linespec parameter must be a string."
    )
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
def assign_parent_to_closing_braces(input_list=None):
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
                if len(obj.text.rstrip())>=1 and obj.text.rstrip()[-1]=='{':
                    opening_brace_objs.append(obj)

                elif len(obj.text.strip())>=1 and obj.text.strip()[0]=='}':
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
    ## Note to self, I made this regex fairly junos-specific...
    input_condition_01 = isinstance(input_list, list) and len(input_list) > 0
    input_condition_02 = '{' not in set(comment_delimiter)
    input_condition_03 = '}' not in set(comment_delimiter)
    if not (input_condition_01 and input_condition_02 and input_condition_03):
        raise ValueError

    lines = list()
    offset = 0
    STOP_WIDTH = stop_width
    for idx, tmp in enumerate(input_list):
        if debug > 0:
            logger.debug("Parse line {}:'{}'".format(idx + 1, tmp.strip()))
        (this_line_indent, child_indent, line) = _parse_line_braces(
            tmp.strip(), comment_delimiter=comment_delimiter)
        lines.append((" " * STOP_WIDTH * (offset + this_line_indent)) + line.strip())
        offset += child_indent

    return lines


class CiscoConfParse(object):
    """Parse Cisco IOS configurations and answer queries about the configs."""

    # Something breaks in CiscoConfParse() if using @logger.catch, below...
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
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).
        encoding : str
            A string holding the coding type.  Default is `locale.getpreferredencoding()`



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
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).

        """
        if not (isinstance(syntax, str) and (syntax in ALL_VALID_SYNTAX)):
            error = "'{}' is an unknown syntax".format(syntax)
            logger.error(error)
            raise ValueError(error)

        self.finished_config_parse = False

        # all IOSCfgLine object instances...
        self.comment_delimiter = comment
        self.factory = factory
        self.ConfigObjs = None
        self.syntax = syntax
        self.ignore_blank_lines = ignore_blank_lines
        self.encoding = encoding or ENCODING
        self.debug = debug

        # Read the configuration lines and detect invalid inputs...
        # tmp_lines = self._get_ccp_lines(config=config, logger=logger)
        if isinstance(config, (str, pathlib.Path,)):
            tmp_lines = self.read_config_file(filepath=config, logger=logger)

        elif isinstance(config, Sequence):
            tmp_lines = config

        else:
            raise ValueError

        assert self._check_ccp_input_good(config=tmp_lines) is True

        # conditionally strip off junos-config braces and other syntax
        #     parsing  issues...
        config_lines = self._handle_ccp_syntax(tmp_lines=tmp_lines, syntax=syntax)

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
    def _handle_ccp_syntax(self, tmp_lines=None, syntax=None):
        """Deal with syntax issues, such as conditionally discarding junos closing brace-lines."""

        assert tmp_lines is not None
        if syntax == "junos":
            err_msg = ("junos parser factory is not yet enabled; use factory=False")
            assert self.factory is False, err_msg
            config_lines = convert_junos_to_ios(tmp_lines, comment_delimiter="#")
        else:
            config_lines = tmp_lines

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
                num_lines, self.syntax, self.comment_delimiter,
                self.factory, self.ignore_blank_lines, self.encoding,
            )
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _validate_ConfigObjs(self):
        """ConfigObjs should be None or an instance of collections.abc.Sequence."""
        raise RuntimeError

        # Important: Ensure we have a sane copy of self and self.ConfigObjs...
        if not isinstance(self, CiscoConfParse):
            err = "CiscoConfParse() did not populate self.ConfigObjs"
            raise ValueError(err)

        if self.debug > 0:
            log_msg = ("assigning self.ConfigObjs = ConfigList(syntax='%s')" % self.syntax)
            logger.info(log_msg)

        if self.ConfigObjs is not None:
            if not isinstance(self.ConfigObjs, Sequence):
                err = "self.ConfigObjs must be an instance of collections.abc.Sequence."
                raise ValueError(err)
            else:
                # self.ConfigObjs is an instance of Sequence...
                return True
        else:
            # self.ConfigObjs is None
            return True

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def read_config_file(self, filepath=None, logger=None, linesplit_rgx=r"\r*\n+"):
        """Read the config lines from the filepath.  Return the list of text configuration commands or raise an error."""

        assert logger is not None
        assert self.finished_config_parse is False

        config_lines = None

        enforce_valid_types(filepath, (str, pathlib.Path),
            "filepath parameter must be a string or pathlib.Path()."
        )

        if isinstance(filepath, (str, pathlib.Path,)) and os.path.isfile(filepath) is True:
            # config string - assume a filename...
            if self.debug > 0:
                logger.debug("reading config from the filepath named '%s'" % filepath)

        elif isinstance(filepath, (str, pathlib.Path,)) and os.path.isfile(filepath) is False:
            if self.debug > 0:
                logger.debug("filepath not found - '%s'" % filepath)
            try:
                _ = open(file=filepath, **self.openargs)

            except FileNotFoundError:
                error = """FATAL - Attempted to open(file='{0}', mode='r', encoding='{1}'); the filepath named:"{0}" does not exist.""".format(filepath, self.openargs['encoding'])
                raise FileNotFoundError(error)

            except OSError:
                error = """FATAL - Attempted to open(file='{0}', mode='r', encoding='{1}'); OSError opening "{0}".""".format(filepath, self.openargs['encoding'])
                raise OSError(error)

            except Exception:
                raise RuntimeError

        else:
            raise ValueError("filepath=\"\"\"%s\"\"\" is an unexpected type().  `filepath` must be a python string or patlib.Path." % filepath)

        # Read the file from disk and return the list of config statements...
        try:
            with open(file=filepath, **self.openargs) as fh:
                text = fh.read()
            rgx = re.compile(linesplit_rgx)
            config_lines = rgx.split(text)
            return config_lines

        except OSError:
            error = "CiscoConfParse could not open() the filepath named '%s'" % filename
            logger.critical(error)
            raise OSError("FATAL - could not open() the config filepath named '{}'".format(filename))

        except Exception as eee:
            error = "FATAL - {}".format(str(eee))
            logger.critical(error)
            raise OSError(error) from eee

    @logger.catch(reraise=True)
    def _DEPRECATED_read_config_file(self, filename=None, logger=None, linesplit_rgx=r"\r*\n+"):
        """Read the configuration from a filename."""
        # config string - assume a filename... open file return lines...

        if not isinstance(filename, (str, pathlib.Path,)):
            raise ValueError("FATAL - filepath must be a string or pathlib.Path() instance")

        if os.path.isfile(filename) is False:
            raise OSError("FATAL - could not open() the config filepath named '{}'".format(filename))

        if self.debug > 0:
            logger.debug("CiscoConfParse().read_config_file() is parsing config from the filepath named '%s'" % filename)

        try:
            with open(file=filename, **self.openargs) as fh:
                text = fh.read()
            rgx = re.compile(linesplit_rgx)
            config_lines = rgx.split(text)
            return config_lines

        except OSError:
            error = "CiscoConfParse could not open() the filepath named '%s'" % filename
            logger.critical(error)
            raise OSError("FATAL - could not open() the config filepath named '{}'".format(filename))

        except Exception as eee:
            error = "FATAL - {}".format(str(eee))
            logger.critical(error)
            raise OSError(error) from eee

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _check_ccp_input_good(self, config=None, logger=None, linesplit_rgx=r"\r*\n+"):
        """The config parameter is a sequence of text config commands.  Return the list of text configuration commands or raise an error."""

        assert self.finished_config_parse is False

        enforce_valid_types(config, (str, pathlib.Path, Sequence,),
            "config parameter must be a string, pathlib.Path() or an instance of collections.abc.Sequence()."
        )

        if False:
            if isinstance(config, Sequence) and len(config) == 0:
                # IMPORTANT - explicitly handle an empty config list...
                raise ValueError("FATAL - the 'config' parameter got an empty {0}".format(type(config)))

        if isinstance(config, Sequence) and len(config) >= 0:
            # Here we assume that `config` is a list of text config lines...
            #
            # config list of text lines...
            if self.debug > 0:
                logger.debug("parsing config stored in the config variable: '%s'" % config)
            return True

        else:
            raise ValueError("config=\"\"\"%s\"\"\" is an unexpected type().  The `config` instance must be an instance of collecitons.abc.Sequence" % config)

    #########################################################################
    # This method is on CiscoConfParse()
    #      do NOT wrap this method in logger.catch() - github issue #249
    #########################################################################
    @property
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
    def ioscfg(self):
        """Return a list containing all text configuration statements."""
        ## I keep ioscfg to emulate legacy ciscoconfparse behavior
        return [ii.text for ii in self.ConfigObjs]

    # This method is on CiscoConfParse()
    @property
    def objs(self):
        """CiscoConfParse().objs is an alias for the CiscoConfParse().ConfigObjs property; it returns a ConfigList() of config-line objects."""
        if self.ConfigObjs is None:
            err_txt = ("ConfigObjs is set to None.  ConfigObjs should be a "
                       "ConfigList() of configuration-line objects".format(self.syntax))
            logger.error(err_txt)
            raise ValueError(err_txt)
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
        self.ConfigObjs._bootstrap_from_text()

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
        self.atomic()  # atomic() calls self.ConfigObjs._bootstrap_from_text()

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_object_branches(
        self,
        branchspec=(),
        regex_flags=0,
        allow_none=None,
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
        if allow_none is not None:
            warning = "The allow_none parameter is deprecated as of version 1.6.16.  Going forward, allow_none is always True."
            logger.warning(warning)
        allow_none = True

        branchspec_is_tuple = isinstance(branchspec, tuple)
        if branchspec_is_tuple is True:

            if debug > 1:
                message = "{}().find_object_branches(branchspec='{}') was called".format(
                    self.__class__.__name__, branchspec,
                )
                logger.info(message)

            if branchspec == ():
                error = "find_object_branches(): branchspec must not be empty"
                logger.error(error)
                raise ValueError(error)

        else:
            error = "find_object_branches(): Please enclose the branchspec regular expressions in a Python tuple"
            logger.error(error)
            raise ValueError(error)

        def list_matching_children(
            parent_obj,
            childspec,
            regex_flags,
            allow_none=True,
            debug=0,
        ):
            ## I'm not using parent_obj.re_search_children() because
            ## re_search_children() doesn't return None for no match...

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
    )""" % (parent_obj, childspec, regex_flags, allow_none, debug)
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
                cobj for cobj in children
                if re.search(childspec, cobj.text, regex_flags)
            ]
            # Return [None] if no children matched...
            if (allow_none is True) and len(segment_list) == 0:
                segment_list = [None]

            # FIXME: Insert debugging here...
            # print("    SEGMENTS "+str(segment_list))
            if debug > 1:
                logger.info(
                    "    list_matching_children() returns segment_list=%s" %
                    segment_list,
                )
            return segment_list

        branches = list()
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
                    allow_none=allow_none,
                    debug=debug,
                )
                if allow_none is True:
                    # Start growing branches from the segments we received...
                    branches = [[kid] for kid in next_kids]
                else:
                    branches = [[kid] for kid in next_kids if kid is not None]

            else:
                new_branches = list()
                for branch in branches:
                    # Extend existing branches into the new_branches
                    if branch[-1] is not None:
                        # Find children to extend the family branch...
                        next_kids = list_matching_children(
                            parent_obj=branch[-1],
                            childspec=childspec,
                            regex_flags=regex_flags,
                            allow_none=allow_none,
                            debug=debug,
                        )

                        for kid in next_kids:
                            # Fork off a new branch and add each matching kid...
                            # Use copy.copy() for a "shallow copy" of branch:
                            #    https://realpython.com/copying-python-objects/
                            tmp = copy.copy(branch)
                            tmp.append(kid)
                            new_branches.append(tmp)
                    elif allow_none is True:
                        branch.append(None)
                        new_branches.append(branch)

                # Ensure we have the most recent branches...
                branches = new_branches

        branches = new_branches
        # If regex_groups is True, assign regexp matches to the return matrix.
        if regex_groups is True:

            return_matrix = list()
            # branchspec = (r"^interfaces", r"\s+(\S+)", r"\s+(unit\s+\d+)", r"family\s+(inet)", r"address\s+(\S+)")
            # for idx_matrix, row in enumerate(self.find_object_branches(branchspec)):
            for _, row in enumerate(branches):
                enforce_valid_types(row, (Sequence,),
                    "row parameter must be an instance of collections.abc.Sequence()."
                )

                # Before we check regex capture groups, allocate an "empty return_row"
                #   of the correct length...
                return_row = [(None,)] * len(branchspec)

                # Populate the return_row below...
                #     return_row will be appended to return_matrix...
                for idx, element in enumerate(row):

                    if isinstance(element, BaseCfgLine):
                        regex_result = re.search(branchspec[idx], element.text)
                        if regex_result is not None:
                            # Save all the regex capture groups in matched_capture...
                            matched_capture = regex_result.groups()
                            if len(matched_capture) == 0:
                                # If the branchspec groups() matches are a
                                # zero-length tuple, populate this return_row
                                # with the whole element's text
                                return_row[idx] = (element.text,)
                            elif len(matched_capture) > 0:
                                # In this case, we found regex capture groups
                                return_row[idx] = matched_capture
                            else:
                                raise ValueError
                        elif (regex_result is None):
                            # No regex capture groups b/c of no regex match...
                            return_row[idx] = (None,)
                        else:
                            raise ValueError()
                    elif element is None:
                        return_row[idx] = (None,)
                    else:
                        substr_01 = "regex matches on {}('{}')".format(
                            type(element), element.text)
                        err_str = substr_01 + " are not supported"
                        raise ValueError(err_str)
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
        if (self.factory is not True):
            err_text = "find_interface_objects() must be" \
                " called with 'factory=True'"
            logger.error(err_text)
            raise ValueError(err_text)

        retval = list()
        if self.syntax in ("ios", "nxos",):
            if exactmatch is True:
                for obj in self.find_objects("^interface"):
                    if intfspec.lower() in obj.abbvs:
                        retval.append(obj)
                        break  # Only break if exactmatch is True
            else:
                err_text = "This method requires exactmatch set True"
                logger.error(err_text)
                raise NotImplementedError(err_text)
        ## TODO: implement ASAConfigLine.abbvs and others
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
            message = "METHOD {}().{}(dnaspec='{}') was called".format(
                self.__class__.__name__, method_name, dnaspec,
            )
            logger.info(message)

        if self.ConfigObjs is None:
            # ConfigObjs should be a list, tuple or Sequence
            err_text = ("CiscoConfParse().ConfigObjs should be a list of "
                        "config lines, but it's not initialized.")
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
                "find_objects('%s', exactmatch=%s) was called" %
                (linespec, exactmatch),
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
    def find_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and their immediate
        children.  This method is different than :meth:`find_all_children`,
        because :meth:`find_all_children` finds children of children.
        :meth:`find_children` only finds immediate children.

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        exactmatch : bool
            boolean that controls whether partial matches are valid
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching configuration lines

        Examples
        --------

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = ['username ddclient password 7 107D3D232342041E3A',
        ...           'archive',
        ...           ' log config',
        ...           '  logging enable',
        ...           '  hidekeys',
        ...           ' path ftp://ns.foo.com//tftpboot/Foo-archive',
        ...           '!',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> p.find_children('^archive')
        ['archive', ' log config', ' path ftp://ns.foo.com//tftpboot/Foo-archive']
        >>>
        """
        if ignore_ws is True:
            linespec = build_space_tolerant_regex(linespec)

        if exactmatch is False:
            parentobjs = self._find_line_OBJ(linespec)
        else:
            parentobjs = self._find_line_OBJ("^%s$" % linespec)

        allobjs = set()
        for parent in parentobjs:
            if parent.has_children is True:
                allobjs.update(set(parent.children))
            allobjs.add(parent)

        return [ii.text for ii in sorted(allobjs)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_all_children(self, linespec, exactmatch=False, ignore_ws=False):
        """Returns the parents matching the linespec, and all their children.
        This method is different than :meth:`find_children`, because
        :meth:`find_all_children` finds children of children.
        :meth:`find_children` only finds immediate children.

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        exactmatch : bool
            boolean that controls whether partial matches are valid
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching configuration lines

        Examples
        --------
        Suppose you are interested in finding all `archive` statements in
        the following configuration...

        .. code::

           username ddclient password 7 107D3D232342041E3A
           archive
            log config
             logging enable
             hidekeys
            path ftp://ns.foo.com//tftpboot/Foo-archive
           !

        Using the config above, we expect to find the following config lines...

        .. code::

           archive
            log config
             logging enable
             hidekeys
            path ftp://ns.foo.com//tftpboot/Foo-archive

        We would accomplish this by querying `find_all_children('^archive')`...

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = ['username ddclient password 7 107D3D232342041E3A',
        ...           'archive',
        ...           ' log config',
        ...           '  logging enable',
        ...           '  hidekeys',
        ...           ' path ftp://ns.foo.com//tftpboot/Foo-archive',
        ...           '!',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> p.find_all_children('^archive')
        ['archive', ' log config', '  logging enable', '  hidekeys', ' path ftp://ns.foo.com//tftpboot/Foo-archive']
        >>>
        """

        if ignore_ws:
            linespec = build_space_tolerant_regex(linespec)

        if exactmatch is False:
            parentobjs = self._find_line_OBJ(linespec)
        else:
            parentobjs = self._find_line_OBJ("^%s$" % linespec)

        allobjs = set()
        for parent in parentobjs:
            allobjs.add(parent)
            allobjs.update(set(parent.all_children))
        return [ii.text for ii in sorted(allobjs)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_blocks(self, linespec, exactmatch=False, ignore_ws=False):
        """Find all siblings matching the linespec, then find all parents of
        those siblings. Return a list of config lines sorted by line number,
        lowest first.  Note: any children of the siblings should NOT be
        returned.

        Parameters
        ----------
        linespec : str
            Text regular expression for the line to be matched
        exactmatch : bool
            boolean that controls whether partial matches are valid
        ignore_ws : bool
            boolean that controls whether whitespace is ignored

        Returns
        -------
        list
            A list of matching configuration lines


        Examples
        --------
        This example finds `bandwidth percent` statements in following config,
        the siblings of those `bandwidth percent` statements, as well
        as the parent configuration statements required to access them.

        .. code::

           !
           policy-map EXTERNAL_CBWFQ
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

        The following config lines should be returned:

        .. code::

           policy-map EXTERNAL_CBWFQ
            class IP_PREC_MEDIUM
             bandwidth percent 50
             queue-limit 100
            class class-default
             bandwidth percent 40
             queue-limit 100

        We do this by quering `find_blocks('bandwidth percent')`...

        .. code-block:: python
           :emphasize-lines: 22,25

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'policy-map EXTERNAL_CBWFQ',
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
           >>> p.find_blocks('bandwidth percent')
           ['policy-map EXTERNAL_CBWFQ', ' class IP_PREC_MEDIUM', '  bandwidth percent 50', '  queue-limit 100', ' class class-default', '  bandwidth percent 40', '  queue-limit 100']
           >>>
           >>> p.find_blocks(' class class-default')
           ['policy-map EXTERNAL_CBWFQ', ' class IP_PREC_HIGH', ' class IP_PREC_MEDIUM', ' class class-default']
           >>>

        """
        tmp = set()

        if ignore_ws:
            linespec = build_space_tolerant_regex(linespec)

        # Find line objects maching the spec
        if exactmatch is False:
            objs = self._find_line_OBJ(linespec)
        else:
            objs = self._find_line_OBJ("^%s$" % linespec)

        for obj in objs:
            tmp.add(obj)
            # Find the siblings of this line
            sib_objs = self._find_sibling_OBJ(obj)
            for sib_obj in sib_objs:
                tmp.add(sib_obj)

        # Find the parents for everything
        pobjs = set()
        for lineobject in tmp:
            for pobj in lineobject.all_parents:
                pobjs.add(pobj)
        tmp.update(pobjs)

        return [ii.text for ii in sorted(tmp)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects_w_child(
        self,
        parentspec,
        childspec,
        ignore_ws=False,
        recurse=False,
    ):
        """
        Return a list of parent :class:`~models_cisco.IOSCfgLine` objects,
        which matched the ``parentspec`` and whose children match ``childspec``.
        Only the parent :class:`~models_cisco.IOSCfgLine` objects will be
        returned.

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
           >>> p.find_objects_w_child('^interface',
           ...     'switchport access vlan 300')
           ...
           [<IOSCfgLine # 5 'interface FastEthernet0/2'>, <IOSCfgLine # 9 'interface FastEthernet0/3'>]
           >>>
        """

        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        return list(
            filter(
                lambda x: x.re_search_children(childspec, recurse=recurse),
                self.find_objects(parentspec),
            ),
        )

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
        enforce_valid_types(childspec, (Sequence,),
            "childspec parameter must be an instance of collections.abc.Sequence()."
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
    @logger.catch(reraise=True)
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

        enforce_valid_types(childspec, (Sequence,),
            "childspec parameter must be an instance of collections.abc.Sequence()."
        )

        retval = []
        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            if isinstance(childspec, Sequence):
                childspec = [build_space_tolerant_regex(ii) for ii in childspec]

            else:
                err_txt = "Cannot call build_space_tolerant_regex()" \
                    " on childspec"
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
    @logger.catch(reraise=True)
    def find_parents_w_child(self, parentspec, childspec, ignore_ws=False):
        """Parse through all children matching childspec, and return a list of
        parents that matched the parentspec.  Only the parent lines will be
        returned.

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
            A list of matching parent configuration lines

        Examples
        --------
        This example finds all ports that are members of access vlan 300
        in following config...

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

        We do this by quering `find_parents_w_child()`; we set our
        parent as `^interface` and set the child as
        `switchport access vlan 300`.

        .. code-block:: python
           :emphasize-lines: 18

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
           >>> p.find_parents_w_child('^interface', 'switchport access vlan 300')
           ['interface FastEthernet0/2', 'interface FastEthernet0/3']
           >>>

        """
        tmp = self.find_objects_w_child(
            parentspec,
            childspec,
            ignore_ws=ignore_ws,
        )
        return [ii.text for ii in tmp]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects_wo_child(self, parentspec, childspec, ignore_ws=False):
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

        We do this by quering `find_objects_wo_child()`; we set our
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
           >>> p.find_objects_wo_child(r'^interface', r'speed\s\d+')
           [<IOSCfgLine # 1 'interface FastEthernet0/1'>, <IOSCfgLine # 5 'interface FastEthernet0/2'>]
           >>>
        """

        if ignore_ws is True:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        return [
            obj for obj in self.find_objects(parentspec)
            if not obj.re_search_children(childspec)
        ]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_parents_wo_child(self, parentspec, childspec, ignore_ws=False):
        r"""Parse through all parents matching parentspec, and return a list of parents that did NOT have children match the childspec.  For simplicity, this method only finds oldest_ancestors without immediate children that match.

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
            A list of matching parent configuration lines

        Examples
        --------
        This example finds all ports that are autonegotiating in the
        following config...

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

        We do this by quering `find_parents_wo_child()`; we set our
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
           >>> p.find_parents_wo_child('^interface', 'speed\s\d+')
           ['interface FastEthernet0/1', 'interface FastEthernet0/2']
           >>>

        """
        tmp = self.find_objects_wo_child(
            parentspec,
            childspec,
            ignore_ws=ignore_ws,
        )
        return [ii.text for ii in tmp]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_children_w_parents(self, parentspec, childspec, ignore_ws=False):
        r"""Parse through the children of all parents matching parentspec,
        and return a list of children that matched the childspec.

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
            A list of matching child configuration lines

        Examples
        --------
        This example finds the port-security lines on FastEthernet0/1 in
        following config...

        .. code::

           !
           interface FastEthernet0/1
            switchport access vlan 532
            switchport port-security
            switchport port-security violation protect
            switchport port-security aging time 5
            switchport port-security aging type inactivity
            spanning-tree portfast
            spanning-tree bpduguard enable
           !
           interface FastEthernet0/2
            switchport access vlan 300
            spanning-tree portfast
            spanning-tree bpduguard enable
           !
           interface FastEthernet0/2
            duplex full
            speed 100
            switchport access vlan 300
            spanning-tree portfast
            spanning-tree bpduguard enable
           !

        The following lines should be returned:

        .. code::

            switchport port-security
            switchport port-security violation protect
            switchport port-security aging time 5
            switchport port-security aging type inactivity

        We do this by quering `find_children_w_parents()`; we set our
        parent as `^interface` and set the child as
        `switchport port-security`.

        .. code-block:: python
           :emphasize-lines: 26

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet0/1',
           ...           ' switchport access vlan 532',
           ...           ' switchport port-security',
           ...           ' switchport port-security violation protect',
           ...           ' switchport port-security aging time 5',
           ...           ' switchport port-security aging type inactivity',
           ...           ' spanning-tree portfast',
           ...           ' spanning-tree bpduguard enable',
           ...           '!',
           ...           'interface FastEthernet0/2',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           ' spanning-tree bpduguard enable',
           ...           '!',
           ...           'interface FastEthernet0/3',
           ...           ' duplex full',
           ...           ' speed 100',
           ...           ' switchport access vlan 300',
           ...           ' spanning-tree portfast',
           ...           ' spanning-tree bpduguard enable',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.find_children_w_parents('^interface\sFastEthernet0/1',
           ... 'port-security')
           [' switchport port-security', ' switchport port-security violation protect', ' switchport port-security aging time 5', ' switchport port-security aging type inactivity']
           >>>

        """
        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        retval = set()
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = child.all_parents
            for parent in parents:
                if re.search(parentspec, parent.text):
                    retval.add(child)

        return [ii.text for ii in sorted(retval)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def find_objects_w_parents(self, parentspec, childspec, ignore_ws=False):
        r"""Parse through the children of all parents matching parentspec,
        and return a list of child objects, which matched the childspec.

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

        We do this by quering `find_objects_w_parents()`; we set our
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
           >>> p.find_objects_w_parents('^\s*interfaces',
           ... r'\s+ge-0/0/1')
           [<IOSCfgLine # 7 '    ge-0/0/1' (parent is # 0)>]
           >>>

        """
        if ignore_ws:
            parentspec = build_space_tolerant_regex(parentspec)
            childspec = build_space_tolerant_regex(childspec)

        retval = set()
        childobjs = self._find_line_OBJ(childspec)
        for child in childobjs:
            parents = child.all_parents
            for parent in parents:
                if re.search(parentspec, parent.text):
                    retval.add(child)

        return sorted(retval)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
    def insert_before(
        self,
        exist_val="",
        new_val="",
        exactmatch=False,
        ignore_ws=False,
        atomic=False,
        new_val_indent = -1,
        **kwargs
    ):
        r"""
        Find all :class:`~models_cisco.IOSCfgLine` objects whose text
        matches ``exist_val``, and insert ``new_val`` before those line
        objects.

        If ``new_val_indent`` >= 0, then ``new_val`` will be inserted with
        the requested indent regardless of any existing indent on ``new_val``.

        Parameters
        ----------
        exist_val : str
            Text regular expression for the line to be matched
        new_val : str
            text to be inserted before all occurances of exist_val
        exactmatch : bool
            if exactmatch is True, do not match on substrings
        ignore_ws : bool
            if ignore_ws is True, ignore whitespace differences
        atomic : bool
            if atomic is True, this change will be commited
        new_val_ident : int
            integer indent for new_val

        Examples
        --------

        .. code-block:: python
           :emphasize-lines: 15

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet 0/1',
           ...           ' description Test intf to CloudFlare',
           ...           ' ip address 192.0.2.1 255.255.255.252',
           ...           ' no ip unreachables',
           ...           '!',
           ...           'interface FastEthernet 0/2',
           ...           ' description ProxySG model 8100',
           ...           ' ip address 192.0.2.5 255.255.255.252',
           ...           ' no ip unreachables',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.insert_before(r"interface\s+FastEthernet\s+0\/2", "default interface FastEthernet 0/2", new_val_indent=0)
        """

        ######################################################################
        #
        # CiscoConfParse().insert_before is a wrapper for CiscoConfParse().ConfigObjs.insert_before()
        #
        # Named parameter migration warnings...
        #   - `linespec` is now called exist_val
        #   - `insertstr` is now called new_val
        ######################################################################
        if kwargs.get("linespec", "") != "":
            exist_val = kwargs.get("linespec")
            logger.info(
                "The parameter named `linespec` is deprecated.  Please use `exist_val` instead",
            )
        if kwargs.get("insertstr", "") != "":
            new_val = kwargs.get("insertstr")
            logger.info(
                "The parameter named `insertstr` is deprecated.  Please use `new_val` instead",
            )


        err_exist_val = "FATAL: exist_val:'%s' must be a non-empty string" % exist_val
        if not isinstance(exist_val, str) or exist_val =="":
            raise ValueError(err_exist_val)
        err_new_val = "FATAL: new_val:'%s' must be a string" % new_val
        if not isinstance(new_val, str) or new_val =="":
            raise ValueError(err_new_val)

        enforce_valid_types(exactmatch, (bool,),
            "exactmatch parameter must be a bool."
        )
        enforce_valid_types(ignore_ws, (bool,),
            "ignore_ws parameter must be a bool."
        )
        enforce_valid_types(new_val_indent, (int,),
            "new_val_indent parameter must be a int."
        )

        objs = self.find_objects(linespec=exist_val, exactmatch=exactmatch, ignore_ws=ignore_ws)
        for _obj in objs:
            exist_indent = len(_obj._text) - len(_obj._text.lstrip())
            assert exist_indent == _obj.indent
            if new_val_indent >= 0:
                # Forces an indent on ``new_val``...
                self.ConfigObjs.insert_before(exist_val, new_val_indent * " " + new_val.lstrip())
            else:
                # Does not force an indent on ``new_val``...
                self.ConfigObjs.insert_before(exist_val, new_val)

        if atomic is True:
            self.atomic()
        return [ii.text for ii in sorted(objs)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def insert_after(
        self,
        exist_val="",
        new_val="",
        exactmatch=False,
        ignore_ws=False,
        atomic=False,
        new_val_indent = -1,
        **kwargs
    ):
        r"""
        Find all :class:`~models_cisco.IOSCfgLine` objects whose text
        matches ``exist_val``, and insert ``new_val`` after those line
        objects.

        If ``new_val_indent`` >= 0, then ``new_val`` will be inserted with
        the requested indent regardless of any existing indent on ``new_val``.

        Parameters
        ----------
        exist_val : str
            Text regular expression for the line to be matched
        new_val : str
            text to be inserted after all occurances of exist_val
        exactmatch : bool
            if exactmatch is True, do not match on substrings
        ignore_ws : bool
            if ignore_ws is True, ignore whitespace differences
        atomic : bool
            if atomic is True, this change will be commited
        new_val_ident : int
            integer indent for new_val

        Examples
        --------

        .. code-block:: python
           :emphasize-lines: 15

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = ['!',
           ...           'interface FastEthernet 0/1',
           ...           ' description Test intf to CloudFlare',
           ...           ' ip address 192.0.2.1 255.255.255.252',
           ...           ' no ip unreachables',
           ...           '!',
           ...           'interface FastEthernet 0/2',
           ...           ' description ProxySG model 8100',
           ...           ' ip address 192.0.2.5 255.255.255.252',
           ...           ' no ip unreachables',
           ...           '!',
           ...     ]
           >>> p = CiscoConfParse(config=config)
           >>> p.insert_after(r"interface\s+FastEthernet\s+0\/2", "no ip proxy-arp", new_val_indent=1)
        """

        ######################################################################
        #
        # CiscoConfParse().insert_after is a wrapper for CiscoConfParse().ConfigObjs.insert_after()
        #
        #
        # Named parameter migration warnings...
        #   - `linespec` is now called exist_val
        #   - `insertstr` is now called new_val
        ######################################################################
        if kwargs.get("linespec", "") != "":
            exist_val = kwargs.get("linespec")
            logger.info(
                "The parameter named `linespec` is deprecated.  Please use `exist_val` instead",
            )
        if kwargs.get("insertstr", "") != "":
            new_val = kwargs.get("insertstr")
            logger.info(
                "The parameter named `insertstr` is deprecated.  Please use `new_val` instead",
            )

        err_exist_val = "FATAL: exist_val:'%s' must be a string" % exist_val
        err_new_val = "FATAL: new_val:'%s' must be a string" % new_val
        enforce_valid_types(exist_val, (str,),
            err_exist_val
        )
        enforce_valid_types(new_val, (str,),
            err_new_val
        )
        enforce_valid_types(exactmatch, (bool,),
            "exactmatch must be a bool"
        )
        enforce_valid_types(ignore_ws, (bool,),
            "ignore_ws must be a bool"
        )
        enforce_valid_types(new_val_indent, (int,),
            "new_val_indent must be a int"
        )

        objs = self.find_objects(linespec=exist_val, exactmatch=exactmatch, ignore_ws=ignore_ws)
        for _obj in objs:
            exist_indent = len(_obj._text) - len(_obj._text.lstrip())
            assert exist_indent == _obj.indent
            if new_val_indent >= 0:
                # Forces an indent on ``new_val``...
                self.ConfigObjs.insert_after(exist_val, new_val_indent*" " + new_val.lstrip())
            else:
                # Does not force an indent on ``new_val``...
                self.ConfigObjs.insert_after(exist_val, new_val)

        if atomic is True:
            self.atomic()
        return [ii.text for ii in sorted(objs)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def insert_after_child(
        self,
        parentspec,
        childspec,
        insertstr="",
        exactmatch=False,
        excludespec=None,
        ignore_ws=False,
        atomic=False,
    ):
        """
        Find all :class:`~models_cisco.IOSCfgLine` objects whose text
        matches ``linespec`` and have a child matching ``childspec``, and
        insert an :class:`~models_cisco.IOSCfgLine` object for ``insertstr``
        after those child objects.
        """
        retval = list()
        modified = False
        for pobj in self._find_line_OBJ(parentspec, exactmatch=exactmatch):
            if excludespec and re.search(excludespec, pobj.text):
                # Exclude replacements on pobj lines which match excludespec
                continue
            for cobj in pobj.children:
                if excludespec and re.search(excludespec, cobj.text):
                    # Exclude replacements on pobj lines which match excludespec
                    continue
                elif re.search(childspec, cobj.text):
                    modified = True
                    retval.append(
                        self.ConfigObjs.insert_after(
                            cobj,
                            insertstr,
                            atomic=atomic,
                        ),
                    )
                else:
                    pass
        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
    def prepend_line(self, linespec):
        """Unconditionally insert an :class:`~models_cisco.IOSCfgLine` object
        for ``linespec`` (a text line) at the top of the configuration"""
        self.ConfigObjs.insert(0, linespec)
        return self.ConfigObjs[0]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
        self.ConfigObjs.append(linespec)
        return self.ConfigObjs[-1]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
            # self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()

        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
            # self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()
        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
            # self.ConfigObjs._reassign_linenums()
            self.ConfigObjs._bootstrap_from_text()

        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def re_search_children(self, regex, recurse=False):
        """Use ``regex`` to search for root parents in the config with text matching regex.  If `recurse` is False, only root parent objects are returned.  A list of matching objects is returned.

        This method is very similar to :func:`~ciscoconfparse.CiscoConfParse.find_objects` (when `recurse` is True); however it was written in response to the use-case described in `Github Issue #156 <https://github.com/mpenning/ciscoconfparse/issues/156>`_.

        Parameters
        ----------
        regex : str
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
            return [
                obj for obj in self.find_objects(regex) if (obj.parent is obj)
            ]
        else:
            # Return any matching object
            return [obj for obj in self.find_objects(regex)]

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def re_match_iter_typed(
        self,
        regex,
        group=1,
        result_type=str,
        default="",
        untyped_default=False,
    ):
        r"""Use ``regex`` to search the root parents in the config
        and return the contents of the regular expression group, at the
        integer ``group`` index, cast as ``result_type``; if there is no
        match, ``default`` is returned.

        Notes
        -----
        Only the first regex match is returned.

        Parameters
        ----------
        regex : str
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

            mm = re.search(regex, cobj.text)
            if (mm is not None):
                return result_type(mm.group(group))
        ## Ref Github issue #121
        if untyped_default:
            return default
        else:
            return result_type(default)

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    @deprecat(reason="req_cfgspec_all_diff() is obsolete; use HDiff() instead.  req_cfgspec_all_diff() will be removed", version = '1.7.0')
    def req_cfgspec_all_diff(self, cfgspec, ignore_ws=False):
        """
        req_cfgspec_all_diff takes a list of required configuration lines,
        parses through the configuration, and ensures that none of cfgspec's
        lines are missing from the configuration.  req_cfgspec_all_diff
        returns a list of missing lines from the config.

        One example use of this method is when you need to enforce routing
        protocol standards, or standards against interface configurations.

        .. warning::

           `req_cfgspec_excl_diff()` and `req_cfgspec_all_diff()` will be deprecated / removed in the future.  `HDiff().unified_diffs()` or `HDiff().raw_diff_dicts()` can be used going forward; however, "some assembly will be required".


        Examples
        --------

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> required_lines = [
        ...     "logging 172.28.26.15",
        ...     "logging 172.16.1.5",
        ...     ]
        >>> diffs = p.req_cfgspec_all_diff(required_lines)
        >>> diffs
        ['logging 172.16.1.5']
        >>>
        """

        # warning issued 2022-06-01
        deprecation_warn_str = "`req_cfgspec_all_diff()` will be deprecated and removed in future versions."
        warnings.warn(deprecation_warn_str, DeprecationWarning)

        rgx = dict()
        if ignore_ws is True:
            for line in cfgspec:
                rgx[line] = build_space_tolerant_regex(line)

        skip_cfgspec = dict()
        retval = list()
        matches = self._find_line_OBJ("[a-zA-Z]")
        ## Make a list of unnecessary cfgspec lines
        for lineobj in matches:
            for reqline in cfgspec:
                if ignore_ws:
                    if re.search(
                        r"^" + rgx[reqline] + "$",
                        lineobj.text.strip(),
                    ):
                        skip_cfgspec[reqline] = True
                else:
                    if lineobj.text.strip() == reqline.strip():
                        skip_cfgspec[reqline] = True
        ## Add items to be configured
        ## TODO: Find a way to add the parent of the missing lines
        for line in cfgspec:
            if not skip_cfgspec.get(line, False):
                retval.append(line)

        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    @deprecat(reason="req_cfgspec_excl_diff() is obsolete; use HDiff() instead.  req_cfgspec_excl_diff() will be removed", version = '1.7.0')
    def req_cfgspec_excl_diff(self, linespec, uncfgspec, cfgspec):
        r"""
        req_cfgspec_excl_diff accepts a linespec, an unconfig spec, and
        a list of required configuration elements.  Return a list of
        configuration diffs to make the configuration comply.  **All** other
        config lines matching the linespec that are *not* listed in the
        cfgspec will be removed with the uncfgspec regex.

        Uses for this method include the need to enforce syslog, acl, or
        aaa standards.

        .. warning::

           `req_cfgspec_excl_diff()` and `req_cfgspec_all_diff()` will be deprecated / removed in the future.  `HDiff().unified_diffs()` or `HDiff().raw_diff_dicts()` can be used going forward; however, "some assembly will be required".

        Examples
        --------

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> required_lines = [
        ...     "logging 172.16.1.5",
        ...     "logging 1.10.20.30",
        ...     "logging 192.168.1.1",
        ...     ]
        >>> linespec = "logging\s+\d+\.\d+\.\d+\.\d+"
        >>> unconfspec = linespec
        >>> diffs = p.req_cfgspec_excl_diff(linespec, unconfspec,
        ...     required_lines)
        >>> diffs
        ['no logging 172.28.26.15', 'logging 172.16.1.5', 'logging 1.10.20.30', 'logging 192.168.1.1']
        >>>
        """

        # warning issued 2022-06-01
        deprecation_warn_str = "`req_cfgspec_excl_diff()` will be deprecated and removed in future versions."
        warnings.warn(deprecation_warn_str, DeprecationWarning)

        violate_objs = list()
        uncfg_objs = list()
        skip_cfgspec = dict()
        retval = list()
        matches = self._find_line_OBJ(linespec)
        ## Make a list of lineobject violations
        for lineobj in matches:
            # Look for config lines to unconfigure
            accept_lineobj = False
            for reqline in cfgspec:
                if lineobj.text.strip() == reqline.strip():
                    accept_lineobj = True
                    skip_cfgspec[reqline] = True
            if accept_lineobj is False:
                # If a violation is found...
                violate_objs.append(lineobj)
                result = re.search(uncfgspec, lineobj.text)
                # add uncfgtext to the violator's lineobject
                lineobj.add_uncfgtext(result.group(0))
        ## Make the list of unconfig objects, recurse through parents
        for vobj in violate_objs:
            parent_objs = vobj.all_parents
            for parent_obj in parent_objs:
                uncfg_objs.append(parent_obj)
            uncfg_objs.append(vobj)
        retval = self._objects_to_uncfg(uncfg_objs, violate_objs)
        ## Add missing lines...
        ## TODO: Find a way to add the parent of the missing lines
        for line in cfgspec:
            if not skip_cfgspec.get(line, False):
                retval.append(line)

        return retval

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
    @deprecat(reason="sync_diff() is obsolete; use HDiff() instead.", version = '1.7.0')
    def sync_diff(
        self,
        cfgspec=None,
        linespec=None,
        uncfgspec=None,
        ignore_order=True,
        remove_lines=True,
        syntax="",
        debug=0,
    ):
        r"""
        ``sync_diff()`` accepts a list of required configuration elements,
        a linespec, and an unconfig spec.  This method return a list of
        Cisco IOS-style configuration diffs to make the configuration comply
        with cfgspec.

        Internally, `sync_diff()` is implemented with :class:`~ciscoconfparse.HDiff()`.


        Parameters
        ----------
        cfgspec : list
            A list of required configuration lines to be used as a config template
        linespec : str
            A regular expression, which filters lines to be diff'd
        uncfgspec : str
            A regular expression, which is used to unconfigure lines.  When ciscoconfparse removes a line, it takes the entire portion of the line that matches ``uncfgspec``, and prepends "no" to it.
        ignore_order : bool
            Indicates whether the configuration should be reordered to minimize the number of diffs.  Default: True (usually it's a good idea to leave ``ignore_order`` True, except for ACL comparisions)
        remove_lines : bool
            Indicates whether the lines which are *not* in ``cfgspec`` should be removed.  Default: True.  When ``remove_lines`` is True, all other config lines matching the linespec that are *not* listed in the cfgspec will be removed with the uncfgspec regex.
        syntax : str
            The expected syntax of the diff lines.  Default is an empty string, ''
        debug : int
            Miscellaneous debugging; Default: 0

        Returns
        -------
        list
            A list of string configuration diffs


        Uses for this method include the need to enforce syslog, acl, or
        aaa standards.

        Examples
        --------

        >>> from ciscoconfparse import CiscoConfParse
        >>> config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     ]
        >>> p = CiscoConfParse(config=config)
        >>> required_lines = [
        ...     "logging 172.16.1.5",
        ...     "logging 1.10.20.30",
        ...     "logging 192.168.1.1",
        ...     ]
        >>> linespec = "logging\s+\d+\.\d+\.\d+\.\d+"
        >>> uncfgspec = linespec
        >>> diffs = p.sync_diff(required_lines,
        ...     linespec, uncfgspec)  # doctest: +SKIP
        >>> diffs                     # doctest: +SKIP
        ['no logging 172.28.26.15', 'logging 172.16.1.5', 'logging 1.10.20.30', 'logging 192.168.1.1']
        >>>
        >>> before_config = [
        ... 'logging trap debugging',
        ... 'logging 172.28.26.15',
        ... 'interface GigabitEthernet0',
        ... ' ip address 1.1.1.1 255.255.255.0',
        ... ]
        >>>
        >>> after_config = [
        ... 'no logging console guaranteed',
        ... 'logging 172.28.26.15',
        ... 'interface GigabitEthernet0',
        ... ' no ip proxy-arp',
        ... ]
        >>>
        >>> my_diff = HDiff(before_config, desired_config)
        """

        if cfgspec is None:
            cfgspec = self._list

        if linespec is None:
            raise ValueError("linespec is a required parameter")

        enforce_valid_types(cfgspec, (Sequence,),
            "cfgspec must be an instance of collections.abc.Sequence()"
        )
        enforce_valid_types(linespec, (str,),
            "linespec must be a string"
        )
        enforce_valid_types(uncfgspec, (str,),
            "uncfgspec must be a string"
        )
        enforce_valid_types(ignore_order, (bool,),
            "ignore_order must be a bool"
        )
        enforce_valid_types(remove_lines, (bool,),
            "remove_lines must be a bool"
        )
        enforce_valid_types(syntax, (str,),
            "syntax must be a str"
        )
        enforce_valid_types(debug, (int,),
            "debug must be an int"
        )

        lrgx = re.compile(linespec)
        retval = []

        _syntax = syntax or self.syntax
        diff = HDiff(before_config=self.ioscfg, after_config=cfgspec, syntax=_syntax, debug=debug)

        for tmp in diff.all_output_dicts:

            action = tmp["diff_word"]
            command = tmp["text"]
            indent = tmp["indent"]
            parents = tmp["parents"]

            # Skip lines that are not part of the expected diff...
            if not lrgx.search(command):
                continue

            if remove_lines is True and action == 'remove':
                if _syntax in set({"ios", "nxos", "asa", }):
                    uu = re.search(uncfgspec, command)
                    remove_cmd = indent * " " + "no " + uu.group(0).strip()
                    # 'no no ' will become ''...
                    remove_cmd = fix_repeated_words(remove_cmd, word="no")

                    # NOTE: if HDiff().compress_dict_diffs() was working as
                    # planned, this manual parent handling might not be
                    # required...
                    #
                    # Append parent remove_cmd command entries (if any...)
                    for pcmd in parents:
                        retval.append(pcmd)

                    retval.append(remove_cmd)
                else:
                    raise ValueError("Cannot remove the command for syntax={}".format(self.syntax))

            elif action == 'add':

                # NOTE: if HDiff().compress_dict_diffs() was working as
                # planned, this manual parent handling might not be
                # required...
                #
                # Append parent command entries (if any...)
                for pcmd in parents:
                    retval.append(pcmd)

                retval.append(command)

        return retval


    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def save_as(self, filepath):
        """Save a text copy of the configuration at ``filepath``; this
        method uses the OperatingSystem's native line separators (such as
        ``\\r\\n`` in Windows)."""
        try:
            with open(filepath, "w", encoding=self.encoding) as newconf:
                for line in self.ioscfg:
                    newconf.write(line + "\n")
            return True
        except Exception as ee:
            logger.error(str(ee))
            raise ee

    ### The methods below are marked SEMI-PRIVATE because they return an object
    ###  or iterable of objects instead of the configuration text itself.

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
    def _find_line_OBJ(self, linespec, exactmatch=False):
        """SEMI-PRIVATE: Find objects whose text matches the linespec"""

        if self.ConfigObjs is None:
            err = "ConfigObjs is None. self.ConfigObjs logic failed."
            raise ValueError(err)

        if self.debug >= 2:
            logger.debug(
                "Looking for match of linespec='%s', exactmatch=%s" %
                (linespec, exactmatch),
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
    @logger.catch(reraise=True)
    def _find_sibling_OBJ(self, lineobject):
        """SEMI-PRIVATE: Takes a singe object and returns a list of sibling
        objects"""
        siblings = lineobject.parent.children
        return siblings

    # This method is on CiscoConfParse()
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
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
    @logger.catch(reraise=True)
    def _objects_to_uncfg(self, objectlist, unconflist):
        # Used by req_cfgspec_excl_diff()
        retval = list()
        unconfdict = dict()
        for unconf in unconflist:
            unconfdict[unconf] = "DEFINED"
        for obj in self._unique_OBJ(objectlist):
            if unconfdict.get(obj, None) == "DEFINED":
                retval.append(obj.uncfgtext)
            else:
                retval.append(obj.text)
        return retval


class HDiff(object):
    """An object to implement diffs against configs or config templates.  By default, the output diffs are ordered roughly as before_config, then after_config.  HDiff() is intended as an internal CiscoConfParse building-block to implement methods such as :meth:`ciscoconfparse.CiscoConfParse.sync_diff`"""

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def __init__(
        self,
        before_config=None,
        after_config=None,
        syntax="ios",
        ordered_diff=False,
        allow_duplicates=False,
        output_format="unified",
        debug=0,
    ):
        """
        Initialize HDiff().

        Parameters
        ----------
        before_config : list
            A list of text configuration statements representing the original config. Default value: `None`
        after_config : list
            A list of text configuration statements representing the most-recent config. Default value: `None`
        syntax : str
            A string holding the configuration type.  Default: 'ios'.  Must be one of: 'ios', 'nxos', 'asa', 'junos'.  Use 'junos' for any brace-delimited network configuration (including F5, Palo Alto, etc...).
        ordered_diff : bool
            A boolean for whether the returned-diff lines must be ordered.  Default value: `False`
        allow_duplicates : bool
            A boolean for whether the returned-diff lines may be duplicated.  Default value: `False`
        debug : int
            ``debug`` defaults to 0, and should be kept that way unless you're working on a tricky config diff problem.  Debug range goes from 0 (no debugging) to 5 (max debugging).  Debug output is not particularly friendly.


        Returns
        -------
        :class:`~ciscoconfparse.HDiff()`

        Examples
        --------
        This example illustrates how to diff a simple Cisco IOS configuration
        with :class:`~ciscoconfparse.HDiff()` into a variable called
        ``parse``.  This example also illustrates what the ``ConfigObjs``
        and ``ioscfg`` attributes contain.

        >>> from ciscoconfparse import HDiff
        >>> begin_config = [
        ...     'logging trap debugging',
        ...     'logging 172.28.26.15',
        ...     'interface GigabitEthernet0',
        ...     ' ip address 1.1.1.1 255.255.255.0',
        ...     ]
        >>> desired_config = [
        ...     'no logging console guaranteed',
        ...     'logging 172.28.26.15',
        ...     'interface GigabitEthernet0',
        ...     ' no ip proxy-arp',
        ...     ]
        >>>
        >>> # by default, diffs are ordered as before_config then after_config
        >>> diff_obj = HDiff(begin_config, desired_config, syntax='ios')
        >>> diff_obj
        <ciscoconfparse.ciscoconfparse.HDiff object at 0x7f8fd292c160>
        >>> for line in diff_obj.unified_diffs():
        ...     print(line)
        ...
        --- /tmp/before 2023-02-10 09:22:08.476463
        +++ /tmp/after  2023-02-10 09:22:08.476463
        @@ -2,1 +2,1 @@
        -logging trap debugging
         logging 172.28.26.15
         interface GigabitEthernet0
        + no ip proxy-arp
        - ip address 1.1.1.1 255.255.255.0
        +no logging console guaranteed
        >>>
        >>>
        >>> # diff_obj.all_output_dicts is a list of dict
        >>> for elem in diff_obj.all_output_dicts:
        ...     print(elem)
        ...
        {'linenum': -1, 'diff_side': 'before', 'diff_word': 'remove', 'indent': 0, 'parents': [], 'text': 'logging trap debugging'}
        {'linenum': -1, 'diff_side': 'before', 'diff_word': 'keep', 'indent': 0, 'parents': [], 'text': 'logging 172.28.26.15'}
        {'linenum': -1, 'diff_side': 'before', 'diff_word': 'keep', 'indent': 0, 'parents': [], 'text': 'interface GigabitEthernet0'}
        {'linenum': 3, 'diff_side': 'after', 'diff_word': 'add', 'indent': 1, 'parents': ['interface GigabitEthernet0'], 'text': ' no ip proxy-arp'}
        {'linenum': -1, 'diff_side': 'before', 'diff_word': 'remove', 'indent': 1, 'parents': ['interface GigabitEthernet0'], 'text': ' ip address 1.1.1.1 255.255.255.0'}
        {'linenum': 0, 'diff_side': 'after', 'diff_word': 'add', 'indent': 0, 'parents': [], 'text': 'no logging console-guaranteed'}
        >>>

        Attributes
        ----------
        parse_before : :class:`~ciscoconfparse.CiscoConfParse`
            The parsed object for `CiscoConfParse(before_config)`
        parse_after : :class:`~ciscoconfparse.CiscoConfParse`
            The parsed object for `CiscoConfParse(after_config)`
        all_output_dicts : list
            A `list` of all the output dicts
        """

        enforce_valid_types(before_config, (str, Sequence, CiscoConfParse,),
            "before_config parameter must be a instance of string, collections.abc.Sequence, or CiscoConfParse instance."
        )
        enforce_valid_types(after_config, (str, Sequence, CiscoConfParse,),
            "after_config parameter must be a instance of string, collections.abc.Sequence, or CiscoConfParse instance."
        )
        enforce_valid_types(syntax, (str,),
            "syntax parameter must be a str."
        )
        enforce_valid_types(ordered_diff, (bool,),
            "ordered_diff parameter must be a bool."
        )
        enforce_valid_types(allow_duplicates, (bool,),
            "allow_duplicates parameter must be a bool."
        )
        enforce_valid_types(debug, (int,),
            "debug parameter must be an int."
        )
        assert syntax in set(ALL_VALID_SYNTAX)

        # Initialize attributes...
        self.syntax = syntax
        self.ordered_diff = ordered_diff
        self.before_config = before_config
        self.after_config = after_config
        self.before_obj = None
        self.after_obj = None
        self.parse_before = None
        self.parse_after = None

        self.before_obj_list = None
        self.after_obj_list = None
        # all_output_dicts contains the diff results as a list of dicts...
        self.all_output_dicts = []
        self.debug = debug


        # TODO - incorporate difflib.get_close_matches() to reorder the
        #     diff (in unified format)
        if syntax=="nxos":
            blank_lines_ignore = False
        else:
            blank_lines_ignore = True

        if not isinstance(before_config, CiscoConfParse):
            self.parse_before = CiscoConfParse(before_config, syntax=syntax, ignore_blank_lines=blank_lines_ignore)

        if not isinstance(after_config, CiscoConfParse):
            self.parse_after = CiscoConfParse(after_config, syntax=syntax, ignore_blank_lines=blank_lines_ignore)


        assert self.parse_before.syntax == self.parse_after.syntax

        if debug > 0:
            logger.info(
                "HDiff().syntax={}".format(self.parse_before.syntax)
            )

        if debug > 1:
            logger.info(
                "HDiff().before_config={0}{1}".format(
                os.linesep, '\n'.join(before_config)
            ))
            logger.info(
                "HDiff().after_config={0}{1}".format(
                os.linesep, '\n'.join(after_config)
            ))

        self.build_diff_obj_lists()

        if syntax=='ios':
            self.build_ios_diffs()

    def build_diff_obj_lists(self):
        assert isinstance(self.parse_before, CiscoConfParse)
        assert isinstance(self.parse_after, CiscoConfParse)

        for before_obj in self.parse_before.objs:
            before_obj.diff_side = "before"

        for after_obj in self.parse_after.objs:
            after_obj.diff_side = "after"

        # NOTE removed in 1.7.15...
        # valid_after_obj_diff_words = set({"add", "unchanged"})

        # Get a list of *CfgLine() before objects which are relevant to the diff...
        self.before_obj_list = self.build_diff_obj_list(
            parse=self.parse_before, default_diff_word="remove"
        )
        # Get a list of *CfgLine() after objects which are relevant to the diff...
        self.after_obj_list = self.build_diff_obj_list(
            parse=self.parse_after, default_diff_word="unknown"
        )

    def build_ios_diffs(self):
        # Handle add / move / change. change is diff_word: remove + diff_word: add
        for after_obj in self.after_obj_list:
            assert isinstance(after_obj, (BaseCfgLine,))

            # Ensure we start with after_obj.diff_word as default_word...
            # it's unknown at this time... NOTE - even though all
            # after_obj.diff_word values are changed in
            # self.find_in_before_obj_list() below, setting to a default state
            # is useful to catch any future bugs...
            assert after_obj.diff_word == "unknown"

            # Check whether we keep the before object, or add a new after object...
            # before_list and after_obj may be rewritten / changed here...
            self.before_obj_list, after_obj = self.find_in_before_obj_list(
                self.before_obj_list, after_obj)

            # Ensure that we rewrote after_obj.diff_word from default_diff_word_after
            # NOTE removed in 1.7.15...
            #assert after_obj.diff_word in valid_after_obj_diff_words

        # At this stage, `dict_diffs()` returns duplicate parent lines...
        tmp_line_dicts = self.dict_diffs(self.before_obj_list, self.after_obj_list)

        # Remove duplicate parent lines with `compress_dict_diffs()`
        self.all_output_dicts = self.compress_dict_diffs(tmp_line_dicts, debug=self.debug)

        if False:
            # status quo sorts before_config lines, then after_config lines...
            #
            # There is no support for special sorting behavior at this point...
            self.sort_lines()


    # This method is on HDiff()
    @logger.catch(reraise=True)
    def DEPRECATED_raw_diff_dicts(self):
        return self.all_output_dicts

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def unified_diff_header(self):
        """
        Return a unified diff header similar to this...

        --- /dev/null 2022-04-25 16:33:07.434605
        +++ /dev/null 2022-04-25 16:33:07.434605
        @@ -7,3 +9,3 @@

        """
        # Good unified diff header description here:
        #     https://unix.stackexchange.com/a/480542/6766

        # return the unified diff header output... suitable for ydiff
        unified_diff_header = list()

        # Add a text header similar to that found in unix unified diffs
        #
        # Tally lines for the unified diff header...
        udiff_timestamp = str(datetime.now().isoformat()).replace("T", " ")
        unified_diff_header.append("--- /tmp/before " + udiff_timestamp)
        unified_diff_header.append("+++ /tmp/after  " + udiff_timestamp)

        left_hand_changed, right_hand_changed = 0, 0
        left_hand_start, right_hand_start = 0, 0
        for idx, obj in enumerate(self.before_obj_list):
            before_word = obj.diff_word
            if before_word == "remove":
                left_hand_start = idx + 1
                break
        for idx, obj in enumerate(self.before_obj_list):
            before_word = obj.diff_word
            if before_word == "remove":
                left_hand_changed += 1

        for idx, obj in enumerate(self.after_obj_list):
            after_word = obj.diff_word
            if after_word == "add":
                right_hand_start = idx + 1
                break
        for idx, obj in enumerate(self.after_obj_list):
            after_word = obj.diff_word
            if after_word == "add":
                right_hand_changed += 1

        # render the unified diff header. Assume we only generate one diff hunk
        unified_diff_header.append("@@ -{},{} +{},{} @@".format(
                    left_hand_changed, left_hand_start, right_hand_changed,
                    right_hand_start))

        return unified_diff_header

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def unified_diffs(self, header=True):
        """
        Return a python list of text which contains the unified diff of the
        before and after HDiff() configurations.
        """

        # gather unified diff output...
        if header is True:
            unified_diff_list = self.unified_diff_header()
        else:
            # Unit tests are easier without the unified diff header...
            unified_diff_list = []

        unified_diff_list.extend(self.unified_diffs_contents())

        return unified_diff_list


    # This method is on HDiff()
    @logger.catch(reraise=True)
    def unified_diffs_contents(self, header=True):
        """
        Return a python list of unified diff contents which contain the unified diff of the
        before and after HDiff() configurations.
        """
        unified_diff_list = []
        for line_dict in self.all_output_dicts:

            if not isinstance(line_dict, dict):
                raise ValueError

            if line_dict["diff_word"] == "add":
                unified_diff_list.append("+" + line_dict["text"])
            elif line_dict["diff_word"] == "remove":
                unified_diff_list.append("-" + line_dict["text"])
            else:
                unified_diff_list.append(" " + line_dict["text"])

        return unified_diff_list

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def sort_lines(self, after_lines=None):
        """
        Typical output line dict-format...
        {
            "linenum": -1,   # before line numbers are skipped...
            "diff_side": "before",
            "diff_word": "keep",
            "indent": 0,
            "parents": [],
            "text": bobj.text,
            "diff_id_list": bobj.diff_id_list,
        }
        """
        # FIXME -> no support for an ordered_diff yet... specifically, parents are
        # not ordered yet and siblings are not ordered either in the diff results.
        # The ordered_diff bool support should order diff parents lines (such as
        # ^interface foo) in the same manner that they show up in the after_config
        # parameter...
        #
        pass

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def dict_diffs(self, before_obj_list, after_obj_list):
        ############################################
        # Render diffs
        ############################################
        all_dict_lines = []
        for bobj in before_obj_list:

            if not isinstance(bobj, BaseCfgLine):
                raise ValueError

            assert bobj.diff_side == "before"

            # FIXME - I am disabling this to prevent redundant rendering of before_obj and after_obj
            if bobj.diff_word == "keep" and bobj.diff_rendered is False:
                bobj.diff_rendered = True
                all_dict_lines.append(
                    {
                        "linenum": -1,   # For now, do not include bobj.linenum
                        "diff_side": "before",
                        "diff_word": "keep",
                        "indent": bobj.indent,
                        "parents": [ii.text for ii in bobj.all_parents],
                        "text": bobj.text,
                        "diff_id_list": bobj.diff_id_list,
                    }
                )
                continue

            elif bobj.diff_word == "remove" and bobj.diff_rendered is False:
                bobj.diff_rendered = True
                all_dict_lines.append(
                    {
                        "linenum": -1,   # For now, do not include bobj.linenum
                        "diff_side": "before",
                        "diff_word": "remove",
                        "indent": bobj.indent,
                        "parents": [ii.text for ii in bobj.all_parents],
                        "text": bobj.text,
                        "diff_id_list": bobj.diff_id_list,
                    }
                )
                continue

            else:
                raise NotImplementedError()

        # Render all "after" lines we haven't considered yet...
        tmp_dict_list = list()
        for aobj in after_obj_list:
            tmp_dict_list = self.render_after_obj_diffs(aobj)
            all_dict_lines.extend(tmp_dict_list)

        return all_dict_lines

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def build_diff_obj_list(
        self, parse=None, default_diff_word=None, consider_whitespace=False
    ):
        """
        Return a list of *CfgLine() objects which are relevant to the diff...
        """
        assert parse is not None
        if not isinstance(default_diff_word, str):
            raise ValueError
        retval = []
        for obj in parse.objs:

            # Will multiple spaces between diff_words affect a diff match?
            if consider_whitespace is False:
                # Rewrite obj.text to remove multiple spaces between terms...
                obj.text = " " * obj.indent + " ".join(obj.text.strip().split())

            # Track whether this term was rendered in the output yet...
            obj.diff_rendered = False

            # Use a single 'diff_word' to describe the diff status of this
            # configuration line...
            obj.diff_word = default_diff_word
            retval.append(obj)

        return retval

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def find_in_before_obj_list(
        self, before_obj_list, after_obj, consider_whitespace=False, debug=0
    ):
        """
        Find matches for after_obj in before_obj_list.  If a match found, the
        before_obj.diff_word is 'keep' and after_obj.diff_word is 'unchanged'.
        If no match is found in before_obj_list, after_obj.diff_word is 'add'.
        """
        # Check before_obj instances...
        if not isinstance(before_obj_list, list):
            raise ValueError
        for before_obj in before_obj_list:
            if not isinstance(before_obj, BaseCfgLine):
                raise ValueError
            assert before_obj.diff_side == "before"

        # Check after_obj...
        if not isinstance(after_obj, BaseCfgLine):
            raise ValueError
        assert after_obj.diff_side == "after"

        after_id_list = after_obj.diff_id_list
        if debug > 0:
            logger.info(
                "Looking for after_obj in before_obj_list.  after_obj:{} -> id_list: {}".format(
                    after_obj, after_id_list
                )
            )

        for before_obj in before_obj_list:

            before_id_list = before_obj.diff_id_list

            if debug > 1:
                logger.debug("    Considering before_obj: {}".format(before_obj))
                logger.debug(
                    "        before_obj.diff_id_list = {}".format(before_id_list)
                )
                logger.debug(
                    "        after_obj.diff_id_list  = {}".format(after_id_list)
                )

            # skip before objects we already considered...
            if before_obj.diff_word == "keep" and (before_id_list != after_id_list):

                # Mark all ancestors with diff_word="keep"
                for bobj in before_obj.geneology:
                    bobj.diff_word = "keep"
                continue

            elif before_obj.diff_word == "keep" and (before_id_list == after_id_list):
                # Walk backwards through after_obj and ensure all parents,
                # grandparents, etc... are kept...

                for bobj in before_obj.geneology:
                    bobj.diff_word = "keep"

                for aobj in after_obj.geneology:
                    aobj.diff_word = "unchanged"

                return before_obj_list, after_obj

            elif before_obj.diff_word == "remove" and (before_id_list != after_id_list):
                continue

            elif before_obj.diff_word == "remove" and (before_id_list == after_id_list):
                # We found a case where before_obj.diff_word should be "keep"
                # instead of before_obj default value of "remove"...
                if debug > 0:
                    logger.debug("    Keeping before obj:'{}'".format(before_obj))
                # Walk backwards through before_obj and ensure all parents,
                # grandparents, etc... are kept...
                for bobj in before_obj.geneology:
                    bobj.diff_word = "keep"

                after_obj.diff_word = "unchanged"
                for aobj in after_obj.geneology:
                    aobj.diff_word = "unchanged"

                return before_obj_list, after_obj

            else:
                # We should never hit this condition...
                raise NotImplementedError(
                    before_obj,
                    after_obj,
                )

        if debug > 0:
            logger.debug("    Adding after_obj:'{}'".format(after_obj))
        after_obj.diff_word = "add"

        return before_obj_list, after_obj

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def render_after_obj_diffs(self, aobj=None):
        """
        Print after_obj (aobj) diffs to stdout.  before_obj should not be
        handled here.
        """
        assert aobj is not None
        if not isinstance(aobj, BaseCfgLine):
            raise ValueError
        assert aobj.diff_word in ["unchanged", "add"]

        output = list()

        if aobj.diff_word == "unchanged" and aobj.diff_rendered is False:

            # Only render aobj.unchanged if it has children...
            if len(aobj.children) > 0:
                output.append(
                    {
                        "linenum": aobj.linenum,
                        "diff_side": "after",
                        "diff_word": aobj.diff_word,
                        "indent": aobj.indent,
                        "parents": [ii.text for ii in aobj.all_parents],
                        "text": aobj.text,
                        "diff_id_list": aobj.diff_id_list,
                    }
                )
                aobj.diff_rendered = True

        elif aobj.diff_word == "unchanged" and aobj.diff_rendered is True:
            # Adding this because I think this condition can be removed
            pass

        elif aobj.diff_word == "add" and aobj.diff_rendered is False:
            output.append(
                {
                    "linenum": aobj.linenum,
                    "diff_side": "after",
                    "diff_word": aobj.diff_word,
                    "indent": aobj.indent,
                    "parents": [ii.text for ii in aobj.all_parents],
                    "text": aobj.text,
                    "diff_id_list": aobj.diff_id_list,
                }
            )
            aobj.diff_rendered = True

        elif aobj.diff_word == "add" and aobj.diff_rendered is True:
            # Adding this because I think this condition can be removed
            pass

        else:
            raise ValueError("We should not hit this case")

        # Return the output list to the caller...
        return output

    # This method is on HDiff()
    @logger.catch(reraise=True)
    def compress_dict_diffs(self, all_lines=None, debug=0):
        """
        Summary
        -------

        - Accept a list of diff dicts (diff dicts are hereafter known as a "line")
        - Note that duplicate line parent lines may exist in the input
        - Organize the lines such that diff parent lines (example: interface Foo) are not duplicated.
        - Return the updated and reorganized line (dict) list.

        A `line` dict will look similar to this:

        ```
        {
            'linenum': -1,          # do not save the before linenum
            'diff_side': 'before',
            'diff_word': 'remove',
            'indent': 1,
            'parents': [],
            'text': ' some command here',
            'diff_id_list': [-7805827718597648250, -565516812775864492]
        }
        ```

        Note that the `diff_id_list` key above contains a list of `hash()`
        values which are calculated as a unique identifier for the combination
        of parent and child objects.  This list of hashes is required because
        it's possible for multiple parents to have the same child command (for
        instance the same 'no ip proxy-arp' child on multiple interface parent
        lines).

        Please note that a config command object will not get the same `hash()`
        value for different script runs of the same code.
        """

        # all_lines must be a python list
        if not isinstance(all_lines, list):
            raise ValueError

        # Ensure that all_line dict entries have the correct keys...
        for line in all_lines:
            assert set(line.keys()) == set(
                {
                    "linenum",
                    "diff_side",
                    "diff_word",
                    "indent",
                    "parents",
                    "text",
                    "diff_id_list",
                }
            )

        retval = []
        lines = dict()   # lines, indexed by diff_id

        if debug > 0:
            logger.info("compress_dict_diffs() will iterate over the `all_lines` variable.")
        for line in all_lines:
            assert isinstance(line, dict)

            if debug > 0:
                logger.debug("compress_dict_diffs()")
                logger.debug("""compress_dict_diffs() - `line`""".format(line))

            # Unwrap keywords and values from the line...
            diff_side = line["diff_side"]
            diff_word = line["diff_word"]
            diff_id_list = tuple(line["diff_id_list"])
            diff_id_list_len = len(diff_id_list)
            diff_id_list_csv = ",".join([str(ii) for ii in diff_id_list])
            text = line["text"]

            # Remove some lines from consideration...
            if lines.get(diff_id_list, None) is not None:
                continue

            if diff_side == "before" and diff_word == "keep":
                if debug > 0:
                    logger.info("compress_dict_diffs() {0},{1} APPEND {2}".format(diff_side, diff_word, line))
                retval.append(line)
                lines[diff_id_list] = len(retval) - 1

            # We can remove pretty easily... don't do anything...
            elif diff_side == "before" and diff_word == "remove":
                if debug > 0:
                    logger.info("compress_dict_diffs() {0},{1} APPEND {2}".format(diff_side, diff_word, line))
                retval.append(line)
                lines[diff_id_list] = len(retval) - 1

            elif diff_side == "after" and diff_word == "unchanged":
                # FIXME - I should insert this somewhere in retval...
                if lines.get(diff_id_list, None) is None:
                    if debug > 0:
                        logger.info("compress_dict_diffs() {0},{1} APPEND {2}".format(diff_side, diff_word, line))
                    retval.append(line)
                    lines[diff_id_list] = len(retval) - 1
                else:
                    if debug > 0:
                        logger.info("compress_dict_diffs() {0},{1} SKIP {2}".format(diff_side, diff_word, line))

            elif diff_side == "after" and diff_word == "add":

                last_idx = -1

                # Calculate values associated with lines...
                line_id_len = len(line["diff_id_list"])
                line_id_csv = ",".join(
                    [str(ii) for ii in line["diff_id_list"]]
                )

                # check retval and find where we should "add" the
                # line...
                for loop_idx, this_dict in enumerate(retval):
                    this_id_len = len(this_dict["diff_id_list"])
                    this_id_csv = ",".join(
                        [str(ii) for ii in this_dict["diff_id_list"]]
                    )

                    # if this_dict (as a string csv) is a substring of line's csv,
                    # check whether this_dict should be line's parent...
                    if this_id_csv in line_id_csv:

                        last_idx = loop_idx

                        # If the length of this_dict["diff_id_list"] is one element
                        # longer than line["diff_id_list"], it's a pretty
                        # safe assumption that this_dict is line's parent...
                        if (this_id_len + 1) == line_id_len:
                            retval.insert(loop_idx + 1, line)
                            lines[diff_id_list] = len(retval) - 1
                            break
                else:
                    # If there's no match above, assume we add line as a
                    # completely new element at the bottom of retval
                    if debug > 0:
                        logger.info("compress_dict_diffs() {0},{1} APPEND {2}".format(diff_side, diff_word, line))
                    retval.append(line)
                    lines[diff_id_list] = len(retval) - 1

            else:
                raise ValueError(line)

            if line["diff_word"] != "remove":
                try:
                    assert tuple(line["diff_id_list"]) in lines.keys()
                except Exception:
                    raise ValueError(line)

        # FIXME - undo this after I work out all bugs
        for line in retval:
            del line["diff_id_list"]

        return retval


class ConfigList(MutableSequence):
    """
    A custom list to hold :class:`~ccp_abc.BaseCfgLine` objects.  Most people will never need to use this class directly.
    """

    @logger.catch(reraise=True)
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

        if isinstance(initlist, str):
            # IMPORTANT This check MUST come first in ConfigList()
            raise OSError

        if not isinstance(initlist, Sequence):
            raise ValueError


        ciscoconfparse_kwarg_val = kwargs.get("CiscoConfParse", None)
        ccp_ref_kwarg_val = kwargs.get("ccp_ref", None)
        if ciscoconfparse_kwarg_val is not None:
            logger.warning(
                "The CiscoConfParse keyword will be deprecated soon.  Please use ccp_ref instead",
            )
        ccp_value = ccp_ref_kwarg_val or ciscoconfparse_kwarg_val

        self._list = list()
        if initlist is not None:
            # XXX should this accept an arbitrary sequence?
            if type(initlist) == type(self._list):
                self._list[:] = initlist
            elif isinstance(initlist, ConfigList):
                self._list[:] = initlist._list[:]
            else:
                self._list = list(initlist)

        self.CiscoConfParse = ccp_value  # FIXME - CiscoConfParse attribute should go away soon
        self.ccp_ref = ccp_value
        self.comment_delimiter = comment_delimiter
        self.factory = factory
        self.ignore_blank_lines = ignore_blank_lines
        self.syntax = syntax
        self.dna = "ConfigList"
        self.debug = debug

        is_valid_syntax = False
        for valid_syntax in ALL_VALID_SYNTAX:
            if self.syntax == valid_syntax:
                is_valid_syntax = True
        assert is_valid_syntax is True

        # Support input configuration as either a list or a generator instance
        #
        # as of python 3.9, getattr() below is slightly faster than
        #     isinstance(initlist, Sequence)
        if getattr(initlist, "__iter__", False):
            if self.syntax == "ios":
                self._list = self._bootstrap_obj_init_ios(initlist)

            elif self.syntax == "asa":
                self._list = self._bootstrap_obj_init_asa(initlist)

            elif self.syntax == "nxos":
                self._list = self._bootstrap_obj_init_nxos(initlist)

            elif self.syntax == "junos":
                self._list = self._bootstrap_obj_init_junos(initlist)

            else:
                error = "No bootstrap method for syntax='%s'" % self.syntax
                logger.critical(error)
                raise NotImplementedError(error)

        else:
            self._list = list()

        if self.debug > 0:
            message = "Create ConfigList() with %i elements" % len(self._list)
            logger.info(message)

        ###
        ### Internal structures
        if self.syntax == 'asa':
            self._RE_NAMES = re.compile(
                r"^\s*name\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)",
            )
            self._RE_OBJNET = re.compile(r"^\s*object-group\s+network\s+(\S+)")
            self._RE_OBJSVC = re.compile(r"^\s*object-group\s+service\s+(\S+)")
            self._RE_OBJACL = re.compile(r"^\s*access-list\s+(\S+)")
            self._network_cache = dict()

    # This method is on ConfigList()
    def __repr__(self):
        return """<ConfigList, syntax='{}', comment='{}', conf={}>""".format(
            self.syntax,
            self.comment_delimiter,
            self._list,
        )

    def __iter__(self):
        return iter(self._list)

    # This method is on ConfigList()
    def __lt__(self, other):
        return self._list < self.__cast(other)

    # This method is on ConfigList()
    def __le__(self, other):
        return self._list < self.__cast(other)

    # This method is on ConfigList()
    def __eq__(self, other):
        return self._list == self.__cast(other)

    # This method is on ConfigList()
    def __gt__(self, other):
        return self._list > self.__cast(other)

    # This method is on ConfigList()
    def __ge__(self, other):
        return self._list >= self.__cast(other)

    # This method is on ConfigList()
    def __cast(self, other):
        return other._list if isinstance(other, ConfigList) else other

    # This method is on ConfigList()
    def __len__(self):
        return len(self._list)

    # This method is on ConfigList()
    def __getitem__(self, ii):
        if isinstance(ii, slice):
            return self.__class__(self._list[ii])
        else:
            return self._list[ii]

    # This method is on ConfigList()
    def __setitem__(self, ii, val):
        self._list[ii] = val

    # This method is on ConfigList()
    def __delitem__(self, ii):
        del self._list[ii]
        self._bootstrap_from_text()

    # This method is on ConfigList()
    def __add__(self, other):
        if isinstance(other, ConfigList):
            return self.__class__(self._list + other._list)
        elif isinstance(other, type(self._list)):
            return self.__class__(self._list + other)
        return self.__class__(self._list + list(other))

    # This method is on ConfigList()
    def __radd__(self, other):
        if isinstance(other, ConfigList):
            return self.__class__(other._list + self._list)
        elif isinstance(other, type(self._list)):
            return self.__class__(other + self._list)
        return self.__class__(list(other) + self._list)

    # This method is on ConfigList()
    def __iadd__(self, other):
        if isinstance(other, ConfigList):
            self._list += other._list
        elif isinstance(other, type(self._list)):
            self._list += other
        else:
            self._list += list(other)
        return self

    # This method is on ConfigList()
    def __mul__(self, val):
        return self.__class__(self._list * val)

    __rmul__ = __mul__

    def __imul__(self, val):
        self._list *= val
        return self

    # This method is on ConfigList()
    def __copy__(self):
        inst = self.__class__.__new__(self.__class__)
        inst.__dict__.update(self.__dict__)
        # Create a copy and avoid triggering descriptors
        inst.__dict__["_list"] = self.__dict__["_list"][:]
        return inst

    # This method is on ConfigList()
    def __str__(self):
        return self.__repr__()

    # This method is on ConfigList()
    def __enter__(self):
        # Add support for with statements...
        # FIXME: *with* statements dont work
        yield from self._list

    # This method is on ConfigList()
    def __exit__(self, *args, **kwargs):
        # FIXME: *with* statements dont work
        self._list[0].confobj.CiscoConfParse.atomic()

    # This method is on ConfigList()
    def __getattribute__(self, arg):
        """Call arg on ConfigList() object, and if that fails, call arg from the ccp_ref attribute"""
        # Try a method call on ASAConfigList()

        # Rewrite self.CiscoConfParse to self.ccp_ref
        if arg == "CiscoConfParse":
            arg = "ccp_ref"

        try:
            return object.__getattribute__(self, arg)
        except Exception:
            calling_function = inspect.stack()[1].function
            caller = inspect.getframeinfo(inspect.stack()[1][0])

            ccp_ref = object.__getattribute__(self, 'ccp_ref')
            ccp_method = ccp_ref.__getattribute__(arg)
            message = """{2} doesn't have an attribute named "{3}". {0}() line {1} called `__getattribute__('{4}')`. CiscoConfParse() is making this work with duct tape in __getattribute__().""".format(
                calling_function, caller.lineno, ccp_ref, ccp_method, arg
            )
            logger.warning(message)
            return ccp_method

    # This method is on ConfigList()
    @junos_unsupported
    def append(self, val):

        if self.debug >= 1:
            logger.debug("    ConfigList().append(val={}) was called.".format(val))

        self._list.append(val)

    # This method is on ConfigList()
    def pop(self, ii=-1):
        return self._list.pop(ii)

    # This method is on ConfigList()
    def remove(self, val):
        self._list.remove(val)

    # This method is on ConfigList()
    def clear(self):
        self._list.clear()

    # This method is on ConfigList()
    def copy(self):
        return self.__class__(self)

    # This method is on ConfigList()
    def count(self, val):
        return self._list.count(val)

    # This method is on ConfigList()
    def index(self, val, *args):
        return self._list.index(val, *args)

    # This method is on ConfigList()
    def reverse(self):
        self._list.reverse()

    # This method is on ConfigList()
    # def sort(self, /, *args, **kwds):
    def sort(self, _unknown_arg, *args, **kwds):
        self._list.sort(*args, **kwds)

    # This method is on ConfigList()
    def extend(self, other):
        if isinstance(other, ConfigList):
            self._list.extend(other._list)
        else:
            self._list.extend(other)

    # This method is on ConfigList()
    def _bootstrap_from_text(self):

        if self.debug >= 1:
            logger.debug("    ConfigList()._bootstrap_from_text() was called.")

        ## reparse all objects from their text attributes... this is *very* slow
        ## Ultimate goal: get rid of all reparsing from text...

        if self.syntax == 'ios':
            self._list = self._bootstrap_obj_init_ios(self.ioscfg)

        elif self.syntax == 'nxos':
            self._list = self._bootstrap_obj_init_nxos(self.ioscfg)

        elif self.syntax == 'asa':
            self._list = self._bootstrap_obj_init_asa(self.ioscfg)

        elif self.syntax == 'junos':
            self._list = self._bootstrap_obj_init_junos(self.ioscfg)

        else:
            error = "no defined bootstrap method for syntax='%s'" % self.syntax
            raise NotImplementedError(error)

        if self.debug >= 3:
            logger.debug("self._list = {}".format(self._list))

    # This method is on ConfigList()
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
    @junos_unsupported
    def insert_before_deprecated(self, exist_val, new_val, atomic=False):
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
        raise NotImplementedError()

##############################################################################

    # This method is on ConfigList()
    def insert_before(self, exist_val, new_val, atomic=False):
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
            calling_filename, calling_lineno, calling_function, exist_val,
            new_val,
        )
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

        if self.factory:
            new_obj = ConfigLineFactory(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
                syntax=self.syntax,
            )
        elif self.syntax == "ios":
            new_obj = IOSCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "nxos":
            new_obj = NXOSCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "asa":
            new_obj = ASACfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "junos":
            new_obj = JunosCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        else:
            logger.error(error)
            raise ValueError(error)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx for idx, list_obj in enumerate(self._list)
            if re.search(exist_val, list_obj.text)
        ]
        for idx in sorted(all_idx, reverse=True):

            # insert at idx - 0 implements 'insert_before()'...
            self._list.insert(idx, new_obj)

        if atomic:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()

        else:
            ## Just renumber lines...
            self._reassign_linenums()

    # This method is on ConfigList()
    @junos_unsupported
    def insert_after(self, exist_val="", new_val="", atomic=False, new_val_indent=-1):
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
            calling_filename, calling_lineno, calling_function, exist_val,
            new_val,
        )
        # exist_val MUST be a string
        if isinstance(exist_val, str) is True and exist_val != "":
            pass

        # Matches "IOSCfgLine", "NXOSCfgLine" and "ASACfgLine"... (and others)
        elif isinstance(exist_val, BaseCfgLine):
            exist_val = exist_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        # new_val MUST be a string
        if isinstance(new_val, str) is True:
            pass

        elif isinstance(new_val, BaseCfgLine):
            new_val = new_val.text

        else:
            logger.error(err_txt)
            raise ValueError(err_txt)

        if self.factory is True:
            new_obj = ConfigLineFactory(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
                syntax=self.syntax,
            )
        elif self.syntax == "ios":
            new_obj = IOSCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "nxos":
            new_obj = NXOSCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "asa":
            new_obj = ASACfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        elif self.syntax == "junos":
            new_obj = JunosCfgLine(
                text=new_val,
                comment_delimiter=self.comment_delimiter,
            )

        else:
            logger.error(error)
            raise ValueError(error)

        # Find all config lines which need to be modified... store in all_idx

        all_idx = [
            idx for idx, list_obj in enumerate(self._list)
            if re.search(exist_val, list_obj._text)
        ]
        for idx in sorted(all_idx, reverse=True):
            self._list.insert(idx + 1, new_obj)

        if atomic is True:
            # Reparse the whole config as a text list
            self._bootstrap_from_text()
        else:
            ## Just renumber lines...
            self._reassign_linenums()

    # This method is on ConfigList()
    @junos_unsupported
    def insert(self, ii, val):

        if not isinstance(ii, int):
            raise ValueError


        # Coerce a string into the appropriate object
        if getattr(val, "capitalize", False):
            if self.factory:
                obj = ConfigLineFactory(
                    text=val,
                    comment_delimiter=self.comment_delimiter,
                    syntax=self.syntax,
                )
            elif self.syntax == "ios":
                obj = IOSCfgLine(
                    text=val,
                    comment_delimiter=self.comment_delimiter,
                )

            elif self.syntax == "nxos":
                obj = NXOSCfgLine(
                    text=val,
                    comment_delimiter=self.comment_delimiter,
                )

            elif self.syntax == "asa":
                obj = ASACfgLine(
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
        self._reassign_linenums()


    # This method is on ConfigList()
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
            if (mm is not None):
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
                        banner_lead, parent.linenum,
                    ),
                )

            idx = parent.linenum
            while (bannerdelimit is not None):
                ## Check whether the banner line has both begin and end delimter
                if idx == parent.linenum:
                    parts = parent.text.split(bannerdelimit)
                    if len(parts) > 2:
                        ## banner has both begin and end delimiter on one line
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead, parent.linenum,
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
                                "found empty text while parsing '{}' in the banner"
                                .format(obj),
                            )
                        pass
                    elif bannerdelimit in obj.text.strip():
                        # Hit the bannerdelimit char... Exit banner parsing here...
                        if self.debug > 0:
                            logger.debug(
                                "{} ends at line"
                                " {}".format(
                                    banner_lead, obj.linenum,
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
        banner_all = [
            r"^(set\s+)*banner\s+{}".format(ii) for ii in banner_str
        ]
        banner_all.append(
            "aaa authentication fail-message",
        )  # Github issue #76
        banner_re = re.compile("|".join(banner_all))

        return banner_re


    # This method is on ConfigList()
    def _bootstrap_obj_init_ios(self, text_list):
        """
        Accept a text list, and format into a list of proper
        IOSCfgLine() objects or JunosCfgLine() objects.

        This method returns a list of IOSCfgLine() objects.
        """
        if not isinstance(text_list, Sequence):
            raise ValueError

        # Build the banner_re regexp... at this point ios
        #    and nxos share the same method...
        banner_re = self._build_banner_re_ios()

        retval = []
        idx = 0

        max_indent = 0
        macro_parent_idx_list = []
        parents = {}
        for txt in text_list:
            if not isinstance(txt, str):
                raise ValueError

            obj = _build_cfgobj_from_text(txt, idx,
                syntax=self.syntax,
                comment_delimiter=self.comment_delimiter,
                factory=self.factory)
            obj.confobj = self
            indent = obj.indent
            is_config_line = obj.is_config_line

            # list out macro parent line numbers...
            if obj.text[0:11] == "macro name ":
                macro_parent_idx_list.append(obj.linenum)

            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent < max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(
                    lambda ii: ii >= indent,
                    sorted(parents.keys(), reverse=True),
                )
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards,
                ##    we can use a cached parent
                parent = parents.get(indent, None)

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
                candidate_parent_index = idx - 1
                while candidate_parent_index >= 0:
                    candidate_parent = retval[candidate_parent_index]
                    if (
                        candidate_parent.indent <
                        indent
                    ) and candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent  # Cache the parent
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval

        # Manually assign a parent on all closing braces
        self._list = assign_parent_to_closing_braces(input_list=self._list)

        # Call _banner_mark_regex() to process banners in the returned obj
        # list.
        # Mark IOS banner begin and end config line objects...
        self._banner_mark_regex(banner_re)
        # We need to use a different method for macros than banners because
        #   macros don't specify a delimiter on their parent line, but
        #   banners call out a delimiter.
        self._macro_mark_children(macro_parent_idx_list)  # Process macros

        # change ignore_blank_lines behavior for Github Issue #229...
        #    Always allow a blank line if it's in a banner or macro...
        if self.ignore_blank_lines is True:
            retval = [obj for obj in self._list if obj.text.strip()!="" or obj.blank_line_keep is True]
            self._list = retval

        return retval

    # This method is on ConfigList()
    def _bootstrap_obj_init_asa(self, text_list):
        """
        Accept a text list, and format into a list of proper
        ASACfgLine() objects

        This method returns a list of ASACfgLine() objects.
        """
        if not isinstance(text_list, Sequence):
            raise ValueError

        # Append text lines as IOSCfgLine objects...
        retval = list()
        idx = 0

        max_indent = 0
        parents = dict()
        for txt in text_list:
            # Reject empty lines if ignore_blank_lines...
            if self.ignore_blank_lines and txt.strip() == "":
                continue

            obj = _build_cfgobj_from_text(txt, idx,
                syntax=self.syntax,
                comment_delimiter=self.comment_delimiter,
                factory=self.factory)
            obj.confobj = self
            indent = obj.indent
            is_config_line = obj.is_config_line

            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent < max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(
                    lambda ii: ii >= indent,
                    sorted(parents.keys(), reverse=True),
                )
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards,
                ##    we can use a cached parent
                parent = parents.get(indent, None)

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
                candidate_parent_index = idx - 1
                while candidate_parent_index >= 0:
                    candidate_parent = retval[candidate_parent_index]
                    if (
                        candidate_parent.indent <
                        indent
                    ) and candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent  # Cache the parent
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval
        ## Insert ASA-specific banner processing here, if required
        return retval

    # This method is on ConfigList()
    def _bootstrap_obj_init_nxos(self, text_list):
        """
        Accept a text list, and format into a list of proper
        NXOSCfgLine() objects

        This method returns a list of NXOSCfgLine() objects.
        """
        if not isinstance(text_list, Sequence):
            raise ValueError

        # Build the banner_re regexp... at this point ios
        #    and nxos share the same method...
        banner_re = self._build_banner_re_ios()

        retval = list()
        idx = 0

        max_indent = 0
        parents = dict()
        for txt in text_list:
            # Reject empty lines if ignore_blank_lines...
            if not isinstance(txt, str):
                raise ValueError

            obj = _build_cfgobj_from_text(txt, idx,
                syntax=self.syntax,
                comment_delimiter=self.comment_delimiter,
                factory=self.factory)
            obj.confobj = self
            indent = obj.indent
            is_config_line = obj.is_config_line

            #
            if not self.factory:
                obj = NXOSCfgLine(txt, self.comment_delimiter)
            elif self.syntax == "nxos":
                obj = ConfigLineFactory(
                    txt,
                    self.comment_delimiter,
                    syntax="nxos",
                )
            else:
                error = "Unexpected line in the config: '%s'" % txt
                logger.error(error)
                raise ValueError(error)

            obj.confobj = self
            obj.linenum = idx
            indent = len(txt) - len(txt.lstrip())
            obj.indent = indent

            is_config_line = obj.is_config_line

            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent < max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(
                    lambda ii: ii >= indent,
                    sorted(parents.keys(), reverse=True),
                )
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards,
                ##    we can use a cached parent
                parent = parents.get(indent, None)

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
                candidate_parent_index = idx - 1
                while candidate_parent_index >= 0:
                    candidate_parent = retval[candidate_parent_index]
                    if (
                        candidate_parent.indent <
                        indent
                    ) and candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent  # Cache the parent
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval
        # Call _banner_mark_regex() to process banners in the returned obj
        # list.
        # Mark NXOS banner begin and end config line objects...
        self._banner_mark_regex(banner_re)  # Process NXOS banners

        # change ignore_blank_lines behavior for Github Issue #229...
        #    Always allow a blank line if it's in a banner or macro...
        if self.ignore_blank_lines is True:
            retval = [obj for obj in self._list if obj.text.strip()!="" or obj.blank_line_keep is True]
            self._list = retval

        return retval

    # This method is on ConfigList()
    def _bootstrap_obj_init_junos(self, text_list):
        """
        Accept a text list, and format into a list of proper
        JunosCfgLine() objects.

        This method returns a list of JunosCfgLine() objects.
        """
        if not isinstance(text_list, Sequence):
            raise ValueError

        retval = list()
        idx = 0

        max_indent = 0
        macro_parent_idx_list = list()
        parents = dict()
        for txt in text_list:
            # Reject empty lines if ignore_blank_lines...
            if not isinstance(txt, str):
                raise ValueError

            if self.ignore_blank_lines and txt.strip() == "":
                continue
            obj = _build_cfgobj_from_text(txt, idx,
                syntax=self.syntax,
                comment_delimiter=self.comment_delimiter,
                factory=self.factory)
            obj.confobj = self
            indent = obj.indent
            is_config_line = obj.is_config_line

            # list out macro parent line numbers...
            if obj.text[0:11] == "macro name ":
                macro_parent_idx_list.append(obj.linenum)

            ## Parent cache:
            ## Maintain indent vs max_indent in a family and
            ##     cache the parent until indent<max_indent
            if (indent < max_indent) and is_config_line:
                parent = None
                # walk parents and intelligently prune stale parents
                stale_parent_idxs = filter(
                    lambda ii: ii >= indent,
                    sorted(parents.keys(), reverse=True),
                )
                for parent_idx in stale_parent_idxs:
                    del parents[parent_idx]
            else:
                ## As long as the child indent hasn't gone backwards,
                ##    we can use a cached parent
                parent = parents.get(indent, None)

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
                candidate_parent_index = idx - 1
                while candidate_parent_index >= 0:
                    candidate_parent = retval[candidate_parent_index]
                    if (
                        candidate_parent.indent <
                        indent
                    ) and candidate_parent.is_config_line:
                        # We found the parent
                        parent = candidate_parent
                        parents[indent] = parent  # Cache the parent
                        break
                    else:
                        candidate_parent_index -= 1

                ## Add the line as a child...
                self._add_child_to_parent(retval, idx, indent, parent, obj)

            ## Handle max_indent
            if (indent == 0) and is_config_line:
                # only do this if it's a config line...
                max_indent = 0
            elif indent > max_indent:
                max_indent = indent

            retval.append(obj)
            idx += 1

        self._list = retval

        # Manually assign a parent on all closing braces
        self._list = assign_parent_to_closing_braces(input_list=self._list)

        # We need to use a different method for macros than banners because
        #   macros don't specify a delimiter on their parent line, but
        #   banners call out a delimiter.
        self._macro_mark_children(macro_parent_idx_list)  # Process macros
        return retval


    # This method is on ConfigList()
    def _add_child_to_parent(self, _list, idx, indent, parentobj, childobj):
        ## parentobj could be None when trying to add a child that should not
        ##    have a parent
        if parentobj is None:
            if self.debug > 0:
                logger.debug("parentobj is None")
            return

        if self.debug >= 4:
            logger.debug(
                "Adding child '{}' to parent"
                " '{}'".format(childobj, parentobj),
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
    def iter_with_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if idx >= begin_index:
                yield obj

    # This method is on ConfigList()
    def iter_no_comments(self, begin_index=0):
        for idx, obj in enumerate(self._list):
            if (idx >= begin_index) and (not obj.is_comment):
                yield obj

    # This method is on ConfigList()
    def _reassign_linenums(self):
        # Call this after any insertion or deletion
        for idx, obj in enumerate(self._list):
            obj.linenum = idx

    # This method is on ConfigList()
    @property
    def all_parents(self):
        return [obj for obj in self._list if obj.has_children]

    # This method is on ConfigList()
    @property
    def last_index(self):
        return self.__len__() - 1

    ##########################################################################
    # Special syntax='asa' methods...
    ##########################################################################

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @property
    def names(self):
        """Return a dictionary of name to address mappings"""
        assert self.syntax == 'asa'

        retval = dict()
        name_rgx = self._RE_NAMES
        for obj in self.ccp_ref.find_objects(name_rgx):
            addr = obj.re_match_typed(name_rgx, group=1, result_type=str)
            name = obj.re_match_typed(name_rgx, group=2, result_type=str)
            retval[name] = addr
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @property
    def object_group_network(self):
        """Return a dictionary of name to object-group network mappings"""
        assert self.syntax == 'asa'

        retval = dict()
        obj_rgx = self._RE_OBJNET
        for obj in self.ccp_ref.find_objects(obj_rgx):
            name = obj.re_match_typed(obj_rgx, group=1, result_type=str)
            retval[name] = obj
        return retval

    # This method was on ASAConfigList(); now tentatively on ConfigList()
    @property
    def access_list(self):
        """Return a dictionary of ACL name to ACE (list) mappings"""
        assert self.syntax == 'asa'

        retval = dict()
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
    def __init__(self, level, nonparents, parents):
        self.level = level
        self.nonparents = nonparents
        self.parents = parents

    def __repr__(self):
        return "<DiffObject level: {}>".format(self.level)


class CiscoPassword(object):
    def __init__(self, ep=""):
        self.ep = ep

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


if False:
    def CCP(syntax="ios"):
        if syntax=="ios":
            return CiscoConfParse(syntax="ios")
        elif syntax=="nxos":
            return CiscoConfParse(syntax="nxos", ignore_blank_lines=False)
        elif syntax=="asa":
            return CiscoConfParse(syntax="asa", ignore_blank_lines=True)
        elif syntax=="junos":
            return CiscoConfParse(syntax="junos", ignore_blank_lines=True)

def ConfigLineFactory(text="", comment_delimiter="!", syntax="ios"):
    # Complicted & Buggy
    # classes = [j for (i,j) in globals().iteritems() if isinstance(j, TypeType) and issubclass(j, BaseCfgLine)]

    ## Manual and simple
    if syntax == "ios":
        classes = [
            IOSIntfLine,
            IOSRouteLine,
            IOSAccessLine,
            IOSAaaLoginAuthenticationLine,
            IOSAaaEnableAuthenticationLine,
            IOSAaaCommandsAuthorizationLine,
            IOSAaaCommandsAccountingLine,
            IOSAaaExecAccountingLine,
            IOSAaaGroupServerLine,
            IOSHostnameLine,
            IOSIntfGlobal,
            IOSCfgLine,
        ]  # This is simple
    elif syntax == "nxos":
        classes = [
            NXOSIntfLine,
            NXOSRouteLine,
            NXOSAccessLine,
            NXOSAaaLoginAuthenticationLine,
            NXOSAaaEnableAuthenticationLine,
            NXOSAaaCommandsAuthorizationLine,
            NXOSAaaCommandsAccountingLine,
            NXOSAaaExecAccountingLine,
            NXOSAaaGroupServerLine,
            NXOSvPCLine,
            NXOSHostnameLine,
            NXOSIntfGlobal,
            NXOSCfgLine,
        ]  # This is simple
    elif syntax == "asa":
        classes = [
            ASAName,
            ASAObjNetwork,
            ASAObjService,
            ASAObjGroupNetwork,
            ASAObjGroupService,
            ASAIntfLine,
            ASAIntfGlobal,
            ASAHostnameLine,
            ASAAclLine,
            ASACfgLine,
        ]
    elif syntax == "junos":
        classes = [JunosCfgLine]

    else:
        err_txt = "'{}' is an unknown syntax".format(syntax)
        logger.error(err_txt)
        raise ValueError(err_txt)

    try:
        for cls in classes:
            if cls.is_object_for(text):
                inst = cls(
                    text=text, comment_delimiter=comment_delimiter,
                )  # instance of the proper subclass
                return inst
    except ValueError:
        err_txt = "Could not find an object for '%s'" % text
        logger.error(err_txt)
        raise ValueError(err_txt)


### TODO: Add unit tests below
if __name__ == "__main__":
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
    elif opts.method == "find_parents_w_child":
        diff = CiscoConfParse(config=opts.config).find_parents_w_child(
            opts.arg1, opts.arg2,
        )
    elif opts.method == "find_parents_wo_child":
        diff = CiscoConfParse(config=opts.config).find_parents_wo_child(
            opts.arg1, opts.arg2,
        )
    elif opts.method == "req_cfgspec_excl_diff":
        diff = CiscoConfParse(config=opts.config).req_cfgspec_excl_diff(
            opts.arg1, opts.arg2, opts.arg3.split(","),
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
        print(
            "   req_cfgspec_excl_diff:  arg1=linespec    arg2=uncfgspec" +
            "   arg3=cfgspec",
        )
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
        error = "ciscoconfparse was called with unknown parameters"
        logger.error(error)
        raise RuntimeError(error)
