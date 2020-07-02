"""
Helper functions and classes to ease the use :class:`.Thread`'s with python's :mod:`threading` library

Utilities for working with :class:`.Event`
------------------------------------------


Classes
^^^^^^^

    ==============================   ==================================================================================================
    Class                            Description
    ==============================   ==================================================================================================
    :class:`.BetterEvent`            **BetterEvent** is a sub-class of :class:`.Event` with more flexibility + features
    :class:`.InvertibleEvent`        (this is just an alias for :class:`.BetterEvent`)
    ==============================   ==================================================================================================


Functions
^^^^^^^^^

    ==============================   ==================================================================================================
    Function                         Description
    ==============================   ==================================================================================================
    :func:`.event_multi_wait`        Allows waiting for more than one :class:`.Event` / :class:`.BetterEvent` at once
    :func:`.event_multi_wait_all`    A wrapper function for :func:`.event_multi_wait` with ``trigger='and'`` as default
    :func:`.event_multi_wait_any`    A wrapper function for :func:`.event_multi_wait` with ``trigger='or'`` as default
    ==============================   ==================================================================================================


Utilities for working with :class:`.Lock` thread locks
------------------------------------------------------

In the Python standard library, you can only use context management directly against a :class:`.Lock` object, which means
you're unable to specify things such as a timeout, whether or not to block, nor a built-in option to request an exception
to be raised if the lock can't be acquired.

And thus, :func:`.lock_acquire_timeout` was created - to solve all of the above problems, in one easy to use context management
function :)

The :func:`.lock_acquire_timeout` function - a context manager ( ``with lock_acquire_timeout(lock)`` ), is designed to allow use of
context management with standard :class:`threading.Lock` objects, with the ability to specify important parameters such as:
 
 * whether or not to **block** while acquiring the lock
 * an optional timeout - so that it gives up waiting for the ``lock.acquire`` after so many seconds
 * whether to raise :class:`.LockWaitTimeout` if the ``acquire`` times out instead of returning ``None``

Functions
^^^^^^^^^

    ==============================   ==================================================================================================
    Function                         Description
    ==============================   ==================================================================================================
    :func:`.lock_acquire_timeout`    Flexible context manager for acquiring :class:`.Locks`'s ``with lock_acquire_timeout(lock)``
    ==============================   ==================================================================================================

Utilities for working with :class:`.Thread` thread objects
----------------------------------------------------------

Using :class:`.SafeLoopThread` for looping threads with :class:`queue.Queue`'s + stop/pause support
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First example - we'll create a sub-class of :class:`.SafeLoopThread` called ``MyThread``::

    >>> # Create a sub-class of SafeLoopThread, and implement a loop() method
    >>> class MyThread(SafeLoopThread):
    ...     loop_sleep = 2    # 'run' will wait this many seconds between each run of your loop(). set to 0 to disable loop sleeps
    ...     def loop(self):
    ...         print("I'm looping!")
    ...
    >>> t = MyThread()   # Construct the class

Once we start the thread, we'll see that ``I'm looping!`` will be printed about once every 2 seconds, since that's what
we set ``loop_sleep`` to::

    >>> t.start()
    I'm looping!
    I'm looping!
    I'm looping!

Using :meth:`.SafeLoopThread.emit_pause` - we can pause the loop, which will silence the ``I'm looping!`` messages::

    >>> t.emit_pause()
    >>> # No output because the loop is now paused

To start the loop again, we can simply unpause it with :meth:`.SafeLoopThread.emit_unpause`::

    >>> t.emit_unpause()
    I'm looping!
    I'm looping!
    I'm looping!

Once we're done with ``MyThread``, unlike a normal :class:`.Thread`, we can ask the thread to shutdown gracefully
using :meth:`.SafeLoopThread.emit_stop` like so::

    >>> t.is_alive()    # First we'll confirm the thread is still running
    True
    >>> t.emit_stop()
    I'm looping!
    >>> # The .loop method will finish it's current iteration (unless you add additional ``should_stop`` checks in the loop)
    >>> # and then shutdown the thread by returning from ``.run``
    >>> t.is_alive()    # We can now see that the thread has shutdown as we requested it to.
    False



Classes
^^^^^^^

    ==============================   ==================================================================================================
    Class                            Description
    ==============================   ==================================================================================================
    :class:`.StopperThread`          A :class:`.Thread` base class which allows you easily add stop/pause support to your own threads
    :class:`.SafeLoopThread`         A :class:`.StopperThread` based class which runs ``.loop`` in a loop, with stop/start support
    ==============================   ==================================================================================================



"""
import queue
import threading
import time
from threading import Lock, Event
from contextlib import contextmanager
from datetime import datetime
from typing import Union, Optional, List

