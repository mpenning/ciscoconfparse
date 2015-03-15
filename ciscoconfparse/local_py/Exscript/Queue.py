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
The heart of Exscript.
"""
import sys
import os
import gc
import select
import threading
import weakref
from functools import partial
from multiprocessing import Pipe
from Exscript.Logger import logger_registry
from Exscript.LoggerProxy import LoggerProxy
from Exscript.util.cast import to_hosts
from Exscript.util.tty import get_terminal_size
from Exscript.util.impl import format_exception, serializeable_sys_exc_info
from Exscript.util.decorator import get_label
from Exscript.AccountManager import AccountManager
from Exscript.workqueue import WorkQueue, Task
from Exscript.AccountProxy import AccountProxy
from Exscript.protocols import prepare

def _account_factory(accm, host, account):
    if account is None:
        account = host.get_account()

    # Specific account requested?
    if account:
        acquired = AccountProxy.for_account_hash(accm, account.__hash__())
    else:
        acquired = AccountProxy.for_host(accm, host)

    # Thread-local accounts don't need a remote proxy.
    if acquired:
        return acquired
    account.acquire()
    return account

def _prepare_connection(func):
    """
    A decorator that unpacks the host and connection from the job argument
    and passes them as separate arguments to the wrapped function.
    """
    def _wrapped(job, *args, **kwargs):
        job_id    = id(job)
        to_parent = job.data['pipe']
        host      = job.data['host']

        # Create a protocol adapter.
        mkaccount = partial(_account_factory, to_parent, host)
        pargs     = {'account_factory': mkaccount,
                     'stdout':          job.data['stdout']}
        pargs.update(host.get_options())
        conn = prepare(host, **pargs)

        # Connect and run the function.
        log_options = get_label(func, 'log_to')
        if log_options is not None:
            # Enable logging.
            proxy  = LoggerProxy(to_parent, log_options['logger_id'])
            log_cb = partial(proxy.log, job_id)
            proxy.add_log(job_id, job.name, job.failures + 1)
            conn.data_received_event.listen(log_cb)
            try:
                conn.connect(host.get_address(), host.get_tcp_port())
                result = func(job, host, conn, *args, **kwargs)
                conn.close(force = True)
            except:
                proxy.log_aborted(job_id, serializeable_sys_exc_info())
                raise
            else:
                proxy.log_succeeded(job_id)
            finally:
                conn.data_received_event.disconnect(log_cb)
        else:
            conn.connect(host.get_address(), host.get_tcp_port())
            result = func(job, host, conn, *args, **kwargs)
            conn.close(force = True)
        return result

    return _wrapped

def _is_recoverable_error(cls):
    # Hack: We can't use isinstance(), because the classes may
    # have been created by another python process; apparently this
    # will cause isinstance() to return False.
    return cls.__name__ in ('CompileError', 'FailException')

def _call_logger(funcname, logger_id, *args):
    logger = logger_registry.get(logger_id)
    if not logger:
        return
    return getattr(logger, funcname)(*args)

class _PipeHandler(threading.Thread):
    """
    Each PipeHandler holds an open pipe to a subprocess, to allow the
    sub-process to access the accounts and communicate status information.
    """
    def __init__(self, account_manager):
        threading.Thread.__init__(self)
        self.daemon = True
        self.accm   = account_manager
        self.to_child, self.to_parent = Pipe()

    def _send_account(self, account):
        if account is None:
            self.to_child.send(account)
            return
        response = (account.__hash__(),
                    account.get_name(),
                    account.get_password(),
                    account.get_authorization_password(),
                    account.get_key())
        self.to_child.send(response)

    def _handle_request(self, request):
        try:
            command, arg = request
            if command == 'acquire-account-for-host':
                account = self.accm.acquire_account_for(arg, self)
                self._send_account(account)
            elif command == 'acquire-account-from-hash':
                account = self.accm.get_account_from_hash(arg)
                if account is not None:
                    account = self.accm.acquire_account(account, self)
                self._send_account(account)
            elif command == 'acquire-account':
                account = self.accm.acquire_account(owner = self)
                self._send_account(account)
            elif command == 'release-account':
                account = self.accm.get_account_from_hash(arg)
                account.release()
                self.to_child.send('ok')
            elif command == 'log-add':
                log = _call_logger('add_log', *arg)
                self.to_child.send(log)
            elif command == 'log-message':
                _call_logger('log', *arg)
            elif command == 'log-aborted':
                _call_logger('log_aborted', *arg)
            elif command == 'log-succeeded':
                _call_logger('log_succeeded', *arg)
            else:
                raise Exception('invalid command on pipe: ' + repr(command))
        except Exception, e:
            self.to_child.send(e)
            raise

    def run(self):
        while True:
            try:
                request = self.to_child.recv()
            except (EOFError, IOError):
                self.accm.release_accounts(self)
                break
            self._handle_request(request)

class Queue(object):
    """
    Manages hosts/tasks, accounts, connections, and threads.
    """

    def __init__(self,
                 domain      = '',
                 verbose     = 1,
                 mode        = 'threading',
                 max_threads = 1,
                 host_driver = None,
                 stdout      = sys.stdout,
                 stderr      = sys.stderr):
        """
        Constructor. All arguments should be passed as keyword arguments.
        Depending on the verbosity level, the following types
        of output are written to stdout/stderr (or to whatever else is
        passed in the stdout/stderr arguments):

          - S = status bar
          - L = live conversation
          - D = debug messages
          - E = errors
          - ! = errors with tracebacks
          - F = fatal errors with tracebacks

        The output types are mapped depending on the verbosity as follows:

          - verbose = -1: stdout = None, stderr = F
          - verbose =  0: stdout = None, stderr = EF
          - verbose =  1, max_threads = 1: stdout = L, stderr = EF
          - verbose =  1, max_threads = n: stdout = S, stderr = EF
          - verbose >=  2, max_threads = 1: stdout = DL, stderr = !F
          - verbose >=  2, max_threads = n: stdout = DS, stderr = !F

        @type  domain: str
        @param domain: The default domain of the contacted hosts.
        @type  verbose: int
        @param verbose: The verbosity level.
        @type  mode: str
        @param mode: 'multiprocessing' or 'threading'
        @type  max_threads: int
        @param max_threads: The maximum number of concurrent threads.
        @type  host_driver: str
        @param host_driver: driver name like "ios" for manual override
        @type  stdout: file
        @param stdout: The output channel, defaults to sys.stdout.
        @type  stderr: file
        @param stderr: The error channel, defaults to sys.stderr.
        """
        self.workqueue         = WorkQueue(mode = mode)
        self.account_manager   = AccountManager()
        self.pipe_handlers     = weakref.WeakValueDictionary()
        self.domain            = domain
        self.verbose           = verbose
        self.stdout            = stdout
        self.stderr            = stderr
        self.host_driver       = host_driver
        self.devnull           = open(os.devnull, 'w')
        self.channel_map       = {'fatal_errors': self.stderr,
                                  'debug':        self.stdout}
        self.completed         = 0
        self.total             = 0
        self.failed            = 0
        self.status_bar_length = 0
        self.set_max_threads(max_threads)

        # Listen to what the workqueue is doing.
        self.workqueue.job_init_event.listen(self._on_job_init)
        self.workqueue.job_started_event.listen(self._on_job_started)
        self.workqueue.job_error_event.listen(self._on_job_error)
        self.workqueue.job_succeeded_event.listen(self._on_job_succeeded)
        self.workqueue.job_aborted_event.listen(self._on_job_aborted)

    def _update_verbosity(self):
        if self.verbose < 0:
            self.channel_map['status_bar'] = self.devnull
            self.channel_map['connection'] = self.devnull
            self.channel_map['errors']     = self.devnull
            self.channel_map['tracebacks'] = self.devnull
        elif self.verbose == 0:
            self.channel_map['status_bar'] = self.devnull
            self.channel_map['connection'] = self.devnull
            self.channel_map['errors']     = self.stderr
            self.channel_map['tracebacks'] = self.devnull
        elif self.verbose == 1 and self.get_max_threads() == 1:
            self.channel_map['status_bar'] = self.devnull
            self.channel_map['connection'] = self.stdout
            self.channel_map['errors']     = self.stderr
            self.channel_map['tracebacks'] = self.devnull
        elif self.verbose == 1:
            self.channel_map['status_bar'] = self.stdout
            self.channel_map['connection'] = self.devnull
            self.channel_map['errors']     = self.stderr
            self.channel_map['tracebacks'] = self.devnull
        elif self.verbose >= 2 and self.get_max_threads() == 1:
            self.channel_map['status_bar'] = self.devnull
            self.channel_map['connection'] = self.stdout
            self.channel_map['errors']     = self.stderr
            self.channel_map['tracebacks'] = self.stderr
        elif self.verbose >= 2:
            self.channel_map['status_bar'] = self.stdout
            self.channel_map['connection'] = self.devnull
            self.channel_map['errors']     = self.stderr
            self.channel_map['tracebacks'] = self.stderr

    def _write(self, channel, msg):
        self.channel_map[channel].write(msg)
        self.channel_map[channel].flush()

    def _create_pipe(self):
        """
        Creates a new pipe and returns the child end of the connection.
        To request an account from the pipe, use::

            pipe = queue._create_pipe()

            # Let the account manager choose an account.
            pipe.send(('acquire-account-for-host', host))
            account = pipe.recv()
            ...
            pipe.send(('release-account', account.id()))

            # Or acquire a specific account.
            pipe.send(('acquire-account', account.id()))
            account = pipe.recv()
            ...
            pipe.send(('release-account', account.id()))

            pipe.close()
        """
        child = _PipeHandler(self.account_manager)
        self.pipe_handlers[id(child)] = child
        child.start()
        return child.to_parent

    def _del_status_bar(self):
        if self.status_bar_length == 0:
            return
        self._write('status_bar', '\b \b' * self.status_bar_length)
        self.status_bar_length = 0

    def get_progress(self):
        """
        Returns the progress in percent.

        @rtype:  float
        @return: The progress in percent.
        """
        if self.total == 0:
            return 0.0
        return 100.0 / self.total * self.completed

    def _print_status_bar(self, exclude = None):
        if self.total == 0:
            return
        percent  = 100.0 / self.total * self.completed
        progress = '%d/%d (%d%%)' % (self.completed, self.total, percent)
        jobs     = self.workqueue.get_running_jobs()
        running  = '|'.join([j.name for j in jobs if j.name != exclude])
        if not running:
            self.status_bar_length = 0
            return
        rows, cols = get_terminal_size()
        text       = 'In progress: [%s] %s' % (running, progress)
        overflow   = len(text) - cols
        if overflow > 0:
            cont      = '...'
            overflow += len(cont) + 1
            strlen    = len(running)
            partlen   = (strlen / 2) - (overflow / 2)
            head      = running[:partlen]
            tail      = running[-partlen:]
            running   = head + cont + tail
            text      = 'In progress: [%s] %s' % (running, progress)
        self._write('status_bar', text)
        self.status_bar_length = len(text)

    def _print(self, channel, msg):
        self._del_status_bar()
        self._write(channel, msg + '\n')
        self._print_status_bar()

    def _dbg(self, level, msg):
        if level > self.verbose:
            return
        self._print('debug', msg)

    def _on_job_init(self, job):
        if job.data is None:
            job.data = {}
        job.data['pipe']   = self._create_pipe()
        job.data['stdout'] = self.channel_map['connection']

    def _on_job_destroy(self, job):
        job.data['pipe'].close()

    def _on_job_started(self, job):
        self._del_status_bar()
        self._print_status_bar()

    def _on_job_error(self, job, exc_info):
        msg   = job.name + ' error: ' + str(exc_info[1])
        trace = ''.join(format_exception(*exc_info))
        self._print('errors', msg)
        if _is_recoverable_error(exc_info[0]):
            self._print('tracebacks', trace)
        else:
            self._print('fatal_errors', trace)

    def _on_job_succeeded(self, job):
        self._on_job_destroy(job)
        self.completed += 1
        self._print('status_bar', job.name + ' succeeded.')
        self._dbg(2, job.name + ' job is done.')
        self._del_status_bar()
        self._print_status_bar(exclude = job.name)

    def _on_job_aborted(self, job):
        self._on_job_destroy(job)
        self.completed += 1
        self.failed    += 1
        self._print('errors', job.name + ' finally failed.')
        self._del_status_bar()
        self._print_status_bar(exclude = job.name)

    def set_max_threads(self, n_connections):
        """
        Sets the maximum number of concurrent connections.

        @type  n_connections: int
        @param n_connections: The maximum number of connections.
        """
        self.workqueue.set_max_threads(n_connections)
        self._update_verbosity()

    def get_max_threads(self):
        """
        Returns the maximum number of concurrent threads.

        @rtype:  int
        @return: The maximum number of connections.
        """
        return self.workqueue.get_max_threads()

    def add_account_pool(self, pool, match = None):
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
            queue.add_account_pool(default_pool)
            queue.add_account_pool(other_pool, use_this_pool)

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
        self.account_manager.add_pool(pool, match)

    def add_account(self, account):
        """
        Adds the given account to the default account pool that Exscript uses
        to log into all hosts that have no specific L{Account} attached.

        @type  account: Account
        @param account: The account that is added.
        """
        self.account_manager.add_account(account)

    def is_completed(self):
        """
        Returns True if the task is completed, False otherwise.
        In other words, this methods returns True if the queue is empty.

        @rtype:  bool
        @return: Whether all tasks are completed.
        """
        return self.workqueue.get_length() == 0

    def join(self):
        """
        Waits until all jobs are completed.
        """
        self._dbg(2, 'Waiting for the queue to finish.')
        self.workqueue.wait_until_done()
        for child in self.pipe_handlers.values():
            child.join()
        self._del_status_bar()
        self._print_status_bar()
        gc.collect()

    def shutdown(self, force = False):
        """
        Stop executing any further jobs. If the force argument is True,
        the function does not wait until any queued jobs are completed but
        stops immediately.

        After emptying the queue it is restarted, so you may still call run()
        after using this method.

        @type  force: bool
        @param force: Whether to wait until all jobs were processed.
        """
        if not force:
            self.join()

        self._dbg(2, 'Shutting down queue...')
        self.workqueue.shutdown(True)
        self._dbg(2, 'Queue shut down.')
        self._del_status_bar()

    def destroy(self, force = False):
        """
        Like shutdown(), but also removes all accounts, hosts, etc., and
        does not restart the queue. In other words, the queue can no longer
        be used after calling this method.

        @type  force: bool
        @param force: Whether to wait until all jobs were processed.
        """
        try:
            if not force:
                self.join()
        finally:
            self._dbg(2, 'Destroying queue...')
            self.workqueue.destroy()
            self.account_manager.reset()
            self.completed         = 0
            self.total             = 0
            self.failed            = 0
            self.status_bar_length = 0
            self._dbg(2, 'Queue destroyed.')
            self._del_status_bar()

    def reset(self):
        """
        Remove all accounts, hosts, etc.
        """
        self._dbg(2, 'Resetting queue...')
        self.account_manager.reset()
        self.workqueue.shutdown(True)
        self.completed         = 0
        self.total             = 0
        self.failed            = 0
        self.status_bar_length = 0
        self._dbg(2, 'Queue reset.')
        self._del_status_bar()

    def _run(self, hosts, callback, queue_function, *args):
        hosts       = to_hosts(hosts, default_domain = self.domain)
        self.total += len(hosts)
        callback    = _prepare_connection(callback)
        task        = Task(self.workqueue)
        for host in hosts:
            name   = host.get_name()
            data   = {'host': host}
            job_id = queue_function(callback, name, *args, data = data)
            if job_id is not None:
                task.add_job_id(job_id)

            if self.host_driver is not None:
                host.set_option('driver', self.host_driver)

        if task.is_completed():
            self._dbg(2, 'No jobs enqueued.')
            return None

        self._dbg(2, 'All jobs enqueued.')
        return task

    def run(self, hosts, function, attempts = 1):
        """
        Add the given function to a queue, and call it once for each host
        according to the threading options.
        Use decorators.bind() if you also want to pass additional
        arguments to the callback function.

        Returns an object that represents the queued task, and that may be
        passed to is_completed() to check the status.

        @type  hosts: string|list(string)|Host|list(Host)
        @param hosts: A hostname or Host object, or a list of them.
        @type  function: function
        @param function: The function to execute.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: An object representing the task.
        """
        return self._run(hosts, function, self.workqueue.enqueue, attempts)

    def run_or_ignore(self, hosts, function, attempts = 1):
        """
        Like run(), but only appends hosts that are not already in the
        queue.

        @type  hosts: string|list(string)|Host|list(Host)
        @param hosts: A hostname or Host object, or a list of them.
        @type  function: function
        @param function: The function to execute.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: A task object, or None if all hosts were duplicates.
        """
        return self._run(hosts,
                         function,
                         self.workqueue.enqueue_or_ignore,
                         attempts)

    def priority_run(self, hosts, function, attempts = 1):
        """
        Like run(), but adds the task to the front of the queue.

        @type  hosts: string|list(string)|Host|list(Host)
        @param hosts: A hostname or Host object, or a list of them.
        @type  function: function
        @param function: The function to execute.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: An object representing the task.
        """
        return self._run(hosts,
                         function,
                         self.workqueue.priority_enqueue,
                         False,
                         attempts)

    def priority_run_or_raise(self, hosts, function, attempts = 1):
        """
        Like priority_run(), but if a host is already in the queue, the
        existing host is moved to the top of the queue instead of enqueuing
        the new one.

        @type  hosts: string|list(string)|Host|list(Host)
        @param hosts: A hostname or Host object, or a list of them.
        @type  function: function
        @param function: The function to execute.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: A task object, or None if all hosts were duplicates.
        """
        return self._run(hosts,
                         function,
                         self.workqueue.priority_enqueue_or_raise,
                         False,
                         attempts)

    def force_run(self, hosts, function, attempts = 1):
        """
        Like priority_run(), but starts the task immediately even if that
        max_threads is exceeded.

        @type  hosts: string|list(string)|Host|list(Host)
        @param hosts: A hostname or Host object, or a list of them.
        @type  function: function
        @param function: The function to execute.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: An object representing the task.
        """
        return self._run(hosts,
                         function,
                         self.workqueue.priority_enqueue,
                         True,
                         attempts)

    def enqueue(self, function, name = None, attempts = 1):
        """
        Places the given function in the queue and calls it as soon
        as a thread is available. To pass additional arguments to the
        callback, use Python's functools.partial().

        @type  function: function
        @param function: The function to execute.
        @type  name: string
        @param name: A name for the task.
        @type  attempts: int
        @param attempts: The number of attempts on failure.
        @rtype:  object
        @return: An object representing the task.
        """
        self.total += 1
        task   = Task(self.workqueue)
        job_id = self.workqueue.enqueue(function, name, attempts)
        if job_id is not None:
            task.add_job_id(job_id)
        self._dbg(2, 'Function enqueued.')
        return task
