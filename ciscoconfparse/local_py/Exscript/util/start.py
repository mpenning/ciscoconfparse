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
Quickstart methods for the Exscript queue.
"""
from Exscript import Queue
from Exscript.util.interact import read_login
from Exscript.util.decorator import autologin

def run(users, hosts, func, **kwargs):
    """
    Convenience function that creates an Exscript.Queue instance, adds
    the given accounts, and calls Queue.run() with the given
    hosts and function as an argument.

    If you also want to pass arguments to the given function, you may use
    util.decorator.bind() like this::

      def my_callback(job, host, conn, my_arg, **kwargs):
          print my_arg, kwargs.get('foo')

      run(account,
          host,
          bind(my_callback, 'hello', foo = 'world'),
          max_threads = 10)

    @type  users: Account|list[Account]
    @param users: The account(s) to use for logging in.
    @type  hosts: Host|list[Host]
    @param hosts: A list of Host objects.
    @type  func: function
    @param func: The callback function.
    @type  kwargs: dict
    @param kwargs: Passed to the Exscript.Queue constructor.
    """
    queue = Queue(**kwargs)
    queue.add_account(users)
    queue.run(hosts, func)
    queue.destroy()

def quickrun(hosts, func, **kwargs):
    """
    A wrapper around run() that creates the account by asking the user
    for entering his login information.

    @type  hosts: Host|list[Host]
    @param hosts: A list of Host objects.
    @type  func: function
    @param func: The callback function.
    @type  kwargs: dict
    @param kwargs: Passed to the Exscript.Queue constructor.
    """
    run(read_login(), hosts, func, **kwargs)

def start(users, hosts, func, **kwargs):
    """
    Like run(), but automatically logs into the host before passing
    the host to the callback function.

    @type  users: Account|list[Account]
    @param users: The account(s) to use for logging in.
    @type  hosts: Host|list[Host]
    @param hosts: A list of Host objects.
    @type  func: function
    @param func: The callback function.
    @type  kwargs: dict
    @param kwargs: Passed to the Exscript.Queue constructor.
    """
    run(users, hosts, autologin()(func), **kwargs)

def quickstart(hosts, func, **kwargs):
    """
    Like quickrun(), but automatically logs into the host before passing
    the connection to the callback function.

    @type  hosts: Host|list[Host]
    @param hosts: A list of Host objects.
    @type  func: function
    @param func: The callback function.
    @type  kwargs: dict
    @param kwargs: Passed to the Exscript.Queue constructor.
    """
    quickrun(hosts, autologin()(func), **kwargs)
