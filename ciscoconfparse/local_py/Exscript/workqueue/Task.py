# Copyright (C) 2007-2011 Samuel Abels.
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
Represents a batch of enqueued actions.
"""
from Exscript.util.event import Event

class Task(object):
    """
    Represents a batch of running actions.
    """
    def __init__(self, workqueue):
        self.done_event = Event()
        self.workqueue  = workqueue
        self.job_ids    = set()
        self.completed  = 0
        self.workqueue.job_succeeded_event.listen(self._on_job_done)
        self.workqueue.job_aborted_event.listen(self._on_job_done)

    def _on_job_done(self, job):
        if job.id not in self.job_ids:
            return
        self.completed += 1
        if self.is_completed():
            self.done_event()

    def is_completed(self):
        """
        Returns True if all actions in the task are completed, returns
        False otherwise.

        @rtype:  bool
        @return: Whether the task is completed.
        """
        return self.completed == len(self.job_ids)

    def wait(self):
        """
        Waits until all actions in the task have completed.
        Does not use any polling.
        """
        for theid in self.job_ids:
            self.workqueue.wait_for(theid)

    def add_job_id(self, theid):
        """
        Adds a job to the task.

        @type  theid: int
        @param theid: The id of the job.
        """
        self.job_ids.add(theid)
