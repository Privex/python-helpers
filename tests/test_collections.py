"""
Test cases for :py:mod:`privex.helpers.collections`

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
import json
from typing import Union
from collections import namedtuple, OrderedDict
from privex.helpers import dictable_namedtuple, is_namedtuple, subclass_dictable_namedtuple, \
    convert_dictable_namedtuple, DictObject, OrderedDictObject
from tests.base import PrivexBaseCase
import logging

log = logging.getLogger(__name__)


class TestDictObject(PrivexBaseCase):
    def test_convert_from_dict(self):
        """Test converting a :class:`dict` into a :class:`.DictObject`"""
        x = dict(hello='world', example='testing')
        y = DictObject(x)
        self.assertEqual(x, y)
        self.assertEqual(y['hello'], 'world')
        self.assertEqual(y['example'], 'testing')
        self.assertEqual(y.hello, 'world')
        self.assertEqual(y.example, 'testing')

    def test_convert_to_dict(self):
        """Test converting a :class:`.DictObject` into a :class:`dict`"""
        x = DictObject(hello='world', example='testing')
        y = dict(x)
        self.assertEqual(x, y)
        self.assertEqual(y['hello'], 'world')
        self.assertEqual(y['example'], 'testing')

    def test_json_dumps(self):
        """Test serializing a simple :class:`.DictObject` into JSON"""
        x = DictObject(hello='world', example='testing')
        j = json.dumps(x)
        self.assertEqual(j, '{"hello": "world", "example": "testing"}')

    def test_json_dumps_nested(self):
        """Test serializing a :class:`.DictObject` with a nested :class:`.DictObject` into JSON"""
        x = DictObject(hello='world', example='testing')
        x.layer = DictObject(test=True)
        j = json.dumps(x)
        self.assertEqual(j, '{"hello": "world", "example": "testing", "layer": {"test": true}}')
    
    def test_set_item(self):
        """Test setting a dictionary key via an item/key ``x['y'] = 123``"""
        x = DictObject()
        x['testing'] = 'testitem'
        self.assertEqual(x['testing'], 'testitem')
        self.assertEqual(x.testing, 'testitem')

    def test_set_attr(self):
        """Test setting a dictionary key via an attribute ``x.y = 123``"""
        x = DictObject()
        x.testing = 'testattr'
        x.other_test = 'example'
        self.assertEqual(x['testing'], 'testattr')
        self.assertEqual(x['other_test'], 'example')
        self.assertEqual(x.testing, 'testattr')
        self.assertEqual(x.other_test, 'example')


class TestOrderedDictObject(PrivexBaseCase):
    def test_convert_from_dict(self):
        """Test converting a :class:`dict` into a :class:`.DictObject`"""
        x = dict(hello='world', example='testing')
        y = OrderedDictObject(x)
        self.assertEqual(x, y)
        self.assertEqual(y['hello'], 'world')
        self.assertEqual(y['example'], 'testing')
        self.assertEqual(y.hello, 'world')
        self.assertEqual(y.example, 'testing')
    
    def test_convert_to_dict(self):
        """Test converting a :class:`.OrderedDictObject` into a :class:`dict`"""
        x = OrderedDictObject(hello='world', example='testing')
        y = dict(x)
        self.assertEqual(x, y)
        self.assertEqual(y['hello'], 'world')
        self.assertEqual(y['example'], 'testing')
    
    def test_json_dumps(self):
        """Test serializing a simple :class:`.OrderedDictObject` into JSON"""
        x = OrderedDictObject(hello='world', example='testing')
        j = json.dumps(x)
        self.assertEqual(j, '{"hello": "world", "example": "testing"}')
    
    def test_json_dumps_nested(self):
        """Test serializing a :class:`.OrderedDictObject` with a nested :class:`.OrderedDictObject` into JSON"""
        x = OrderedDictObject(hello='world', example='testing')
        x.layer = OrderedDictObject(test=True)
        j = json.dumps(x)
        self.assertEqual(j, '{"hello": "world", "example": "testing", "layer": {"test": true}}')
    
    def test_set_item(self):
        """Test setting a dictionary key via an item/key ``x['y'] = 123``"""
        x = OrderedDictObject()
        x['testing'] = 'testitem'
        self.assertEqual(x['testing'], 'testitem')
        self.assertEqual(x.testing, 'testitem')
    
    def test_set_attr(self):
        """Test setting a dictionary key via an attribute ``x.y = 123``"""
        x = OrderedDictObject()
        x.testing = 'testattr'
        x.other_test = 'example'
        self.assertEqual(x['testing'], 'testattr')
        self.assertEqual(x['other_test'], 'example')
        self.assertEqual(x.testing, 'testattr')
        self.assertEqual(x.other_test, 'example')


class TestIsNamedTuple(PrivexBaseCase):
    """
    Test the function :func:`.is_namedtuple` against various different types and objects to ensure it returns ``True``
    or ``False`` appropriately, with tests containing a mixture of both :func:`collections.namedtuple` 
    and :func:`.dictable_namedtuple`.

    """
    Person = namedtuple('Person', 'first_name last_name')
    named_persons = (Person('John', 'Doe'), Person('Dave', 'Johnson'), Person('Aaron', 'Swartz'))

    DictPerson = dictable_namedtuple('Person', 'first_name last_name')
    dict_persons = (DictPerson('John', 'Doe'), DictPerson('Dave', 'Johnson'), DictPerson('Aaron', 'Swartz'))

    def test_real_namedtuple(self):
        """Test :func:`.is_namedtuple` returns ``True`` when all arguments are valid namedtuple's"""
        john, dave, aaron = self.named_persons
        self.assertTrue(is_namedtuple(john))
        self.assertTrue(is_namedtuple(dave))
        self.assertTrue(is_namedtuple(aaron))
        self.assertTrue(is_namedtuple(john, dave, aaron))
    
    def test_dictable_namedtuple(self):
        """Test :func:`.is_namedtuple` returns ``True`` when all arguments are valid dictable_namedtuple's"""
        john, dave, aaron = self.dict_persons
        self.assertTrue(is_namedtuple(john))
        self.assertTrue(is_namedtuple(dave))
        self.assertTrue(is_namedtuple(aaron))
        self.assertTrue(is_namedtuple(john, dave, aaron))

    def test_dictable_plus_normal_namedtuple(self):
        """Test :func:`.is_namedtuple` returns ``True`` when arguments are a mix of namedtuple + dictable_namedtuple's"""
        john, dave, aaron = self.named_persons
        d_john, d_dave, d_aaron = self.dict_persons
        self.assertTrue(is_namedtuple(john, d_dave))
        self.assertTrue(is_namedtuple(d_john, aaron))
        self.assertTrue(is_namedtuple(john, d_john, d_dave, dave, aaron, d_aaron))

    def test_real_namedtuple_plus_invalid(self):
        """(namedtuples) Test :func:`.is_namedtuple` returns ``False`` when some arguments are NOT namedtuple's"""
        john, dave, aaron = self.named_persons
        self.assertTrue(is_namedtuple(john))
        self.assertFalse(is_namedtuple(john, ['hello', 'world']))
        self.assertFalse(is_namedtuple(dave, dict(hello='world')))
        self.assertFalse(is_namedtuple(dave, aaron, 12345))

    def test_dictable_namedtuple_plus_invalid(self):
        """(dictable_namedtuples) Test :func:`.is_namedtuple` returns ``False`` when some arguments are NOT namedtuple's"""
        john, dave, aaron = self.dict_persons
        self.assertTrue(is_namedtuple(john))
        self.assertFalse(is_namedtuple(john, ['hello', 'world']))
        self.assertFalse(is_namedtuple(dave, dict(hello='world')))
        self.assertFalse(is_namedtuple(dave, aaron, 12345))

    def test_not_namedtuple_dict(self):
        """Test that dictionaries are not namedtuple's"""
        self.assertFalse(is_namedtuple(
            dict(hello='world')
        ))
    
    def test_not_namedtuple_list(self):
        """Test that list's are not namedtuple's"""
        self.assertFalse(is_namedtuple(
            ['hello', 'world']
        ))
    
    def test_not_namedtuple_tuple(self):
        """Test that tuple's are not namedtuple's"""
        self.assertFalse(is_namedtuple(
            ('hello', 'world',)
        ))
    
    def test_not_namedtuple_int(self):
        """Test that int's are not namedtuple's"""
        self.assertFalse(is_namedtuple(123))
    
    def test_not_namedtuple_float(self):
        """Test that float's are not namedtuple's"""
        self.assertFalse(is_namedtuple(12.3))

    def test_not_namedtuple_class(self):
        """Test that classes and instances of classes are not namedtuple's"""
        class ExampleClass:
            pass
        self.assertFalse(is_namedtuple(ExampleClass))
        self.assertFalse(is_namedtuple(ExampleClass()))


