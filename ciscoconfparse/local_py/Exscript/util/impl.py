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
Development tools.
"""
import sys
import warnings
import traceback
from functools import wraps

def add_label(obj, name, **kwargs):
    """
    Labels an object such that it can later be checked with
    L{has_label()}.

    @type  obj: object
    @param obj: The object that is labeled.
    @type  name: str
    @param name: A label.
    @type  kwargs: dict
    @param kwargs: Optional values to store with the label.
    @rtype:  object
    @return: The labeled function.
    """
    labels = obj.__dict__.setdefault('_labels', dict())
    labels[name] = kwargs
    return obj

def get_label(obj, name):
    """
    Checks whether an object has the given label attached (see
    L{mark_function()}) and returns the associated options.

    @type  obj: object
    @param obj: The object to check for the label.
    @type  name: str
    @param name: A label.
    @rtype:  dict or None
    @return: The optional values if the label is attached, None otherwise.
    """
    labels = obj.__dict__.get('_labels')
    if labels is None:
        return None
    return labels.get(name)

def copy_labels(src, dst):
    """
    Copies all labels of one object to another object.

    @type  src: object
    @param src: The object to check read the labels from.
    @type  dst: object
    @param dst: The object into which the labels are copied.
    """
    labels = src.__dict__.get('_labels')
    if labels is None:
        return
    dst.__dict__['_labels'] = labels.copy()

def serializeable_exc_info(thetype, ex, tb):
    """
    Since traceback objects can not be pickled, this function manipulates
    exception info tuples before they are passed accross process
    boundaries.
    """
    return thetype, ex, ''.join(traceback.format_exception(thetype, ex, tb))

def serializeable_sys_exc_info():
    """
    Convenience wrapper around serializeable_exc_info, equivalent to
    serializeable_exc_info(sys.exc_info()).
    """
    return serializeable_exc_info(*sys.exc_info())

def format_exception(thetype, ex, tb):
    """
    This function is a drop-in replacement for Python's
    traceback.format_exception().

    Since traceback objects can not be pickled, Exscript is forced to
    manipulate them before they are passed accross process boundaries.
    This leads to the fact the Python's traceback.format_exception()
    no longer works for those objects.

    This function works with any traceback object, regardless of whether
    or not Exscript manipulated it.
    """
    if isinstance(tb, str):
        return tb
    return ''.join(traceback.format_exception(thetype, ex, tb))

def deprecation(msg):
    """
    Prints a deprecation warning.
    """
    warnings.warn('deprecated',
                  category   = DeprecationWarning,
                  stacklevel = 2)

def deprecated(func):
    """
    A decorator for marking functions as deprecated. Results in
    a printed warning message when the function is used.
    """
    def decorated(*args, **kwargs):
        warnings.warn('Call to deprecated function %s.' % func.__name__,
                      category   = DeprecationWarning,
                      stacklevel = 2)
        return func(*args, **kwargs)
    decorated.__name__ = func.__name__
    decorated.__doc__  = func.__doc__
    decorated.__dict__.update(func.__dict__)
    return decorated

def synchronized(func):
    """
    Decorator for synchronizing method access.
    """
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        try:
            rlock = self._sync_lock
        except AttributeError:
            from multiprocessing import RLock
            rlock = self.__dict__.setdefault('_sync_lock', RLock())
        with rlock:
            return func(self, *args, **kwargs)
    return wrapped

def debug(func):
    """
    Decorator that prints a message whenever a function is entered or left.
    """
    @wraps(func)
    def wrapped(*args, **kwargs):
        arg = repr(args) + ' ' + repr(kwargs)
        sys.stdout.write('Entering ' + func.__name__ + arg + '\n')
        try:
            result = func(*args, **kwargs)
        except:
            sys.stdout.write('Traceback caught:\n')
            sys.stdout.write(format_exception(*sys.exc_info()))
            raise
        arg = repr(result)
        sys.stdout.write('Leaving ' + func.__name__ + '(): ' + arg + '\n')
        return result
    return wrapped

class Decorator(object):
    def __init__(self, obj):
        self.__dict__['obj'] = obj

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            self.__dict__[name] = value
        else:
            setattr(self.obj, name, value)

    def __getattr__(self, name):
        if name in self.__dict__.keys():
            return self.__dict__[name]
        return getattr(self.obj, name)

class _Context(Decorator):
    def __enter__(self):
        return self

    def __exit__(self, thetype, value, traceback):
        pass

class Context(_Context):
    def __exit__(self, thetype, value, traceback):
        return self.release()

    def context(self):
        return _Context(self)
