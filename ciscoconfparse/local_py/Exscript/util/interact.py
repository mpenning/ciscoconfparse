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
Tools for interacting with the user on the command line.
"""
import os
import sys
import getpass
import ConfigParser
import shutil
from tempfile           import NamedTemporaryFile
from Exscript           import Account
from Exscript.util.cast import to_list

class InputHistory(object):
    """
    When prompting a user for input it is often useful to record his
    input in a file, and use previous input as a default value.
    This class allows for recording user input in a config file to
    allow for such functionality.
    """

    def __init__(self,
                 filename = '~/.exscript_history',
                 section  = os.path.basename(sys.argv[0])):
        """
        Constructor. The filename argument allows for listing on or
        more config files, and is passed to Python's RawConfigParser; please
        consult the documentation of RawConfigParser.read() if you require
        more information.
        The optional section argument allows to specify
        a section under which the input is stored in the config file.
        The section defaults to the name of the running script.

        Silently creates a tempfile if the given file can not be opened,
        such that the object behavior does not change, but the history
        is not remembered across instances.

        @type  filename: str|list(str)
        @param filename: The config file.
        @type  section: str
        @param section: The section in the configfile.
        """
        self.section = section
        self.parser  = ConfigParser.RawConfigParser()
        filename     = os.path.expanduser(filename)

        try:
            self.file = open(filename, 'a+')
        except IOError:
            import warnings
            warnings.warn('could not open %s, using tempfile' % filename)
            self.file = NamedTemporaryFile()

        self.parser.readfp(self.file)
        if not self.parser.has_section(self.section):
            self.parser.add_section(self.section)

    def get(self, key, default = None):
        """
        Returns the input with the given key from the section that was
        passed to the constructor. If either the section or the key
        are not found, the default value is returned.

        @type  key: str
        @param key: The key for which to return a value.
        @type  default: str|object
        @param default: The default value that is returned.
        @rtype:  str|object
        @return: The value from the config file, or the default.
        """
        if not self.parser:
            return default
        try:
            return self.parser.get(self.section, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return default

    def set(self, key, value):
        """
        Saves the input with the given key in the section that was
        passed to the constructor. If either the section or the key
        are not found, they are created.

        Does nothing if the given value is None.

        @type  key: str
        @param key: The key for which to define a value.
        @type  value: str|None
        @param value: The value that is defined, or None.
        @rtype:  str|None
        @return: The given value.
        """
        if value is None:
            return None

        self.parser.set(self.section, key, value)
        with NamedTemporaryFile(delete = False) as tmpfile:
            self.parser.write(tmpfile)

        self.file.close()
        shutil.move(tmpfile.name, self.file.name)
        self.file = open(self.file.name)
        return value

def prompt(key,
           message,
           default = None,
           strip   = True,
           check   = None,
           history = None):
    """
    Prompt the user for input. This function is similar to Python's built
    in raw_input, with the following differences:

        - You may specify a default value that is returned if the user
          presses "enter" without entering anything.
        - The user's input is recorded in a config file, and offered
          as the default value the next time this function is used
          (based on the key argument).

    The config file is based around the L{InputHistory}. If a history object
    is not passed in the history argument, a new one will be created.

    The key argument specifies under which name the input is saved in the
    config file.

    The given default value is only used if a default was not found in the
    history.

    The strip argument specifies that the returned value should be stripped
    of whitespace (default).

    The check argument allows for validating the input; if the validation
    fails, the user is prompted again before the value is stored in the
    InputHistory. Example usage::

        def validate(input):
            if len(input) < 4:
                return 'Please enter at least 4 characters!'
        value = prompt('test', 'Enter a value', 'My Default', check = validate)
        print 'You entered:', value

    This leads to the following output::

        Please enter a value [My Default]: abc
        Please enter at least 4 characters!
        Please enter a value [My Default]: Foobar
        You entered: Foobar

    The next time the same code is started, the input 'Foobar' is remembered::

        Please enter a value [Foobar]:        (enters nothing)
        You entered: Foobar

    @type  key: str
    @param key: The key under which to store the input in the L{InputHistory}.
    @type  message: str
    @param message: The user prompt.
    @type  default: str|None
    @param default: The offered default if none was found in the history.
    @type  strip: bool
    @param strip: Whether to remove whitespace from the input.
    @type  check: callable
    @param check: A function that is called for validating the input.
    @type  history: L{InputHistory}|None
    @param history: The history used for recording default values, or None.
    """
    if history is None:
        history = InputHistory()
    default = history.get(key, str(default))
    while True:
        if default is None:
            value = raw_input('%s: ' % message)
        else:
            value = raw_input('%s [%s]: ' % (message, default)) or default
        if strip:
            value = value.strip()
        if not check:
            break
        errors = check(value)
        if errors:
            print '\n'.join(to_list(errors))
        else:
            break
    history.set(key, value)
    return value

def get_filename(key, message, default = None, history = None):
    """
    Like L{prompt()}, but only accepts the name of an existing file
    as an input.

    @type  key: str
    @param key: The key under which to store the input in the L{InputHistory}.
    @type  message: str
    @param message: The user prompt.
    @type  default: str|None
    @param default: The offered default if none was found in the history.
    @type  history: L{InputHistory}|None
    @param history: The history used for recording default values, or None.
    """
    def _validate(string):
        if not os.path.isfile(string):
            return 'File not found. Please enter a filename.'
    return prompt(key, message, default, True, _validate, history)

def get_user():
    """
    Prompts the user for his login name, defaulting to the USER environment
    variable. Returns a string containing the username.
    May throw an exception if EOF is given by the user.

    @rtype:  string
    @return: A username.
    """
    # Read username and password.
    try:
        env_user = getpass.getuser()
    except KeyError:
        env_user = ''
    if env_user is None or env_user == '':
        user = raw_input('Please enter your user name: ')
    else:
        user = raw_input('Please enter your user name [%s]: ' % env_user)
        if user == '':
            user = env_user
    return user

def get_login():
    """
    Prompts the user for the login name using get_user(), and also asks for
    the password.
    Returns a tuple containing the username and the password.
    May throw an exception if EOF is given by the user.

    @rtype:  (string, string)
    @return: A tuple containing the username and the password.
    """
    user     = get_user()
    password = getpass.getpass('Please enter your password: ')
    return user, password

def read_login():
    """
    Like get_login(), but returns an Account object.

    @rtype:  Account
    @return: A new account.
    """
    user, password = get_login()
    return Account(user, password)
