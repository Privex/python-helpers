from time import sleep
from typing import List, Union, Dict

from privex.loghelper import LogHelper

from tests.base import PrivexBaseCase
from privex.helpers import thread as modthread, LockConflict, random_str, OrderedDictObject
from privex.helpers.thread import BetterEvent, event_multi_wait_all, event_multi_wait_any, lock_acquire_timeout, SafeLoopThread
from collections import namedtuple
from threading import Event, Lock
import threading
import queue

import logging

LOG_FORMATTER = logging.Formatter('[%(asctime)s]: %(name)-25s -> %(funcName)-35s : %(levelname)-8s:: %(message)s')
_lh = LogHelper(__name__, handler_level=logging.DEBUG, formatter=LOG_FORMATTER)
_lh.add_console_handler()
_lh.copy_logger('privex.helpers.thread')

log = logging.getLogger(__name__)

# release_lock = BetterEvent(name='Global Release Lock event')
shared_lock = threading.Lock()
shared_queue = queue.Queue()

stop_threads = BetterEvent(name='Global stop_threads')
            
LockCheck = namedtuple('LockCheck', 'thread_id was_locked lock_exception thread_name')
UnlockEvent = namedtuple('UnlockEvent', 'thread_id thread_name')


class LockerThread(SafeLoopThread):
    loop_sleep = 0.05
    
    def __init__(self, lock: threading.Lock, timeout=2, fail=True, hold_lock_start=True, **kwargs):
        kwargs = dict(kwargs)
        # Arguments passed to lock_acquire_timeout
        self.lock = lock
        self.timeout = timeout
        self.fail = fail
        
        # Amount of time to wait between each `release_lock` check after the lock is acquired.
        # self.lock_hold_sleep = kwargs.get('lock_hold_sleep', 0.2)
        # When the release_lock is in the SET position, the thread will hold the lock until release_lock is cleared.
        self.release_lock = BetterEvent(name='Release Lock')
        if not hold_lock_start:
            log.info("hold_lock_start is False. Triggering event self.release_lock (do not hold lock)")
            self.release_lock.set()
        
        self.event_change_lock = Lock()
        self.pause_if_locked = kwargs.pop('pause_if_locked', True)
        
        super().__init__(stop_events=[stop_threads], **kwargs)
    
    @property
    def should_lock(self):
        return not self.release_lock.is_set()
    
    def emit_lock(self, event_lock_timeout=None):
        with lock_acquire_timeout(self.event_change_lock, event_lock_timeout, fail=True, block=event_lock_timeout is not None):
            return self.release_lock.clear()

    def emit_unlock(self, event_lock_timeout=None):
        with lock_acquire_timeout(self.event_change_lock, event_lock_timeout, fail=True, block=event_lock_timeout is not None):
            return self.release_lock.set()
    
    def loop(self):
        if not self.should_lock:
            log.debug(f" [{self.name}] Waiting for release_lock event to be cleared...")
            ev_trig = event_multi_wait_any(self.release_lock, *self.stop_events, invert_idx=[0], wait_timeout=20)
            return log.debug(f" [{self.name}] Finished waiting due to events: {ev_trig}")
        
        log.info(f" [{self.name}] Acquiring lock: %s", self.lock)
        try:
            with modthread.lock_acquire_timeout(self.lock, self.timeout, fail=self.fail) as locked:
                if not locked:
                    log.debug(f" [{self.name}] did not acquire lock. not waiting to hold lock open.")
                    if self.pause_if_locked:
                        log.debug(f" [{self.name}] pause_if_locked is True. setting release_lock to pause lock acquisition attempts.")
                        try:
                            self.emit_unlock()
                        except LockConflict:
                            log.debug(f" [{self.name}] got lock conflict while setting release_lock...")
                
                self.out_queue.put(LockCheck(self.ident, locked, lock_exception=None, thread_name=self.name))
                if not locked:
                    return log.debug(f" [{self.name}] lock not acquired, returning loop...")
                log.debug(f" [{self.name}] waiting until release_lock or any event in stop_events is triggered...")
                ev_trig = event_multi_wait_any(self.release_lock, *self.stop_events)
                log.debug(f" [{self.name}] finished waiting to release lock due to events: {ev_trig}")

                if locked:
                    log.debug(f" [{self.name}] release_lock released or thread stop event fired. releasing previously acquired lock.")
                was_locked = bool(locked)
            log.debug(f" [{self.name}] finished lock_acquire_timeout context manager block. lock will be released if we held it...")
            if was_locked:
                self.out_queue.put(UnlockEvent(self.ident, self.name))
        except LockConflict as e:
            log.debug(f" [{self.name}] Lock conflict / timeout exception was raised: %s %s", type(e), str(e))
            self.out_queue.put(LockCheck(self.ident, None, e, thread_name=self.name))
        except Exception as e:
            log.exception(f" [{self.name}] Exception raised while acquiring lock: %s %s", type(e), str(e))
            self.out_queue.put(LockCheck(self.ident, None, e, thread_name=self.name))
        

ThreadTypes = Union[threading.Thread, LockerThread]


