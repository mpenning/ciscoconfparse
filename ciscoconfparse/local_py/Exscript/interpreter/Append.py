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
from Exscript.parselib         import Token
from Exscript.interpreter.Term import Term

class Append(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Append', lexer, parser, parent)

        # First expect an expression.
        lexer.expect(self, 'keyword', 'append')
        lexer.expect(self, 'whitespace')
        self.expr = Term(lexer, parser, parent)

        # Expect "to" keyword.
        lexer.expect(self, 'whitespace')
        lexer.expect(self, 'keyword', 'to')

        # Expect a variable name.
        lexer.expect(self, 'whitespace')
        _, self.varname = lexer.token()
        lexer.expect(self, 'varname')
        self.parent.define(**{self.varname: []})

        self.mark_end()

    def value(self, context):
        existing = self.parent.get(self.varname)
        args     = {self.varname: existing + self.expr.value(context)}
        self.parent.define(**args)
        return 1

    def dump(self, indent = 0):
        print (' ' * indent) + self.name, "to", self.varname
        self.expr.dump(indent + 1)
