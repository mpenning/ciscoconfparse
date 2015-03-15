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
A Telnet server.
"""
import select
from Exscript.servers.Server import Server

class Telnetd(Server):
    """
    A Telnet server. Usage::

        device = VirtualDevice('myhost')
        daemon = Telnetd('localhost', 1234, device)
        device.add_command('ls', 'ok', prompt = True)
        device.add_command('exit', daemon.exit_command)
        daemon.start() # Start the server.
        daemon.exit()  # Stop the server.
        daemon.join()  # Wait until it terminates.
    """

    def _recvline(self, conn):
        while not '\n' in self.buf:
            self._poll_child_process()
            r, w, x = select.select([conn], [], [], self.timeout)
            if not self.running:
                return None
            if not r:
                continue
            buf = conn.recv(1024)
            if not buf:
                self.running = False
                return None
            self.buf += buf.replace('\r\n', '\n').replace('\r', '\n')
        lines    = self.buf.split('\n')
        self.buf = '\n'.join(lines[1:])
        return lines[0] + '\n'

    def _shutdown_notify(self, conn):
        try:
            conn.send('Server is shutting down.\n')
        except Exception:
            pass

    def _handle_connection(self, conn):
        conn.send(self.device.init())

        while self.running:
            line = self._recvline(conn)
            if not line:
                continue
            response = self.device.do(line)
            if response:
                conn.send(response)
