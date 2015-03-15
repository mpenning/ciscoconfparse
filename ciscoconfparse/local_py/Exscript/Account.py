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
Representing user accounts.
"""
import threading
from Exscript.util.event import Event
from Exscript.util.impl import Context

class Account(object):
    """
    This class represents a user account.
    """

    def __init__(self, name, password = '', password2 = None, key = None):
        """
        Constructor.

        The authorization password is only required on hosts that
        separate the authentication from the authorization procedure.
        If an authorization password is not given, it defaults to the
        same value as the authentication password.

        @type  name: string
        @param name: A username.
        @type  password: string
        @param password: The authentication password.
        @type  password2: string
        @param password2: The authorization password, if required.
        @type  key: PrivateKey
        @param key: A private key, if required.
        """
        self.acquired_event         = Event()
        self.released_event         = Event()
        self.changed_event          = Event()
        self.name                   = name
        self.password               = password
        self.authorization_password = password2
        self.key                    = key
        self.synclock               = threading.Condition(threading.Lock())
        self.lock                   = threading.Lock()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, thetype, value, traceback):
        self.release()

    def context(self):
        """
        When you need a 'with' context for an already-acquired account.
        """
        return Context(self)

    def acquire(self, signal = True):
        """
        Locks the account.

        @type  signal: bool
        @param signal: Whether to emit the acquired_event signal.
        """
        with self.synclock:
            while not self.lock.acquire(False):
                self.synclock.wait()
            if signal:
                self.acquired_event(self)
            self.synclock.notify_all()

    def release(self, signal = True):
        """
        Unlocks the account.

        @type  signal: bool
        @param signal: Whether to emit the released_event signal.
        """
        with self.synclock:
            self.lock.release()
            if signal:
                self.released_event(self)
            self.synclock.notify_all()

    def set_name(self, name):
        """
        Changes the name of the account.

        @type  name: string
        @param name: The account name.
        """
        self.name = name
        self.changed_event.emit(self)

    def get_name(self):
        """
        Returns the name of the account.

        @rtype:  string
        @return: The account name.
        """
        return self.name

    def set_password(self, password):
        """
        Changes the password of the account.

        @type  password: string
        @param password: The account password.
        """
        self.password = password
        self.changed_event.emit(self)

    def get_password(self):
        """
        Returns the password of the account.

        @rtype:  string
        @return: The account password.
        """
        return self.password

    def set_authorization_password(self, password):
        """
        Changes the authorization password of the account.

        @type  password: string
        @param password: The new authorization password.
        """
        self.authorization_password = password
        self.changed_event.emit(self)

    def get_authorization_password(self):
        """
        Returns the authorization password of the account.

        @rtype:  string
        @return: The account password.
        """
        return self.authorization_password or self.password

    def get_key(self):
        """
        Returns the key of the account, if any.

        @rtype:  PrivateKey|None
        @return: A key object.
        """
        return self.key
