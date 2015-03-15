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
from Exscript import Account
from Exscript.util.cast import to_host
from Exscript.util.url import Url
from Exscript.protocols.Protocol import Protocol
from Exscript.protocols.Telnet import Telnet
from Exscript.protocols.SSH2 import SSH2
from Exscript.protocols.Dummy import Dummy

protocol_map = {'dummy':  Dummy,
                'pseudo': Dummy,
                'telnet': Telnet,
                'ssh':    SSH2,
                'ssh2':   SSH2}

def get_protocol_from_name(name):
    """
    Returns the protocol class for the protocol with the given name.

    @type  name: str
    @param name: The name of the protocol.
    @rtype:  Protocol
    @return: The protocol class.
    """
    cls = protocol_map.get(name)
    if not cls:
        raise ValueError('Unsupported protocol "%s".' % name)
    return cls

def create_protocol(name, **kwargs):
    """
    Returns an instance of the protocol with the given name.

    @type  name: str
    @param name: The name of the protocol.
    @rtype:  Protocol
    @return: An instance of the protocol.
    """
    cls = protocol_map.get(name)
    if not cls:
        raise ValueError('Unsupported protocol "%s".' % name)
    return cls(**kwargs)

def prepare(host, default_protocol = 'telnet', **kwargs):
    """
    Creates an instance of the protocol by either parsing the given
    URL-formatted hostname using L{Exscript.util.url}, or according to
    the options of the given L{Exscript.Host}.

    @type  host: str or Host
    @param host: A URL-formatted hostname or a L{Exscript.Host} instance.
    @type  default_protocol: str
    @param default_protocol: Protocol that is used if the URL specifies none.
    @type  kwargs: dict
    @param kwargs: Passed to the protocol constructor.
    @rtype:  Protocol
    @return: An instance of the protocol.
    """
    host     = to_host(host, default_protocol = default_protocol)
    protocol = host.get_protocol()
    conn     = create_protocol(protocol, **kwargs)
    if protocol == 'pseudo':
        filename = host.get_address()
        conn.device.add_commands_from_file(filename)
    return conn

def connect(host, default_protocol = 'telnet', **kwargs):
    """
    Like L{prepare()}, but also connects to the host by calling
    L{Protocol.connect()}. If the URL or host contain any login info, this
    function also logs into the host using L{Protocol.login()}.

    @type  host: str or Host
    @param host: A URL-formatted hostname or a L{Exscript.Host} object.
    @type  default_protocol: str
    @param default_protocol: Protocol that is used if the URL specifies none.
    @type  kwargs: dict
    @param kwargs: Passed to the protocol constructor.
    @rtype:  Protocol
    @return: An instance of the protocol.
    """
    host    = to_host(host)
    conn    = prepare(host, default_protocol, **kwargs)
    account = host.get_account()
    conn.connect(host.get_address(), host.get_tcp_port())
    if account is not None:
        conn.login(account)
    return conn

import inspect 
__all__ = [name for name, obj in locals().items()
           if not (name.startswith('_') or inspect.ismodule(obj))]