from privex.helpers.exceptions import LockWaitTimeout, EventWaitTimeout

import logging

log = logging.getLogger(__name__)

__all__ = [
    'lock_acquire_timeout', 'BetterEvent', 'InvertibleEvent',
    'StopperThread', 'SafeLoopThread',
    'event_multi_wait', 'event_multi_wait_all', 'event_multi_wait_any'
]


@contextmanager
def lock_acquire_timeout(lock: Lock, timeout: Union[int, float] = 10, fail=False, block=True):
    """
    A context manager (``with lock_acquire_timeout(mylock) as locked:``) for acquiring thread locks and waiting for them to be released,
    and giving up if the lock isn't released within ``timeout``.
    
    Yields a boolean in the ``with`` context which is ``True`` if the :class:`threading.Lock` was acquired within ``timeout``,
    or ``False`` if it wasn't.
    
        >>> from privex.helpers import lock_acquire_timeout
        >>> from threading import Lock
        >>>
        >>> my_lock = Lock()
        >>>
        >>> def some_func():
        ...     print("attempting to acquire a lock on 'my_lock'... will wait up to 30 secs...")
        ...     with lock_acquire_timeout(my_lock, timeout=30) as locked:
        ...         if not locked:
        ...             raise Exception("Failed to acquire 'my_lock' after waiting 30 seconds!")
        ...         print("successfully acquired a lock on 'my_lock'")
        ...     print("finished. my_lock should have been automatically released.")
    
    Original written by "robbles" on StackOverflow: https://stackoverflow.com/a/16782391/2648583
    
    :param Lock lock:           The :class:`threading.Lock` object to attempt to acquire a lock on
    :param int|float timeout:   The amount of seconds to wait for ``lock`` to be released if it's already locked
    :param bool fail:           (Default: ``False``) If this is ``True``, will raise :class:`.LockWaitTimeout` if we fail to
                                acquire the lock ``lock`` within ``timeout`` seconds.
    :param bool block:          If this is set to ``False``, ``timeout`` will be nulled and a non-blocking acquire will be done.
    :raises LockWaitTimeout:    When ``fail`` is ``True`` and we fail to acquire ``lock`` within ``timeout`` seconds.
    """
    timeout = timeout if block else None
    fail_msg = f"after waiting {timeout} seconds." if block else "(non-blocking acquire)"
    if block:
        log.debug("acquiring lock with timeout %s", timeout)
        result = lock.acquire(blocking=block, timeout=timeout)
    else:
        log.debug("non-blocking mode requested. ignoring timeout - using non-blocking acquire")
        result = lock.acquire(blocking=block)
    if not result and fail:
        raise LockWaitTimeout(f"Failed to acquire lock '{lock}' {fail_msg}")
    log.debug("post-acquire - result was %s after timeout %s - handing to context...", result, timeout)

    yield result
    log.debug("lock context finished")
    if result:
        lock.release()


