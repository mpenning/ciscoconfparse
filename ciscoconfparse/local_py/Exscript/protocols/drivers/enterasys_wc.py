# Copyright (C) 2014 Enno Groeper <groepeen@cms.hu-berlin.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
A driver for Enterasys/Extreme (HiPath) Wireless Controller devices.

Created using a C5110 device.
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re = [re.compile(r'[\r\n]Username: $')]
_password_re = [re.compile(r'[\r\n]Password: $')]
_prompt_re = [
    re.compile(r'[\r\n][a-zA-Z0-9-_ .]+# $'),  # base prompt
    re.compile(r'[\r\n][a-zA-Z0-9-_ .]+(?::[A-Za-z0-9_.-]+)*# $')
]
_hwc_re = re.compile(r'Enterasys Wireless Convergence OS', re.I)


class EnterasysWCDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'enterasys_wc')
        self.user_re = _user_re
        self.password_re = _password_re
        self.prompt_re = _prompt_re

    def check_head_for_os(self, string):
        if _hwc_re.search(string):
            return 85
        return 0

    def init_terminal(self, conn):
        pass
