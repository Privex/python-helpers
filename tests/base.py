"""
Various classes / functions / attributes used by test cases (no actual test cases in here)

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
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from privex.helpers.common import empty, empty_if
from privex.helpers.types import STRBYTES

import logging

log = logging.getLogger(__name__)


class EmptyIter(object):
    """A mock iterable object with zero length for testing empty()"""
    def __len__(self):
        return 0


class PrivexBaseCase(unittest.TestCase):
    """
    Base test-case for module test cases to inherit.

    Contains useful class attributes such as ``falsey`` and ``empty_vals`` that are used
    across different unit tests.
    """

    falsey = ['false', 'FALSE', False, 0, '0', 'no']
    """Normal False-y values, as various types"""

    falsey_empty = falsey + [None, '', 'null']
    """False-y values, plus 'empty' values like '' and None"""

    truthy = [True, 'TRUE', 'true', 'yes', 'y', '1', 1]
    """Truthful values, as various types"""

    empty_vals = [None, '']
    empty_lst = empty_vals + [[], (), set(), {}, EmptyIter()]
    empty_zero = empty_vals + [0, '0']


class TempFileBase(PrivexBaseCase):
    _tempdir: Optional[Path]
    temp_files: Union[List[str], Tuple[str, ...]] = ()
    """A list or tuple of temporary filenames to create, with the placeholder content ``hello world``"""
    temp_files_ct: Dict[str, Union[str, bytes]] = {}
    """
    A dictionary of temporary filenames mapped to their contents, as either :class:`.str` or :class:`.bytes`
    """
    
    def setUp(self) -> None:
        self._tempdir = None
        self._setup_temp_files()
        # self.git = Git(repo=self.temp_repo1)

    def tearDown(self) -> None:
        self._cleanup_temp_files()
    
    @property
    def tempdir(self) -> Path:
        if not hasattr(self, '_tempdir') or empty(self._tempdir):
            self._tempdir = Path(tempfile.mkdtemp())
        return self._tempdir
    
    @tempdir.setter
    def tempdir(self, value: Union[str, Path]):
        if not isinstance(value, Path): value = Path(value)
        self._tempdir = value
    
    @tempdir.deleter
    def tempdir(self):
        if not empty(self._tempdir):
            log.info(f"[{self.__class__.__name__}] Removing tempdir folder from filesystem: {self._tempdir}")
            shutil.rmtree(self._tempdir)
        self._tempdir = None
    
    def _setup_temp_files(self):
        for t in self.temp_files:
            log.debug(f"[{self.__class__.__name__}] Creating test file: {t!r} (tempdir: {self.tempdir})")
            self._create_test_file(t)
        for t, c in self.temp_files_ct.items():
            log.debug(f"[{self.__class__.__name__}] Creating test file: {t!r} (tempdir: {self.tempdir})")
            self._create_test_file(t, contents=c)
    
    def _cleanup_temp_files(self):
        # shutil.rmtree(self.tempdir)
        # self.tempdir = None
        del self.tempdir
        
    def _create_test_file(self, filename, folder=None, contents: STRBYTES = "hello world"):
        fpath = Path(empty_if(folder, self.tempdir)) / filename
        log.debug(f"[{self.__class__.__name__}] Creating test file: {filename!r} (full path: '{fpath!s}')")

        with open(str(fpath), 'wb' if isinstance(contents, bytes) else 'w') as fp:
            fp.write(contents)
        return fpath