class BetterEvent(Event):
    """
    :class:`.BetterEvent` (alias :attr:`.InvertibleEvent`) is a more flexible version of :class:`threading.Event`, which
    adds many new capabilities / features on top of :class:`threading.Event`:
    
     * The ``wait_on`` constructor parameter allows you to choose what flag states that the standard :meth:`.wait` will
       trigger upon:
       
        * ``'set'`` - the default - works like :class:`threading.Event`, :meth:`.wait` only triggers when the event is in
          the "set" state, i.e. :attr:`._flag` is ``True``
        * ``'clear'`` - opposite of the default - works opposite to :class:`threading.Event`, :meth:`.wait` only triggers when the event
          is in the "clear" state, i.e. :attr:`._flag` is ``False``
        * ``'both'`` - In the ``both`` setting, :meth:`.wait` will simply wait until :attr:`._flag` is changed, whether from
          ``set`` to ``clear``, or ``clear`` to ``set``.
          This wait_on setting only works as long as ``notify_set`` and ``notify_clear`` are set to ``True``
     
     * The ``default`` constructor parameter allows you to choose whether the event starts as "cleared" (``False`` - default), or
       "set" (``True``), which is useful when using some of the alternative ``wait_on`` settings.
     
     * New ``fail`` parameter for :meth:`.wait`, :meth:`.wait_set` and :meth:`.wait_clear` - when this is set to ``True``,
       the method will raise :class:`.EventWaitTimeout` when the timeout is hit, instead of just returning ``False``.
    
     * New :meth:`.wait_set` method, this works like the classic :class:`threading.Event` ``wait`` method - it's only triggered
       when :attr:`._flag` is set to ``True`` (set) - no matter what ``wait_on`` setting is active.
     
     * New :meth:`.wait_clear` method, this works opposite to the classic :class:`threading.Event` ``wait`` method - it's only triggered
       when :attr:`._flag` is set to ``False`` (cleared) - no matter what ``wait_on`` setting is active.
    
    
    **Example Usage**
    
    Below is a very simple thread class using :class:`.SafeLoopThread` which uses a :class:`.BetterEvent` so we can signal
    when it can start running, and when it's allowed to restart itself::
    
        >>> from privex.helpers import BetterEvent, SafeLoopThread
        >>>
        >>> class MyThread(SafeLoopThread):
        ...     def __init__(self, *args, trig, **kwargs):
        ...         self.trig = trig
        ...         super().__init__(*args, **kwargs)
        ...     def loop(self):
        ...         print("Waiting for trig to become set before doing stuff...")
        ...         self.trig.wait()   # Same behaviour as threading.Event.wait - waits for trig.set()
        ...         print("trig is set. doing stuff...")
        ...         print("finished doing stuff.")
        ...         print("Waiting for trig to become clear before restarting loop...")
        ...         self.trig.wait_clear()  # Unlike threading.Event, BetterEvent allows waiting for the "clear" signal
        ...
        >>> evt = BetterEvent(name='My Event')
        >>> t = MyThread(trig=evt)
        >>> t.start()
        Waiting for trig to become set before doing stuff...
        >>> evt.set()   # We flip evt (trig) to "set", which notifies MyThread it can proceed.
        trig is set. doing stuff...
        finished doing stuff.
        Waiting for trig to become clear before restarting loop...
        >>> evt.clear()  # Unlike threading.Event, we can "clear" the event, and MyThread will detect the "clear" signal instantly.
        Waiting for trig to become set before doing stuff...
        >>> evt.set()    # The loop restarted. Now we can flip trig back to "set"
        trig is set. doing stuff...
        finished doing stuff.
        Waiting for trig to become clear before restarting loop...
    
    
    """
    wait_on: str
    name: Optional[str]
    notify_set: bool
    notify_clear: bool
    
    _flag: bool
    _cond: threading.Condition
    
    def __init__(self, wait_on: str = 'set', name: str = None, default: bool = False, notify_set=True, notify_clear=True):
        """
        
        :param wait_on: ``set`` (default) - :meth:`.wait` triggers when event is "set". ``clear`` - :meth:`.wait` triggers when
                        event is "clear". ``both`` - :meth:`.wait` triggers when the event state flips from "set" to "clear" or vice versa.
        
        :param str name: An optional name to identify this event
        
        :param default: The default state of the event. Either ``False`` for "clear", or ``True`` for "set"
        
        :param notify_set: Whether to notify state listeners :meth:`.wait` :meth:`.wait_set` :meth:`.wait_clear`
                           when :meth:`.set` is called and the state changes from "clear" to "set"
                           
        :param notify_clear: Whether to notify state listeners :meth:`.wait` :meth:`.wait_set` :meth:`.wait_clear`
                             when :meth:`.clear` is called and the state changes from "set" to "clear"
        """
        super().__init__()
        self._cond = threading.Condition(Lock())
        self._flag = default
        self.name = name
        self.notify_set = notify_set
        self.notify_clear = notify_clear
        self.wait_on = wait_on.lower()
        if self.wait_on not in ['set', 'clear', 'both']:
            raise AttributeError("wait_on must be either 'set', 'clear' or 'both'")
        
    def set(self):
        with self._cond:
            if self._flag: return False
            self._flag = True
            if self.notify_set: self._cond.notify_all()
            return True

    def clear(self):
        with self._cond:
            if not self._flag: return False
            self._flag = False
            if self.notify_clear: self._cond.notify_all()
            return True
    
    def _fail_or_signal(self, signal, timeout, fail=False):
        if fail and not signal:
            raise EventWaitTimeout(f"Timed out after waiting {timeout} seconds for event signal (event: {self})")
        return signal
    
    def wait_set(self, timeout: Optional[float] = None, fail=False) -> bool:
        """Wait until :attr:`._flag` is ``True``"""
        timeout = None if timeout is None else float(timeout)
        with self._cond:
            signaled = self._flag
            if not signaled:
                signaled = self._cond.wait(timeout)
            return self._fail_or_signal(signaled, timeout, fail=fail)

    def wait_clear(self, timeout: Optional[float] = None, fail=False) -> bool:
        """Wait until :attr:`._flag` is ``False``"""
        timeout = None if timeout is None else float(timeout)
        with self._cond:
            flag, signaled = self._flag, True
            if flag:
                signaled = self._cond.wait(timeout)
            return self._fail_or_signal(signaled, timeout, fail=fail)

    def wait(self, timeout: Optional[Union[int, float]] = None, fail=False) -> bool:
        """
        Multi-purpose ``wait`` method which works similarly to :meth:`threading.Event.wait` but with some extra features.
        
        This method's behaviour will vary depending on what the :attr:`.wait_on` setting is set to:
        
        * ``'set'`` - the default - works like :class:`threading.Event`, :meth:`.wait` only triggers when the event is in
          the "set" state, i.e. :attr:`._flag` is ``True``
        
        * ``'clear'`` - opposite of the default - works opposite to :class:`threading.Event`, :meth:`.wait` only triggers when the event
          is in the "clear" state, i.e. :attr:`._flag` is ``False``
        
        * ``'both'`` - In the ``both`` setting, :meth:`.wait` will simply wait until :attr:`._flag` is changed, whether from
          ``set`` to ``clear``, or ``clear`` to ``set``.
          This wait_on setting only works as long as ``notify_set`` and ``notify_clear`` are set to ``True``
        
        :param bool fail: If ``True``, raise :class:`.EventWaitTimeout` if ``timeout`` was reached while waiting for the event to change.
        :param float timeout: Maximum amount of time to wait before giving up (``None`` to disable timeout)
        :return bool signal: This method returns the internal flag on exit, so it will always return
                             ``True`` except if a timeout is given and the operation times out.
        """
        timeout = None if timeout is None else float(timeout)
        with self._cond:
            flag, signaled = self._flag, True
            if self.wait_on == 'set' and not flag:
                signaled = self._cond.wait(timeout)
            if self.wait_on == 'clear' and flag:
                signaled = self._cond.wait(timeout)
            if self.wait_on == 'both':
                signaled = self._cond.wait(timeout)
            return self._fail_or_signal(signaled, timeout, fail=fail)
    
    def __str__(self):
        return f"<BetterEvent name='{self.name}' wait_on='{self.name}' status='{'set' if self._flag else 'clear'}' >"
    
    def __repr__(self):
        return self.__str__()


