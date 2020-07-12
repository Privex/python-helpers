import asyncio
import inspect
from time import sleep
from typing import Union, Coroutine, Type, Callable

from privex import helpers
from privex.helpers import r_cache_async, get_async_type
from privex.helpers.exceptions import PrivexException
from tests import PrivexBaseCase
import logging

log = logging.getLogger(__name__)


async def f_await(coro: Union[Coroutine, Type[Coroutine], Callable], *args, **kwargs):
    """
    Small async function which ``await``'s passed co-routines for testing purposes. Primarily intended to
    be ran via synchronous async helper functions e.g. :func:`.loop_run` or :func:`.run_sync`.
    
    Example usage::
    
        >>> from privex.helpers import loop_run
        >>> async def some_func(x, y): return x + y
        >>> # Example: Running f_await via loop_run synchronously, while f_await natively async `await`'s some_func
        >>> loop_run(f_await(some_func(5, 10)))
        15
        >>> loop_run(f_await(some_func, 2, 5))
        7
    
    If ``coro`` is an async function or standard callable, then it will try to un-nest the coroutine by calling ``coro``,
    and calling the returned result if it's also an async function / callable.
    
    Helps ensure any decorator function  wrapping (e.g. :func:`.awaitable`) is properly unwrapped.
    """
    if asyncio.iscoroutinefunction(coro) or callable(coro):
        coro = coro(*args, **kwargs)
        if asyncio.iscoroutinefunction(coro) or callable(coro):
            coro = coro(*args, **kwargs)
    
    if asyncio.iscoroutine(coro):
        res = await coro
    elif type(coro) in [str, bytes, int] or isinstance(coro, (list, dict, tuple,)):
        log.error("WARNING: f_await was passed a non-coroutine object (type: %s). Object value: %s", type(coro), coro)
        return coro
    else:
        raise AttributeError(f"f_await failed to detect type for '{type(coro)}' object...")
    return res


