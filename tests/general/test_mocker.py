import inspect

from privex import helpers
from tests import PrivexBaseCase

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
