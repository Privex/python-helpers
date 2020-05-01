"""
General test cases for various un-categorized functions / classes e.g. :py:func:`.chunked` and :py:func:`.inject_items`

**Copyright**::

        +===================================================+
        |                 © 2019 Privex Inc.                |
        |               https://www.privex.io               |
        +===================================================+
        |                                                   |
        |        Originally Developed by Privex Inc.        |
        |        License: X11 / MIT                         |
        |                                                   |
        |        Core Developer(s):                         |
        |                                                   |
        |          (+)  Chris (@someguy123) [Privex]        |
        |          (+)  Kale (@kryogenic) [Privex]          |
        |                                                   |
        +===================================================+

    Copyright 2019     Privex Inc.   ( https://www.privex.io )


"""
import os
from decimal import Decimal
from os import path, makedirs
from tempfile import TemporaryDirectory, NamedTemporaryFile, mkstemp
from typing import Union, Tuple, List, TextIO, BinaryIO
from privex import helpers
from tests import PrivexBaseCase
import logging

log = logging.getLogger(__name__)


def _create_test_file(tfile: BinaryIO, nlines=10) -> List[str]:
    """Helper function for populating a testing temp file with numbered example lines for comparison"""
    lines = [f"This is an example line {i}\n".encode('utf-8') for i in range(1, nlines+1)]
    tfile.writelines(lines)
    tfile.flush()
    return [l.decode().strip("\n") for l in lines]


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
    
    def test_filter_form_dict1(self):
        """
        Test :func:`.filter_form` with a standard dict
        """
        
        x = dict(lorem="hello", ipsum=2, dolor=['world'])
        y = helpers.filter_form(x, 'lorem', 'dolor')
        
        self.assertIn('lorem', y)
        self.assertIn('dolor', y)
        self.assertNotIn('ipsum', y)
        
        self.assertIsInstance(y['lorem'], str)
        self.assertIsInstance(y['dolor'], list)

    def test_filter_form_dict_cast(self):
        """
        Test :func:`.filter_form` with a dict and auto-casting
        """
    
        x = dict(lorem="1", ipsum=2, dolor="3.14", world="test")
        y = helpers.filter_form(x, 'lorem', 'ipsum', 'dolor', cast=Decimal)
    
        self.assertIn('lorem', y)
        self.assertIn('ipsum', y)
        self.assertIn('dolor', y)
        self.assertNotIn('world', y)
    
        self.assertIsInstance(y['lorem'], Decimal)
        self.assertIsInstance(y['ipsum'], Decimal)
        self.assertIsInstance(y['dolor'], Decimal)
        self.assertEqual(y['lorem'], Decimal('1'))
        self.assertEqual(y['dolor'], Decimal('3.14'))


class TestGeneralExtractSettings(PrivexBaseCase):
    """Test cases for :func:`.extract_settings`"""
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


