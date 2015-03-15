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
Utilities for reading data from files.
"""
import re
import os
import base64
import codecs
import imp
from Exscript import Account
from Exscript.util.cast import to_host

def get_accounts_from_file(filename):
    """
    Reads a list of user/password combinations from the given file
    and returns a list of Account instances. The file content
    has the following format::

        [account-pool]
        user1 = cGFzc3dvcmQ=
        user2 = cGFzc3dvcmQ=

    Note that "cGFzc3dvcmQ=" is a base64 encoded password.
    If the input file contains extra config sections other than
    "account-pool", they are ignored.
    Each password needs to be base64 encrypted. To encrypt a password,
    you may use the following command::

        python -c 'import base64; print base64.b64encode("thepassword")'

    @type  filename: string
    @param filename: The name of the file containing the list of accounts.
    @rtype:  list[Account]
    @return: The newly created account instances.
    """
    accounts           = []
    cfgparser          = __import__('ConfigParser', {}, {}, [''])
    parser             = cfgparser.RawConfigParser()
    parser.optionxform = str
    parser.read(filename)
    for user, password in parser.items('account-pool'):
        accounts.append(Account(user, base64.decodestring(password)))
    return accounts


def get_hosts_from_file(filename,
                        default_protocol  = 'telnet',
                        default_domain    = '',
                        remove_duplicates = False,
                        encoding          = 'utf-8'):
    """
    Reads a list of hostnames from the file with the given name.

    @type  filename: string
    @param filename: A full filename.
    @type  default_protocol: str
    @param default_protocol: Passed to the Host constructor.
    @type  default_domain: str
    @param default_domain: Appended to each hostname that has no domain.
    @type  remove_duplicates: bool
    @param remove_duplicates: Whether duplicates are removed.
    @type  encoding: str
    @param encoding: The encoding of the file.
    @rtype:  list[Host]
    @return: The newly created host instances.
    """
    # Open the file.
    if not os.path.exists(filename):
        raise IOError('No such file: %s' % filename)

    # Read the hostnames.
    have  = set()
    hosts = []
    with codecs.open(filename, 'r', encoding) as file_handle:
        for line in file_handle:
            hostname = line.split('#')[0].strip()
            if hostname == '':
                continue
            if remove_duplicates and hostname in have:
                continue
            have.add(hostname)
            hosts.append(to_host(hostname, default_protocol, default_domain))

    return hosts


def get_hosts_from_csv(filename,
                       default_protocol = 'telnet',
                       default_domain   = '',
                       encoding         = 'utf-8'):
    """
    Reads a list of hostnames and variables from the tab-separated .csv file
    with the given name. The first line of the file must contain the column
    names, e.g.::

        address	testvar1	testvar2
        10.0.0.1	value1	othervalue
        10.0.0.1	value2	othervalue2
        10.0.0.2	foo	bar

    For the above example, the function returns *two* host objects, where
    the 'testvar1' variable of the first host holds a list containing two
    entries ('value1' and 'value2'), and the 'testvar1' variable of the
    second host contains a list with a single entry ('foo').

    Both, the address and the hostname of each host are set to the address
    given in the first column. If you want the hostname set to another value,
    you may add a second column containing the hostname::

        address	hostname	testvar
        10.0.0.1	myhost	value
        10.0.0.2	otherhost	othervalue

    @type  filename: string
    @param filename: A full filename.
    @type  default_protocol: str
    @param default_protocol: Passed to the Host constructor.
    @type  default_domain: str
    @param default_domain: Appended to each hostname that has no domain.
    @type  encoding: str
    @param encoding: The encoding of the file.
    @rtype:  list[Host]
    @return: The newly created host instances.
    """
    # Open the file.
    if not os.path.exists(filename):
        raise IOError('No such file: %s' % filename)

    with codecs.open(filename, 'r', encoding) as file_handle:
        # Read and check the header.
        header = file_handle.readline().rstrip()
        if re.search(r'^(?:hostname|address)\b', header) is None:
            msg  = 'Syntax error in CSV file header:'
            msg += ' File does not start with "hostname" or "address".'
            raise Exception(msg)
        if re.search(r'^(?:hostname|address)(?:\t[^\t]+)*$', header) is None:
            msg  = 'Syntax error in CSV file header:'
            msg += ' Make sure to separate columns by tabs.'
            raise Exception(msg)
        varnames = [str(v) for v in header.split('\t')]
        varnames.pop(0)

        # Walk through all lines and create a map that maps hostname to
        # definitions.
        last_uri = ''
        line_re  = re.compile(r'[\r\n]*$')
        hosts    = []
        for line in file_handle:
            if line.strip() == '':
                continue

            line   = line_re.sub('', line)
            values = line.split('\t')
            uri    = values.pop(0).strip()

            # Add the hostname to our list.
            if uri != last_uri:
                #print "Reading hostname", hostname_url, "from csv."
                host     = to_host(uri, default_protocol, default_domain)
                last_uri = uri
                hosts.append(host)

            # Define variables according to the definition.
            for i, varname in enumerate(varnames):
                try:
                    value = values[i]
                except IndexError:
                    value = ''
                if varname == 'hostname':
                    host.set_name(value)
                else:
                    host.append(varname, value)

    return hosts


def load_lib(filename):
    """
    Loads a Python file containing functions, and returns the
    content of the __lib__ variable. The __lib__ variable must contain
    a dictionary mapping function names to callables.

    Returns a dictionary mapping the namespaced function names to
    callables. The namespace is the basename of the file, without file
    extension.

    The result of this function can later be passed to run_template::

        functions = load_lib('my_library.py')
        run_template(conn, 'foo.exscript', **functions)

    @type  filename: string
    @param filename: A full filename.
    @rtype:  dict[string->object]
    @return: The loaded functions.
    """
    # Open the file.
    if not os.path.exists(filename):
        raise IOError('No such file: %s' % filename)

    name = os.path.splitext(os.path.basename(filename))[0]
    module = imp.load_source(name, filename)

    return dict((name + '.' + k, v) for (k, v) in module.__lib__.iteritems())
