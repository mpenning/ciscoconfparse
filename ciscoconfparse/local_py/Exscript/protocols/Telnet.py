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
The Telnet protocol.
"""
from Exscript.util.tty            import get_terminal_size
from Exscript.protocols           import telnetlib
from Exscript.protocols.Protocol  import Protocol
from Exscript.protocols.Exception import ProtocolException, \
                                         TimeoutException, \
                                         DriverReplacedException, \
                                         ExpectCancelledException

class Telnet(Protocol):
    """
    The Telnet protocol adapter.
    """

    def __init__(self, **kwargs):
        Protocol.__init__(self, **kwargs)
        self.tn = None

    def _telnetlib_received(self, data):
        self._receive_cb(data)
        self.buffer.append(data)

    def _connect_hook(self, hostname, port, init_timeout):
        assert self.tn is None
        rows, cols = get_terminal_size()
        self.tn = telnetlib.Telnet(hostname,
                                   port or 23,
                                   init_timeout     = init_timeout,
                                   termsize         = (rows, cols),
                                   termtype         = self.termtype,
                                   stderr           = self.stderr,
                                   receive_callback = self._telnetlib_received)
        if self.debug >= 5:
            self.tn.set_debuglevel(1)
        if self.tn is None:
            return False
        return True

    def send(self, data):
        self._dbg(4, 'Sending %s' % repr(data))
        try:
            self.tn.write(data)
        except Exception:
            self._dbg(1, 'Error while writing to connection')
            raise

    def _domatch(self, prompt, flush):
        if flush:
            func = self.tn.expect
        else:
            func = self.tn.waitfor

        # Wait for a prompt.
        clean = self.get_driver().clean_response_for_re_match
        self.response = None
        try:
            result, match, self.response = func(prompt, self.timeout, cleanup = clean)
        except Exception:
            self._dbg(1, 'Error while waiting for ' + repr(prompt))
            raise

        if match:
            self._dbg(2, "Got a prompt, match was %s" % repr(match.group()))
            self.buffer.pop(len(self.response))

        self._dbg(5, "Response was %s" % repr(self.response))

        if result == -1:
            error = 'Error while waiting for response from device'
            raise TimeoutException(error)
        if result == -2:
            if self.driver_replaced:
                self.driver_replaced = False
                raise DriverReplacedException()
            else:
                raise ExpectCancelledException()
        if self.response is None:
            raise ProtocolException('whoops - response is None')

        return result, match

    def cancel_expect(self):
        self.tn.cancel_expect = True

    def _set_terminal_size(self, rows, cols):
        self.tn.set_window_size(rows, cols)

    def interact(self, key_handlers = None, handle_window_size = True):
        return self._open_shell(self.tn.sock, key_handlers, handle_window_size)

    def close(self, force = False):
        if self.tn is None:
            return
        if not force:
            try:
                self.response = self.tn.read_all()
            except Exception:
                pass
        self.tn.close()
        self.tn = None
        self.buffer.clear()
