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
from Exscript.parselib          import Token
from Exscript.interpreter.Regex import Regex
from Exscript.interpreter.Term  import Term

class Extract(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Extract', lexer, parser, parent)
        self.varnames  = []
        self.variables = {}
        self.append    = False
        self.source    = None

        if parser.no_prompt: 
            msg = "'extract' keyword does not work with --no-prompt"
            lexer.syntax_error(msg, self)

        # First expect a regular expression.
        lexer.expect(self, 'keyword', 'extract')
        lexer.expect(self, 'whitespace')
        self.regex = Regex(lexer, parser, parent)

        # Expect "as" keyword.
        lexer.expect(self, 'whitespace')
        if lexer.next_if('keyword', 'as'):
            self.append = False
        elif lexer.next_if('keyword', 'into'):
            self.append = True
        else:
            _, token = lexer.token()
            msg      = 'Expected "as" or "into" but got %s' % token
            lexer.syntax_error(msg, self)

        # Expect a list of variable names.
        while 1:
            # Variable name.
            lexer.expect(self, 'whitespace')
            _, token = lexer.token()
            lexer.expect(self, 'varname')
            if token in self.variables:
                lexer.syntax_error('Duplicate variable name %s', self)
            self.varnames.append(token)
            self.variables[token] = []

            # Comma.
            if lexer.next_if('comma'):
                continue
            break
        self.parent.define(**self.variables)

        if len(self.varnames) != self.regex.n_groups:
            count = (len(self.varnames), self.regex.n_groups)
            error = '%s variables, but regex has %s groups' % count
            lexer.syntax_error(error, self)

        # Handle the "from" keyword.
        lexer.skip('whitespace')
        if lexer.next_if('keyword', 'from'):
            lexer.expect(self, 'whitespace')
            self.source = Term(lexer, parser, parent)
        self.mark_end()

    def extract(self, context):
        # Re-initialize the variable content, because this method
        # might be called multiple times.
        for varname in self.varnames:
            self.variables[varname] = []

        if self.source is None:
            buffer = self.parent.get('__response__')
        else:
            buffer = self.source.value(context)
        #print "Buffer contains", buffer

        # Walk through all lines, matching each one against the regular
        # expression.
        for line in buffer:
            match = self.regex.value(context).search(line)
            if match is None:
                continue

            # If there was a match, store the extracted substrings in our
            # list variables.
            i = 0
            for varname in self.varnames:
                i += 1
                try:
                    value = match.group(i)
                except IndexError:
                    # This happens if the user provided a regex with less 
                    # groups in it than the number of variables.
                    msg  = 'Extract: %s variables, but regular expression' % i
                    msg += '\ncontains only %s groups.' % (i - 1)
                    self.lexer.runtime_error(msg, self)
                self.variables[varname].append(value)

    def value(self, context):
        self.extract(context)
        if not self.append:
            self.parent.define(**self.variables)
        else:
            for key in self.variables:
                existing = self.parent.get(key)
                self.parent.define(**{key: existing + self.variables[key]})
        return 1


    def dump(self, indent = 0):
        mode = self.append and 'into' or 'as'
        source = self.source is not None and self.source or 'buffer'
        print (' ' * indent) + self.name, self.regex.string,
        print mode, self.varnames, "from", source
