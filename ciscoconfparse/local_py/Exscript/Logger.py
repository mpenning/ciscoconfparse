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
Logging to memory.
"""
import weakref
from itertools import chain, ifilter
from collections import defaultdict
from Exscript.Log import Log

logger_registry = weakref.WeakValueDictionary() # Map id(logger) to Logger.

class Logger(object):
    """
    A QueueListener that implements logging for the queue.
    Logs are kept in memory, and not written to the disk.
    """

    def __init__(self):
        """
        Creates a new logger instance. Use the L{Exscript.util.log.log_to}
        decorator to send messages to the logger.
        """
        logger_registry[id(self)] = self
        self.logs    = defaultdict(list)
        self.started = 0
        self.success = 0
        self.failed  = 0

    def _reset(self):
        self.logs = defaultdict(list)

    def get_succeeded_actions(self):
        """
        Returns the number of jobs that were completed successfully.
        """
        return self.success

    def get_aborted_actions(self):
        """
        Returns the number of jobs that were aborted.
        """
        return self.failed

    def get_logs(self):
        return list(chain.from_iterable(self.logs.itervalues()))

    def get_succeeded_logs(self):
        func = lambda x: x.has_ended() and not x.has_error()
        return list(ifilter(func, self.get_logs()))

    def get_aborted_logs(self):
        func = lambda x: x.has_ended() and x.has_error()
        return list(ifilter(func, self.get_logs()))

    def _get_log(self, job_id):
        return self.logs[job_id][-1]

    def add_log(self, job_id, name, attempt):
        log = Log(name)
        log.started()
        self.logs[job_id].append(log)
        self.started += 1
        return log

    def log(self, job_id, message):
        # This method is called whenever a sub thread sends a log message
        # via a pipe. (See LoggerProxy and Queue.PipeHandler)
        log = self._get_log(job_id)
        log.write(message)

    def log_aborted(self, job_id, exc_info):
        log = self._get_log(job_id)
        log.aborted(exc_info)
        self.failed += 1

    def log_succeeded(self, job_id):
        log = self._get_log(job_id)
        log.succeeded()
        self.success += 1
