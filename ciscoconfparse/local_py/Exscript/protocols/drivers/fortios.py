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
A driver for FortiOS devices.

Created using a Fortigate device and FortiOS 5.0.
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re = [re.compile(r'[\r\n]Username: $')]
_password_re = [re.compile(r'[\r\n]Password: $')]
_prompt_re = [
    re.compile(r'^[a-zA-Z0-9-_ .]+ # $'),  # first prompt
    re.compile(r'[\r\n][a-zA-Z0-9-_ .]+ (?:\([A-Za-z0-9_/.-]+\) )?# $')
]
_fortios_re = [
    _prompt_re[0],  # first prompt
    re.compile(r'^[a-zA-Z0-9-_.]+@[a-zA-Z0-9-_.]+\'s password:')
]
_error_re = [re.compile(r'^Command fail.'),
             re.compile(r'^object check operator error')
             ]

# example errors:
#invalid netmask.
#object check operator error, -9, discard the setting
#Command fail. Return code -9

#entry not found in datasource
#value parse error before 'imported'
#Command fail. Return code -3


class FortiOSDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'fortios')
        self.user_re = _user_re
        self.password_re = _password_re
        self.prompt_re = _prompt_re
        self.error_re = _error_re

    def check_head_for_os(self, string):
        # By default Fortigate shows only prompt
        if len(string.splitlines()) == 1:
            for head_re in _fortios_re:
                if head_re.search(string):
                    return 50
        return 0

    def init_terminal(self, conn):
        conn.execute('config global')
        conn.execute('config system console')
        conn.execute('set output standard')  # no paging
        conn.execute('end')  # config system console
        conn.execute('end')  # config global
