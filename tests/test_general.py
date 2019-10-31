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


    
        
        

