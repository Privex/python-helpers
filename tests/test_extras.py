"""
Test cases for :py:mod:`privex.helpers.extras`

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
from os.path import join
from typing import Optional

import pytest
import logging
from privex.helpers import extras, empty_if, run_sync
from tests.base import PrivexBaseCase

log = logging.getLogger(__name__)

# Fallback objects to avoid undeclared variables despite pytest skip
attr, AttribDictable, Example = object, object, object

# We only import `attr` and `AttribDictable` if `attrs` is installed.
# We also create the `Example` class for use in test cases.
if extras.HAS_ATTRS:
    import attr
    from privex.helpers.extras import AttribDictable, Git


    @attr.s
    class Example(AttribDictable):
        hello = attr.ib(type=str)
        testing = attr.ib(type=bool, default=True)


@pytest.mark.skipif(extras.HAS_ATTRS is False, reason='extras.HAS_ATTRS is False (is `attrs` installed?)')
class TestAttrs(PrivexBaseCase):
    
    def test_dictable_set_get(self):
        """Test setting and getting attributes on a :class:`.AttribDictable` attrs instance"""
        x = Example(hello='world')
        self.assertEqual(x.hello, 'world')
        self.assertEqual(x['hello'], 'world')
        
        x.hello = 'lorem'
        self.assertEqual(x.hello, 'lorem')
        self.assertEqual(x['hello'], 'lorem')
        
        x['hello'] = 'ipsum'
        self.assertEqual(x.hello, 'ipsum')
        self.assertEqual(x['hello'], 'ipsum')

    def test_dictable_cast_dict(self):
        """Test casting an :class:`.AttribDictable` attrs instance to a dict"""
        x = Example(hello='world')
        d = dict(x)
        self.assertIsInstance(d, dict)
        self.assertEqual(d, dict(hello='world', testing=True))


class TestGit(PrivexBaseCase):
    git: Optional[Git]
    
    def setUp(self) -> None:
        self.temp_repo1 = tempfile.mkdtemp()
        self.git = Git(repo=self.temp_repo1)
        self._create_test_file('testfile')
        self._create_test_file('testfile2')
        self._create_test_file('testfile3')
    
    def tearDown(self) -> None:
        shutil.rmtree(self.temp_repo1)
        self.git = None
        self.temp_repo1 = None

    # noinspection PyUnresolvedReferences
    async def _commit_async(self):
        await self.git.init()
        await self.git.add("testfile")
        await self.git.commit("added testfile")
        _git_log = await self.git.log()
        return _git_log.split('\n')

    # noinspection PyUnresolvedReferences
    async def _checkout_async(self, b, new=False):
        return await self.git.checkout(b, new=new)
    
    def _create_test_file(self, filename, folder=None):
        fpath = join(empty_if(folder, self.temp_repo1), filename)
        with open(fpath, 'w') as fp:
            fp.write("hello world")
        return fpath
    
    def test_init(self):
        res = self.git.init()
        self.assertIn("Initialized empty Git repository", res)

    def test_init_async(self):
        async def _test_init():
            return await self.git.init()

        self.assertIn("Initialized empty Git repository", run_sync(_test_init))

    def test_add(self):
        self.git.init()
        self.git.add("testfile")
        status = self.git.status()
        
        found = False
        for s in status.split('\n'):
            s_status, s_file = s[0:2], s[2:].strip()
            # log.info("s_status: '%s'   s_file: '%s'", s_status, s_file)
            if s_status == "A " and s_file == "testfile":
                found = True
        
        self.assertTrue(found)

    def test_add_async(self):
        async def _add_async(g):
            await g.init()
            await g.add("testfile")
            return await g.status()
        status = run_sync(_add_async, self.git)
        found = False
        for s in status.split('\n'):
            s_status, s_file = s[0:2], s[2:].strip()
            # log.info("s_status: '%s'   s_file: '%s'", s_status, s_file)
            if s_status == "A " and s_file == "testfile":
                found = True
        self.assertTrue(found)

    def test_commit(self):
        self.git.init()
        self.git.add("testfile")
        comm = self.git.commit("added testfile")
        git_log = self.git.log().split('\n')
        self.assertIn("added testfile", git_log[0])

    def test_commit_async(self):
        # async def _commit_async(g):
        #     await g.init()
        #     await g.add("testfile")
        #     await g.commit("added testfile")
        #     _git_log = await g.log()
        #     return _git_log.split('\n')

        git_log = run_sync(self._commit_async)
        self.assertIn("added testfile", git_log[0])

    def test_checkout(self):
        self.git.init()
        self.git.add("testfile")
        self.git.commit("added testfile")
        b = self.git.checkout("test", new=True)
        self.assertIn("Switched to a new branch 'test'", b)
        b = self.git.checkout("master")
        self.assertIn("Switched to branch 'master'", b)

    def test_checkout_async(self):
        run_sync(self._commit_async)
        b = run_sync(self._checkout_async, 'test', new=True)
        self.assertIn("Switched to a new branch 'test'", b)
        b = run_sync(self._checkout_async, 'master')
        self.assertIn("Switched to branch 'master'", b)
    
    def test_get_current_commit(self):
        git_log = run_sync(self._commit_async)
        last_commit = git_log[0].split()[0]
        current_commit = self.git.get_current_commit()
        self.assertIn(last_commit, current_commit)

    def test_get_current_branch(self):
        run_sync(self._commit_async)
        self.assertEqual(self.git.get_current_branch(), 'master')
        run_sync(self._checkout_async, 'testing', new=True)
        self.assertEqual(self.git.get_current_branch(), 'testing')
        run_sync(self._checkout_async, 'master')
        self.assertEqual(self.git.get_current_branch(), 'master')

    def test_get_current_tag(self):
        run_sync(self._commit_async)
        self.git.tag('1.0.0')
        self.assertEqual(self.git.get_current_tag(), '1.0.0')
        # Checkout testing and make a new commit so we can confirm checking tags between branches works
        self.git.checkout('testing', new=True)
        self.git.add('testfile2')
        self.git.commit('added testfile2')
        self.git.tag('1.0.1')
        self.assertEqual(self.git.get_current_tag(), '1.0.1')
        self.assertEqual(self.git.get_current_tag('master'), '1.0.0')