InvertibleEvent = BetterEvent


class StopperThread(threading.Thread):
    """
    A :class:`threading.Thread` thread sub-class which implements :class:`.BetterEvent` events allowing you to signal
    the thread when you want it to shutdown or pause.
    
    You must check :attr:`.should_stop` / :attr:`.should_run` and :attr:`.should_pause` within your thread run body
    to detect when your thread needs to shutdown / pause.
    """
    stop_events: List[threading.Event]
    
    def __init__(self, *args, default_stop=False, default_pause=False, stop_events=None, pause_events=None, **kwargs):
        stop_events = [] if stop_events is None else stop_events
        pause_events = [] if pause_events is None else pause_events
        self.ev_stop = BetterEvent(default=default_stop, name=f'{self.__class__.__name__} ev_stop')
        self.ev_pause = BetterEvent(default=default_pause, name=f'{self.__class__.__name__} ev_pause')
        self.stop_events = [self.ev_stop] + stop_events
        self.pause_events = [self.ev_pause] + pause_events
        super().__init__(*args, **kwargs)

    @property
    def should_pause(self) -> bool:
        return any([ev.is_set() for ev in self.pause_events])
    
    @property
    def should_stop(self) -> bool:
        return any([ev.is_set() for ev in self.stop_events])
    
    @property
    def should_run(self) -> bool:
        return not self.should_stop
    
    def emit_stop(self):
        return self.ev_stop.set()
    
    def emit_start(self):
        return self.ev_stop.clear()

    def emit_pause(self):
        return self.ev_pause.set()

    def emit_unpause(self):
        return self.ev_pause.clear()


