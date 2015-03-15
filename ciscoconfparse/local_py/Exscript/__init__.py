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
"""
The core module.
"""
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category = DeprecationWarning)
    import paramiko
from Exscript.version     import __version__
from Exscript.Account     import Account
from Exscript.AccountPool import AccountPool
from Exscript.PrivateKey  import PrivateKey
from Exscript.Queue       import Queue
from Exscript.Host        import Host
from Exscript.Logger      import Logger
from Exscript.FileLogger  import FileLogger

import inspect 
__all__ = [name for name, obj in locals().items()
           if not (name.startswith('_') or inspect.ismodule(obj))]
