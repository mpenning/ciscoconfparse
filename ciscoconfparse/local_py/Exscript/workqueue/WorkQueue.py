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
from Exscript.util.event import Event
from Exscript.workqueue.Job import Thread, Process
from Exscript.workqueue.Pipeline import Pipeline
from Exscript.workqueue.MainLoop import MainLoop

class WorkQueue(object):
    """
    This class implements the asynchronous workqueue and is the main API
    for using the workqueue module.
    """
    def __init__(self,
                 collection = None,
                 debug = 0,
                 max_threads = 1,
                 mode = 'threading'):
        """
        Constructor.

        @type  debug: int
        @param debug: The debug level.
        @type  max_threads: int
        @param max_threads: The maximum number of concurrent threads.
        """
        if mode == 'threading':
            self.job_cls = Thread
        elif mode == 'multiprocessing':
            self.job_cls = Process
        else:
            raise TypeError('invalid "mode" argument: ' + repr(mode))
        if collection is None:
            self.collection = Pipeline(max_threads)
        else:
            self.collection = collection
            collection.set_max_working(max_threads)
        self.job_init_event      = Event()
        self.job_started_event   = Event()
        self.job_error_event     = Event()
        self.job_succeeded_event = Event()
        self.job_aborted_event   = Event()
        self.queue_empty_event   = Event()
        self.debug               = debug
        self.main_loop           = None
        self._init()

    def _init(self):
        self.main_loop       = MainLoop(self.collection, self.job_cls)
        self.main_loop.debug = self.debug
        self.main_loop.job_init_event.listen(self.job_init_event)
        self.main_loop.job_started_event.listen(self.job_started_event)
        self.main_loop.job_error_event.listen(self.job_error_event)
        self.main_loop.job_succeeded_event.listen(self.job_succeeded_event)
        self.main_loop.job_aborted_event.listen(self.job_aborted_event)
        self.main_loop.queue_empty_event.listen(self.queue_empty_event)
        self.main_loop.start()

    def _check_if_ready(self):
        if self.main_loop is None:
            raise Exception('main loop is already destroyed')

    def set_debug(self, debug = 1):
        """
        Set the debug level.

        @type  debug: int
        @param debug: The debug level.
        """
        self._check_if_ready()
        self.debug           = debug
        self.main_loop.debug = debug

    def get_max_threads(self):
        """
        Returns the maximum number of concurrent threads.

        @rtype:  int
        @return: The number of threads.
        """
        self._check_if_ready()
        return self.collection.get_max_working()

    def set_max_threads(self, max_threads):
        """
        Set the maximum number of concurrent threads.

        @type  max_threads: int
        @param max_threads: The number of threads.
        """
        if max_threads is None:
            raise TypeError('max_threads must not be None.')
        self._check_if_ready()
        self.collection.set_max_working(max_threads)

    def enqueue(self, function, name = None, times = 1, data = None):
        """
        Appends a function to the queue for execution. The times argument
        specifies the number of attempts if the function raises an exception.
        If the name argument is None it defaults to whatever id(function)
        returns.

        @type  function: callable
        @param function: The function that is executed.
        @type  name: str
        @param name: Stored in Job.name.
        @type  times: int
        @param times: The maximum number of attempts.
        @type  data: object
        @param data: Optional data to store in Job.data.
        @rtype:  int
        @return: The id of the new job.
        """
        self._check_if_ready()
        return self.main_loop.enqueue(function, name, times, data)

    def enqueue_or_ignore(self, function, name = None, times = 1, data = None):
        """
        Like enqueue(), but does nothing if a function with the same name
        is already in the queue.
        Returns a job id if a new job was added, returns None otherwise.

        @type  function: callable
        @param function: The function that is executed.
        @type  name: str
        @param name: Stored in Job.name.
        @type  times: int
        @param times: The maximum number of attempts.
        @type  data: object
        @param data: Optional data to store in Job.data.
        @rtype:  int or None
        @return: The id of the new job.
        """
        self._check_if_ready()
        return self.main_loop.enqueue_or_ignore(function, name, times, data)

    def priority_enqueue(self,
                         function,
                         name        = None,
                         force_start = False,
                         times       = 1,
                         data        = None):
        """
        Like L{enqueue()}, but adds the given function at the top of the
        queue.
        If force_start is True, the function is immediately started even when
        the maximum number of concurrent threads is already reached.

        @type  function: callable
        @param function: The function that is executed.
        @type  name: str
        @param name: Stored in Job.name.
        @type  force_start: bool
        @param force_start: Whether to start execution immediately.
        @type  times: int
        @param times: The maximum number of attempts.
        @type  data: object
        @param data: Optional data to store in Job.data.
        @rtype:  int
        @return: The id of the new job.
        """
        self._check_if_ready()
        return self.main_loop.priority_enqueue(function,
                                               name,
                                               force_start,
                                               times,
                                               data)

    def priority_enqueue_or_raise(self,
                                  function,
                                  name        = None,
                                  force_start = False,
                                  times       = 1,
                                  data        = None):
        """
        Like priority_enqueue(), but if a function with the same name is
        already in the queue, the existing function is moved to the top of
        the queue and the given function is ignored.
        Returns a job id if a new job was added, returns None otherwise.

        @type  function: callable
        @param function: The function that is executed.
        @type  name: str
        @param name: Stored in Job.name.
        @type  times: int
        @param times: The maximum number of attempts.
        @type  data: object
        @param data: Optional data to store in Job.data.
        @rtype:  int or None
        @return: The id of the new job.
        """
        self._check_if_ready()
        return self.main_loop.priority_enqueue_or_raise(function,
                                                        name,
                                                        force_start,
                                                        times,
                                                        data)

    def unpause(self):
        """
        Restart the execution of enqueued jobs after pausing them.
        This method is the opposite of pause().
        This method is asynchronous.
        """
        self.collection.unpause()

    def pause(self):
        """
        Stop the execution of enqueued jobs.
        Executing may later be resumed by calling unpause().
        This method is asynchronous.
        """
        self.collection.pause()

    def wait_for(self, job_id):
        """
        Waits until the job with the given id is completed.

        @type  job_id: int
        @param job_id: The job that is executed.
        """
        self._check_if_ready()
        self.main_loop.wait_for(job_id)

    def wait_until_done(self):
        """
        Waits until the queue is empty.
        """
        self.collection.wait_all()

    def shutdown(self, restart = True):
        """
        Stop the execution of enqueued jobs, and wait for all running
        jobs to complete. This method is synchronous and returns as soon
        as all jobs are terminated (i.e. all threads are stopped).

        If restart is True, the workqueue is restarted and paused,
        so you may fill it with new jobs.

        If restart is False, the WorkQueue can no longer be used after calling
        this method.

        @type  restart: bool
        @param restart: Whether to restart the queue after shutting down.
        """
        self._check_if_ready()
        self.collection.stop()
        self.collection.wait()
        self.main_loop.join()
        self.main_loop = None
        self.collection.clear()
        if restart:
            self.collection.start()
            self._init()

    def destroy(self):
        """
        Like shutdown(), but does not restart the queue and does not
        wait for already started jobs to complete.
        """
        self._check_if_ready()
        self.collection.stop()
        self.main_loop.join()
        self.main_loop = None
        self.collection.clear()

    def is_paused(self):
        """
        Returns True if the queue is currently active (i.e. not
        paused and not shut down), False otherwise.

        @rtype:  bool
        @return: Whether enqueued jobs are currently executed.
        """
        if self.main_loop is None:
            return True
        return self.collection.paused

    def get_running_jobs(self):
        """
        Returns a list of all jobs that are currently in progress.

        @rtype:  list[Job]
        @return: A list of running jobs.
        """
        return self.collection.get_working()

    def get_length(self):
        """
        Returns the number of currently non-completed jobs.

        @rtype:  int
        @return: The length of the queue.
        """
        return len(self.collection)
