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
from Exscript.parselib            import Token
from Exscript.interpreter.Execute import Execute

class Enter(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Enter', lexer, parser, parent)

        lexer.expect(self, 'keyword', 'enter')
        lexer.skip(['whitespace', 'newline'])

        self.execute = Execute(lexer, parser, parent, '')

    def value(self, context):
        return self.execute.value(context)

    def dump(self, indent = 0):
        print (' ' * indent) + self.name
        self.execute.dump(indent + 1)
