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
import Expression
from Exscript.parselib              import Token
from Exscript.interpreter.Exception import PermissionError

class FunctionCall(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'FunctionCall', lexer, parser, parent)
        self.funcname  = None
        self.arguments = []

        # Extract the function name.
        _, token = lexer.token()
        lexer.expect(self, 'open_function_call')
        self.funcname = token[:-1]
        function      = self.parent.get(self.funcname)
        if function is None:
            lexer.syntax_error('Undefined function %s' % self.funcname, self)

        # Parse the argument list.
        _, token = lexer.token()
        while 1:
            if lexer.next_if('close_bracket'):
                break
            self.arguments.append(Expression.Expression(lexer, parser, parent))
            ttype, token = lexer.token()
            if not lexer.next_if('comma') and not lexer.current_is('close_bracket'):
                error = 'Expected separator or argument list end but got %s'
                lexer.syntax_error(error % ttype, self)

        if parser.secure_only and not hasattr(function, '_is_secure'):
            msg = 'Use of insecure function %s is not permitted' % self.funcname
            lexer.error(msg, self, PermissionError)

        self.mark_end()

    def dump(self, indent = 0):
        print (' ' * indent) + self.name, self.funcname, 'start'
        for argument in self.arguments:
            argument.dump(indent + 1)
        print (' ' * indent) + self.name, self.funcname, 'end.'

    def value(self, context):
        argument_values = [arg.value(context) for arg in self.arguments]
        function        = self.parent.get(self.funcname)
        if function is None:
            self.lexer.runtime_error('Undefined function %s' % self.funcname, self)
        return function(self.parent, *argument_values)
