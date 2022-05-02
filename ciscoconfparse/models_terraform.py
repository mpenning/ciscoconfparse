""" models_terraform.py - Parse, Query, Build, and Modify terraform-style configurations

     Copyright (C) 2021-2022 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2015-2019 David Michael Pennington at Samsung Data Services

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [.dot.] net
"""
### HUGE UGLY WARNING:
###   Anything in models_terraform.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_terraform.py at your own risk.  You have been warned :-)

import re

from ciscoconfparse.ccp_abc import BaseCfgLine
from ciscoconfparse.ccp_util import IPv4Obj

#
# -------------  Terraform Configuration line object
#

class TfLine(BaseCfgLine):
    r"""An object for a parsed terraform-style configuration line.
    :class:`~models_terraform.TfLine` objects contain references to other
    parent and child :class:`~models_terraform.TfLine` objects.

    Notes
    -----
    Originally, :class:`~models_terraform.TfLine` objects were only
    intended for advanced ciscoconfparse users.  As of ciscoconfparse
    version 0.9.10, *all users* are strongly encouraged to prefer the
    methods directly on :class:`~models_terraform.TfLine` objects.
    Ultimately, if you write scripts which call methods on
    :class:`~models_terraform.TfLine` objects, your scripts will be much
    more efficient than if you stick strictly to the classic
    :class:`~ciscoconfparse.CiscoConfParse` methods.

    Parameters
    ----------
    text : str
        A string containing a text copy of the terraform configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.
     comment_delimiter : str
         A string which is considered a comment for the configuration format.  Since this is for Cisco terraform-style configurations, it defaults to ``!``.

    Attributes
    ----------
    text : str
        A string containing the parsed terraform configuration statement
    linenum : int
        The line number of this configuration statement in the original config; default is -1 when first initialized.
    parent : :class:`~models_terraform.TfLine()`
        The parent of this object; defaults to ``self``.
    children : list
        A list of ``TfLine()`` objects which are children of this object.
    child_indent : int
        An integer with the indentation of this object's children
    indent : int
        An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
    is_comment : bool
        A boolean indicating whether this is a comment

    Returns
    -------
    :class:`~models_terraform.TfLine`

    """

    def __init__(self, *args, **kwargs):
        """
        Accept a terraform line number and initialize family relationship
        attributes"""
        super().__init__(*args, **kwargs)
        raise NotImplementedError()

    def __repr__(self):
        return """<TfLine {}>""".format(self.line_type, )

    @classmethod
    def is_object_for(cls, line="", re=re):
        ## Default object, for now
        return True

    @property
    def line_type(self):
        """
        Return whether this is a resource, provider or variable line
        """
        retval = self.geneology[0].text.split()[0]
        # FIXME - handle terraform tfvar lines in the future...
        assert retval in set({"resource", "provider", "variable"})
        return retval

    @property
    def resource_type(self):
        return self.geneology[0].text.split()[1]

    @property
    def resource_id(self):
        return self.geneology[0].text.split()[2]

    @property
    def is_resource(self):
        if parent.linenum == self.linenum and "resource" in geneology[0].text:
            return True
        return False
