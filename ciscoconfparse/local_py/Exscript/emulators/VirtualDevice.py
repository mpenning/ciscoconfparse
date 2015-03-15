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
Defines the behavior of a device, as needed by L{Exscript.servers}.
"""
from Exscript.emulators import CommandSet

class VirtualDevice(object):
    """
    An object that emulates a remote device.
    """
    LOGIN_TYPE_PASSWORDONLY, \
    LOGIN_TYPE_USERONLY, \
    LOGIN_TYPE_BOTH, \
    LOGIN_TYPE_NONE = range(1, 5)

    PROMPT_STAGE_USERNAME, \
    PROMPT_STAGE_PASSWORD, \
    PROMPT_STAGE_CUSTOM = range(1, 4)

    def __init__(self,
                 hostname,
                 echo       = True,
                 login_type = LOGIN_TYPE_BOTH,
                 strict     = True,
                 banner     = None):
        """
        @type  hostname: str
        @param hostname: The hostname, used for the prompt.

        @keyword banner: A string to show as soon as the connection is opened.
        @keyword login_type: integer constant, one of LOGIN_TYPE_PASSWORDONLY,
            LOGIN_TYPE_USERONLY, LOGIN_TYPE_BOTH, LOGIN_TYPE_NONE.
        @keyword echo: whether to echo the command in a response.
        @keyword strict: Whether to raise when a given command has no handler.
        """
        self.hostname        = hostname
        self.banner          = banner or 'Welcome to %s!\n' % str(hostname)
        self.echo            = echo
        self.login_type      = login_type
        self.prompt          = hostname + '> '
        self.logged_in       = False
        self.commands        = CommandSet(strict = strict)
        self.user_prompt     = 'User: '
        self.password_prompt = 'Password: '
        self.init()

    def _get_prompt(self):
        if self.prompt_stage == self.PROMPT_STAGE_USERNAME:
            if self.login_type == self.LOGIN_TYPE_USERONLY:
                self.prompt_stage = self.PROMPT_STAGE_CUSTOM
            else:
                self.prompt_stage = self.PROMPT_STAGE_PASSWORD
            return self.user_prompt
        elif self.prompt_stage == self.PROMPT_STAGE_PASSWORD:
            self.prompt_stage = self.PROMPT_STAGE_CUSTOM
            return self.password_prompt
        elif self.prompt_stage == self.PROMPT_STAGE_CUSTOM:
            self.logged_in = True
            return self.prompt
        else:
            raise Exception('invalid prompt stage')

    def _create_autoprompt_handler(self, handler):
        if isinstance(handler, str):
            return lambda x: handler + '\n' + self._get_prompt()
        else:
            return lambda x: handler(x) + '\n' + self._get_prompt()

    def get_prompt(self):
        """
        Returns the prompt of the device.

        @rtype:  str
        @return: The current command line prompt.
        """
        return self.prompt

    def set_prompt(self, prompt):
        """
        Change the prompt of the device.

        @type  prompt: str
        @param prompt: The new command line prompt.
        """
        self.prompt = prompt

    def add_command(self, command, handler, prompt = True):
        """
        Registers a command.

        The command may be either a string (which is then automatically
        compiled into a regular expression), or a pre-compiled regular
        expression object.

        If the given response handler is a string, it is sent as the
        response to any command that matches the given regular expression.
        If the given response handler is a function, it is called
        with the command passed as an argument.

        @type  command: str|regex
        @param command: A string or a compiled regular expression.
        @type  handler: function|str
        @param handler: A string, or a response handler.
        @type  prompt: bool
        @param prompt: Whether to show a prompt after completing the command.
        """
        if prompt:
            thehandler = self._create_autoprompt_handler(handler)
        else:
            thehandler = handler
        self.commands.add(command, thehandler)

    def add_commands_from_file(self, filename, autoprompt = True):
        """
        Wrapper around add_command_handler that reads the handlers from the
        file with the given name. The file is a Python script containing
        a list named 'commands' of tuples that map command names to
        handlers.

        @type  filename: str
        @param filename: The name of the file containing the tuples.
        @type  autoprompt: bool
        @param autoprompt: Whether to append a prompt to each response.
        """
        if autoprompt:
            deco = self._create_autoprompt_handler
        else:
            deco = None
        self.commands.add_from_file(filename, deco)

    def init(self):
        """
        Init or reset the virtual device.

        @rtype:  str
        @return: The initial response of the virtual device.
        """
        self.logged_in = False

        if self.login_type == self.LOGIN_TYPE_PASSWORDONLY:
            self.prompt_stage = self.PROMPT_STAGE_PASSWORD
        elif self.login_type == self.LOGIN_TYPE_NONE:
            self.prompt_stage = self.PROMPT_STAGE_CUSTOM
        else:
            self.prompt_stage = self.PROMPT_STAGE_USERNAME

        return self.banner + self._get_prompt()

    def do(self, command):
        """
        "Executes" the given command on the virtual device, and returns
        the response.

        @type  command: str
        @param command: The command to be executed.
        @rtype:  str
        @return: The response of the virtual device.
        """
        echo = self.echo and command or ''
        if not self.logged_in:
            return echo + '\n' + self._get_prompt()

        response = self.commands.eval(command)
        if response is None:
            return echo + '\n' + self._get_prompt()
        return echo + response
