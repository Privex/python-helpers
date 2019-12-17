from typing import Dict
from privex import helpers
from tests.base import PrivexBaseCase
import logging

log = logging.getLogger(__name__)


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



