"""
General test cases for various un-categorized functions / classes e.g. :py:func:`.chunked` and :py:func:`.inject_items`

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )

    Permission is hereby granted, free of charge, to any person obtaining a copy of
    this software and associated documentation files (the "Software"), to deal in
    the Software without restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
    Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
    PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
    OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import inspect
from typing import Union

from privex import helpers
from tests.base import PrivexBaseCase


class TestGeneral(PrivexBaseCase):
    """General test cases that don't fit under a specific category"""
    
    def setUp(self):
        self.tries = 0
    
    def test_chunked(self):
        """Create a 20 element long list, split it into 4 chunks, and verify the chunks are correctly made"""
        x = list(range(0, 20))
        c = list(helpers.chunked(x, 4))
        self.assertEqual(len(c), 4)
        self.assertEqual(c[0], [0, 1, 2, 3, 4])
        self.assertEqual(c[1], [5, 6, 7, 8, 9])

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
    
    def test_retry_on_err(self):
        """Test that the :class:`helpers.retry_on_err` decorator retries a function 3 times as expected"""
        
        @helpers.retry_on_err(max_retries=3, delay=0.2)
        def retry_func(cls):
            cls.tries += 1
            raise Exception
        
        with self.assertRaises(Exception):
            retry_func(self)
        
        # The first run should cause tries = 1, then after 3 re-tries it should reach 4 tries in total.
        self.assertEqual(self.tries, 4)

    def test_retry_on_err_return(self):
        """Test that the :class:`helpers.retry_on_err` decorator can return correctly after some retries"""
    
        @helpers.retry_on_err(max_retries=3, delay=0.2)
        def retry_func(cls):
            if cls.tries < 3:
                cls.tries += 1
                raise Exception
            return 'success'
        
        ret = retry_func(self)
    
        # retry_func stops raising exceptions after the 2nd retry (try 3), thus 3 tries in total
        self.assertEqual(self.tries, 3)
        self.assertEqual(ret, 'success')
    
    def test_inject_items(self):
        """Test :py:func:`.inject_items` injecting into a list after position 1"""
        a = ['a', 'b', 'g']
        b = ['c', 'd', 'e', 'f']
        # Position 1 is the 2nd element of ``a`` - which is the letter 'b'
        c = helpers.inject_items(b, a, 1)
        self.assertListEqual(c, ['a', 'b', 'c', 'd', 'e', 'f', 'g'])

    def test_inject_items_2(self):
        """Test :py:func:`.inject_items` injecting into a list after position 3"""
        a = ['a', 'b', 'c', 'd', 'h']
        b = ['e', 'f', 'g']
        # Position 3 is the 4th element of ``a`` - which is the letter 'd'
        c = helpers.inject_items(b, a, 3)
        self.assertListEqual(c, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])

    def test_human_name_str_bytes(self):
        """Test :py:func:`.human_name` with string and bytes names"""
        self.assertEqual(helpers.human_name('example_function'), 'Example Function')
        self.assertEqual(helpers.human_name('ExampleClass'), 'Example Class')
        self.assertEqual(helpers.human_name('longerExample_class'), 'Longer Example Class')

        self.assertEqual(helpers.human_name(b'example_function'), 'Example Function')
        self.assertEqual(helpers.human_name(b'ExampleClass'), 'Example Class')
        self.assertEqual(helpers.human_name(b'longerExample_class'), 'Longer Example Class')
    
    def test_human_name_func(self):
        """Test :py:func:`.human_name` with function references"""
    
        def example_function():
            pass
        
        def anotherExampleFunction():
            pass
        
        self.assertEqual(helpers.human_name(example_function), 'Example Function')
        self.assertEqual(helpers.human_name(anotherExampleFunction), 'Another Example Function')

    def test_human_name_class(self):
        """Test :py:func:`.human_name` with class references and class instances"""
        
        class ExampleClass:
            pass
        
        class _AnotherExample:
            pass
        
        class Testing_class:
            pass

        # Direct class reference
        self.assertEqual(helpers.human_name(ExampleClass), 'Example Class')
        self.assertEqual(helpers.human_name(_AnotherExample), 'Another Example')
        self.assertEqual(helpers.human_name(Testing_class), 'Testing Class')

        # Class instances
        self.assertEqual(helpers.human_name(ExampleClass()), 'Example Class')
        self.assertEqual(helpers.human_name(_AnotherExample()), 'Another Example')
        self.assertEqual(helpers.human_name(Testing_class()), 'Testing Class')


Mocker = helpers.Mocker
mock_decorator = helpers.mock_decorator