class SafeLoopThread(StopperThread):
    loop_sleep: float = 0.1
    pause_sleep: float = 0.5
    
    def __init__(self, *args, default_stop=False, default_pause=False, **kwargs):
        """
        This is a simple loop thread class which uses :class:`.StopperThread` to allow an application to signal to the thread
        that it should shutdown or temporarily pause the loop.
        
        Note that if you have a long loop which takes a long time to run, you should regularly check :attr:`.should_stop`
        and :attr:`.should_pause` within your loop, so that the loop can shutdown or pause quickly when you request it to.
        
        Example usage::
        
            >>> # Create a sub-class of SafeLoopThread, and implement a loop() method
            >>> class MyThread(SafeLoopThread):
            ...     loop_sleep = 2    # 'run' will wait this many seconds between each run of your loop(). set to 0 to disable loop sleeps
            ...     def loop(self):
            ...         print("I'm looping!")
            ...
            >>> t = MyThread(default_pause=True)
            >>> t.start()
            >>> # No output because default_pause was set to True. To start the loop, we'll unpause it
            >>> t.emit_unpause()
            I'm looping!
            I'm looping!
            I'm looping!
            >>> t.emit_pause()
            >>> # We can re-pause the loop from our main thread, and the output stops again.
            >>> # If we unpause the thread again, we can also ask the thread to stop looping and shutdown using emit_stop
            >>> t.emit_unpause()
            I'm looping!
            I'm looping!
            >>> t.emit_stop()
            >>> t.is_alive()
            False
            >>> # Because we sent a STOP event, 'run' stopped looping, and returned.
            >>> # To be able to start the same thread object again, we'd need to clear the STOP event first
            >>> t.emit_start()  # Clear the STOP event we set with emit_stop
            >>> t.start()       # Start the thread again
            I'm looping!
            I'm looping!
        
        
        :param args:
        :param default_stop:  If ``True``, will trigger the event :attr:`.ev_stop` in the constructor, which will prevent the thread
                              from being able to start until :attr:`.ev_stop` is cleared e.g. via :meth:`.emit_start`
        :param default_pause:  If ``True``, will trigger the event :attr:`.ev_pause` in the constructor, which will cause 'run'
                              to wait until :attr:`.ev_pause` is cleared e.g. via :meth:`.emit_unpause` before starting the loop
        :param kwargs:
        :key List[Union[Event,BetterEvent]] stop_events: Additional :class:`.Event` or :class:`.BetterEvent` 's which when set, will
                                                         cause :attr:`.should_stop` to become True.
        :key List[Union[Event,BetterEvent]] pause_events: Additional :class:`.Event` or :class:`.BetterEvent` 's which when set, will
                                                          cause :attr:`.should_pause` to become True.
        """
        self.in_queue = queue.Queue()
        self.out_queue = queue.Queue()
        super().__init__(*args, default_stop=default_stop, default_pause=default_pause, **kwargs)
    
    def loop(self):
        raise NotImplemented("child must implement .loop")
    
    def run(self) -> None:
        log.debug(" [%s] Starting loop thread: %s", self.name, self.__class__.__name__)
        while self.should_run:
            if self.should_pause:
                log.debug(" [%s] should_pause is True. Pausing loop until should_pause is cleared.", self.name, self.__class__.__name__)
                while self.should_pause:
                    time.sleep(self.pause_sleep if self.pause_sleep > 0 else 0.5)

            log.debug(" [%s] Running: %s.loop()", self.name, self.__class__.__name__)
            self.loop()
            if self.loop_sleep > 0:
                time.sleep(self.loop_sleep)
        
        return log.debug(" [%s] Finished loop thread %s", self.name, self.__class__.__name__)


