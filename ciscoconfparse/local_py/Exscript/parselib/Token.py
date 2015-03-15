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

class Token(object):
    """
    Abstract base class for all tokens.
    """

    class Iterator(object):
        """
        A tree iterator that walks through all tokens.
        """
        def __init__(self, current):
            """
            Constructor.
            """
            self.path = [current]

        def __iter__(self):
            return self

        def _next(self):
            # Make sure that the end is not yet reached.
            if len(self.path) == 0:
                raise StopIteration()

            # If the current token has children, the first child is the next item.
            current  = self.path[-1]
            children = current.get_children()
            if len(children) > 0:
                self.path.append(children[0])
                return current

            # Ending up here, this task has no children. Crop the path until we
            # reach a task that has unvisited children, or until we hit the end.
            while True:
                old_child = self.path.pop(-1)
                if len(self.path) == 0:
                    break

                # If this task has a sibling, choose it.
                parent   = self.path[-1]
                children = parent.get_children()
                pos      = children.index(old_child)
                if len(children) > pos + 1:
                    self.path.append(children[pos + 1])
                    break
            return current

        def next(self):
            # By using this loop we avoid an (expensive) recursive call.
            while True:
                next = self._next()
                if next is not None:
                    return next

    def __init__(self, name, lexer, parser, parent = None):
        self.lexer    = lexer
        self.parser   = parser
        self.parent   = parent
        self.name     = name
        self.children = []
        self.start    = lexer.current_char
        self.end      = lexer.current_char + 1

    def value(self, context):
        for child in self.get_children():
            child.value(context)

    def mark_start(self):
        self.start = self.lexer.current_char
        if self.start >= self.end:
            self.end = self.start + 1

    def mark_end(self, char = None):
        self.end = char and char or self.lexer.current_char

    def __iter__(self):
        """
        Returns an iterator that points to the first token.
        """
        return Token.Iterator(self)

    def add(self, child):
        self.children.append(child)

    def get_children(self):
        return self.children

    def dump(self, indent = 0):
        print (' ' * indent) + self.name
        for child in self.get_children():
            child.dump(indent + 1)
