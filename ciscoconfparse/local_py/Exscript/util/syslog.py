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
Send messages to a syslog server.
"""
import os
import sys
import imp
import socket

# This way of loading a module prevents Python from looking in the
# current directory. (We need to avoid it due to the syslog module
# name collision.)
syslog = imp.load_module('syslog', *imp.find_module('syslog'))

def netlog(message,
           source   = None,
           host     = 'localhost',
           port     = 514,
           priority = syslog.LOG_DEBUG,
           facility = syslog.LOG_USER):
    """
    Python's built in syslog module does not support networking, so
    this is the alternative.
    The source argument specifies the message source that is
    documented on the receiving server. It defaults to "scriptname[pid]",
    where "scriptname" is sys.argv[0], and pid is the current process id.
    The priority and facility arguments are equivalent to those of
    Python's built in syslog module.

    @type  source: str
    @param source: The source address.
    @type  host: str
    @param host: The IP address or hostname of the receiving server.
    @type  port: str
    @param port: The TCP port number of the receiving server.
    @type  priority: int
    @param priority: The message priority.
    @type  facility: int
    @param facility: The message facility.
    """
    if not source:
        source = '%s[%s]' + (sys.argv[0], os.getpid())
    data = '<%d>%s: %s' % (priority + facility, source, message)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (host, port))
    sock.close()
