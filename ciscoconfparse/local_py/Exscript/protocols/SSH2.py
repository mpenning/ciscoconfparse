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
SSH version 2 support, based on paramiko.
"""
import os
import time
import select
import socket
import paramiko
import Crypto
from binascii               import hexlify
from paramiko               import util
from paramiko.resource      import ResourceManager
from paramiko.ssh_exception import SSHException, \
                                   AuthenticationException, \
                                   BadHostKeyException
from Exscript.util.tty            import get_terminal_size
from Exscript.PrivateKey          import PrivateKey
from Exscript.protocols.Protocol  import Protocol
from Exscript.protocols.Exception import ProtocolException, \
                                         LoginFailure, \
                                         TimeoutException, \
                                         DriverReplacedException, \
                                         ExpectCancelledException

# Workaround for paramiko error; avoids a warning message.
util.log_to_file(os.devnull)

# Register supported key types.
keymap = {'rsa': paramiko.RSAKey, 'dss': paramiko.DSSKey}
for key in keymap:
    PrivateKey.keytypes.add(key)

class SSH2(Protocol):
    """
    The secure shell protocol version 2 adapter, based on Paramiko.
    """
    KEEPALIVE_INTERVAL = 2.5 * 60    # Two and a half minutes

    def __init__(self, **kwargs):
        Protocol.__init__(self, **kwargs)
        self.client = None
        self.shell  = None
        self.cancel = False

        # Since each protocol may be created in it's own thread, we must
        # re-initialize the random number generator to make sure that
        # child threads have no way of guessing the numbers of the parent.
        # If we don't, PyCrypto generates an error message for security
        # reasons.
        try:
            Crypto.Random.atfork()
        except AttributeError:
            # pycrypto versions that have no "Random" module also do not
            # detect the missing atfork() call, so they do not raise.
            pass

        # Paramiko client stuff.
        self._system_host_keys   = paramiko.HostKeys()
        self._host_keys          = paramiko.HostKeys()
        self._host_keys_filename = None

        if self.verify_fingerprint:
            self._missing_host_key = self._reject_host_key
        else:
            self._missing_host_key = self._add_host_key

    def _reject_host_key(self, key):
        name = key.get_name()
        fp   = hexlify(key.get_fingerprint())
        msg  = 'Rejecting %s host key for %s: %s' % (name, self.host, fp)
        self._dbg(1, msg)

    def _add_host_key(self, key):
        name = key.get_name()
        fp   = hexlify(key.get_fingerprint())
        msg  = 'Adding %s host key for %s: %s' % (name, self.host, fp)
        self._dbg(1, msg)
        self._host_keys.add(self.host, name, key)
        if self._host_keys_filename is not None:
            self._save_host_keys()

    def _save_host_keys(self):
        with open(self._host_keys_filename, 'w') as file:
            file.write('# SSH host keys collected by Exscript\n')
            for hostname, keys in self._host_keys.iteritems():
                for keytype, key in keys.iteritems():
                    line = ' '.join((hostname, keytype, key.get_base64()))
                    file.write(line + '\n')

    def _load_system_host_keys(self, filename = None):
        """
        Load host keys from a system (read-only) file.  Host keys read with
        this method will not be saved back by L{save_host_keys}.

        This method can be called multiple times.  Each new set of host keys
        will be merged with the existing set (new replacing old if there are
        conflicts).

        If C{filename} is left as C{None}, an attempt will be made to read
        keys from the user's local "known hosts" file, as used by OpenSSH,
        and no exception will be raised if the file can't be read.  This is
        probably only useful on posix.

        @param filename: the filename to read, or C{None}
        @type filename: str

        @raise IOError: if a filename was provided and the file could not be
            read
        """
        if filename is None:
            # try the user's .ssh key file, and mask exceptions
            filename = os.path.expanduser('~/.ssh/known_hosts')
            try:
                self._system_host_keys.load(filename)
            except IOError:
                pass
            return
        self._system_host_keys.load(filename)

    def _paramiko_connect(self):
        # Find supported address families.
        addrinfo = socket.getaddrinfo(self.host, self.port)
        for family, socktype, proto, canonname, sockaddr in addrinfo:
            af = family
            addr = sockaddr
            if socktype == socket.SOCK_STREAM:
                break

        # Open a socket.
        sock = socket.socket(af, socket.SOCK_STREAM)
        try:
            sock.settimeout(self.init_timeout or None)
        except:
            pass
        sock.connect(addr)

        # Init the paramiko protocol.
        t = paramiko.Transport(sock)
        t.start_client()
        ResourceManager.register(self, t)

        # Check system host keys.
        server_key = t.get_remote_server_key()
        keytype = server_key.get_name()
        our_server_key = self._system_host_keys.get(self.host, {}).get(keytype, None)
        if our_server_key is None:
            our_server_key = self._host_keys.get(self.host, {}).get(keytype, None)
        if our_server_key is None:
            self._missing_host_key(server_key)
            # if the callback returns, assume the key is ok
            our_server_key = server_key
        if server_key != our_server_key:
            raise BadHostKeyException(self.host, server_key, our_server_key)

        t.set_keepalive(self.KEEPALIVE_INTERVAL)
        return t

    def _paramiko_auth_none(self, username, password = None):
        self.client.auth_none(username)

    def _paramiko_auth_password(self, username, password):
        self.client.auth_password(username, password or '')

    def _paramiko_auth_agent(self, username, password = None):
        keys = paramiko.Agent().get_keys()
        if not keys:
            raise AuthenticationException('auth agent found no keys')

        saved_exception = AuthenticationException(
            'Failed to authenticate with given username')

        for key in keys:
            try:
                fp = hexlify(key.get_fingerprint())
                self._dbg(1, 'Trying SSH agent key %s' % fp)
                self.client.auth_publickey(username, key)
                return
            except SSHException, e:
                saved_exception = e
        raise saved_exception

    def _paramiko_auth_key(self, username, keys, password):
        if password is None:
            password = ''

        saved_exception = AuthenticationException(
            'Failed to authenticate with given username and password/key')

        for pkey_class, filename in keys:
            try:
                key = pkey_class.from_private_key_file(filename, password)
                fp  = hexlify(key.get_fingerprint())
                self._dbg(1, 'Trying key %s in %s' % (fp, filename))
                self.client.auth_publickey(username, key)
                return
            except SSHException, e:
                saved_exception = e
            except IOError, e:
                saved_exception = e
        raise saved_exception

    def _paramiko_auth_autokey(self, username, password):
        keyfiles = []
        for cls, file in ((paramiko.RSAKey, '~/.ssh/id_rsa'), # Unix
                          (paramiko.DSSKey, '~/.ssh/id_dsa'), # Unix
                          (paramiko.RSAKey, '~/ssh/id_rsa'),  # Windows
                          (paramiko.DSSKey, '~/ssh/id_dsa')): # Windows
            file = os.path.expanduser(file)
            if os.path.isfile(file):
                keyfiles.append((cls, file))
        self._paramiko_auth_key(username, keyfiles, password)

    def _paramiko_auth(self, username, password):
        for method in (self._paramiko_auth_password,
                       self._paramiko_auth_agent,
                       self._paramiko_auth_autokey,
                       self._paramiko_auth_none):
            self._dbg(1, 'Authenticating with %s' % method.__name__)
            try:
                method(username, password)
                return
            except BadHostKeyException, e:
                self._dbg(1, 'Bad host key!')
                last_exception = e
            except AuthenticationException, e:
                self._dbg(1, 'Authentication with %s failed' % method.__name__)
                last_exception = e
            except SSHException, e:
                self._dbg(1, 'Missing host key.')
                last_exception = e
        raise LoginFailure('Login failed: ' + str(last_exception))

    def _paramiko_shell(self):
        rows, cols = get_terminal_size()

        try:
            self.shell = self.client.open_session()
            self.shell.get_pty(self.termtype, cols, rows)
            self.shell.invoke_shell()
        except SSHException, e:
            self._dbg(1, 'Failed to open shell.')
            raise LoginFailure('Failed to open shell: ' + str(e))

    def _connect_hook(self, hostname, port, init_timeout):
        self.host   = hostname
        self.port   = port or 22
        self.client = self._paramiko_connect()
        self._load_system_host_keys()
        return True

    def _protocol_authenticate(self, user, password):
        self._paramiko_auth(user, password)
        self._paramiko_shell()

    def _protocol_authenticate_by_key(self, user, key):
        # Allow multiple key files.
        key_file = key.get_filename()
        if key_file is None:
            key_file = []
        elif isinstance(key_file, (str, unicode)):
            key_file = [key_file]

        # Try each key.
        keys = []
        for file in key_file:
            keys.append((keymap[key.get_type()], file))
        self._dbg(1, 'authenticating using _paramiko_auth_key().')
        self._paramiko_auth_key(user, keys, key.get_password())

        self._paramiko_shell()

    def send(self, data):
        self._dbg(4, 'Sending %s' % repr(data))
        self.shell.sendall(data)

    def _wait_for_data(self):
        end = time.time() + self.timeout
        while True:
            readable, writeable, excp = select.select([self.shell], [], [], 1)
            if readable:
                return True
            if time.time() > end:
                return False

    def _fill_buffer(self):
        # Wait for a response of the device.
        if not self._wait_for_data():
            error = 'Timeout while waiting for response from device'
            raise TimeoutException(error)

        # Read the response.
        data = self.shell.recv(200)
        if not data:
            return False
        self._receive_cb(data)
        self.buffer.append(data)
        return True

    def _domatch(self, prompt, flush):
        self._dbg(1, "Expecting a prompt")
        self._dbg(2, "Expected pattern: " + repr(p.pattern for p in prompt))
        search_window_size = 150
        while not self.cancel:
            # Check whether what's buffered matches the prompt.
            driver        = self.get_driver()
            search_window = self.buffer.tail(search_window_size)
            search_window, incomplete_tail = driver.clean_response_for_re_match(search_window)
            match         = None
            for n, regex in enumerate(prompt):
                match = regex.search(search_window)
                if match is not None:
                    break

            if not match:
                if not self._fill_buffer():
                    error = 'EOF while waiting for response from device'
                    raise ProtocolException(error)
                continue

            end = self.buffer.size() - len(search_window) + match.end()
            if flush:
                self.response = self.buffer.pop(end)
            else:
                self.response = self.buffer.head(end)
            return n, match

        # Ending up here, self.cancel_expect() was called.
        self.cancel = False
        if self.driver_replaced:
            self.driver_replaced = False
            raise DriverReplacedException()
        raise ExpectCancelledException()

    def cancel_expect(self):
        self.cancel = True

    def _set_terminal_size(self, rows, cols):
        self.shell.resize_pty(cols, rows)

    def interact(self, key_handlers = None, handle_window_size = True):
        return self._open_shell(self.shell, key_handlers, handle_window_size)

    def close(self, force = False):
        if self.shell is None:
            return
        if not force:
            self._fill_buffer()
        self.shell.close()
        self.shell = None
        self.client.close()
        self.client = None
        self.buffer.clear()
