from __future__ import absolute_import

""" __main__.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2014-2019 David Michael Pennington

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
     mike [~at~] pennington [/dot\] net
"""
# Follow PEP366...
# https://stackoverflow.com/a/6655098/667301
if (__name__ == "__main__") and (__package__ is None):
    import sys
    import os

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(1, parent_dir)
    import ciscoconfparse

    __package__ = str("ciscoconfparse")
    del sys, os
