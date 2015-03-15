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

class LoggerProxy(object):
    """
    An object that has a 1:1 relation to a Logger object in another
    process.
    """
    def __init__(self, parent, logger_id):
        """
        Constructor.

        @type  parent: multiprocessing.Connection
        @param parent: A pipe to the associated pipe handler.
        """
        self.parent    = parent
        self.logger_id = logger_id

    def add_log(self, job_id, name, attempt):
        self.parent.send(('log-add', (self.logger_id, job_id, name, attempt)))
        response = self.parent.recv()
        if isinstance(response, Exception):
            raise response
        return response

    def log(self, job_id, message):
        self.parent.send(('log-message', (self.logger_id, job_id, message)))

    def log_aborted(self, job_id, exc_info):
        self.parent.send(('log-aborted', (self.logger_id, job_id, exc_info)))

    def log_succeeded(self, job_id):
        self.parent.send(('log-succeeded', (self.logger_id, job_id)))