class TestDictableNamedtuple(PrivexBaseCase):
    """
    Test the function :func:`.dictable_namedtuple` and compare it against :func:`collections.namedtuple` to ensure
    that dictable_namedtuple's should be backwards compatible with code that takes namedtuple's.

    Also tests new functionality that only exists in dictable_namedtuple's, and compares it against
    standard namedtuples, including:

        * Test getting by item/key, i.e. ``john['first_name']``, and confirm normal namedtuples 
          raise exceptions
        
        * Test setting new item/key's and attributes ``item['color'] = 'Brown'``, and confirm 
          normal namedtuples raise exceptions
        
        * Test casting dictable namedtuple's to dict's ``dict(item)``, and confirm normal 
          namedtuples raise exceptions
    
    """

    Item = dictable_namedtuple('Item', 'name description')
    """A :func:`.dictable_namedtuple` type, representing an 'item'"""
    NmItem = namedtuple('Item', 'name description')
    """A :func:`collections.namedtuple` type, representing an 'item'"""
    example_items = Item('Box', 'Small Cardboard Box'), NmItem('Box', 'Small Cardboard Box')
    """A tuple containing an instance of both :py:attr:`.Item` and :py:attr:`.NmItem`"""

    def setUp(self):
        """
        At the start of each test, reset :attr:`.example_items`, :attr:`.Item` and :attr:`.NmItem` 
        in-case any tests have modified them
        """
        self.Item = Item = dictable_namedtuple('Item', 'name description')
        self.NmItem = NmItem = namedtuple('Item', 'name description')
        self.example_items = Item('Box', 'Small Cardboard Box'), NmItem('Box', 'Small Cardboard Box')

    def test_metadata(self):
        """
        Confirm sameness of class/instance metadata such as class name/qualname, module name, and stringification
        between :func:`.dictable_namedtuple` and :func:`collections.namedtuple`
        """
        di, ni = self.example_items
        di_cls, ni_cls = di.__class__, ni.__class__
        self.assertEqual(di_cls.__name__, ni_cls.__name__)
        self.assertEqual(di_cls.__qualname__, ni_cls.__qualname__)
        self.assertEqual(di_cls.__module__, ni_cls.__module__)
        self.assertEqual(str(di), str(ni))
    
    def test_get_attr(self):
        """Confirm getting attributes is equivalent on dictable namedtuple to standard namedtuple"""
        di, ni = self.example_items

        self.assertEqual(di.name, ni.name)
        self.assertEqual(di.description, ni.description)
    
    def test_get_item(self):
        """Test we can access named items on on dictable namedtuple while standard namedtuple raises exceptions"""
        di, ni = self.example_items

        self.assertEqual(di['name'], 'Box')
        self.assertEqual(di['description'], 'Small Cardboard Box')

        # The standard ``namedtuple`` instances don't support accessing fields via string "item" keys. 
        # They should throw a TypeError, KeyError, or AttributeError when we try and access a key.
        with self.assertRaises((TypeError, KeyError, AttributeError,)):
            x = ni['name']
        
        with self.assertRaises((TypeError, KeyError, AttributeError,)):
            x = ni['description']

    def test_get_index(self):
        """Test we can access by integer index on dictable + normal namedtuple"""
        di, ni = self.example_items

        self.assertEqual(di[0], ni[0])
        self.assertEqual(di[1], ni[1])
        self.assertEqual(di[1], 'Small Cardboard Box')
    
    def test_set_item(self):
        """Test that we can create the new item/key ``color`` on the dictable_namedtuple"""
        di, ni = self.example_items

        di['color'] = 'Brown'
        self.assertEqual(di['color'], 'Brown')
        self.assertEqual(di.color, 'Brown')
        self.assertIn('color', dict(di))
        self.assertIn("color='Brown'", str(di))

        # The standard ``namedtuple`` instances don't allow modification after creation.
        # They should throw a ValueError or a TypeError.
        with self.assertRaises((ValueError, TypeError,)):
            ni['color'] = 'Brown'
    
    def test_set_attr(self):
        """Test that we can create the new attribute ``color`` on the dictable_namedtuple"""
        di, ni = self.example_items

        di.color = 'Brown'
        self.assertEqual(di['color'], 'Brown')
        self.assertEqual(di.color, 'Brown')
        self.assertIn('color', dict(di))
        self.assertIn("color='Brown'", str(di))

        # The standard ``namedtuple`` instances don't allow modification after creation.
        # They should throw a ValueError or a AttributeError.
        with self.assertRaises((ValueError, AttributeError,)):
            ni.color = 'Brown'
    
    def test_dict_cast(self):
        """Test casting dictable_namedtuple using ``dict`` works as expected, but fails on normal namedtuple"""
        di, ni = self.example_items
        
        self._check_cast_dict(di)

        # The standard ``namedtuple`` instances cannot be casted to a dict, they should throw a ValueError
        # or a TypeError.
        with self.assertRaises((ValueError, TypeError,)):
            dict_ni = dict(ni)
    
    def test_asdict(self):
        """Test ``._asdict`` works on both dictable + normal namedtuple"""
        di, ni = self.example_items

        self._check_asdict(di)

        self._check_asdict(ni)

    def _check_asdict(self, inst):
        dict_inst = inst._asdict()
        self.assertIn(type(dict_inst), [dict, OrderedDict])
        self.assertListEqual(['name', 'description'], list(dict_inst.keys()))
        self.assertListEqual(['Box', 'Small Cardboard Box'], list(dict_inst.values()))

    def _check_cast_dict(self, inst):
        dict_inst = dict(inst)
        self.assertIn(type(dict_inst), [dict, OrderedDict])
        self.assertListEqual(['name', 'description'], list(dict_inst.keys()))
        self.assertListEqual(['Box', 'Small Cardboard Box'], list(dict_inst.values()))

    def test_subclass(self):
        """Test subclass_dictable_namedtuple converts :attr:`.NmItem` into a dictable_namedtuple type """
        d_nt = subclass_dictable_namedtuple(self.NmItem)
        
        di = d_nt('Box', 'Small Cardboard Box')
        self._check_dictable(di)

    def test_convert(self):
        """Test convert_dictable_namedtuple converts example namedtuple instance into a dictable_namedtuple instance"""
        ni = self.example_items[1]
        di = convert_dictable_namedtuple(ni)
        self._check_dictable(di)

    def _check_dictable(self, di):
        # Confirm the object is named 'Item'
        self.assertIn('Item(', str(di))
        # Test accessing by attribute
        self.assertEqual(di.name, 'Box')
        self.assertEqual(di.description, 'Small Cardboard Box')
        # Test accessing by item/key
        self.assertEqual(di['name'], 'Box')
        self.assertEqual(di['description'], 'Small Cardboard Box')
        # Test accessing by tuple index
        self.assertEqual(di[0], 'Box')
        self.assertEqual(di[1], 'Small Cardboard Box')
        # Test converting to a dict (via dict())
        self._check_cast_dict(di)
        # Test converting to a dict (via ._asdict())
        self._check_asdict(di)
