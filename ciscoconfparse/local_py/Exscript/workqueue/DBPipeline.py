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
import sqlalchemy as sa
from multiprocessing import Condition, RLock

def _transaction(function, *args, **kwargs):
    def wrapper(self, *args, **kwargs):
        with self.engine.contextual_connect(close_with_result = True).begin():
            return function(*args, **kwargs)
    wrapper.__name__ = function.__name__
    wrapper.__dict__ = function.__dict__
    wrapper.__doc__  = function.__doc__
    return wrapper

class DBPipeline(object):
    """
    Like L{Exscript.workqueue.Pipeline}, but keeps all queued objects
    in a database, instead of using in-memory data structures.
    """
    def __init__(self, engine, max_working = 1):
        self.condition     = Condition(RLock())
        self.engine        = engine
        self.max_working   = max_working
        self.running       = False
        self.paused        = False
        self.metadata      = sa.MetaData(self.engine)
        self._table_prefix = 'exscript_pipeline_'
        self._table_map    = {}
        self.__update_table_names()
        self.clear()

    def __add_table(self, table):
        """
        Adds a new table to the internal table list.
        
        @type  table: Table
        @param table: An sqlalchemy table.
        """
        pfx = self._table_prefix
        self._table_map[table.name[len(pfx):]] = table

    def __update_table_names(self):
        """
        Adds all tables to the internal table list.
        """
        pfx = self._table_prefix
        self.__add_table(sa.Table(pfx + 'job', self.metadata,
            sa.Column('id',     sa.Integer, primary_key = True),
            sa.Column('name',   sa.String(150), index = True),
            sa.Column('status', sa.String(50), index = True),
            sa.Column('job',    sa.PickleType()),
            mysql_engine = 'INNODB'
        ))

    @synchronized
    def install(self):
        """
        Installs (or upgrades) database tables.
        """
        self.metadata.create_all()

    @synchronized
    def uninstall(self):
        """
        Drops all tables from the database. Use with care.
        """
        self.metadata.drop_all()

    @synchronized
    def clear_database(self):
        """
        Drops the content of any database table used by this library.
        Use with care.

        Wipes out everything, including types, actions, resources and acls.
        """
        delete = self._table_map['job'].delete()
        delete.execute()

    def debug(self, debug = True):
        """
        Enable/disable debugging.

        @type  debug: bool
        @param debug: True to enable debugging.
        """
        self.engine.echo = debug

    def set_table_prefix(self, prefix):
        """
        Define a string that is prefixed to all table names in the database.

        @type  prefix: string
        @param prefix: The new prefix.
        """
        self._table_prefix = prefix
        self.__update_table_names()

    def get_table_prefix(self):
        """
        Returns the current database table prefix.
        
        @rtype:  string
        @return: The current prefix.
        """
        return self._table_prefix

    def __len__(self):
        return self._table_map['job'].count().execute().fetchone()[0]

    def __contains__(self, item):
        return self.has_id(id(item))

    def get_from_name(self, name):
        """
        Returns the item with the given name, or None if no such item
        is known.
        """
        with self.condition:
            tbl_j = self._table_map['job']
            query = tbl_j.select(tbl_j.c.name == name)
            row   = query.execute().fetchone()
            if row is None:
                return None
            return row.job

    def has_id(self, item_id):
        """
        Returns True if the queue contains an item with the given id.
        """
        tbl_j = self._table_map['job']
        query = tbl_j.select(tbl_j.c.id == item_id).count()
        return query.execute().fetchone()[0] > 0

    def task_done(self, item):
        with self.condition:
            self.working.remove(item)
            self.all.remove(id(item))
            self.condition.notify_all()

    def append(self, item):
        with self.condition:
            self.queue.append(item)
            self.all.add(id(item))
            self.condition.notify_all()

    def appendleft(self, item, force = False):
        with self.condition:
            if force:
                self.force.append(item)
            else:
                self.queue.appendleft(item)
            self.all.add(id(item))
            self.condition.notify_all()

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
            self.appendleft(item, force)
            self.condition.notify_all()

    def clear(self):
        with self.condition:
            self.queue    = deque()
            self.force    = deque()
            self.sleeping = set()
            self.working  = set()
            self.all      = set()
            self.condition.notify_all()

    def stop(self):
        """
        Force the next() method to return while in another thread.
        The return value of next() will be None.
        """
        with self.condition:
            self.running = False
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
        assert id(item) in self.all
        with self.condition:
            self.sleeping.add(item)
            self.condition.notify_all()

    def wake(self, item):
        assert id(item) in self.all
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

    def _get_next(self):
        # We need to leave sleeping items in the queue because else we
        # would not know their original position after they wake up.
        # So we need to temporarily remove sleeping items from the top of
        # the queue here.
        sleeping = self._popleft_sleeping()

        # Get the first non-sleeping item from the queue.
        try:
            next = self.queue.popleft()
        except IndexError:
            next = None

        # Re-insert sleeping items.
        self.queue.extendleft(sleeping)
        return next

    def next(self):
        with self.condition:
            self.running = True
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