class TestAsyncX(PrivexBaseCase):
    """Test cases related to the :mod:`privex.helpers.asyncx` module"""

    async def _tst_async(self, a, b):
        """Basic async function used for testing async code"""
        return a * 2, b * 3

    def _tst_sync(self, a, b):
        """Basic sync function used for testing sync code"""
        return a * 2, b * 3

    def test_run_sync(self):
        """Test helpers.async.run_sync by running an async function from this synchronous test"""
        x, y = helpers.run_sync(self._tst_async, 5, 10)
        d, e = helpers.run_sync(self._tst_async, 1, 2)
        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)

    @helpers.async_sync
    def test_async_decorator(self):
        """Test the async_sync decorator by wrapping this unit test"""
    
        x, y = yield from self._tst_async(5, 10)
        d, e = yield from self._tst_async(1, 2)
    
        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)

    def test_async_decorator_return(self):
        """Test the async_sync decorator handles returning async data from synchronous function"""
    
        async_func = self._tst_async
    
        @helpers.async_sync
        def non_async(a, b):
            f, g = yield from async_func(a, b)
            return f, g
    
        x, y = non_async(5, 10)
        d, e = non_async(1, 2)
    
        self.assertEqual(x, 10)
        self.assertEqual(y, 30)
        self.assertEqual(d, 2)
        self.assertEqual(e, 6)
    
    def test_awaitable(self):
        """Test that :func:`.awaitable` allows us to run an async function synchronously, without breaking async await"""
        async def example_func_async(a, b): return a + b
        
        @helpers.awaitable
        def example_func(a, b): return example_func_async(a, b)
        
        async def call_example_async():
            return await example_func("hello", " world")
        
        self.assertEqual(helpers.run_sync(call_example_async), "hello world")
        self.assertEqual(example_func("hello", " world"), "hello world")

    def test_awaitable_class(self):
        """Test :func:`.awaitable_class` converts a class - allowing async functions to be called synchronously"""
        class ExampleAsyncCls:
            async def example_async(self): return "hello world"

            def example_sync(self): return "hello world"
        
        wrapped_cls = helpers.awaitable_class(ExampleAsyncCls)
        
        self.assertEqual(ExampleAsyncCls.__name__, wrapped_cls.__name__)
        self.assertEqual(ExampleAsyncCls.__qualname__, wrapped_cls.__qualname__)
        self.assertEqual(ExampleAsyncCls.__module__, wrapped_cls.__module__)
        
        exm_inst = ExampleAsyncCls()
        wrp_inst = wrapped_cls()
        
        self.assertEqual(exm_inst.example_sync(), 'hello world')
        # Confirm that ExampleAsyncCls.example_async returns a coroutine, and await it using loop_run + f_await
        exm_async = exm_inst.example_async()
        self.assertTrue(inspect.iscoroutine(exm_async))
        self.assertEqual(helpers.loop_run(f_await(exm_async)), 'hello world')

        self.assertEqual(wrp_inst.example_sync(), 'hello world')
        # Confirm on the wrapped class that example_async() can be ran synchronously
        self.assertEqual(wrp_inst.example_async(), 'hello world')
        # Confirm that example_async() still returns a coroutine when called from an async context,
        # then await it using loop_run + f_await
        self.assertEqual(helpers.loop_run(f_await(wrp_inst.example_async)), 'hello world')

    def test_awaitable_class_decorator(self):
        @helpers.awaitable_class
        class ExampleAsyncCls:
            async def example_async(self): return "hello world"
        
            def example_sync(self): return "hello world"

        wrp_inst = ExampleAsyncCls()

        # Confirm both example_sync and example_async work synchronously and return correct data
        self.assertEqual(wrp_inst.example_sync(), 'hello world')
        self.assertEqual(wrp_inst.example_async(), 'hello world')

        # Call example_async() from f_await (a proper async context)
        async_coro = f_await(wrp_inst.example_async)
        self.assertEqual(helpers.loop_run(async_coro), 'hello world')

    def test_awaitable_mixin(self):
        """Test :class:`.AwaitableMixin` when sub-classed enables async methods to be called synchronously"""
        class ExampleAsyncCls(helpers.AwaitableMixin):
            async def example_async(self):
                return "hello world"
        
            def example_sync(self):
                return "hello world"

        wrp_inst = ExampleAsyncCls()
        
        # Confirm both example_sync and example_async work synchronously and return correct data
        self.assertEqual(wrp_inst.example_sync(), 'hello world')
        self.assertEqual(wrp_inst.example_async(), 'hello world')
        
        # Call example_async() from f_await (a proper async context)
        async_coro = f_await(wrp_inst.example_async)
        self.assertEqual(helpers.loop_run(async_coro), 'hello world')

    def test_async_aobject(self):
        """Test :class:`.aobject` sub-classes with async constructors can be constructed and used correctly"""
        class ExampleAsyncObject(helpers.aobject):
            async def _init(self):
                self.example = await self.get_example()
            
            async def get_example(self):
                return "hello world"

            __init__ = _init
        
        async def setup_async_object():
            # noinspection PyUnresolvedReferences
            o = await ExampleAsyncObject()
            return o.example
        
        self.assertEqual(helpers.run_sync(setup_async_object), "hello world")

    def test_async_cache(self):
        """Test :func:`.r_cache_async` with an async function"""
        @r_cache_async('privex_tests:some_func', cache_time=2)
        async def some_func(some: int, args: int = 2):
            return some + args

        self.assertEqual(helpers.run_sync(some_func, 5, 10), 15)
        self.assertEqual(helpers.run_sync(some_func, 10, 20), 15)
        sleep(2)
        self.assertEqual(helpers.run_sync(some_func, 10, 30), 40)

    def test_async_cache_key(self):
        """Test :func:`.r_cache_async` with an async function and async cache key"""

        async def mk_key(some: int, *args, **kwargs):
            return f'privex_tests:some_func:{some}'

        @r_cache_async(mk_key, cache_time=2)
        async def some_func(some: int, args: int = 2):
            return some + args
    
        # We cache based on the first argument. If we pass 5,10 and 5,20 then 5,20 should get the cached 5,10 result.
        self.assertEqual(helpers.run_sync(some_func, 5, 10), 15)
        self.assertEqual(helpers.run_sync(some_func, 5, 20), 15)
        # But 10,20 should get an up to date result.
        self.assertEqual(helpers.run_sync(some_func, 10, 20), 30)
        sleep(2)
        # Confirm the cache key for some=5 expired by calling with 5,30
        self.assertEqual(helpers.run_sync(some_func, 5, 30), 35)
    
    def test_async_type_corofunc(self):
        """Test :func`._tst_async` with a async function reference"""
        self.assertEqual(get_async_type(self._tst_async), 'coro func')

    def test_async_type_coro(self):
        """Test :func`._tst_async` with a coroutine (called async function) reference"""
        a = self._tst_async(1, 2)
        self.assertEqual(get_async_type(a), 'coro')
        # close the coroutine just to avoid "never awaited" warnings :)
        a.close()

    def test_async_type_syncfunc(self):
        """Test :func`._tst_async` with a standard synchronous function reference"""
        self.assertEqual(get_async_type(self._tst_sync), 'sync func')

    def test_async_type_unknown(self):
        """Test :func`._tst_async` with an integer reference"""
        self.assertEqual(get_async_type(self._tst_sync(1, 2)), 'unknown')


class TestAsyncXThread(PrivexBaseCase):
    """Test cases for thread-related functions/classes in the :mod:`privex.helpers.asyncx` module"""
    def test_run_coro_thread(self):
        """
        Test :func:`.run_coro_thread` basic functionality - run an AsyncIO function with positional args, kwargs, plus a mixture
        of positional/kw args, and validate the returned data matches the expected output given the arguments that were passed.
        """
    
        async def example_func(lorem: int, ipsum: int):
            return f"example - number: {lorem + ipsum}"
        
        # Test running example_func with positional arguments
        self.assertEqual(helpers.run_coro_thread(example_func, 10, 15), "example - number: 25")
        # Test running example_func with keyword arguments
        self.assertEqual(helpers.run_coro_thread(example_func, lorem=120, ipsum=500), "example - number: 620")
        # Test running example_func with a mixture of positional and keyword arguments
        self.assertEqual(helpers.run_coro_thread(example_func, 420, ipsum=600), "example - number: 1020")

    def test_run_coro_thread_exception(self):
        """Test that :func:`.run_coro_thread` raises exceptions when the async coroutine thread emits one via the queue"""
        async def another_func(lorem: int, ipsum: int):
            if lorem > 100: raise PrivexException('lorem over 100')
            if ipsum > 100: raise AttributeError('ipsum over 100')
            return lorem + ipsum

        self.assertEqual(helpers.run_coro_thread(another_func, 30, 12), 42)
        self.assertEqual(helpers.run_coro_thread(another_func, 50, ipsum=15), 65)
        with self.assertRaisesRegex(PrivexException, 'lorem over 100'):
            helpers.run_coro_thread(another_func, 500, 12)
        with self.assertRaisesRegex(AttributeError, 'ipsum over 100'):
            helpers.run_coro_thread(another_func, 5, 900)


