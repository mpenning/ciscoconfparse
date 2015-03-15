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
A driver for AIX.
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re     = [re.compile(r'[\r\n]Authorized Login: $')]
_password_re = [re.compile(r'[\r\n]\w+\'s Password: $')]
_aix_re      = re.compile(r'\bAIX\b')

class AIXDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'aix')
        self.user_re     = _user_re
        self.password_re = _password_re

    def check_head_for_os(self, string):
        if _user_re[0].search(string):
            return 70
        if _aix_re.search(string):
            return 75
        return 0
