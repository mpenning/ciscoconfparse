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
Logging utilities.
"""
from Exscript.FileLogger import FileLogger
from Exscript.util.impl import add_label

_loggers = []

def log_to(logger):
    """
    Wraps a function that has a connection passed such that everything that
    happens on the connection is logged using the given logger.

    @type  logger: Logger
    @param logger: The logger that handles the logging.
    """
    logger_id = id(logger)
    def decorator(function):
        func = add_label(function, 'log_to', logger_id = logger_id)
        return func
    return decorator

def log_to_file(logdir, mode = 'a', delete = False, clearmem = True):
    """
    Like L{log_to()}, but automatically creates a new FileLogger
    instead of having one passed.
    Note that the logger stays alive (in memory) forever. If you need
    to control the lifetime of a logger, use L{log_to()} instead.
    """
    logger = FileLogger(logdir, mode, delete, clearmem)
    _loggers.append(logger)
    return log_to(logger)
