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
A driver for HP ProCurve switches.
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re       = [re.compile(r'[\r\n]Username: ?$')]
_password_re   = [re.compile(r'[\r\n]Password: ?$')]
_prompt_re     = [re.compile(r'[\r\n][\-\w+\.:/]+[>#] ?$')]
_error_re      = [re.compile(r'(?:invalid|incomplete|ambiguous) input:', re.I)]
_login_fail_re = [re.compile(r'[\r\n]invalid password', re.I),
                  re.compile(r'unable to verify password', re.I),
                  re.compile(r'unable to login', re.I)]
_clean_res_re  = [(re.compile(r'\x1bE'), "\r\n"), (re.compile(r'(?:\x1b\[|\x9b)[\x30-\x3f]*[\x40-\x7e]'), "")]

class HPProCurveDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'hp_pro_curve')
        self.user_re        = _user_re
        self.password_re    = _password_re
        self.prompt_re      = _prompt_re
        self.error_re       = _error_re
        self.login_error_re = _login_fail_re
        self.clean_res_re   = _clean_res_re

    def check_head_for_os(self, string):
        if 'ProCurve' in string:
            return 95
        if 'Hewlett-Packard' in string:
            return 50
        return 0

    def clean_response_for_re_match(self, response):
        start = response[:10].find('\x1b')
        if start != -1:
            response = response[start:]
        for regexp, sub in self.clean_res_re:
            response = regexp.subn(sub, response)[0]
        i = response.find('\x1b')
        if i > -1:
            return response[:i], response[i:]
        return response, ''

    def init_terminal(self, conn):
        conn.execute('\r\n')
