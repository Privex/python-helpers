import asyncio
import inspect
from typing import Union, Coroutine, Type, Callable

from privex import helpers
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
