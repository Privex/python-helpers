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
from os import path, makedirs
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Union, Dict

from privex import helpers
from tests.base import PrivexBaseCase
import logging

log = logging.getLogger(__name__)


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

    def test_call_sys_read(self):
        """Test reading output from call_sys by calling 'ls -l' on a temporary folder with spaces in it"""
        with TemporaryDirectory() as td:
            _temp_dir = 'path with/spaces in it'
            temp_dir = path.join(td, 'path with', 'spaces in it')
            makedirs(temp_dir)
            with NamedTemporaryFile(dir=temp_dir) as tfile:
                tfile.write(b'hello world')
                out, err = helpers.call_sys('ls', '-l', _temp_dir, cwd=td)
                out = helpers.stringify(out)
                self.assertIn(path.basename(tfile.name), out)

    def test_call_sys_write(self):
        """Test piping data into a process with call_sys"""
        out, err = helpers.call_sys('wc', '-c', write='hello world')
        out = int(out)
        self.assertEqual(out, 11)
    
    @helpers.async_sync
    def test_call_sys_async_read(self):
        """Test reading output from call_sys_async by calling 'ls -l' on a temporary folder with spaces in it"""
        with TemporaryDirectory() as td:
            _temp_dir = 'path with/spaces in it'
            temp_dir = path.join(td, 'path with', 'spaces in it')
            makedirs(temp_dir)
            with NamedTemporaryFile(dir=temp_dir) as tfile:
                tfile.write(b'hello world')
                out, err = yield from helpers.call_sys_async('ls', '-l', _temp_dir, cwd=td)
                out = helpers.stringify(out)
                self.assertIn(path.basename(tfile.name), out)

    @helpers.async_sync
    def test_call_sys_async_write(self):
        """Test piping data into a process with call_sys_async"""
        out, err = yield from helpers.call_sys_async('wc', '-c', write='hello world')
        out = int(out)
        self.assertEqual(out, 11)
    
    ex_settings = dict(
        DB_USER='root', DB_PASS='ExamplePass', DB_HOST='localhost', DB_NAME='example_db', FAKE_SETTING='hello',
        EXAMPLE='world', HELLO_DB='lorem ipsum'
    )
    
    class ExSettingsClass:
        DB_USER = 'root'
        DB_PASS = 'ExamplePass'
        DB_HOST = 'localhost'
        DB_NAME = 'example_db'
        FAKE_SETTING = 'hello'
        EXAMPLE = 'world'
        HELLO_DB = 'lorem ipsum'

    class ExSettingsInst:
        def __init__(self):
            self.db_user = 'root'
            self.db_pass = 'ExamplePass'
            self.db_host = 'localhost'
            self.db_name = 'example_db'
            self.fake_setting = 'hello'
            self.example = 'world'
            self.hello_db = 'lorem ipsum'

    def test_extract_settings_dict(self):
        """Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a ``dict``"""
        ex_settings = self.ex_settings
        extracted = helpers.extract_settings('DB_', ex_settings)
        self._compare_settings(ex_settings, extracted)

    def _compare_settings(self, ex_settings: Union[dict, type, object], extracted: dict,
                          uppercase=False, orig_uppercase=True):
        """
        This is a helper method for :func:`.extract_settings` test cases which use :attr:`.ex_settings` or :class:`.ExSettingsClass`,
        which helps avoid duplicating test case code.
        
            * Tests that ``extracted`` is a dictionary
            * Tests that ``extracted`` contains exactly 4 items
            * Tests that ``user``, ``pass``, ``host``, and ``name`` (or uppercase versions) are present in ``extracted``, and match the
              equivalent values on ``ex_settings``.
        
        :param ex_settings:    The original settings object which :func:`.extract_settings` was extracting from
        :param extracted:      The extracted settings dict returned by :func:`.extract_settings`
        :param uppercase:      If ``True``, check ``extracted`` for ``USER``, ``PASS`` etc. instead of their lowercase versions.
        :param orig_uppercase: If ``True``, check ``ex_settings`` for ``DB_USER``, ``DB_PASS`` etc. instead of their lowercase versions.
        """
        if not isinstance(ex_settings, dict):
            ex_settings = dict(ex_settings.__dict__)
        
        _key_map = (('user', 'db_user',), ('pass', 'db_pass',),
                    ('host', 'db_host',), ('name', 'db_name',),)
        e_up, s_up = uppercase, orig_uppercase
        key_map = [(_ek.upper() if e_up else _ek, _sk.upper() if s_up else _sk) for _ek, _sk in _key_map]
        
        self.assertTrue(isinstance(extracted, dict))
        self.assertEqual(len(extracted.keys()), 4)
        
        for _ek, _sk in key_map:
            self.assertEqual(extracted[_ek], ex_settings[_sk])

    def test_extract_settings_class(self):
        """Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a class"""
        extracted = helpers.extract_settings('DB_', self.ExSettingsClass)
    
        self._compare_settings(self.ExSettingsClass, extracted)

    def test_extract_settings_class_instance(self):
        """Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a class instance/object"""
        inst = self.ExSettingsInst()
        extracted = helpers.extract_settings('DB_', inst)
    
        self._compare_settings(inst, extracted, orig_uppercase=False)

    def test_extract_settings_class_instance_case_sensitive(self):
        """
        Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a class instance/object (case sensitive)
        """
        inst = self.ExSettingsInst()
        extracted = helpers.extract_settings('db_', inst, _case_sensitive=True)
    
        self._compare_settings(inst, extracted, orig_uppercase=False)

    def test_extract_settings_class_instance_case_sensitive_fail(self):
        """
        Test :func:`.extract_settings` returns empty dict for ``DB_`` prefixed settings from a class instance
        (case sensitive)
        """
        inst = self.ExSettingsInst()
        extracted = helpers.extract_settings('DB_', inst, _case_sensitive=True)
    
        self.assertTrue(isinstance(extracted, dict))
        self.assertEqual(len(extracted.keys()), 0)

    def test_extract_settings_modules(self):
        """Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a python module"""
        from privex.helpers import settings as ex_settings
        
        keys_ex = [k for k in ex_settings.__dict__.keys() if k[:6] == 'REDIS_']
        
        extracted = helpers.extract_settings('REDIS_', ex_settings)
        self.assertEqual(extracted['db'], ex_settings.REDIS_DB)
        self.assertEqual(extracted['port'], ex_settings.REDIS_PORT)
        self.assertEqual(extracted['host'], ex_settings.REDIS_HOST)
        
        self.assertEqual(len(extracted.keys()), len(keys_ex))

    def test_extract_settings_case_sensitive(self):
        """Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a class (case sensitive)"""
        extracted = helpers.extract_settings('DB_', self.ExSettingsClass, _case_sensitive=True)

        self._compare_settings(self.ExSettingsClass, extracted, uppercase=True)

    def test_extract_settings_case_sensitive_fail(self):
        """Test :func:`.extract_settings` returns empty dict for ``db_`` prefix from a class (case sensitive)"""
        extracted = helpers.extract_settings('db_', self.ExSettingsClass, _case_sensitive=True)
    
        self.assertTrue(isinstance(extracted, dict))
        self.assertEqual(len(extracted.keys()), 0)

    def test_extract_settings_case_sensitive_lowercase_keys(self):
        """
        Test :func:`.extract_settings` can correctly extract ``DB_`` prefixed settings from a class
        (case sensitive + lowercase keys)
        """
        extracted = helpers.extract_settings('DB_', self.ExSettingsClass, _case_sensitive=True, _keys_lower=True)
        self._compare_settings(self.ExSettingsClass, extracted, uppercase=False)

    def test_extract_settings_case_sensitive_lowercase_keys_fail(self):
        """
        Test :func:`.extract_settings` returns empty dict for ``db_`` prefixed settings from a class
        (case sensitive + lowercase keys)
        """
        extracted = helpers.extract_settings('db_', self.ExSettingsClass, _case_sensitive=True, _keys_lower=True)
    
        self.assertTrue(isinstance(extracted, dict))
        self.assertEqual(len(extracted.keys()), 0)


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
        async def example_func_async(a, b): return a + b
        
        @helpers.awaitable
        def example_func(a, b): return example_func_async(a, b)
        
        async def call_example_async():
            return await example_func("hello", " world")
        
        self.assertEqual(helpers.run_sync(call_example_async), "hello world")
        self.assertEqual(example_func("hello", " world"), "hello world")
    
    def test_async_aobject(self):
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