class TestMocker(PrivexBaseCase):
    def test_mocker_attributes(self):
        """Set an attribute on a Mocker instance and confirm we can retrieve it again"""
        m = Mocker()
        m.example = 'hello'
        self.assertEqual(m.example, 'hello')
        m.other_example = 12345
        self.assertEqual(m.other_example, 12345)

    def test_mocker_items(self):
        """Set an item on a Mocker instance and confirm we can retrieve it again"""
        m = Mocker()
        m['example'] = 'hello'
        self.assertEqual(m['example'], 'hello')
        m['other_example'] = 12345
        self.assertEqual(m['other_example'], 12345)
    
    def test_mocker_items_attributes_equiv(self):
        """Set an attribute and item on a Mocker instance and confirm both can be accessed as items or attributes"""
        m = Mocker()
        m.example = 'hello'
        m['other_example'] = 12345
        self.assertEqual(m.example, 'hello')
        self.assertEqual(m.other_example, 12345)
        self.assertEqual(m['example'], 'hello')
        self.assertEqual(m['other_example'], 12345)
    
    def _check_inst_name(self, inst: Mocker, name: str):
        """Helper method - check the class ``__name__`` + ``__qualname__`` and instance ``__name__`` match ``name``"""
        self.assertEqual(inst.__class__.__name__, name)
        self.assertEqual(inst.__class__.__qualname__, name)
        self.assertEqual(inst.__name__, name)

    def _check_inst_mod(self, inst: Mocker, name: str):
        """Helper method - check the class ``__module__`` and instance ``__module__`` match ``name``"""
        self.assertEqual(inst.__module__, name)
        self.assertEqual(inst.__class__.__module__, name)
    
    def test_mocker_make_class(self):
        """Create a "disguised" Mocker class and confirm the class name is correct"""
        test_fake = Mocker.make_mock_class('TestFake')
        self._check_inst_name(test_fake, 'TestFake')
        self.assertIn('TestFake object', str(test_fake))

    def test_mocker_make_class_not_instance(self):
        """Create a "disguised" Mocker class with instance=False and confirm it's a class, not an instance"""
        # Get the raw class for TestFakeCls, not an instance
        test_fake_cls = Mocker.make_mock_class('TestFakeCls', instance=False)
        # Confirm it's definitely a class, not some sort-of instance
        self.assertTrue(inspect.isclass(test_fake_cls))
        
        # Now we initialise it, and confirm the instance is correct, just like test_mocker_make_class
        test_fake = test_fake_cls()
        self.assertTrue(isinstance(test_fake, test_fake_cls))
        self._check_inst_name(test_fake, 'TestFakeCls')
        self.assertIn('TestFakeCls object', str(test_fake))

    def test_mocker_make_class_module(self):
        """Create a "disguised" Mocker class with a custom module and confirm the class name + module is correct"""
        mod_fake = Mocker.make_mock_class('ModFake', module='example.package')
        self._check_inst_name(mod_fake, 'ModFake')
        self._check_inst_mod(mod_fake, 'example.package')

        self.assertIn('<example.package.ModFake object', str(mod_fake))

    def test_mocker_make_class_module_isolation(self):
        """Create two "disguised" mocker classes and confirm both instances have independent class names/modules"""
        test_fake = Mocker.make_mock_class('TestFake', module='other.example')
        mod_fake = Mocker.make_mock_class('ModFake', module='package.example')

        self._check_inst_name(mod_fake, 'ModFake')
        self._check_inst_name(test_fake, 'TestFake')
        self._check_inst_mod(mod_fake, 'package.example')
        self._check_inst_mod(test_fake, 'other.example')

        self.assertIn('<package.example.ModFake object', str(mod_fake))
        self.assertIn('<other.example.TestFake object', str(test_fake))

    def test_mocker_add_modules(self):
        m = Mocker()
        
        # To make sure adding a module actually makes any difference, we verify that we can't get, nor set
        # items on the faked first layer attributes.
        with self.assertRaises(AttributeError):
            m.fakemod.other_example()
        
        # A strange thing about Python is that you can set attributes on functions, so we can't just set an attr.
        # If it's a function/lambda as expected, then we definitely can't set an item on it :)
        # noinspection PyTypeChecker
        with self.assertRaises((AttributeError, TypeError,)):
            m.fakemod['test_attr'] = 'hello'
        
        m.add_mock_module('fakemod')
        
        self.assertTrue(isinstance(m.fakemod, Mocker))
        # noinspection PyCallingNonCallable
        self.assertIsNone(m.fakemod.test_attr())
        m.fakemod.test_attr = 'hello'
        self.assertEqual(m.fakemod.test_attr, 'hello')

        # Let's check if multiple modules work properly by adding 'extramod' to the same instance
        with self.assertRaises(AttributeError):
            m.extramod.test_func()
        # noinspection PyTypeChecker
        with self.assertRaises((AttributeError, TypeError,)):
            m.extramod['hello'] = 'world'

        m.add_mock_module('extramod')
        self.assertTrue(isinstance(m.extramod, Mocker))
        m.extramod.hello = 'world'
        self.assertEqual(m.extramod.hello, 'world')
        # Just to be safe, let's make sure that our previous module 'fakemod' still exists and holds our attributes.
        self.assertEqual(m.fakemod.test_attr, 'hello')

    

        
        
        


