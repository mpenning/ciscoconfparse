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
Defines the behavior of commands by mapping commands to functions.
"""
import re

class CommandSet(object):
    """
    A set of commands to be used by the Dummy adapter.
    """

    def __init__(self, strict = True):
        """
        Constructor.
        """
        self.strict        = strict
        self.response_list = []

    def add(self, command, response):
        """
        Register a command/response pair.

        The command may be either a string (which is then automatically
        compiled into a regular expression), or a pre-compiled regular
        expression object.

        If the given response handler is a string, it is sent as the
        response to any command that matches the given regular expression.
        If the given response handler is a function, it is called
        with the command passed as an argument.

        @type  command: str|regex
        @param command: A string or a compiled regular expression.
        @type  response: function|str
        @param response: A reponse, or a response handler.
        """
        if isinstance(command, str):
            command = re.compile(command)
        elif not hasattr(command, 'search'):
            raise TypeError('command argument must be str or a regex')
        self.response_list.append((command, response))

    def add_from_file(self, filename, handler_decorator = None):
        """
        Wrapper around add() that reads the handlers from the
        file with the given name. The file is a Python script containing
        a list named 'commands' of tuples that map command names to
        handlers.

        @type  filename: str
        @param filename: The name of the file containing the tuples.
        @type  handler_decorator: function
        @param handler_decorator: A function that is used to decorate
               each of the handlers in the file.
        """
        args = {}
        execfile(filename, args)
        commands = args.get('commands')
        if commands is None:
            raise Exception(filename + ' has no variable named "commands"')
        elif not hasattr(commands, '__iter__'):
            raise Exception(filename + ': "commands" is not iterable')
        for key, handler in commands:
            if handler_decorator:
                handler = handler_decorator(handler)
            self.add(key, handler)

    def eval(self, command):
        """
        Evaluate the given string against all registered commands and
        return the defined response.

        @type  command: str
        @param command: The command that is evaluated.
        @rtype:  str or None
        @return: The response, if one was defined.
        """
        for cmd, response in self.response_list:
            if not cmd.match(command):
                continue
            if response is None:
                return None
            elif isinstance(response, str):
                return response
            else:
                return response(command)
        if self.strict:
            raise Exception('Undefined command: ' + repr(command))
        return None