_evt_btevt = Union[BetterEvent, Event]

_bl_list_btevt = Optional[Union[bool, List[_evt_btevt]]]


def event_multi_wait(*events: _evt_btevt, trigger='and', event_sleep=0.5, wait_timeout=None, fail=True, **kwargs) -> _bl_list_btevt:
    """
    Wait for multiple :class:`threading.Event` or :class:`.BetterEvent` 's to become "set", or "clear".
    
    For standard :class:`threading.Event` 's - only "set" can be waited on. You must use :class:`.BetterEvent` (generally
    works as a drop-in replacement) to be able to use the ``invert`` or ``invert_indexes`` options.
    
    Basic example::
    
        >>> do_something_else = Event()
        >>> stop_running = Event()
        >>>
        >>> def some_thread():
        ...     # do some stuff...
        ...     # now we wait for further instructions, until either do_something_else or stop_running is signalled:
        ...     event_multi_wait(do_something_else, stop_running, trigger='any')
        ...     if stop_running.is_set(): return False
        ...     if do_something_else.is_set():
        ...         # do something else.


    :param Event|BetterEvent events:    Multiple :class:`threading.Event` references to be waited on.

    :param str trigger:                 To return when ALL events are set, specify one of ``and|all|every``, while to return when ANY
                                        of the specified events are set, specify one of ``or|any|either``

    :param float|int event_sleep:       The maximum amount of time per event check iteration. This is divided by the amount of events
                                        which were passed, so we can use the highly efficient ``event.wait()`` method.

    :param float|int wait_timeout:      The maximum amount of time (in seconds) to wait for all/any of the ``events`` to signal.
                                        Set to ``None`` to disable wait timeout. When timing out, raises :class:`.EventWaitTimeout`
                                        if ``fail=True``, otherwise simply returns ``None``.

    :param bool fail:       When wait_timeout is hit, will raise :class:`.EventWaitTimeout` if ``fail=True``, otherwise
                            will simply return ``None``.
    
    :param kwargs:          Additional settings
    
    :key bool invert:       (Default: ``False``) Wait for ``events`` to become "clear" (``False``). NOTE: This only
                            works with :class:`.BetterEvent` events.
    
    :key list invert_indexes: Wait for the events at these indexes to become "clear" instead of "set".
                              If ``invert`` is set to ``True``, then we'll wait for these indexes to become "set" instead of "clear".
                              NOTE: This only works with :class:`.BetterEvent` events.
    :return bool success:   ``True`` if ``events`` met the ``trigger``, otherwise ``None``
    :return List[_evt_btevt] events: If :class:`.BetterEvents` are passed, and ``trigger`` is "any", then a list of the events
                                     which were set (or if ``invert`` is ``True``, then events that weren't set.
                              
    """
    # Returns True if an event is set the correct direction depending on invert mode and invert_indexes
    def _filter_event(evt: Union[Event, BetterEvent], index: int) -> bool:
        if invert:   # invert mode - "set" = False, "clear" = True (opposite if index in invert_indexes)
            return evt.is_set() if index in invert_indexes else not evt.is_set()
        elif index in invert_indexes:  # normal mode (in invert_indexes) - "set" = False, "clear" = True
            return not evt.is_set()
        else:  # normal mode - "set" = True, "clear" = False
            return evt.is_set()
    
    # Handles deciding whether to use .wait or .wait_clear depending on invert mode and invert_indexes
    def _wait_event(evt: Union[Event, BetterEvent], index: int):
        if invert:
            if index in invert_indexes:  # In invert mode, we wait for events in invert_indexes to be "set"
                evt.wait(sleep_ev)
            else:  # In invert mode, we wait for events to be "clear" when not in invert_indexes
                evt.wait_clear(sleep_ev)
        elif index in invert_indexes:  # In normal mode, we wait for events in invert_indexes to be "clear"
            evt.wait_clear(sleep_ev)
        else:  # If we're not in invert mode, and the event isn't in invert_indexes, then we just use normal .wait()
            evt.wait(sleep_ev)
    
    if len(events) < 1:
        raise AttributeError("event_multi_wait expects one or more events passed as positional arguments...")
    
    invert = kwargs.get('invert', kwargs.get('inverted', False))
    invert_indexes: List[_evt_btevt] = kwargs.get('invert_indexes', kwargs.get('invert_idx', []))
    
    is_better_events = all([isinstance(v, BetterEvent) for v in events])
    if invert and not is_better_events:
        raise AttributeError("You specified invert=True or invert_indexes but one or more passed events are not BetterEvent classes.")
    
    all_is_set = lambda: [_filter_event(evt=v, index=i) for i, v in enumerate(events)]
    event_sleep = float(event_sleep)
    wait_timeout = None if wait_timeout is None else float(wait_timeout)
    
    start_time = datetime.utcnow()
    sleep_ev = event_sleep / len(events)
    if trigger.lower() in ['and', 'all', 'every']:
        while not all(all_is_set()):
            if wait_timeout is not None and (datetime.utcnow() - start_time).total_seconds() > wait_timeout:
                if fail:
                    raise EventWaitTimeout(f"Waited {wait_timeout} seconds for all {len(events)} Event's to signal. Giving up.")
                return None
            for idx, ev in enumerate(events):
                _wait_event(evt=ev, index=idx)
        return True
    
    if trigger.lower() in ['or', 'any', 'either']:
        while not any(all_is_set()):
            if wait_timeout is not None and (datetime.utcnow() - start_time).total_seconds() > wait_timeout:
                if fail:
                    raise EventWaitTimeout(f"Waited {wait_timeout} seconds for any of the {len(events)} Event's to signal. Giving up.")
                return None
            for idx, ev in enumerate(events):
                _wait_event(evt=ev, index=idx)
        
        if is_better_events:
            return [v for i, v in enumerate(events) if _filter_event(evt=v, index=i)]
        return True
    
    raise AttributeError("event_multi_wait expects 'trigger' to be one of: ['and', 'all', 'every', 'or', 'any', 'either']")


def event_multi_wait_all(*events: _evt_btevt, event_sleep=0.5, wait_timeout=None, fail=True, **kwargs) -> bool:
    """
    Wrapper function for :meth:`.event_wait_many` with ``trigger`` defaulting to ``and`` (return when ALL events are triggered)
    """
    return event_multi_wait(*events, trigger='and', event_sleep=event_sleep, wait_timeout=wait_timeout, fail=fail, **kwargs)


def event_multi_wait_any(*events: _evt_btevt, event_sleep=0.5, wait_timeout=None, fail=True, **kwargs) -> bool:
    """
    Wrapper function for :meth:`.event_wait_many` with ``trigger`` defaulting to ``or`` (return when ANY event triggers)
    """
    return event_multi_wait(*events, trigger='or', event_sleep=event_sleep, wait_timeout=wait_timeout, fail=fail, **kwargs)
