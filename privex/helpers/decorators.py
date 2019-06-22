"""
Class Method / Function decorators

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
import functools
import logging
from time import sleep

DEF_RETRY_MSG = "Exception while running '%s', will retry %d more times."
DEF_FAIL_MSG = "Giving up after attempting to retry function '%s' %d times."

log = logging.getLogger(__name__)


def retry_on_err(max_retries: int = 3, delay: int = 3, **retry_conf):
    """
    Decorates a function or class method, wraps the function/method with a try/catch block, and will automatically
    re-run the function with the same arguments up to `max_retries` time after any exception is raised, with a
    ``delay`` second delay between re-tries.

    If it still throws an exception after ``max_retries`` retries, it will log the exception details with ``fail_msg``,
    and then re-raise it.

    Usage (retry up to 5 times, 1 second between retries, stop immediately if IOError is detected):

        >>> @retry_on_err(5, 1, fail_on=[IOError])
        ... def my_func(self, some=None, args=None):
        ...     if some == 'io': raise IOError()
        ...      raise FileExistsError()

    This will be re-ran 5 times, 1 second apart after each exception is raised, before giving up:

        >>> my_func()

    Where-as this one will immediately re-raise the caught IOError on the first attempt, as it's passed in ``fail_on``:

        >>> my_func('io')


    :param int max_retries:  Maximum total retry attempts before giving up
    :param int delay:        Amount of time in seconds to sleep before re-trying the wrapped function
    :param retry_conf:       Less frequently used arguments, pass in as keyword args:

    - (list) fail_on:  A list() of Exception types that should result in immediate failure (don't retry, raise)

    - (str) retry_msg: Override the log message used for retry attempts. First message param %s is func name,
      second message param %d is retry attempts remaining

    - (str) fail_msg:  Override the log message used after all retry attempts are exhausted. First message param %s
      is func name, and second param %d is amount of times retried.

    """
    retry_msg = retry_conf['retry_msg'] if 'retry_msg' in retry_conf else DEF_RETRY_MSG
    fail_msg = retry_conf['fail_msg'] if 'fail_msg' in retry_conf else DEF_FAIL_MSG
    fail_on = list(retry_conf['fail_on']) if 'fail_on' in retry_conf else []

    def _decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            retries = 0
            if 'retry_attempts' in kwargs:
                retries = int(kwargs['retry_attempts'])
                del kwargs['retry_attempts']

            try:
                return f(*args, **kwargs)
            except Exception as e:
                if type(e) in fail_on:
                    log.warning('Giving up. Re-raising exception %s (as requested by `fail_on` arg)', type(e))
                    raise e
                if retries < max_retries:
                    log.exception(retry_msg, f.__name__, max_retries - retries)
                    sleep(delay)
                    kwargs['retry_attempts'] = retries + 1
                    return wrapper(*args, **kwargs)
                log.exception(fail_msg, f.__name__, max_retries)
                raise e
        return wrapper
    return _decorator