def some_func(x, y, z=123, *args, **kwargs):
    """This is an example function used by :class:`.TestInspectFunctions`"""
    pass


class SimpleExample:
    """This is an example basic class used by :class:`.TestInspectFunctions`"""
    def __init__(self, hello, world, lorem='ipsum', **kwargs):
        pass


class BaseOne:
    """This is an example parent class used by :class:`.TestInspectFunctions`"""
    def __init__(self, a, b, c='hello'):
        pass


class BaseTwo(BaseOne):
    """This is an example parent class used by :class:`.TestInspectFunctions`"""
    def __init__(self, d, e, c='orange', **kw):
        super().__init__(a=kw.get('a'), b=kw.get('b'), c=c)


class InheritExample(BaseTwo):
    """This is an example inheritance class used by :class:`.TestInspectFunctions`"""
    def __init__(self, some, more='args', d='banana', **kw):
        super().__init__(some=some, more=more, **kw)


class TestInspectFunctions(PrivexBaseCase):
    def test_function_params_func(self):
        """Test :func:`.get_function_params` with a normal function"""
        params = helpers.get_function_params(some_func)
        self.assertIn('x', params)
        self.assertIn('y', params)
        self.assertIn('z', params)
        self.assertNotIn('*args', params)
        self.assertNotIn('**kwargs', params)
        self.assertEqual(params['z'].default, 123)

    def test_function_params_class(self):
        """Test :func:`.get_function_params` with a plain class without check_parents / merge"""
        params = helpers.get_function_params(SimpleExample)
        self.assertIn('hello', params)
        self.assertIn('world', params)
        self.assertIn('lorem', params)
        self.assertNotIn('**kwargs', params)
        self.assertEqual(params['lorem'].default, 'ipsum')

    def test_function_params_class_no_parents(self):
        """Test :func:`.get_function_params` with an inherited class without check_parents / merge"""
        params = helpers.get_function_params(InheritExample, check_parents=False)
        self.assertIn('some', params)
        self.assertIn('more', params)
        self.assertIn('d', params)
        self.assertNotIn('a', params)
        self.assertNotIn('b', params)
        self.assertNotIn('e', params)

    def test_function_params_class_parents(self):
        """Test :func:`.get_function_params` with an inherited class using check_parents=True and merge=False"""
        params = helpers.get_function_params(InheritExample, check_parents=True, merge=False)
        params: Dict[type, Dict[str, helpers.T_PARAM]]
        self.assertIn(BaseOne, params)
        self.assertIn(BaseTwo, params)
        self.assertIn(InheritExample, params)
        
        self.assertIn('some', params[InheritExample])
        self.assertIn('more', params[InheritExample])
        self.assertIn('d', params[InheritExample])
        
        self.assertIn('a', params[BaseOne])
        self.assertIn('b', params[BaseOne])
        self.assertIn('c', params[BaseOne])
        
        self.assertIn('d', params[BaseTwo])
        self.assertIn('e', params[BaseTwo])
        self.assertIn('c', params[BaseTwo])
        
        self.assertEqual(params[BaseTwo]['c'].default, 'orange')
        self.assertEqual(params[BaseOne]['c'].default, 'hello')
        self.assertEqual(params[BaseTwo]['d'].default, helpers.INS_EMPTY)
        self.assertEqual(params[InheritExample]['d'].default, 'banana')

    def test_function_params_class_parents_merge(self):
        """Test :func:`.get_function_params` with an inherited class using check_parents=True and merge=True"""
        params = helpers.get_function_params(InheritExample, check_parents=True, merge=True)
        self.assertIn('some', params)
        self.assertIn('more', params)
        self.assertIn('a', params)
        self.assertIn('b', params)
        self.assertIn('c', params)
        self.assertIn('d', params)
        self.assertIn('e', params)
        self.assertEqual(params['c'].default, 'orange')
        self.assertEqual(params['d'].default, 'banana')

    def test_construct_dict_func(self):
        """Test :func:`.construct_dict` with calling a function using a dict"""
    
        def limited_func(hello, example='world'):
            return "success"
        
        data = dict(hello='world', example='yes', lorem='ipsum')
        with self.assertRaises(TypeError):
            limited_func(**data)
        
        res = helpers.construct_dict(limited_func, data)
        self.assertEqual(res, "success")

    def test_construct_dict_class(self):
        """Test :func:`.construct_dict` with constructing a class using a dict"""
        class LimitedClass:
            def __init__(self, hello, example='world'):
                self.hello = hello
                self.example = example
        
        data = dict(hello='world', example='yes', lorem='ipsum')
        with self.assertRaises(TypeError):
            LimitedClass(**data)
    
        res = helpers.construct_dict(LimitedClass, data)
        self.assertEqual(res.hello, 'world')
        self.assertEqual(res.example, 'yes')




        


