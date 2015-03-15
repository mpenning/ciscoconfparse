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
from copy              import deepcopy
from Exscript.parselib import Token

class Scope(Token):
    def __init__(self, name, lexer, parser, parent = None, *args, **kwargs):
        Token.__init__(self, name, lexer, parser, parent)
        self.variables      = kwargs.get('variables', {})
        self.children       = []
        self.exit_requested = 0
        for key in self.variables:
            if key.find('.') < 0 and not key.startswith('_'):
                assert type(self.variables[key]) == type([])

    def exit_request(self):
        self.exit_requested = 1

    def define(self, **kwargs):
        if self.parent is not None:
            return self.parent.define(**kwargs)
        for key in kwargs:
            if key.find('.') >= 0 or key.startswith('_') \
              or type(kwargs[key]) == type([]):
                self.variables[key] = kwargs[key]
            else:
                self.variables[key] = [kwargs[key]]

    def define_object(self, **kwargs):
        self.variables.update(kwargs)

    def is_defined(self, name):
        if name in self.variables:
            return 1
        if self.parent is not None:
            return self.parent.is_defined(name)
        return 0

    def get_vars(self):
        """
        Returns a complete dict of all variables that are defined in this 
        scope, including the variables of the parent.
        """
        if self.parent is None:
            vars = {}
            vars.update(self.variables)
            return vars
        vars = self.parent.get_vars()
        vars.update(self.variables)
        return vars

    def copy_public_vars(self):
        """
        Like get_vars(), but does not include any private variables and
        deep copies each variable.
        """
        vars = self.get_vars()
        vars = dict([k for k in vars.iteritems() if not k[0].startswith('_')])
        return deepcopy(vars)

    def get(self, name, default = None):
        if name in self.variables:
            return self.variables[name]
        if self.parent is None:
            return default
        return self.parent.get(name, default)

    def value(self, context):
        result = 1
        for child in self.children:
            result = child.value(context)
        return result

    def dump(self, indent = 0):
        print (' ' * indent) + self.name, 'start'
        for child in self.children:
            child.dump(indent + 1)
        print (' ' * indent) + self.name, 'end'

    def dump1(self):
        if self.parent is not None:
            self.parent.dump1()
            return
        print "Scope:", self.variables
