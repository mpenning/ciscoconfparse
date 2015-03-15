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
Representing a device to connect with.
"""
from Exscript.Account   import Account
from Exscript.util.cast import to_list
from Exscript.util.ipv4 import is_ip, clean_ip
from Exscript.util.url  import Url

def _is_ip(string):
    # Adds IPv6 support.
    return ':' in string or is_ip(string)

class Host(object):
    """
    Represents a device on which to open a connection.
    """
    __slots__ = ('protocol',
                 'vars',
                 'account',
                 'name',
                 'address',
                 'tcp_port',
                 'options')

    def __init__(self, uri, default_protocol = 'telnet'):
        """
        Constructor. The given uri is passed to Host.set_uri().
        The default_protocol argument defines the protocol that is used
        in case the given uri does not specify it.

        @type  uri: string
        @param uri: A hostname; see set_uri() for more info.
        @type  default_protocol: string
        @param default_protocol: The protocol name.
        """
        self.protocol = default_protocol
        self.vars     = None    # To save memory, do not init with a dict.
        self.account  = None
        self.name     = None
        self.address  = None
        self.tcp_port = None
        self.options  = None
        self.set_uri(uri) 

    def __copy__(self):
        host = Host(self.get_uri())
        host.set_name(self.get_name())
        return host

    def set_uri(self, uri):
        """
        Defines the protocol, hostname/address, TCP port number, username,
        and password from the given URL. The hostname may be URL formatted,
        so the following formats are all valid:

            - myhostname
            - myhostname.domain
            - ssh:hostname
            - ssh:hostname.domain
            - ssh://hostname
            - ssh://user@hostname
            - ssh://user:password@hostname
            - ssh://user:password@hostname:21

        For a list of supported protocols please see set_protocol().

        @type  uri: string
        @param uri: An URL formatted hostname.
        """
        try:
            uri = Url.from_string(uri, self.protocol)
        except ValueError:
            raise ValueError('Hostname parse error: ' + repr(uri))
        hostname = uri.hostname or ''
        name     = uri.path and hostname + uri.path or hostname
        self.set_protocol(uri.protocol)
        self.set_tcp_port(uri.port)
        self.set_name(name)
        self.set_address(name)

        if uri.username is not None \
           or uri.password1 is not None \
           or uri.password2:
            account = Account(uri.username, uri.password1, uri.password2)
            self.set_account(account)

        for key, val in uri.vars.iteritems():
            self.set(key, val)

    def get_uri(self):
        """
        Returns a URI formatted representation of the host, including all
        of it's attributes except for the name. Uses the
        address, not the name of the host to build the URI.

        @rtype:  str
        @return: A URI.
        """
        url = Url()
        url.protocol = self.get_protocol()
        url.hostname = self.get_address()
        url.port     = self.get_tcp_port()
        url.vars     = dict((k, to_list(v))
                            for (k, v) in self.get_all().iteritems()
                            if isinstance(v, str) or isinstance(v, list))

        if self.account:
            url.username  = self.account.get_name()
            url.password1 = self.account.get_password()
            url.password2 = self.account.authorization_password

        return str(url)

    def get_dict(self):
        """
        Returns a dict containing the host's attributes. The following
        keys are contained:

            - hostname
            - address
            - protocol
            - port

        @rtype:  dict
        @return: The resulting dictionary.
        """
        return {'hostname': self.get_name(),
                'address':  self.get_address(),
                'protocol': self.get_protocol(),
                'port':     self.get_tcp_port()}

    def set_name(self, name):
        """
        Set the hostname of the remote host without
        changing username, password, protocol, and TCP port number.

        @type  name: string
        @param name: A hostname or IP address.
        """
        self.name = name

    def get_name(self):
        """
        Returns the name.

        @rtype:  string
        @return: The hostname excluding the name.
        """
        return self.name

    def set_address(self, address):
        """
        Set the address of the remote host the is contacted, without
        changing hostname, username, password, protocol, and TCP port
        number.
        This is the actual address that is used to open the connection.

        @type  address: string
        @param address: A hostname or IP name.
        """
        if is_ip(address):
            self.address = clean_ip(address)
        else:
            self.address = address

    def get_address(self):
        """
        Returns the address that is used to open the connection.

        @rtype:  string
        @return: The address that is used to open the connection.
        """
        return self.address

    def set_protocol(self, protocol):
        """
        Defines the protocol. The following protocols are currently
        supported:

            - telnet: Telnet
            - ssh1: SSH version 1
            - ssh2: SSH version 2
            - ssh: Automatically selects the best supported SSH version
            - dummy: A virtual device that accepts any command, but that
              does not respond anything useful.
            - pseudo: A virtual device that loads a file with the given
              "hostname". The given file is a Python file containing
              information on how the virtual device shall respond to
              commands. For more information please refer to the
              documentation of
              protocols.Dummy.load_command_handler_from_file().

        @type  protocol: string
        @param protocol: The protocol name.
        """
        self.protocol = protocol

    def get_protocol(self):
        """
        Returns the name of the protocol.

        @rtype:  string
        @return: The protocol name.
        """
        return self.protocol

    def set_option(self, name, value):
        """
        Defines a (possibly protocol-specific) option for the host.
        Possible options include:

            verify_fingerprint: bool

        @type  name: str
        @param name: The option name.
        @type  value: object
        @param value: The option value.
        """
        if name not in ('debug', 'verify_fingerprint', 'driver'):
            raise TypeError('No such option: ' + repr(name))
        if self.options is None:
            self.options = {}
        self.options[name] = value

    def get_option(self, name, default = None):
        """
        Returns the value of the given option if it is defined, returns
        the given default value otherwise.

        @type  name: str
        @param name: The option name.
        @type  default: object
        @param default: A default value.
        """
        if self.options is None:
            return default
        return self.options.get(name, default)

    def get_options(self):
        """
        Return a dictionary containing all defined options.

        @rtype:  dict
        @return: The options.
        """
        if self.options is None:
            return {}
        return self.options

    def set_tcp_port(self, tcp_port):
        """
        Defines the TCP port number.

        @type  tcp_port: int
        @param tcp_port: The TCP port number.
        """
        if tcp_port is None:
            self.tcp_port = None
            return
        self.tcp_port = int(tcp_port)

    def get_tcp_port(self):
        """
        Returns the TCP port number.

        @rtype:  string
        @return: The TCP port number.
        """
        return self.tcp_port

    def set_account(self, account):
        """
        Defines the account that is used to log in.

        @type  account: L{Exscript.Account}
        @param account: The account.
        """
        self.account = account

    def get_account(self):
        """
        Returns the account that is used to log in.

        @rtype:  Account
        @return: The account.
        """
        return self.account

    def set(self, name, value):
        """
        Stores the given variable/value in the object for later retrieval.

        @type  name: string
        @param name: The name of the variable.
        @type  value: object
        @param value: The value of the variable.
        """
        if self.vars is None:
            self.vars = {}
        self.vars[name] = value

    def set_all(self, variables):
        """
        Like set(), but replaces all variables by using the given
        dictionary. In other words, passing an empty dictionary
        results in all variables being removed.

        @type  variables: dict
        @param variables: The dictionary with the variables.
        """
        self.vars = dict(variables)

    def append(self, name, value):
        """
        Appends the given value to the list variable with the given name.

        @type  name: string
        @param name: The name of the variable.
        @type  value: object
        @param value: The appended value.
        """
        if self.vars is None:
            self.vars = {}
        if name in self.vars:
            self.vars[name].append(value)
        else:
            self.vars[name] = [value]

    def set_default(self, name, value):
        """
        Like set(), but only sets the value if the variable is not already
        defined.

        @type  name: string
        @param name: The name of the variable.
        @type  value: object
        @param value: The value of the variable.
        """
        if self.vars is None:
            self.vars = {}
        if name not in self.vars:
            self.vars[name] = value

    def has_key(self, name):
        """
        Returns True if the variable with the given name is defined, False
        otherwise.

        @type  name: string
        @param name: The name of the variable.
        @rtype:  bool
        @return: Whether the variable is defined.
        """
        if self.vars is None:
            return False
        return name in self.vars

    def get(self, name, default = None):
        """
        Returns the value of the given variable, or the given default
        value if the variable is not defined.

        @type  name: string
        @param name: The name of the variable.
        @type  default: object
        @param default: The default value.
        @rtype:  object
        @return: The value of the variable.
        """
        if self.vars is None:
            return default
        return self.vars.get(name, default)

    def get_all(self):
        """
        Returns a dictionary containing all variables.

        @rtype:  dict
        @return: The dictionary with the variables.
        """
        if self.vars is None:
            self.vars = {}
        return self.vars
