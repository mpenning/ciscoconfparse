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
import re
from Exscript.interpreter.String import String

# Matches any opening parenthesis that is neither preceeded by a backslash
# nor has a "?:" or "?<" appended.
bracket_re = re.compile(r'(?<!\\)\((?!\?[:<])', re.I)

modifier_grammar = (
    ('modifier',     r'[i]'),
    ('invalid_char', r'.'),
)

modifier_grammar_c = []
for thetype, regex in modifier_grammar:
    modifier_grammar_c.append((thetype, re.compile(regex, re.M|re.S)))

class Regex(String):
    def __init__(self, lexer, parser, parent):
        self.delimiter = lexer.token()[1]
        # String parser collects the regex.
        String.__init__(self, lexer, parser, parent)
        self.n_groups = len(bracket_re.findall(self.string))
        self.flags    = 0

        # Collect modifiers.
        lexer.set_grammar(modifier_grammar_c)
        while lexer.current_is('modifier'):
            if lexer.next_if('modifier', 'i'):
                self.flags = self.flags | re.I
            else:
                modifier = lexer.token()[1]
                error    = 'Invalid regular expression modifier "%s"' % modifier
                lexer.syntax_error(error, self)
        lexer.restore_grammar()

        # Compile the regular expression.
        try:
            re.compile(self.string, self.flags)
        except Exception, e:
            error = 'Invalid regular expression %s: %s' % (repr(self.string), e)
            lexer.syntax_error(error, self)

    def _escape(self, token):
        char = token[1]
        if char == self.delimiter:
            return char
        return token

    def value(self, context):
        pattern = String.value(self, context)[0]
        return re.compile(pattern, self.flags)


    def dump(self, indent = 0):
        print (' ' * indent) + self.name, self.string
