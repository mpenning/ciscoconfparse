# Copyright (C) 2007-2010 Samuel Abels.
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
A driver for devices running Juniper ERX OS.
"""
import re
from Exscript.protocols.drivers.driver import Driver
from Exscript.protocols.drivers.ios    import _prompt_re

_user_re     = [re.compile(r'[\r\n]User: $')]
_password_re = [re.compile(r'[\r\n](Telnet password:|Password:) $')]
_junos_re    = re.compile(r'\bJuniper Networks\b', re.I)

class JunOSERXDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'junos_erx')
        self.user_re     = _user_re
        self.password_re = _password_re
        self.prompt_re   = _prompt_re

    def check_head_for_os(self, string):
        if _junos_re.search(string):
            return 75
        return 0

    def init_terminal(self, conn):
        conn.execute('terminal length 60')
        conn.execute('terminal width 150')

    def auto_authorize(self, conn, account, flush, bailout):
        conn.send('enable 15\r')
        conn.app_authorize(account, flush, bailout)
