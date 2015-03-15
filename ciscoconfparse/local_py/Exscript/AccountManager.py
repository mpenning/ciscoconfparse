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
Manages user accounts.
"""
from Exscript.AccountPool import AccountPool

class AccountManager(object):
    """
    Keeps track of available user accounts and assigns them to the
    worker threads.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.default_pool = None
        self.pools        = None
        self.reset()

    def reset(self):
        """
        Removes all account pools.
        """
        self.default_pool = AccountPool()
        self.pools        = []

    def add_pool(self, pool, match = None):
        """
        Adds a new account pool. If the given match argument is
        None, the pool the default pool. Otherwise, the match argument is
        a callback function that is invoked to decide whether or not the
        given pool should be used for a host.

        When Exscript logs into a host, the account is chosen in the following
        order:

            # Exscript checks whether an account was attached to the
            L{Host} object using L{Host.set_account()}), and uses that.

            # If the L{Host} has no account attached, Exscript walks
            through all pools that were passed to L{Queue.add_account_pool()}.
            For each pool, it passes the L{Host} to the function in the
            given match argument. If the return value is True, the account
            pool is used to acquire an account.
            (Accounts within each pool are taken in a round-robin
            fashion.)

            # If no matching account pool is found, an account is taken
            from the default account pool.

            # Finally, if all that fails and the default account pool
            contains no accounts, an error is raised.

        Example usage::

            def do_nothing(conn):
                conn.autoinit()

            def use_this_pool(host):
                return host.get_name().startswith('foo')

            default_pool = AccountPool()
            default_pool.add_account(Account('default-user', 'password'))

            other_pool = AccountPool()
            other_pool.add_account(Account('user', 'password'))

            queue = Queue()
            queue.account_manager.add_pool(default_pool)
            queue.account_manager.add_pool(other_pool, use_this_pool)

            host = Host('localhost')
            queue.run(host, do_nothing)

        In the example code, the host has no account attached. As a result,
        the queue checks whether use_this_pool() returns True. Because the
        hostname does not start with 'foo', the function returns False, and
        Exscript takes the 'default-user' account from the default pool.

        @type  pool: AccountPool
        @param pool: The account pool that is added.
        @type  match: callable
        @param match: A callback to check if the pool should be used.
        """
        if match is None:
            self.default_pool = pool
        else:
            self.pools.append((match, pool))

    def add_account(self, account):
        """
        Adds the given account to the default account pool that Exscript uses
        to log into all hosts that have no specific L{Account} attached.

        @type  account: Account
        @param account: The account that is added.
        """
        self.default_pool.add_account(account)

    def get_account_from_hash(self, account_hash):
        """
        Returns the account with the given hash, if it is contained in any
        of the pools. Returns None otherwise.

        @type  account_hash: str
        @param account_hash: The hash of an account object.
        """
        for _, pool in self.pools:
            account = pool.get_account_from_hash(account_hash)
            if account is not None:
                return account
        return self.default_pool.get_account_from_hash(account_hash)

    def acquire_account(self, account = None, owner = None):
        """
        Acquires the given account. If no account is given, one is chosen
        from the default pool.

        @type  account: Account
        @param account: The account that is added.
        @type  owner: object
        @param owner: An optional descriptor for the owner.
        @rtype:  L{Account}
        @return: The account that was acquired.
        """
        if account is not None:
            for _, pool in self.pools:
                if pool.has_account(account):
                    return pool.acquire_account(account, owner)

            if not self.default_pool.has_account(account):
                # The account is not in any pool.
                account.acquire()
                return account

        return self.default_pool.acquire_account(account, owner)

    def acquire_account_for(self, host, owner = None):
        """
        Acquires an account for the given host and returns it.
        The host is passed to each of the match functions that were
        passed in when adding the pool. The first pool for which the
        match function returns True is chosen to assign an account.

        @type  host: L{Host}
        @param host: The host for which an account is acquired.
        @type  owner: object
        @param owner: An optional descriptor for the owner.
        @rtype:  L{Account}
        @return: The account that was acquired.
        """
        # Check whether a matching account pool exists.
        for match, pool in self.pools:
            if match(host) is True:
                return pool.acquire_account(owner = owner)

        # Else, choose an account from the default account pool.
        return self.default_pool.acquire_account(owner = owner)

    def release_accounts(self, owner):
        """
        Releases all accounts that were acquired by the given owner.

        @type  owner: object
        @param owner: The owner descriptor as passed to acquire_account().
        """
        for _, pool in self.pools:
            pool.release_accounts(owner)
        self.default_pool.release_accounts(owner)
