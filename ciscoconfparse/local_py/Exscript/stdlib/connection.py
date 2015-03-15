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
from Exscript             import Account
from Exscript.stdlib.util import secure_function

@secure_function
def authenticate(scope):
    """
    Looks for any username/password prompts on the current connection
    and logs in using the login information that was passed to Exscript.
    """
    scope.get('__connection__').app_authenticate()
    return True

@secure_function
def authenticate_user(scope, user = [None], password = [None]):
    """
    Like authenticate(), but logs in using the given user and password.
    If a user and password are not given, the function uses the same
    user and password that were used at the last login attempt; it is
    an error if no such attempt was made before.

    @type  user: string
    @param user: A username.
    @type  password: string
    @param password: A password.
    """
    conn = scope.get('__connection__')
    user = user[0]
    if user is None:
        conn.app_authenticate()
    else:
        account = Account(user, password[0])
        conn.app_authenticate(account)
    return True

@secure_function
def authorize(scope, password = [None]):
    """
    Looks for a password prompt on the current connection
    and enters the given password.
    If a password is not given, the function uses the same
    password that was used at the last login attempt; it is
    an error if no such attempt was made before.

    @type  password: string
    @param password: A password.
    """
    conn     = scope.get('__connection__')
    password = password[0]
    if password is None:
        conn.app_authorize()
    else:
        account = Account('', password)
        conn.app_authorize(account)
    return True

@secure_function
def auto_authorize(scope, password = [None]):
    """
    Executes a command on the remote host that causes an authorization
    procedure to be started, then authorizes using the given password
    in the same way in which authorize() works.
    Depending on the detected operating system of the remote host the
    following commands are started:

      - on IOS, the "enable" command is executed.
      - nothing on other operating systems yet.

    @type  password: string
    @param password: A password.
    """
    conn     = scope.get('__connection__')
    password = password[0]
    if password is None:
        conn.auto_app_authorize()
    else:
        account = Account('', password)
        conn.auto_app_authorize(account)
    return True

@secure_function
def autoinit(scope):
    """
    Make the remote host more script-friendly by automatically executing
    one or more commands on it.
    The commands executed depend on the currently used driver.
    For example, the driver for Cisco IOS would execute the
    following commands::

        term len 0
        term width 0
    """
    scope.get('__connection__').autoinit()
    return True

@secure_function
def close(scope):
    """
    Closes the existing connection with the remote host. This function is
    rarely used, as normally Exscript closes the connection automatically
    when the script has completed.
    """
    conn = scope.get('__connection__')
    conn.close(1)
    scope.define(__response__ = conn.response)
    return True

@secure_function
def exec_(scope, data):
    """
    Sends the given data to the remote host and waits until the host
    has responded with a prompt.
    If the given data is a list of strings, each item is sent, and
    after each item a prompt is expected.

    This function also causes the response of the command to be stored
    in the built-in __response__ variable.

    @type  data: string
    @param data: The data that is sent.
    """
    conn     = scope.get('__connection__')
    response = []
    for line in data:
        conn.send(line)
        conn.expect_prompt()
        response += conn.response.split('\n')[1:]
    scope.define(__response__ = response)
    return True

@secure_function
def execline(scope, data):
    """
    Like exec(), but appends a newline to the command in data before sending
    it.

    @type  data: string
    @param data: The data that is sent.
    """
    conn     = scope.get('__connection__')
    response = []
    for line in data:
        conn.execute(line)
        response += conn.response.split('\n')[1:]
    scope.define(__response__ = response)
    return True

@secure_function
def guess_os(scope):
    """
    Guesses the operating system of the connected host.

    The recognition is based on the past conversation that has happened
    on the host; Exscript looks for known patterns and maps them to specific
    operating systems.

    @rtype:  string
    @return: The operating system.
    """
    conn = scope.get('__connection__')
    return [conn.guess_os()]

@secure_function
def send(scope, data):
    """
    Like exec(), but does not wait for a response of the remote host after
    sending the command.

    @type  data: string
    @param data: The data that is sent.
    """
    conn = scope.get('__connection__')
    for line in data:
        conn.send(line)
    return True

@secure_function
def sendline(scope, data):
    """
    Like execline(), but does not wait for a response of the remote host after
    sending the command.

    @type  data: string
    @param data: The data that is sent.
    """
    conn = scope.get('__connection__')
    for line in data:
        conn.send(line + '\r')
    return True

@secure_function
def wait_for(scope, prompt):
    """
    Waits until the response of the remote host contains the given pattern.

    @type  prompt: regex
    @param prompt: The prompt pattern.
    """
    conn = scope.get('__connection__')
    conn.expect(prompt)
    scope.define(__response__ = conn.response)
    return True

@secure_function
def set_prompt(scope, prompt = None):
    """
    Defines the pattern that is recognized at any future time when Exscript
    needs to wait for a prompt.
    In other words, whenever Exscript waits for a prompt, it searches the
    response of the host for the given pattern and continues as soon as the
    pattern is found.

    Exscript waits for a prompt whenever it sends a command (unless the send()
    method was used). set_prompt() redefines as to what is recognized as a
    prompt.

    @type  prompt: regex
    @param prompt: The prompt pattern.
    """
    conn = scope.get('__connection__')
    conn.set_prompt(prompt)
    return True

@secure_function
def set_error(scope, error_re = None):
    """
    Defines a pattern that, whenever detected in the response of the remote
    host, causes an error to be raised.

    In other words, whenever Exscript waits for a prompt, it searches the
    response of the host for the given pattern and raises an error if the
    pattern is found.

    @type  error_re: regex
    @param error_re: The error pattern.
    """
    conn = scope.get('__connection__')
    conn.set_error_prompt(error_re)
    return True

@secure_function
def set_timeout(scope, timeout):
    """
    Defines the time after which Exscript fails if it does not receive a
    prompt from the remote host.

    @type  timeout: int
    @param timeout: The timeout in seconds.
    """
    conn = scope.get('__connection__')
    conn.set_timeout(int(timeout[0]))
    return True
