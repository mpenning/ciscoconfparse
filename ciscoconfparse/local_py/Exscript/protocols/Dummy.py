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
A client that talks to a L{Exscript.emulators.VirtualDevice}.
"""
from Exscript.emulators           import VirtualDevice
from Exscript.protocols.Protocol  import Protocol
from Exscript.protocols.Exception import TimeoutException, \
                                         DriverReplacedException, \
                                         ExpectCancelledException

class Dummy(Protocol):
    """
    This protocol adapter does not open a network connection, but talks to
    a L{Exscript.emulators.VirtualDevice} internally.
    """

    def __init__(self, device = None, **kwargs):
        """
        @note: Also supports all keyword arguments that L{Protocol} supports.

        @keyword device: The L{Exscript.emulators.VirtualDevice} with
            which to communicate.
        """
        Protocol.__init__(self, **kwargs)
        self.device    = device
        self.init_done = False
        self.cancel    = False
        self.response  = None
        if not self.device:
            self.device = VirtualDevice('dummy', strict = False)

    def is_dummy(self):
        return True

    def _expect_any(self, prompt_list, flush = True):
        self._doinit()

        # Cancelled by a callback during self._say().
        if self.cancel:
            self.cancel = False
            return -2, None, self.response

        # Look for a match in the buffer.
        for i, prompt in enumerate(prompt_list):
            matches = prompt.search(str(self.buffer))
            if matches is not None:
                self.response = self.buffer.head(matches.start())
                if flush:
                    self.buffer.pop(matches.end())
                return i, matches, self.response

        # "Timeout".
        return -1, None, self.response

    def _say(self, string):
        self._receive_cb(string)
        self.buffer.append(string)

    def cancel_expect(self):
        self.cancel = True

    def _connect_hook(self, hostname, port, init_timeout=None):
        # To more correctly mimic the behavior of a network device, we
        # do not send the banner here, but in authenticate() instead.
        self.buffer.clear()
        return True

    def _doinit(self):
        if not self.init_done:
            self.init_done = True
            self._say(self.device.init())

    def _protocol_authenticate(self, user, password):
        self._doinit()

    def _protocol_authenticate_by_key(self, user, key):
        self._doinit()

    def send(self, data):
        self._dbg(4, 'Sending %s' % repr(data))
        self._say(self.device.do(data))

    def _domatch(self, prompt, flush):
        # Wait for a prompt.
        result, match, self.response = self._expect_any(prompt, flush)

        if match:
            self._dbg(2, "Got a prompt, match was %s" % repr(match.group()))
        else:
            self._dbg(2, "No prompt match")

        self._dbg(5, "Response was %s" % repr(str(self.buffer)))

        if result == -1:
            error = 'Error while waiting for response from device'
            raise TimeoutException(error)
        if result == -2:
            if self.driver_replaced:
                self.driver_replaced = False
                raise DriverReplacedException()
            else:
                raise ExpectCancelledException()

        return result, match

    def close(self, force = False):
        self._say('\n')
        self.buffer.clear()
