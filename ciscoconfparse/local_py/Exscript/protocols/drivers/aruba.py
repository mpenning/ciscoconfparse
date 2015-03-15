"""
A driver for Aruba controllers
"""
import re
from Exscript.protocols.drivers.driver import Driver

_user_re = [re.compile(r'user ?name: ?$', re.I)]
_password_re = [re.compile(r'(?:[\r\n]Password: ?|last resort password:)$')]
_tacacs_re = re.compile(r'[\r\n]s\/key[\S ]+\r?%s' % _password_re[0].pattern)
_prompt_re = [re.compile(r'[\r\n]\(\w+\) [>#] ?$')]
_error_re = [re.compile(r'%Error'),
             re.compile(r'invalid input', re.I),
             re.compile(r'(?:incomplete|ambiguous) command', re.I),
             re.compile(r'connection timed out', re.I),
             re.compile(r'[^\r\n]+ not found', re.I)]
_aruba_prompt_re = [re.compile(r'\(Aruba\d?\d?\d?\d?\) >')]


class ArubaDriver(Driver):
    def __init__(self):
        Driver.__init__(self, 'aruba')
        self.user_re = _user_re
        self.password_re = _password_re
        self.prompt_re = _prompt_re
        self.error_re = _error_re

    def check_head_for_os(self, string):
        if 'aruba' in string.lower():
            return 88

    def init_terminal(self, conn):
        conn.execute('no paging')

    def auto_authorize(self, conn, account, flush, bailout):
        conn.send('enable\r')
        conn.app_authorize(account, flush, bailout)
