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
import copy
from Exscript.parselib            import Lexer
from Exscript.interpreter.Program import Program

class Parser(object):
    def __init__(self, **kwargs):
        self.no_prompt     = kwargs.get('no_prompt',     False)
        self.strip_command = kwargs.get('strip_command', True)
        self.secure_only   = kwargs.get('secure',        False)
        self.debug         = kwargs.get('debug',         0)
        self.variables     = {}

    def define(self, **kwargs):
        for key, value in kwargs.iteritems():
            if hasattr(value, '__iter__') or hasattr(value, '__call__'):
                self.variables[key] = value
            else:
                self.variables[key] = [value]

    def define_object(self, **kwargs):
        self.variables.update(kwargs)

    def _create_lexer(self):
        variables = copy.deepcopy(self.variables)
        return Lexer(Program, self, variables, debug = self.debug)

    def parse(self, string, filename = None):
        lexer = self._create_lexer()
        return lexer.parse(string, filename)

    def parse_file(self, filename):
        lexer = self._create_lexer()
        return lexer.parse_file(filename)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        filename = 'test.exscript'
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
    else:
        sys.exit(1)
    parser   = Parser(debug = 5)
    compiled = parser.parse_file(filename)
    compiled.dump()
