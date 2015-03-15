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
from Exscript.parselib                 import Token
from Exscript.interpreter.Variable     import Variable
from Exscript.interpreter.Number       import Number
from Exscript.interpreter.FunctionCall import FunctionCall
from Exscript.interpreter.String       import String
from Exscript.interpreter.Regex        import Regex

class Term(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Term', lexer, parser, parent)
        self.term = None
        self.lft  = None
        self.rgt  = None
        self.op   = None

        # Expect a term.
        ttype, token = lexer.token()
        if lexer.current_is('varname'):
            if not parent.is_defined(token):
                lexer.error('Undeclared variable %s' % token, self, ValueError)
            self.term = Variable(lexer, parser, parent)
        elif lexer.current_is('open_function_call'):
            self.term = FunctionCall(lexer, parser, parent)
        elif lexer.current_is('string_delimiter'):
            self.term = String(lexer, parser, parent)
        elif lexer.next_if('number'):
            self.term = Number(token)
        elif lexer.next_if('keyword', 'false'):
            self.term = Number(0)
        elif lexer.next_if('keyword', 'true'):
            self.term = Number(1)
        elif lexer.next_if('octal_number'):
            self.term = Number(int(token[1:], 8))
        elif lexer.next_if('hex_number'):
            self.term = Number(int(token[2:], 16))
        elif lexer.current_is('regex_delimiter'):
            self.term = Regex(lexer, parser, parent)
        else:
            lexer.syntax_error('Expected term but got %s' % ttype, self)
        self.mark_end()

    def priority(self):
        return 6

    def value(self, context):
        return self.term.value(context)

    def dump(self, indent = 0):
        print (' ' * indent) + self.name
        self.term.dump(indent + 1)
