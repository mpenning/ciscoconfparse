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
from uuid import uuid4
from collections import deque
from multiprocessing import Condition, RLock

class Pipeline(object):
    """
    A collection that is similar to Python's Queue object, except
    it also tracks items that are currently sleeping or in progress.
    """
    def __init__(self, max_working = 1):
        self.condition   = Condition(RLock())
        self.max_working = max_working
        self.running     = True
        self.paused      = False
        self.queue       = None
        self.force       = None
        self.sleeping    = None
        self.working     = None
        self.item2id     = None
        self.id2item     = None # for performance reasons
        self.name2id     = None
        self.id2name     = None
        self.clear()

    def __len__(self):
        with self.condition:
            return len(self.id2item)

    def __contains__(self, item):
        with self.condition:
            return item in self.item2id

    def _register_item(self, name, item):
        uuid               = uuid4().hex
        self.id2item[uuid] = item
        self.item2id[item] = uuid
        if name is None:
            return uuid
        if name in self.name2id:
            msg = 'an item named %s is already queued' % repr(name)
            raise AttributeError(msg)
        self.name2id[name] = uuid
        self.id2name[uuid] = name
        return uuid

    def get_from_name(self, name):
        """
        Returns the item with the given name, or None if no such item
        is known.
        """
        with self.condition:
            try:
                item_id = self.name2id[name]
            except KeyError:
                return None
            return self.id2item[item_id]
        return None

    def has_id(self, item_id):
        """
        Returns True if the queue contains an item with the given id.
        """
        return item_id in self.id2item

    def task_done(self, item):
        with self.condition:
            try:
                self.working.remove(item)
            except KeyError:
                # This may happen if we receive a notification from a
                # thread that was previously enqueued, but then the
                # workqueue was forcefully stopped without waiting for
                # child threads to complete.
                self.condition.notify_all()
                return
            item_id = self.item2id.pop(item)
            self.id2item.pop(item_id)
            try:
                name = self.id2name.pop(item_id)
            except KeyError:
                pass
            else:
                self.name2id.pop(name)
            self.condition.notify_all()

    def append(self, item, name = None):
        """
        Adds the given item to the end of the pipeline.
        """
        with self.condition:
            self.queue.append(item)
            uuid = self._register_item(name, item)
            self.condition.notify_all()
            return uuid

    def appendleft(self, item, name = None, force = False):
        with self.condition:
            if force:
                self.force.append(item)
            else:
                self.queue.appendleft(item)
            uuid = self._register_item(name, item)
            self.condition.notify_all()
            return uuid

    def prioritize(self, item, force = False):
        """
        Moves the item to the very left of the queue.
        """
        with self.condition:
            # If the job is already running (or about to be forced),
            # there is nothing to be done.
            if item in self.working or item in self.force:
                return
            self.queue.remove(item)
            if force:
                self.force.append(item)
            else:
                self.queue.appendleft(item)
            self.condition.notify_all()

    def clear(self):
        with self.condition:
            self.queue    = deque()
            self.force    = deque()
            self.sleeping = set()
            self.working  = set()
            self.item2id  = dict()
            self.id2item  = dict()
            self.name2id  = dict()
            self.id2name  = dict()
            self.condition.notify_all()

    def stop(self):
        """
        Force the next() method to return while in another thread.
        The return value of next() will be None.
        """
        with self.condition:
            self.running = False
            self.condition.notify_all()

    def start(self):
        with self.condition:
            self.running = True
            self.condition.notify_all()

    def pause(self):
        with self.condition:
            self.paused = True
            self.condition.notify_all()

    def unpause(self):
        with self.condition:
            self.paused = False
            self.condition.notify_all()

    def sleep(self, item):
        with self.condition:
            self.sleeping.add(item)
            self.condition.notify_all()

    def wake(self, item):
        assert item in self.sleeping
        with self.condition:
            self.sleeping.remove(item)
            self.condition.notify_all()

    def wait_for_id(self, item_id):
        with self.condition:
            while self.has_id(item_id):
                self.condition.wait()

    def wait(self):
        """
        Waits for all currently running tasks to complete.
        """
        with self.condition:
            while self.working:
                self.condition.wait()

    def wait_all(self):
        """
        Waits for all queued and running tasks to complete.
        """
        with self.condition:
            while len(self) > 0:
                self.condition.wait()

    def with_lock(self, function, *args, **kwargs):
        with self.condition:
            return function(self, *args, **kwargs)

    def set_max_working(self, max_working):
        with self.condition:
            self.max_working = int(max_working)
            self.condition.notify_all()

    def get_max_working(self):
        return self.max_working

    def get_working(self):
        return list(self.working)

    def _popleft_sleeping(self):
        sleeping = []
        while True:
            try:
                node = self.queue[0]
            except IndexError:
                break
            if node not in self.sleeping:
                break
            sleeping.append(node)
            self.queue.popleft()
        return sleeping

    def _get_next(self, pop = True):
        # We need to leave sleeping items in the queue because else we
        # would not know their original position after they wake up.
        # So we need to temporarily remove sleeping items from the top of
        # the queue here.
        sleeping = self._popleft_sleeping()

        # Get the first non-sleeping item from the queue.
        if pop:
            try:
                next = self.queue.popleft()
            except IndexError:
                next = None
        else:
            try:
                next = self.queue[0]
            except IndexError:
                next = None

        # Re-insert sleeping items.
        self.queue.extendleft(sleeping)
        return next

    def try_next(self):
        """
        Like next(), but only returns the item that would be selected
        right now, without locking and without changing the queue.
        """
        with self.condition:
            try:
                return self.force[0]
            except IndexError:
                pass

            return self._get_next(False)

    def next(self):
        with self.condition:
            while self.running:
                if self.paused:
                    self.condition.wait()
                    continue

                # Wait until enough slots are available.
                if len(self.working) - \
                   len(self.sleeping) - \
                   len(self.force) >= self.max_working:
                    self.condition.wait()
                    continue

                # Forced items are returned regardless of how many tasks
                # are already working.
                try:
                    next = self.force.popleft()
                except IndexError:
                    pass
                else:
                    self.working.add(next)
                    return next

                # Return the first non-sleeping task.
                next = self._get_next()
                if next is None:
                    self.condition.wait()
                    continue
                self.working.add(next)
                return next
        return None
