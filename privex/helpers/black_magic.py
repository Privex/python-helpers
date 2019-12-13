"""
This module contains *somewhat risky* code that uses app introspection e.g. via :mod:`inspect`.

Most functions / classes in this module will **ONLY work on CPython** (the official Python interpreter from python.org),
and their functionality is not guaranteed to be stable as they interact with the interpreter to enable special functionality
such as detecting the function/class/module which called your function/method.

Functions and methods in this module may be updated with breaking API changes at any time, especially if they're needed
to adjust for a change in Python itself. Please ensure that any usage of this module is properly wrapped in a try/catch block,
and avoid relying on functions/methods in this module for critical functionality of your application.

Most useful functions:

 * :func:`.calling_function` - Returns the name of the function/method which called your function/method
 
 * :func:`.calling_module` - Returns the name of the module which called your function/method
 
 * :func:`.caller_name` - Returns the fully qualified module path to the function/method/module which called
   your function/method


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
import inspect
from typing import Optional


def calling_function(skip=2) -> Optional[str]:
    """
    Returns the name of the function which called your function/method.
    
    Example::
        
        >>> def x(skip=2): return calling_function(skip=2)
        >>>
        >>> def y(skip=2): return x(skip)
        >>>
        >>> def z(skip=2): return y(skip)
        >>>
        >>> print(y())   # The call to x() returns that 'y' is the function which called it.
        y
        >>> print(z())   # The call to z() calls y() -> x() - still returning that 'y' is the caller of x()
        y
        >>> # If we adjust skip to 3 instead of 2, we can see that z() is the function that called y() which called x()
        >>> print(z(3))
        z
        
    :param int skip: Skip this many frames.
                     0 = calling_function()
                     1 = function which called calling_function()
                     2 = function which called the function that called calling_function() (default)
                     and so on...
     
    :return str|None function_name: Either a string containing the function name, or ``None`` if you've skipped too many frames.
    
    """
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    
    if len(calframe) <= skip:
        return None
    return calframe[skip][3]


def last_frames():
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)
    return curframe, calframe


def last_stack_frame(frame_num=2):
    return inspect.stack()[frame_num]


def calling_module(skip=2) -> Optional[str]:
    """
    Returns the name of the module which called your function/method.
    
    :param int skip: Skip this many frames.
                 0 = module containing calling_function()
                 1 = module which called calling_function()
                 2 = module which called the function that called calling_function() (default)
                 and so on...
    :return str|None mod_name: Either a string containing the module name, or ``None`` if you've skipped too many frames.
                               If called from the main python script, then ``'__main__'`` will be returned instead of a
                               proper module path.
    """
    stk = inspect.stack()
    if len(stk) <= skip:
        return None
    mod = inspect.getmodule(stk[skip][0])
    if mod is None:
        return '__main__'
    return mod.__name__


def caller_name(skip=2) -> Optional[str]:
    """
    Get the fully qualified name of a caller in the format ``some.module.SomeClass.method``
    
    .. Attention::    While class instance methods will be returned correctly, class static methods will not show up as expected.
                      The static method ``some.module.SomeClass.some_static`` would be returned as ``some.module.some_static``,
                      as if it were a top-level function in the module.
    
    
    Original source: https://stackoverflow.com/a/9812105
    
    **Basic Example**
    
    When used within the main program (the script you run ``python3 xxx.py`` on), the module will be reported as ``__main__``.
    
    File ``hello.py``::
        
        >>> from privex.helpers.black_magic import caller_name
        >>>
        >>> def f2():
        ...     return caller_name()
        >>>
        >>> def f1():
        ...     return f2()
        ...
        >>> print(f"[{__name__}] f1 result: {f1()}")
        [__main__] f1 result: __main__.f1
    
    However, as we can see below, when we create and run ``world.py`` which imports ``hello.py``, it correctly returns the
    path ``hello.f1``.
    
    File ``world.py``::
        
        >>> from hello import f1
        >>>
        >>> print(f"[{__name__}] f1 result: {f1()}")
        [hello] f1 result: hello.f1
        [__main__] f1 result: hello.f1

    
    **More Complex Example**
    
    File ``some/module/hello.py``::
        
        >>> from privex.helpers.black_magic import caller_name
        >>>
        >>> class SomeClass:
        >>>     def example_method(self, skip=2):
        ...         return caller_name(skip)
        ...
    
    File ``some/module/world.py``::
        
        >>> from some.module.hello import SomeClass
        >>>
        >>> class OtherClass:
        ...     def call_some(self, skip=2):
        ...         return SomeClass().example_method(skip)
        ...
    
    File ``test.py``::
        
        >>> from some.module.hello import SomeClass
        >>> from some.module.world import OtherClass
        >>>
        >>> def main_func():
        ...     print('SomeClass (2)', SomeClass().example_method())
        ...     print('OtherClass (1)', OtherClass().call_some(1))
        ...     print('OtherClass (2)', OtherClass().call_some())
        ...     print('OtherClass (3)', OtherClass().call_some(3))
        ...
        >>> main_func()
        SomeClass (2) test.main_func
        OtherClass (1) some.module.hello.SomeClass.example_method
        OtherClass (2) some.module.world.OtherClass.call_some
        OtherClass (3) test.main_func
    
    

    :param int skip: Specifies how many levels of stack to skip while getting caller name.
                     ``skip=1`` means "who called caller_name",
                     ``skip=2`` means "who called this function/method" etc.

    :return str caller: A fully qualified module path, e.g. ``some.module.SomeClass.some_method``
                        ``None`` is returned if skipped levels exceed stack height.
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return None
    parentframe = stack[start][0]
    
    name = []
    module = inspect.getmodule(parentframe)
    
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    
    # Avoid circular refs and frame leaks
    # https://docs.python.org/2.7/library/inspect.html#the-interpreter-stack
    del parentframe, stack
    
    _caller = ".".join(name)
    
    if _caller in ["", None]:
        return None
    return _caller
