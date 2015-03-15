# Copyright (C) 2012 Job Snijders <job.snijders@atrato-ip.com>
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
A driver for Brocade XMR/MLX devices.
"""

import re
from Exscript.protocols.drivers.driver import Driver

_user_re     = [re.compile(r'[\r\n](Please Enter Login Name: |User Name:)$')]
_password_re = [re.compile(r'[\r\n](Please Enter Password: |Password:)$')]
_warning     = r'(?:Warning: \d+ user\(s\) already in config mode\.)'
_prompt      = r'[\r\n]?(telnet|SSH)@[\-\w+\.:]+(?:\([\-\/\w]+\))?[>#]$'
_prompt_re   = [re.compile(_warning + r'?' + _prompt)]                                                                                                                         
_error_re    = [re.compile(r'%Error'),
                re.compile(r'Invalid input', re.I),
                re.compile(r'(?:incomplete|ambiguous) command', re.I),
                re.compile(r'connection timed out', re.I),
                re.compile(r'[^\r\n]+ not found', re.I)]

class BrocadeDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'brocade')
        self.user_re     = _user_re
        self.password_re = _password_re
        self.prompt_re   = _prompt_re
        self.error_re    = _error_re

    def check_head_for_os(self, string):
        if 'User Access Verification\r\n\r\nPlease Enter Login Name' in string:
            return 95
        if _prompt_re[0].search(string):
            return 90
        return 0

    def init_terminal(self, conn):
        conn.execute('terminal length 0')

    def auto_authorize(self, conn, account, flush, bailout):
        conn.send('enable\r')
        conn.app_authorize(account, flush, bailout)
