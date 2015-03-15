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
from Exscript.parselib           import Token
from Exscript.interpreter.String import String, string_re

class Execute(String):
    def __init__(self, lexer, parser, parent, command):
        Token.__init__(self, 'Execute', lexer, parser, parent)
        self.string        = command
        self.no_prompt     = parser.no_prompt
        self.strip_command = parser.strip_command

        # The lexer has parsed the command, including a newline.
        # Make the debugger point to the beginning of the command.
        self.start -= len(command) + 1
        self.mark_end(self.start + len(command))

        # Make sure that any variables specified in the command are declared.
        string_re.sub(self.variable_test_cb, command)
        self.parent.define(__response__ = [])

    def value(self, context):
        if not self.parent.is_defined('__connection__'):
            error = 'Undefined variable "__connection__"'
            self.lexer.runtime_error(error, self)
        conn = self.parent.get('__connection__')

        # Substitute variables in the command for values.
        command = string_re.sub(self.variable_sub_cb, self.string)
        command = command.lstrip()

        # Execute the command.
        if self.no_prompt:
            conn.send(command + '\r')
            response = ''
        else:
            conn.execute(command)
            response = conn.response.replace('\r\n', '\n')
            response = response.replace('\r', '\n').split('\n')

        if self.strip_command:
            response = response[1:]
        if len(response) == 0:
            response = ['']

        self.parent.define(__response__ = response)
        return 1


    def dump(self, indent = 0):
        print (' ' * indent) + self.name, self.string
