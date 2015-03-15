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
import Term
from Exscript.parselib import Token

class ExpressionNode(Token):
    def __init__(self, lexer, parser, parent, parent_node = None):
        # Skip whitespace before initializing the token to make sure that self.start
        # points to the beginning of the expression (which makes for prettier error
        # messages).
        lexer.skip(['whitespace', 'newline'])

        Token.__init__(self, 'ExpressionNode', lexer, parser, parent)
        self.lft         = None
        self.rgt         = None
        self.op          = None
        self.op_type     = None
        self.parent_node = parent_node

        # The "not" operator requires special treatment because it is
        # positioned left of the term.
        if not lexer.current_is('logical_operator', 'not'):
            self.lft = Term.Term(lexer, parser, parent)

            # The expression may end already (a single term is also an
            # expression).
            lexer.skip(['whitespace', 'newline'])
            if not lexer.current_is('arithmetic_operator') and \
               not lexer.current_is('logical_operator') and \
               not lexer.current_is('comparison') and \
               not lexer.current_is('regex_delimiter'):
                self.mark_end()
                return

        # Expect the operator.
        self.op_type, self.op = lexer.token()
        if not lexer.next_if('arithmetic_operator') and \
           not lexer.next_if('logical_operator') and \
           not lexer.next_if('comparison') and \
           not lexer.next_if('regex_delimiter'):
            self.mark_end()
            msg = 'Expected operator but got %s' % self.op_type
            lexer.syntax_error(msg, self)

        # Expect the second term.
        self.rgt = ExpressionNode(lexer, parser, parent, self)
        self.mark_end()


    def priority(self):
        if self.op is None:
            return 8
        elif self.op_type == 'arithmetic_operator' and self.op == '%':
            return 7
        elif self.op_type == 'arithmetic_operator' and self.op == '*':
            return 6
        elif self.op_type == 'regex_delimiter':
            return 6
        elif self.op_type == 'arithmetic_operator' and self.op != '.':
            return 5
        elif self.op == '.':
            return 4
        elif self.op_type == 'comparison':
            return 3
        elif self.op == 'not':
            return 2
        elif self.op_type == 'logical_operator':
            return 1
        else:
            raise Exception('Invalid operator.')


    def value(self, context):
        # Special behavior where we only have one term.
        if self.op is None:
            return self.lft.value(context)
        elif self.op == 'not':
            return [not self.rgt.value(context)[0]]

        # There are only two types of values: Regular expressions and lists.
        # We also have to make sure that empty lists do not cause an error.
        lft_lst = self.lft.value(context)
        if type(lft_lst) == type([]):
            if len(lft_lst) > 0:
                lft = lft_lst[0]
            else:
                lft = ''
        rgt_lst = self.rgt.value(context)
        if type(rgt_lst) == type([]):
            if len(rgt_lst) > 0:
                rgt = rgt_lst[0]
            else:
                rgt = ''

        if self.op_type == 'arithmetic_operator' and self.op != '.':
            error = 'Operand for %s is not a number' % (self.op)
            try:
                lft = int(lft)
            except ValueError:
                self.lexer.runtime_error(error, self.lft)
            try:
                rgt = int(rgt)
            except ValueError:
                self.lexer.runtime_error(error, self.rgt)

        # Two-term expressions.
        if self.op == 'is':
            return [lft == rgt]
        elif self.op == 'matches':
            regex = rgt_lst
            # The "matches" keyword requires a regular expression as the right hand
            # operand. The exception throws if "regex" does not have a match() method.
            try:
                regex.match(str(lft))
            except AttributeError:
                error = 'Right hand operator is not a regular expression'
                self.lexer.runtime_error(error, self.rgt)
            for line in lft_lst:
                if regex.search(str(line)):
                    return [1]
            return [0]
        elif self.op == 'is not':
            #print "LFT: '%s', RGT: '%s', RES: %s" % (lft, rgt, [lft != rgt])
            return [lft != rgt]
        elif self.op == 'in':
            return [lft in rgt_lst]
        elif self.op == 'not in':
            return [lft not in rgt_lst]
        elif self.op == 'ge':
            return [int(lft) >= int(rgt)]
        elif self.op == 'gt':
            return [int(lft) > int(rgt)]
        elif self.op == 'le':
            return [int(lft) <= int(rgt)]
        elif self.op == 'lt':
            return [int(lft) < int(rgt)]
        elif self.op == 'and':
            return [lft and rgt]
        elif self.op == 'or':
            return [lft or rgt]
        elif self.op == '*':
            return [int(lft) * int(rgt)]
        elif self.op == '/':
            return [int(lft) / int(rgt)]
        elif self.op == '%':
            return [int(lft) % int(rgt)]
        elif self.op == '.':
            return [str(lft) + str(rgt)]
        elif self.op == '+':
            return [int(lft) + int(rgt)]
        elif self.op == '-':
            return [int(lft) - int(rgt)]


    def dump(self, indent = 0):
        print (' ' * indent) + self.name, self.op, 'start'
        if self.lft is not None:
            self.lft.dump(indent + 1)
        print (' ' * (indent + 1)) + 'Operator', self.op
        if self.rgt is not None:
            self.rgt.dump(indent + 1)
        print (' ' * indent) + self.name, self.op, 'end.'