class TestGeneralTail(PrivexBaseCase):
    """Test cases for :func:`.io_tail` and :func:`.tail`"""
    
    def test_io_tail_500_lines_300(self):
        """
        Test :func:`.io_tail` by tailing 300 lines of a 500 line file, then comparing each line from generated chunks against the
        original lines written to the file.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 500)
            
            i = -1  # Position -1 is the last line in the ``lines`` list
            for chunk in helpers.io_tail(tfile, 300):
                # We reverse each chunk, so that we can cleanly compare last lines -> first lines
                chunk.reverse()
                # We lower i by 1 for each line in the chunk, so we're reading ``lines`` backwards, while reading the reversed ``chunk``
                # from the last line until the first line of the chunk.
                for l in chunk:
                    self.assertEqual(l, lines[i], msg=f"l == lines[{i}] // '{l}' == '{lines[i]}'")
                    i -= 1
            # Since the last line of ``lines`` was -1 instead of -0, the final iteration should result in -301
            self.assertEqual(i, -301)
    
    def test_tail_10_lines_3(self):
        """
        Test :func:`.tail` by comparing the last 3 lines of a 10 line testing file.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 10)
            
            tailed = helpers.tail(tfile.name, 3)
            self.assertEqual(len(tailed), 3)
            self.assertEqual(tailed[0], "This is an example line 8")
            self.assertEqual(tailed[1], "This is an example line 9")
            self.assertEqual(tailed[2], "This is an example line 10")
    
    def test_tail_10_lines_5(self):
        """
        Test :func:`.tail` by comparing the first and last tailed 5 lines of a 10 line testing file.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 10)
            
            tailed = helpers.tail(tfile.name, 5)
            self.assertEqual(len(tailed), 5)
            self.assertEqual(tailed[0], lines[-5])
            self.assertEqual(tailed[4], lines[-1])
    
    def test_tail_10_lines_10(self):
        """
        Test :func:`.tail` works when ``nlines`` is equal to the amount of lines in the file. We tail 10 lines of a 10 line test file,
        then compare all 10 original lines against the output from tail.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 10)
            
            tailed = helpers.tail(tfile.name, 10)
            self.assertEqual(len(tailed), 10)
            for i, l in enumerate(lines):
                self.assertEqual(tailed[i], lines[i], msg=f"tailed[{i}] == lines[{i}] // '{tailed[i]}' == '{lines[i]}'")
    
    def test_tail_500_lines_20(self):
        """
        Test :func:`.tail` with a larger test file. Tailing 20 lines of a 500 line test file.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 500)
            
            tailed = helpers.tail(tfile.name, 20)
            self.assertEqual(len(tailed), 20)
            # Compare the last 20 lines from ``lines``, against ``tailed`` starting from position 0
            i = 0
            for l in lines[480:]:
                self.assertEqual(tailed[i], l, msg=f"tailed[i] == l // '{tailed[i]}' == '{l}'")
                i += 1
    
    def test_tail_500_lines_300(self):
        """
        Test :func:`.tail` with a larger line count. Tailing 300 lines of a 500 line test file.
        """
        with NamedTemporaryFile() as tfile:
            lines = _create_test_file(tfile, 500)
            
            tailed = helpers.tail(tfile.name, 300)
            self.assertEqual(len(tailed), 300)
            # Compare the last 300 lines from ``lines``, against ``tailed`` starting from position 0
            i = 0
            for l in lines[200:]:
                self.assertEqual(tailed[i], l, msg=f"tailed[i] == l // '{tailed[i]}' == '{l}'")
                i += 1


class TestGeneralAlmost(PrivexBaseCase):
    def test_two_numbers(self):
        """Test :func:`.almost` with two Decimal numbers"""
        self.assertTrue(helpers.almost(Decimal('5'), Decimal('5.001')))
        self.assertFalse(helpers.almost(Decimal('5'), Decimal('5.3')))

    def test_four_numbers(self):
        """Test :func:`.almost` with four string numbers"""
        self.assertTrue(helpers.almost('5', '5.005', '4.99', '5.006'))
        self.assertFalse(helpers.almost('5', '5.3', '5.01', '4.99'))

    def test_two_numbers_pt1tolerance(self):
        """Test :func:`.almost` with two string numbers and 0.1 tolerance"""
        self.assertTrue(helpers.almost('10', '10.1', tolerance='0.1'))
        self.assertFalse(helpers.almost('10', '10.2', tolerance='0.1'))

    def test_four_numbers_pt1tolerance(self):
        """Test :func:`.almost` with four string numbers and 0.1 tolerance"""
        self.assertTrue(helpers.almost('10', '10.1', '10.05', '9.9', tolerance='0.1'))
        self.assertFalse(helpers.almost('10', '10.05', '10.3', '10.2', tolerance='0.1'))

    def test_two_numbers_fail_kwarg(self):
        """Test :func:`.almost` with two string numbers and ``fail=True`` kwarg"""
        self.assertTrue(helpers.almost('5', '5.001', fail=True))
        with self.assertRaises(AssertionError):
            helpers.almost('5', '5.3', fail=True)

    def test_two_numbers_test_kwarg(self):
        """Test :func:`.almost` with two string numbers and ``test=True`` kwarg"""
        self.assertTrue(helpers.almost('5', '5.001', test=True))
        with self.assertRaises(AssertionError):
            helpers.almost('5', '5.3', test=True)

