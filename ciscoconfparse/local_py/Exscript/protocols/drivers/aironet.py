# Copyright (C) 2015 Mike Pennington, Samuel Abels
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
A driver for Cisco Aironet Wireless Controllers
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re     = [re.compile(r'User:\s$', re.I)]
_password_re = [re.compile(r'(?:[\r\n]Password: ?|last resort password:)$')]
_prompt_re   = [re.compile(r'[\r\n].Cisco\sController.\s>$')]
_error_re    = [re.compile(r'%Error'),
                re.compile(r'invalid input', re.I),
                re.compile(r'(?:incomplete|ambiguous) command', re.I),
                re.compile(r'connection timed out', re.I),
                re.compile(r'[^\r\n]+ not found', re.I)]

class AironetDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'aironet')
        self.user_re     = _user_re
        self.prompt_re   = _prompt_re

    def check_head_for_os(self, string):
        if '(Cisco Controller)' in string:
            return 90
        return 0

    def init_terminal(self, conn):
        conn.execute('config pager disable')
