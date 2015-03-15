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
import sys
import threading
import multiprocessing
from copy import copy
from functools import partial
from multiprocessing import Pipe
from Exscript.util.impl import serializeable_sys_exc_info

class _ChildWatcher(threading.Thread):
    def __init__(self, child, callback):
        threading.Thread.__init__(self)
        self.child = child
        self.cb    = callback

    def __copy__(self):
        watcher = _ChildWatcher(copy(self.child), self.cb)
        return watcher

    def run(self):
        to_child, to_self = Pipe()
        try:
            self.child.start(to_self)
            result = to_child.recv()
            self.child.join()
        except:
            result = sys.exc_info()
        finally:
            to_child.close()
            to_self.close()
        if result == '':
            self.cb(None)
        else:
            self.cb(result)

def _make_process_class(base, clsname):
    class process_cls(base):
        def __init__(self, id, function, name, data):
            base.__init__(self, name = name)
            self.id       = id
            self.pipe     = None
            self.function = function
            self.failures = 0
            self.data     = data

        def run(self):
            """
            Start the associated function.
            """
            try:
                self.function(self)
            except:
                self.pipe.send(serializeable_sys_exc_info())
            else:
                self.pipe.send('')
            finally:
                self.pipe = None

        def start(self, pipe):
            self.pipe = pipe
            base.start(self)
    process_cls.__name__ = clsname
    return process_cls

Thread = _make_process_class(threading.Thread, 'Thread')
Process = _make_process_class(multiprocessing.Process, 'Process')

class Job(object):
    __slots__ = ('id',
                 'func',
                 'name',
                 'times',
                 'failures',
                 'data',
                 'child',
                 'watcher')

    def __init__(self, function, name, times, data):
        self.id       = None
        self.func     = function
        self.name     = name is None and str(id(function)) or name
        self.times    = times
        self.failures = 0
        self.data     = data
        self.child    = None
        self.watcher  = None

    def start(self, child_cls, on_complete):
        self.child = child_cls(self.id, self.func, self.name, self.data)
        self.child.failures = self.failures
        self.watcher = _ChildWatcher(self.child, partial(on_complete, self))
        self.watcher.start()

    def join(self):
        self.watcher.join()
        self.child = None
