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
from Exscript.parselib                   import Token
from Exscript.interpreter.ExpressionNode import ExpressionNode

class Expression(Token):
    def __init__(self, lexer, parser, parent):
        Token.__init__(self, 'Expression', lexer, parser, parent)

        # Parse the expression.
        self.root = ExpressionNode(lexer, parser, parent)

        # Reorder the tree according to the operator priorities.
        self.prioritize(self.root)
        self.mark_end()


    def prioritize(self, start, prio = 1):
        #print "Prioritizing from", start.op, "with prio", prio, (start.lft, start.rgt)
        if prio == 6:
            return
        root = start
        while root is not None and root.priority() <= prio:
            root = root.rgt
        if root is None:
            self.prioritize(start, prio + 1)
            return

        # Find the next node that has the current priority.
        previous = root
        current  = root.rgt
        while current is not None and current.priority() != prio:
            previous = current
            current  = current.rgt
        if current is None:
            self.prioritize(start, prio + 1)
            return

        # Reparent the expressions.
        #print "Prio of", root.op, 'is higher than', current.op
        previous.rgt = current.lft
        current.lft  = root

        # Change the pointer of the parent of the root node.
        # If this was the root of the entire tree we need to change that as
        # well.
        if root.parent_node is None:
            self.root = current
        elif root.parent_node.lft == root:
            root.parent_node.lft = current
        elif root.parent_node.rgt == root:
            root.parent_node.rgt = current

        root.parent_node = current

        # Go ahead prioritizing the children.
        self.prioritize(current.lft, prio + 1)
        self.prioritize(current.rgt, prio)

    def value(self, context):
        return self.root.value(context)

    def dump(self, indent = 0):
        print (' ' * indent) + self.name, 'start'
        self.root.dump(indent + 1)
        print (' ' * indent) + self.name, 'end.'
