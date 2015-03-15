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
An abstract base class for all protocols.
"""
import re
import sys
import select
import socket
import signal
import errno
import os
from functools import partial
from Exscript.util.impl import Context, _Context
from Exscript.util.buffer import MonitoredBuffer
from Exscript.util.crypt import otp
from Exscript.util.event import Event
from Exscript.util.cast import to_regexs
from Exscript.util.tty import get_terminal_size
from Exscript.protocols.drivers import driver_map, Driver
from Exscript.protocols.OsGuesser import OsGuesser
from Exscript.protocols.Exception import InvalidCommandException, \
                                         LoginFailure, \
                                         TimeoutException, \
                                         DriverReplacedException, \
                                         ExpectCancelledException

try:
    import termios
    import tty
    _have_termios = True
except ImportError:
    _have_termios = False

_skey_re = re.compile(r'(?:s\/key|otp-md4) (\d+) (\S+)')

class Protocol(object):
    """
    This is the base class for all protocols; it defines the common portions
    of the API.

    The goal of all protocol classes is to provide an interface that
    is unified across protocols, such that the adapters may be used
    interchangeably without changing any other code.

    In order to achieve this, the main challenge are the differences
    arising from the authentication methods that are used.
    The reason is that many devices may support the following variety
    authentication/authorization methods:

        1. Protocol level authentication, such as SSH's built-in
           authentication.

                - p1: password only
                - p2: username
                - p3: username + password
                - p4: username + key
                - p5: username + key + password

        2. App level authentication, such that the authentication may
           happen long after a connection is already accepted.
           This type of authentication is normally used in combination with
           Telnet, but some SSH hosts also do this (users have reported
           devices from Enterasys). These devices may also combine
           protocol-level authentication with app-level authentication.
           The following types of app-level authentication exist:

                - a1: password only
                - a2: username
                - a3: username + password

        3. App level authorization: In order to implement the AAA protocol,
           some devices ask for two separate app-level logins, whereas the
           first serves to authenticate the user, and the second serves to
           authorize him.
           App-level authorization may support the same methods as app-level
           authentication:

                - A1: password only
                - A2: username
                - A3: username + password

    We are assuming that the following methods are used:

        - Telnet:

          - p1 - p5: never
          - a1 - a3: optional
          - A1 - A3: optional

        - SSH:

          - p1 - p5: optional
          - a1 - a3: optional
          - A1 - A3: optional

    To achieve authentication method compatibility across different
    protocols, we must hide all this complexity behind one single API
    call, and figure out which ones are supported.

    As a use-case, our goal is that the following code will always work,
    regardless of which combination of authentication methods a device
    supports::

        key = PrivateKey.from_file('~/.ssh/id_rsa', 'my_key_password')

        # The user account to use for protocol level authentication.
        # The key defaults to None, in which case key authentication is
        # not attempted.
        account = Account(name     = 'myuser',
                          password = 'mypassword',
                          key      = key)

        # The account to use for app-level authentication.
        # password2 defaults to password.
        app_account = Account(name      = 'myuser',
                              password  = 'my_app_password',
                              password2 = 'my_app_password2')

        # app_account defaults to account.
        conn.login(account, app_account = None, flush = True)

    Another important consideration is that once the login is complete, the
    device must be in a clearly defined state, i.e. we need to
    have processed the data that was retrieved from the connected host.

    More precisely, the buffer that contains the incoming data must be in
    a state such that the following call to expect_prompt() will either
    always work, or always fail.

    We hide the following methods behind the login() call::

        # Protocol level authentication.
        conn.protocol_authenticate(...)
        # App-level authentication.
        conn.app_authenticate(...)
        # App-level authorization.
        conn.app_authorize(...)

    The code produces the following result::

        Telnet:
            conn.protocol_authenticate -> NOP
            conn.app_authenticate
                -> waits for username or password prompt, authenticates,
                   returns after a CLI prompt was seen.
            conn.app_authorize
                -> calls driver.enable(), waits for username or password
                   prompt, authorizes, returns after a CLI prompt was seen.

        SSH:
            conn.protocol_authenticate -> authenticates using user/key/password
            conn.app_authenticate -> like Telnet
            conn.app_authorize -> like Telnet

    We can see the following:

        - protocol_authenticate() must not wait for a prompt, because else
          app_authenticate() has no way of knowing whether an app-level
          login is even necessary.

        - app_authenticate() must check the buffer first, to see if
          authentication has already succeeded. In the case that
          app_authenticate() is not necessary (i.e. the buffer contains a
          CLI prompt), it just returns.

          app_authenticate() must NOT eat the prompt from the buffer, because
          else the result may be inconsistent with devices that do not do
          any authentication; i.e., when app_authenticate() is not called.

        - Since the prompt must still be contained in the buffer,
          conn.driver.app_authorize() needs to eat it before it sends the
          command for starting the authorization procedure.

          This has a drawback - if a user attempts to call app_authorize()
          at a time where there is no prompt in the buffer, it would fail.
          So we need to eat the prompt only in cases where we know that
          auto_app_authorize() will attempt to execute a command. Hence
          the driver requires the Driver.supports_auto_authorize() method.

          However, app_authorize() must not eat the CLI prompt that follows.

        - Once all logins are processed, it makes sense to eat the prompt
          depending on the wait parameter. Wait should default to True,
          because it's better that the connection stalls waiting forever,
          than to risk that an error is not immediately discovered due to
          timing issues (this is a race condition that I'm not going to
          detail here).
    """

    def __init__(self,
                 driver             = None,
                 stdout             = None,
                 stderr             = None,
                 debug              = 0,
                 init_timeout       = 30,
                 timeout            = 30,
                 logfile            = None,
                 termtype           = 'dumb',
                 verify_fingerprint = True,
                 account_factory    = None):
        """
        Constructor.
        The following events are provided:

          - data_received_event: A packet was received from the connected host.
          - otp_requested_event: The connected host requested a
          one-time-password to be entered.

        @keyword driver: Driver()|str
        @keyword stdout: Where to write the device response. Defaults to
            os.devnull.
        @keyword stderr: Where to write debug info. Defaults to stderr.
        @keyword debug: An integer between 0 (no debugging) and 5 (very
            verbose debugging) that specifies the amount of debug info
            sent to the terminal. The default value is 0.
        @keyword init_timeout: Timeout for the initial TCP connection attempt
        @keyword timeout: See set_timeout(). The default value is 30.
        @keyword logfile: A file into which a log of the conversation with the
            device is dumped.
        @keyword termtype: The terminal type to request from the remote host,
            e.g. 'vt100'.
        @keyword verify_fingerprint: Whether to verify the host's fingerprint.
        @keyword account_factory: A function that produces a new L{Account}.
        """
        self.data_received_event   = Event()
        self.otp_requested_event   = Event()
        self.os_guesser            = OsGuesser()
        self.auto_driver           = driver_map[self.guess_os()]
        self.proto_authenticated   = False
        self.app_authenticated     = False
        self.app_authorized        = False
        self.manual_user_re        = None
        self.manual_password_re    = None
        self.manual_prompt_re      = None
        self.manual_error_re       = None
        self.manual_login_error_re = None
        self.driver_replaced       = False
        self.host                  = None
        self.port                  = None
        self.last_account          = None
        self.termtype              = termtype
        self.verify_fingerprint    = verify_fingerprint
        self.manual_driver         = None
        self.debug                 = debug
        self.init_timeout          = init_timeout
        self.timeout               = timeout
        self.logfile               = logfile
        self.response              = None
        self.buffer                = MonitoredBuffer()
        self.account_factory       = account_factory
        if stdout is None:
            self.stdout = open(os.devnull, 'w')
        else:
            self.stdout = stdout
        if stderr is None:
            self.stderr = sys.stderr
        else:
            self.stderr = stderr
        if logfile is None:
            self.log = None
        else:
            self.log = open(logfile, 'a')

        # set manual_driver
        if driver is not None:
            if isinstance(driver, str):
                if driver in driver_map:
                    self.manual_driver = driver_map[driver]
                else:
                    self._dbg(1, 'Invalid driver string given. Ignoring...')
            elif isinstance(driver, Driver):
                self.manual_driver = driver
            else:
                self._dbg(1, 'Invalid driver given. Ignoring...')

    def __copy__(self):
        """
        Overwritten to return the very same object instead of copying the
        stream, because copying a network connection is impossible.

        @rtype:  Protocol
        @return: self
        """
        return self

    def __deepcopy__(self, memo):
        """
        Overwritten to return the very same object instead of copying the
        stream, because copying a network connection is impossible.

        @type  memo: object
        @param memo: Please refer to Python's standard library documentation.
        @rtype:  Protocol
        @return: self
        """
        return self

    def _driver_replaced_notify(self, old, new):
        self.driver_replaced = True
        self.cancel_expect()
        msg = 'Protocol: driver replaced: %s -> %s' % (old.name, new.name)
        self._dbg(1, msg)

    def _receive_cb(self, data, remove_cr = True):
        # Clean the data up.
        if remove_cr:
            text = data.replace('\r', '')
        else:
            text = data

        # Write to a logfile.
        self.stdout.write(text)
        self.stdout.flush()
        if self.log is not None:
            self.log.write(text)

        # Check whether a better driver is found based on the incoming data.
        old_driver = self.get_driver()
        self.os_guesser.data_received(data, self.is_app_authenticated())
        self.auto_driver = driver_map[self.guess_os()]
        new_driver       = self.get_driver()
        if old_driver != new_driver:
            self._driver_replaced_notify(old_driver, new_driver)

        # Send signals to subscribers.
        self.data_received_event(data)

    def is_dummy(self):
        """
        Returns True if the adapter implements a virtual device, i.e.
        it isn't an actual network connection.

        @rtype:  Boolean
        @return: True for dummy adapters, False for network adapters.
        """
        return False

    def _dbg(self, level, msg):
        if self.debug < level:
            return
        self.stderr.write(self.get_driver().name + ': ' + msg + '\n')

    def set_driver(self, driver = None):
        """
        Defines the driver that is used to recognize prompts and implement
        behavior depending on the remote system.
        The driver argument may be an instance of a protocols.drivers.Driver
        subclass, a known driver name (string), or None.
        If the driver argument is None, the adapter automatically chooses
        a driver using the guess_os() function.

        @type  driver: Driver()|str
        @param driver: The pattern that, when matched, causes an error.
        """
        if driver is None:
            self.manual_driver = None
        elif isinstance(driver, str):
            if driver not in driver_map:
                raise TypeError('no such driver:' + repr(driver))
            self.manual_driver = driver_map[driver]
        elif isinstance(driver, Driver):
            self.manual_driver = driver
        else:
            raise TypeError('unsupported argument type:' + type(driver))

    def get_driver(self):
        """
        Returns the currently used driver.

        @rtype:  Driver
        @return: A regular expression.
        """
        if self.manual_driver:
            return self.manual_driver
        return self.auto_driver

    def autoinit(self):
        """
        Make the remote host more script-friendly by automatically executing
        one or more commands on it.
        The commands executed depend on the currently used driver.
        For example, the driver for Cisco IOS would execute the
        following commands::

            term len 0
            term width 0
        """
        self.get_driver().init_terminal(self)

    def set_username_prompt(self, regex = None):
        """
        Defines a pattern that is used to monitor the response of the
        connected host for a username prompt.

        @type  regex: RegEx
        @param regex: The pattern that, when matched, causes an error.
        """
        if regex is None:
            self.manual_user_re = regex
        else:
            self.manual_user_re = to_regexs(regex)

    def get_username_prompt(self):
        """
        Returns the regular expression that is used to monitor the response
        of the connected host for a username prompt.

        @rtype:  regex
        @return: A regular expression.
        """
        if self.manual_user_re:
            return self.manual_user_re
        return self.get_driver().user_re

    def set_password_prompt(self, regex = None):
        """
        Defines a pattern that is used to monitor the response of the
        connected host for a password prompt.

        @type  regex: RegEx
        @param regex: The pattern that, when matched, causes an error.
        """
        if regex is None:
            self.manual_password_re = regex
        else:
            self.manual_password_re = to_regexs(regex)

    def get_password_prompt(self):
        """
        Returns the regular expression that is used to monitor the response
        of the connected host for a username prompt.

        @rtype:  regex
        @return: A regular expression.
        """
        if self.manual_password_re:
            return self.manual_password_re
        return self.get_driver().password_re

    def set_prompt(self, prompt = None):
        """
        Defines a pattern that is waited for when calling the expect_prompt()
        method.
        If the set_prompt() method is not called, or if it is called with the
        prompt argument set to None, a default prompt is used that should
        work with many devices running Unix, IOS, IOS-XR, or Junos and others.

        @type  prompt: RegEx
        @param prompt: The pattern that matches the prompt of the remote host.
        """
        if prompt is None:
            self.manual_prompt_re = prompt
        else:
            self.manual_prompt_re = to_regexs(prompt)

    def get_prompt(self):
        """
        Returns the regular expressions that is matched against the host
        response when calling the expect_prompt() method.

        @rtype:  list(re.RegexObject)
        @return: A list of regular expression objects.
        """
        if self.manual_prompt_re:
            return self.manual_prompt_re
        return self.get_driver().prompt_re

    def set_error_prompt(self, error = None):
        """
        Defines a pattern that is used to monitor the response of the
        connected host. If the pattern matches (any time the expect() or
        expect_prompt() methods are used), an error is raised.

        @type  error: RegEx
        @param error: The pattern that, when matched, causes an error.
        """
        if error is None:
            self.manual_error_re = error
        else:
            self.manual_error_re = to_regexs(error)

    def get_error_prompt(self):
        """
        Returns the regular expression that is used to monitor the response
        of the connected host for errors.

        @rtype:  regex
        @return: A regular expression.
        """
        if self.manual_error_re:
            return self.manual_error_re
        return self.get_driver().error_re

    def set_login_error_prompt(self, error = None):
        """
        Defines a pattern that is used to monitor the response of the
        connected host during the authentication procedure.
        If the pattern matches an error is raised.

        @type  error: RegEx
        @param error: The pattern that, when matched, causes an error.
        """
        if error is None:
            self.manual_login_error_re = error
        else:
            self.manual_login_error_re = to_regexs(error)

    def get_login_error_prompt(self):
        """
        Returns the regular expression that is used to monitor the response
        of the connected host for login errors; this is only used during
        the login procedure, i.e. app_authenticate() or app_authorize().

        @rtype:  regex
        @return: A regular expression.
        """
        if self.manual_login_error_re:
            return self.manual_login_error_re
        return self.get_driver().login_error_re

    def set_timeout(self, timeout):
        """
        Defines the maximum time that the adapter waits before a call to
        L{expect()} or L{expect_prompt()} fails.

        @type  timeout: int
        @param timeout: The maximum time in seconds.
        """
        self.timeout = int(timeout)

    def get_timeout(self):
        """
        Returns the current timeout in seconds.

        @rtype:  int
        @return: The timeout in seconds.
        """
        return self.timeout

    def _connect_hook(self, host, port, init_timeout):
        """
        Should be overwritten.
        """
        raise NotImplementedError()

    def connect(self, hostname = None, port = None, init_timeout = None):
        """
        Opens the connection to the remote host or IP address.

        @type  hostname: string
        @param hostname: The remote host or IP address.
        @type  port: int
        @param port: The remote TCP port number.
        @type  init_timeout: int
        @param init_timeout: The initial TCP SYN timeout
        """
        if hostname is not None:
            self.host = hostname
        return self._connect_hook(self.host, port, self.init_timeout)

    def _get_account(self, account):
        if isinstance(account, Context) or isinstance(account, _Context):
            return account.context()
        if account is None:
            account = self.last_account
        if self.account_factory:
            account = self.account_factory(account)
        else:
            if account is None:
                raise TypeError('An account is required')
            account.__enter__()
        self.last_account = account
        return account.context()

    def login(self, account = None, app_account = None, flush = True):
        """
        Log into the connected host using the best method available.
        If an account is not given, default to the account that was
        used during the last call to login(). If a previous call was not
        made, use the account that was passed to the constructor. If that
        also fails, raise a TypeError.

        The app_account is passed to L{app_authenticate()} and
        L{app_authorize()}.
        If app_account is not given, default to the value of the account
        argument.

        @type  account: Account
        @param account: The account for protocol level authentication.
        @type  app_account: Account
        @param app_account: The account for app level authentication.
        @type  flush: bool
        @param flush: Whether to flush the last prompt from the buffer.
        """
        with self._get_account(account) as account:
            if app_account is None:
                app_account = account
            self.authenticate(account, flush = False)
            if self.get_driver().supports_auto_authorize():
                self.expect_prompt()
            self.auto_app_authorize(app_account, flush = flush)

    def authenticate(self, account = None, app_account = None, flush = True):
        """
        Like login(), but skips the authorization procedure.

        @note: If you are unsure whether to use L{authenticate()} or
            L{login()}, stick with L{login}.

        @type  account: Account
        @param account: The account for protocol level authentication.
        @type  app_account: Account
        @param app_account: The account for app level authentication.
        @type  flush: bool
        @param flush: Whether to flush the last prompt from the buffer.
        """
        with self._get_account(account) as account:
            if app_account is None:
                app_account = account

            self.protocol_authenticate(account)
            self.app_authenticate(app_account, flush = flush)

    def _protocol_authenticate(self, user, password):
        pass

    def _protocol_authenticate_by_key(self, user, key):
        pass

    def protocol_authenticate(self, account = None):
        """
        Low-level API to perform protocol-level authentication on protocols
        that support it.

        @note: In most cases, you want to use the login() method instead, as
           it automatically chooses the best login method for each protocol.

        @type  account: Account
        @param account: An account object, like login().
        """
        with self._get_account(account) as account:
            user     = account.get_name()
            password = account.get_password()
            key      = account.get_key()
            if key is None:
                self._dbg(1, "Attempting to authenticate %s." % user)
                self._protocol_authenticate(user, password)
            else:
                self._dbg(1, "Authenticate %s with key." % user)
                self._protocol_authenticate_by_key(user, key)
        self.proto_authenticated = True

    def is_protocol_authenticated(self):
        """
        Returns True if the protocol-level authentication procedure was
        completed, False otherwise.

        @rtype:  bool
        @return: Whether the authentication was completed.
        """
        return self.proto_authenticated

    def _app_authenticate(self,
                          account,
                          password,
                          flush   = True,
                          bailout = False):
        user = account.get_name()

        while True:
            # Wait for any prompt. Once a match is found, we need to be able
            # to find out which type of prompt was matched, so we build a
            # structure to allow for mapping the match index back to the
            # prompt type.
            prompts = (('login-error', self.get_login_error_prompt()),
                       ('username',    self.get_username_prompt()),
                       ('skey',        [_skey_re]),
                       ('password',    self.get_password_prompt()),
                       ('cli',         self.get_prompt()))
            prompt_map  = []
            prompt_list = []
            for section, sectionprompts in prompts:
                for prompt in sectionprompts:
                    prompt_map.append((section, prompt))
                    prompt_list.append(prompt)

            # Wait for the prompt.
            try:
                index, match = self._waitfor(prompt_list)
            except TimeoutException:
                if self.response is None:
                    self.response = ''
                msg = "Buffer: %s" % repr(self.response)
                raise TimeoutException(msg)
            except DriverReplacedException:
                # Driver replaced, retry.
                self._dbg(1, 'Protocol.app_authenticate(): driver replaced')
                continue
            except ExpectCancelledException:
                self._dbg(1, 'Protocol.app_authenticate(): expect cancelled')
                raise
            except EOFError:
                self._dbg(1, 'Protocol.app_authenticate(): EOF')
                raise

            # Login error detected.
            section, prompt = prompt_map[index]
            if section == 'login-error':
                raise LoginFailure("Login failed")

            # User name prompt.
            elif section == 'username':
                self._dbg(1, "Username prompt %s received." % index)
                self.expect(prompt) # consume the prompt from the buffer
                self.send(user + '\r')
                continue

            # s/key prompt.
            elif section == 'skey':
                self._dbg(1, "S/Key prompt received.")
                self.expect(prompt) # consume the prompt from the buffer
                seq  = int(match.group(1))
                seed = match.group(2)
                self.otp_requested_event(account, seq, seed)
                self._dbg(2, "Seq: %s, Seed: %s" % (seq, seed))
                phrase = otp(password, seed, seq)

                # A password prompt is now required.
                self.expect(self.get_password_prompt())
                self.send(phrase + '\r')
                self._dbg(1, "Password sent.")
                if bailout:
                    break
                continue

            # Cleartext password prompt.
            elif section == 'password':
                self._dbg(1, "Cleartext password prompt received.")
                self.expect(prompt) # consume the prompt from the buffer
                self.send(password + '\r')
                if bailout:
                    break
                continue

            # Shell prompt.
            elif section == 'cli':
                self._dbg(1, 'Shell prompt received.')
                if flush:
                    self.expect_prompt()
                break

            else:
                assert False # No such section

    def app_authenticate(self, account = None, flush = True, bailout = False):
        """
        Attempt to perform application-level authentication. Application
        level authentication is needed on devices where the username and
        password are requested from the user after the connection was
        already accepted by the remote device.

        The difference between app-level authentication and protocol-level
        authentication is that in the latter case, the prompting is handled
        by the client, whereas app-level authentication is handled by the
        remote device.

        App-level authentication comes in a large variety of forms, and
        while this method tries hard to support them all, there is no
        guarantee that it will always work.

        We attempt to smartly recognize the user and password prompts;
        for a list of supported operating systems please check the
        Exscript.protocols.drivers module.

        Returns upon finding the first command line prompt. Depending
        on whether the flush argument is True, it also removes the
        prompt from the incoming buffer.

        @type  account: Account
        @param account: An account object, like login().
        @type  flush: bool
        @param flush: Whether to flush the last prompt from the buffer.
        @type  bailout: bool
        @param bailout: Whether to wait for a prompt after sending the password.
        """
        with self._get_account(account) as account:
            user     = account.get_name()
            password = account.get_password()
            self._dbg(1, "Attempting to app-authenticate %s." % user)
            self._app_authenticate(account, password, flush, bailout)
        self.app_authenticated = True

    def is_app_authenticated(self):
        """
        Returns True if the application-level authentication procedure was
        completed, False otherwise.

        @rtype:  bool
        @return: Whether the authentication was completed.
        """
        return self.app_authenticated

    def app_authorize(self, account = None, flush = True, bailout = False):
        """
        Like app_authenticate(), but uses the authorization password
        of the account.

        For the difference between authentication and authorization
        please google for AAA.

        @type  account: Account
        @param account: An account object, like login().
        @type  flush: bool
        @param flush: Whether to flush the last prompt from the buffer.
        @type  bailout: bool
        @param bailout: Whether to wait for a prompt after sending the password.
        """
        with self._get_account(account) as account:
            user     = account.get_name()
            password = account.get_authorization_password()
            if password is None:
                password = account.get_password()
            self._dbg(1, "Attempting to app-authorize %s." % user)
            self._app_authenticate(account, password, flush, bailout)
        self.app_authorized = True

    def auto_app_authorize(self, account = None, flush = True, bailout = False):
        """
        Like authorize(), but instead of just waiting for a user or
        password prompt, it automatically initiates the authorization
        procedure by sending a driver-specific command.

        In the case of devices that understand AAA, that means sending
        a command to the device. For example, on routers running Cisco
        IOS, this command executes the 'enable' command before expecting
        the password.

        In the case of a device that is not recognized to support AAA, this
        method does nothing.

        @type  account: Account
        @param account: An account object, like login().
        @type  flush: bool
        @param flush: Whether to flush the last prompt from the buffer.
        @type  bailout: bool
        @param bailout: Whether to wait for a prompt after sending the password.
        """
        with self._get_account(account) as account:
            self._dbg(1, 'Calling driver.auto_authorize().')
            self.get_driver().auto_authorize(self, account, flush, bailout)

    def is_app_authorized(self):
        """
        Returns True if the application-level authorization procedure was
        completed, False otherwise.

        @rtype:  bool
        @return: Whether the authorization was completed.
        """
        return self.app_authorized

    def send(self, data):
        """
        Sends the given data to the remote host.
        Returns without waiting for a response.

        @type  data: string
        @param data: The data that is sent to the remote host.
        @rtype:  Boolean
        @return: True on success, False otherwise.
        """
        raise NotImplementedError()

    def execute(self, command):
        """
        Sends the given data to the remote host (with a newline appended)
        and waits for a prompt in the response. The prompt attempts to use
        a sane default that works with many devices running Unix, IOS,
        IOS-XR, or Junos and others. If that fails, a custom prompt may
        also be defined using the set_prompt() method.
        This method also modifies the value of the response (self.response)
        attribute, for details please see the documentation of the
        expect() method.

        @type  command: string
        @param command: The data that is sent to the remote host.
        @rtype:  int, re.MatchObject
        @return: The index of the prompt regular expression that matched,
          and the match object.
        """
        self.send(command + '\r')
        return self.expect_prompt()

    def _domatch(self, prompt, flush):
        """
        Should be overwritten.
        """
        raise NotImplementedError()

    def _waitfor(self, prompt):
        re_list  = to_regexs(prompt)
        patterns = [p.pattern for p in re_list]
        self._dbg(2, 'waiting for: ' + repr(patterns))
        result = self._domatch(re_list, False)
        return result

    def waitfor(self, prompt):
        """
        Monitors the data received from the remote host and waits until
        the response matches the given prompt.
        Once a match has been found, the buffer containing incoming data
        is NOT changed. In other words, consecutive calls to this function
        will always work, e.g.::

            conn.waitfor('myprompt>')
            conn.waitfor('myprompt>')
            conn.waitfor('myprompt>')

        will always work. Hence in most cases, you probably want to use
        expect() instead.

        This method also stores the received data in the response
        attribute (self.response).

        Returns the index of the regular expression that matched.

        @type  prompt: str|re.RegexObject|list(str|re.RegexObject)
        @param prompt: One or more regular expressions.
        @rtype:  int, re.MatchObject
        @return: The index of the regular expression that matched,
          and the match object.

        @raise TimeoutException: raised if the timeout was reached.
        @raise ExpectCancelledException: raised when cancel_expect() was
            called in a callback.
        @raise ProtocolException: on other internal errors.
        @raise Exception: May raise other exceptions that are caused
            within the underlying protocol implementations.
        """
        while True:
            try:
                result = self._waitfor(prompt)
            except DriverReplacedException:
                continue # retry
            return result

    def _expect(self, prompt):
        result = self._domatch(to_regexs(prompt), True)
        return result

    def expect(self, prompt):
        """
        Like waitfor(), but also removes the matched string from the buffer
        containing the incoming data. In other words, the following may not
        alway complete::

            conn.expect('myprompt>')
            conn.expect('myprompt>') # timeout

        Returns the index of the regular expression that matched.

        @note: May raise the same exceptions as L{waitfor}.

        @type  prompt: str|re.RegexObject|list(str|re.RegexObject)
        @param prompt: One or more regular expressions.
        @rtype:  int, re.MatchObject
        @return: The index of the regular expression that matched,
          and the match object.
        """
        while True:
            try:
                result = self._expect(prompt)
            except DriverReplacedException:
                continue # retry
            return result

    def expect_prompt(self):
        """
        Monitors the data received from the remote host and waits for a
        prompt in the response. The prompt attempts to use
        a sane default that works with many devices running Unix, IOS,
        IOS-XR, or Junos and others. If that fails, a custom prompt may
        also be defined using the set_prompt() method.
        This method also stores the received data in the response
        attribute (self.response).

        @rtype:  int, re.MatchObject
        @return: The index of the prompt regular expression that matched,
          and the match object.
        """
        result = self.expect(self.get_prompt())

        # We skip the first line because it contains the echo of the command
        # sent.
        self._dbg(5, "Checking %s for errors" % repr(self.response))
        for line in self.response.split('\n')[1:]:
            for prompt in self.get_error_prompt():
                if not prompt.search(line):
                    continue
                args = repr(prompt.pattern), repr(line)
                self._dbg(5, "error prompt (%s) matches %s" % args)
                raise InvalidCommandException('Device said:\n' + self.response)

        return result

    def add_monitor(self, pattern, callback, limit = 80):
        """
        Calls the given function whenever the given pattern matches the
        incoming data.

        @note: If you want to catch all incoming data regardless of a
        pattern, use the L{Protocol.on_data_received} event instead.

        Arguments passed to the callback are the protocol instance, the
        index of the match, and the match object of the regular expression.

        @type  pattern: str|re.RegexObject|list(str|re.RegexObject)
        @param pattern: One or more regular expressions.
        @type  callback: callable
        @param callback: The function that is called.
        @type  limit: int
        @param limit: The maximum size of the tail of the buffer
                      that is searched, in number of bytes.
        """
        self.buffer.add_monitor(pattern, partial(callback, self), limit)

    def cancel_expect(self):
        """
        Cancel the current call to L{expect()} as soon as control returns
        to the protocol adapter. This method may be used in callbacks to
        the events emitted by this class, e.g. Protocol.data_received_event.
        """
        raise NotImplementedError()

    def _call_key_handlers(self, key_handlers, data):
        if key_handlers is not None:
            for key, func in key_handlers.iteritems():
                if data == key:
                    func(self)
                    return True
        return False

    def _set_terminal_size(self, rows, cols):
        raise NotImplementedError()

    def _open_posix_shell(self,
                          channel,
                          key_handlers,
                          handle_window_size):
        # We need to make sure to use an unbuffered stdin, else multi-byte
        # chars (such as arrow keys) won't work properly.
        stdin  = os.fdopen(sys.stdin.fileno(), 'r', 0)
        oldtty = termios.tcgetattr(stdin)

        # Update the terminal size whenever the size changes.
        if handle_window_size:
            def handle_sigwinch(signum, frame):
                rows, cols = get_terminal_size()
                self._set_terminal_size(rows, cols)
            signal.signal(signal.SIGWINCH, handle_sigwinch)
            handle_sigwinch(None, None)

        # Read from stdin and write to the network, endlessly.
        try:
            tty.setraw(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())
            channel.settimeout(0.0)

            while True:
                try:
                    r, w, e = select.select([channel, stdin], [], [])
                except select.error, e:
                    code, message = e
                    if code == errno.EINTR:
                        # This may happen when SIGWINCH is called
                        # during the select; we just retry then.
                        continue
                    raise

                if channel in r:
                    try:
                        data = channel.recv(1024)
                    except socket.timeout:
                        pass
                    if not data:
                        self._dbg(1, 'EOF from remote')
                        break
                    self._receive_cb(data, False)
                    self.buffer.append(data)
                if stdin in r:
                    data = stdin.read(1)
                    self.buffer.clear()
                    if len(data) == 0:
                        break

                    # Temporarily revert stdin behavior while callbacks are
                    # active.
                    curtty = termios.tcgetattr(stdin)
                    termios.tcsetattr(stdin, termios.TCSADRAIN, oldtty)
                    is_handled = self._call_key_handlers(key_handlers, data)
                    termios.tcsetattr(stdin, termios.TCSADRAIN, curtty)

                    if not is_handled:
                        channel.send(data)
        finally:
            termios.tcsetattr(stdin, termios.TCSADRAIN, oldtty)

    def _open_windows_shell(self, channel, key_handlers):
        import threading

        def writeall(sock):
            while True:
                data = sock.recv(256)
                if not data:
                    self._dbg(1, 'EOF from remote')
                    break
                self._receive_cb(data)

        writer = threading.Thread(target=writeall, args=(channel,))
        writer.start()

        try:
            while True:
                data = sys.stdin.read(1)
                if not data:
                    break
                if not self._call_key_handlers(key_handlers, data):
                    channel.send(data)
        except EOFError:
            self._dbg(1, 'User hit ^Z or F6')

    def _open_shell(self, channel, key_handlers, handle_window_size):
        if _have_termios:
            return self._open_posix_shell(channel, key_handlers, handle_window_size)
        else:
            return self._open_windows_shell(channel, key_handlers, handle_window_size)

    def interact(self, key_handlers = None, handle_window_size = True):
        """
        Opens a simple interactive shell. Returns when the remote host
        sends EOF.
        The optional key handlers are functions that are called whenever
        the user presses a specific key. For example, to catch CTRL+y::

            conn.interact({'\031': mycallback})

        @type  key_handlers: dict(str: callable)
        @param key_handlers: A dictionary mapping chars to a functions.
        @type  handle_window_size: bool
        @param handle_window_size: Whether the connected host is notified
          when the terminal size changes.
        """
        raise NotImplementedError()

    def close(self, force = False):
        """
        Closes the connection with the remote host.
        """
        raise NotImplementedError()

    def get_host(self):
        """
        Returns the name or address of the currently connected host.

        @rtype:  string
        @return: A name or an address.
        """
        return self.host

    def guess_os(self):
        """
        Returns an identifier that specifies the operating system that is
        running on the remote host. This OS is obtained by watching the
        response of the remote host, such as any messages retrieved during
        the login procedure.

        The OS is also a wild guess that often depends on volatile
        information, so there is no guarantee that this will always work.

        @rtype:  string
        @return: A string to help identify the remote operating system.
        """
        return self.os_guesser.get('os')
