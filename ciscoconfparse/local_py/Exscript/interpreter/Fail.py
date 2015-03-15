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
from Exscript.parselib               import Token
from Exscript.interpreter.Expression import Expression
from Exscript.interpreter.Exception  import FailException

class Fail(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Fail', lexer, parser, parent)
        self.expression = None

        # "fail" keyword.
        lexer.expect(self, 'keyword', 'fail')
        lexer.expect(self, 'whitespace')
        self.msg = Expression(lexer, parser, parent)

        # 'If' keyword with an expression.
        #token = lexer.token()
        if lexer.next_if('keyword', 'if'):
            lexer.expect(self, 'whitespace')
            self.expression = Expression(lexer, parser, parent)

        # End of expression.
        self.mark_end()
        lexer.skip(['whitespace', 'newline'])

    def value(self, context):
        if self.expression is None or self.expression.value(context)[0]:
            raise FailException(self.msg.value(context)[0])
        return 1

    def dump(self, indent = 0):
        print (' ' * indent) + self.name, 'start'
        self.msg.dump(indent + 1)
        self.expression.dump(indent + 1)
        print (' ' * indent) + self.name, 'end.'
