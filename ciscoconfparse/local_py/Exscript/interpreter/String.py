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
from Exscript.parselib import Token

varname_re = re.compile(r'((?:__)?[a-zA-Z][\w_]*(?:__)?)')
string_re  = re.compile(r'(\\?)\$([\w_]*)')

grammar = [
    ('escaped_data', r'\\.'),
]

grammar_c = []
for thetype, regex in grammar:
    grammar_c.append((thetype, re.compile(regex)))

class String(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, self.__class__.__name__, lexer, parser, parent)

        # Create a grammar depending on the delimiting character.
        tok_type, delimiter = lexer.token()
        escaped_delimiter   = '\\' + delimiter
        data                = r'[^\r\n\\' + escaped_delimiter + ']+'
        delimiter_re        = re.compile(escaped_delimiter)
        data_re             = re.compile(data)
        grammar_with_delim  = grammar_c[:]
        grammar_with_delim.append(('string_data',      data_re))
        grammar_with_delim.append(('string_delimiter', delimiter_re))
        lexer.set_grammar(grammar_with_delim)

        # Begin parsing the string.
        lexer.expect(self, 'string_delimiter')
        self.string = ''
        while 1:
            if lexer.current_is('string_data'):
                self.string += lexer.token()[1]
                lexer.next()
            elif lexer.current_is('escaped_data'):
                self.string += self._escape(lexer.token()[1])
                lexer.next()
            elif lexer.next_if('string_delimiter'):
                break
            else:
                ttype = lexer.token()[0]
                lexer.syntax_error('Expected string but got %s' % ttype, self)

        # Make sure that any variables specified in the command are declared.
        string_re.sub(self.variable_test_cb, self.string)
        self.mark_end()
        lexer.restore_grammar()

    def _escape(self, token):
        char = token[1]
        if char == 'n':
            return '\n'
        elif char == 'r':
            return '\r'
        elif char == '$': # Escaping is done later, in variable_sub_cb.
            return token
        return char

    def _variable_error(self, field, msg):
        self.start += self.string.find(field)
        self.end    = self.start + len(field)
        self.lexer.runtime_error(msg, self)

    # Tokens that include variables in a string may use this callback to
    # substitute the variable against its value.
    def variable_sub_cb(self, match):
        field   = match.group(0)
        escape  = match.group(1)
        varname = match.group(2)
        value   = self.parent.get(varname)

        # Check the variable name syntax.
        if escape:
            return '$' + varname
        elif varname == '':
            return '$'
        if not varname_re.match(varname):
            msg = '%s is not a variable name' % repr(varname)
            self._variable_error(field, msg)

        # Check the variable value.
        if value is None:
            msg = 'Undefined variable %s' % repr(varname)
            self._variable_error(field, msg)
        elif hasattr(value, 'func_name'):
            msg = '%s is a function, not a variable name' % repr(varname)
            self._variable_error(field, msg)
        elif isinstance(value, list):
            if len(value) > 0:
                value = '\n'.join([str(v) for v in value])
            else:
                value = ''
        return str(value)

    # Tokens that include variables in a string may use this callback to
    # make sure that the variable is already declared.
    def variable_test_cb(self, match):
        self.variable_sub_cb(match)
        return match.group(0)

    def value(self, context):
        return [string_re.sub(self.variable_sub_cb, self.string)]

    def dump(self, indent = 0):
        print (' ' * indent) + 'String "' + self.string + '"'
