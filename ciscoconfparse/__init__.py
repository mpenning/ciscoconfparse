r""" __init__.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
     Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corp.
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

import sys

from ciscoconfparse.ccp_util import PythonOptimizeCheck
from ciscoconfparse.ciscoconfparse import *
from ciscoconfparse.ccp_util import IPv4Obj
from ciscoconfparse.ccp_util import IPv6Obj
from ciscoconfparse.ccp_util import CiscoIOSInterface, CiscoIOSXRInterface
from ciscoconfparse.ccp_util import CiscoRange
from ciscoconfparse.ccp_util import run_this_posix_command
from ciscoconfparse.ccp_util import ccp_logger_control
from ciscoconfparse.ccp_util import configure_loguru
from ciscoconfparse.ccp_util import as_text_list
from ciscoconfparse.ccp_util import junos_unsupported
from ciscoconfparse.ccp_util import log_function_call
from ciscoconfparse.ccp_util import enforce_valid_types
from ciscoconfparse.ccp_util import fix_repeated_words
from ciscoconfparse.ccp_util import __ccp_re__
from ciscoconfparse.ccp_util import _get_ipv4
from ciscoconfparse.ccp_util import _get_ipv6
from ciscoconfparse.ccp_util import ip_factory
from ciscoconfparse.ccp_util import collapse_addresses
from ciscoconfparse.ccp_util import L4Object
from ciscoconfparse.ccp_util import DNSResponse
from ciscoconfparse.ccp_util import dns_query
from ciscoconfparse.ccp_util import check_valid_ipaddress

from dns.resolver import Resolver
from dns.exception import DNSException

assert sys.version_info >= (3, 7)

# Throw errors for PYTHONOPTIMIZE and `python -O ...` by executing
#     PythonOptimizeCheck()...
_ = PythonOptimizeCheck()