class TestThreading(PrivexBaseCase):
    """Test cases for :mod:`privex.helpers.thread` functions/classes"""
    threads: Union[OrderedDictObject, Dict[str, ThreadTypes]] = OrderedDictObject()
    
    def tearDown(self) -> None:
        if len(self.threads) > 0:
            stop_threads.set()
            sleep(0.3)
            thread_keys = list(self.threads.keys())
            for name in thread_keys:
                t = self.threads[name]
                if not t.is_alive():
                    log.debug("Thread '%s' is dead. Removing from thread dict...", name)
                    del self.threads[name]
                    continue
                log.debug("Thread '%s' is still alive. Joining and waiting for it to shutdown...", name)
                if hasattr(t, 'emit_stop'):
                    log.debug("Thread '%s' has emit_stop method. Calling emit_stop before joining.", name)
                    t.emit_stop()
                t.join(3)
                log.debug("Removing stopped thread %s", name)
                del self.threads[name]
                log.debug("Successfully removed stopped thread %s", name)
        
        # Reset global event thread signals to their default, empty queues, and release any leftover locks.
        # if release_lock.is_set(): release_lock.clear()
        if shared_lock.locked(): shared_lock.release()
        while not shared_queue.empty():
            shared_queue.get_nowait()
        if stop_threads.is_set(): stop_threads.clear()

    @classmethod
    def _mk_locker(cls, lock: threading.Lock, timeout=2, fail=True, hold_lock_start=False, name=None, **kwargs) -> LockerThread:
        """
        
        :param threading.Lock lock:
        :param int|float timeout:
        :param bool fail:
        :param bool hold_lock_start:
        :param str name:
        :param kwargs:
        :return:
        """
        auto_start = kwargs.pop('auto_start', True)
        name = random_str(8) if name is None else name
        t = LockerThread(lock, timeout=timeout, fail=fail, hold_lock_start=hold_lock_start, **kwargs)
        t.name = name
        t.daemon = kwargs.pop('daemon', False)
        if auto_start:
            t.start()
        cls.threads[name] = t
        return t
    
    @staticmethod
    def _cleanup_lockers(*lockers: LockerThread):
        for l in lockers:
            l.emit_unlock()     # Release any lock they might be holding
            l.emit_stop()       # Stop the locker thread
            if l.is_alive():    # Join the thread if it's alive so that it can shutdown correctly.
                l.join(1)
    
    def test_lock_acquire_timeout_basic(self):
        # First we test that we can successfully acquire an unlocked lock
        t1 = self._mk_locker(shared_lock, timeout=2, fail=False, name="acquire_lock_timeout_t1")
        self.assertFalse(shared_lock.locked())
        self.assertTrue(t1.emit_lock(), msg="emit_lock should've returned True to acknowledge release_lock flipping")
        # Check the LockCheck result from the thread queue
        res: LockCheck = t1.out_queue.get(block=True, timeout=2)
        self.assertTrue(res.was_locked)
        self.assertTrue(shared_lock.locked())
        self.assertIsNone(res.lock_exception)
        self.assertEqual(res.thread_name, "acquire_lock_timeout_t1")
        
        # Ask t1 to release the lock
        t1.emit_unlock()
        res: UnlockEvent = t1.out_queue.get(block=True, timeout=2)
        self.assertEqual(res.thread_name, 'acquire_lock_timeout_t1')
        self.assertFalse(shared_lock.locked())
        # Stop t1
        t1.emit_stop()
        t1.join(1)

    def test_lock_acquire_timeout_timed_out(self):
        self.assertFalse(shared_lock.locked())
        # First we acquire a lock using our first thread
        log.debug(" >>> thread 1 acquire")
        t1 = self._mk_locker(shared_lock, timeout=4, fail=False, name="timeout_t1")
        t1.emit_lock()
        sleep(0.2)
        self.assertTrue(shared_lock.locked())       # Confirm our lock is locked
        # Now we try and acquire the lock with a second thread
        log.debug(" >>> thread 2 acquire (test lock timeout fail)")
        t2 = self._mk_locker(shared_lock, timeout=2, fail=False, name="timeout_t2")
        t2.emit_lock()
        # Confirm that t2 failed to get the lock
        res: LockCheck = t2.out_queue.get(block=True, timeout=4)
        self.assertFalse(res.was_locked)
        self.assertTrue(shared_lock.locked())
        self.assertIsNone(res.lock_exception)
        # Now we'll ask t2 to try and get the lock again, wait 200ms and release the lock
        log.debug(" >>> thread 2 acquiring (unlocking thread 1)")
        t2.emit_lock()
        sleep(0.2)
        log.debug(" >>> thread 1 unlocking")
        t1.emit_unlock()
        # If the lock wait timeout was being acknowledged, t2 should now have the lock.
        log.debug(" >>> get thread 2 out_queue")
        res: LockCheck = t2.out_queue.get(block=True, timeout=4)
        self.assertTrue(res.was_locked)
        self.assertTrue(shared_lock.locked())
        # Now we'll release the lock and confirm the lock is unlocked again
        log.debug(" >>> thread 2 unlock")
        t2.emit_unlock()
        res: UnlockEvent = t2.out_queue.get(block=True, timeout=4)
        self.assertEqual(res.thread_name, 'timeout_t2')
        self.assertFalse(shared_lock.locked())
        log.debug(" >>> cleanup")
        # If we got this far - everything is fine :) - stop the threads and cleanup
        self._cleanup_lockers(t1, t2)
        
        
        


