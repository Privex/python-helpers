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
from pathlib import Path
from typing import Optional

import pytest
import logging
from privex.helpers import DictObject, STRBYTES, byteify, extras, run_coro_thread, run_sync, stringify
from privex.helpers.crypto import hash as phash

from privex.helpers.crypto.hash import FILE_BLOCK_SIZE, MIN_BLOCK_SIZE
from tests.base import PrivexBaseCase, TempFileBase

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


class TestGit(TempFileBase):
    git: Optional[Git]
    temp_files = ('testfile', 'testfile2', 'testfile3')
    
    def setUp(self) -> None:
        super().setUp()
        # self.temp_repo1 = tempfile.mkdtemp()
        self.git = Git(repo=self.tempdir)
        # self._create_test_file('testfile')
        # self._create_test_file('testfile2')
        # self._create_test_file('testfile3')
    
    def tearDown(self) -> None:
        super().tearDown()
        # shutil.rmtree(self.temp_repo1)
        self.git = None
        # self.temp_repo1 = None

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
    
    # def _create_test_file(self, filename, folder=None):
    #     fpath = join(empty_if(folder, self.temp_repo1), filename)
    #     with open(fpath, 'w') as fp:
    #         fp.write("hello world")
    #     return fpath
    
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


class TestHashing(TempFileBase):
    # git: Optional[Git]
    temp_files = ('hello',)
    temp_files_ct = {
        'lorem.txt': "lorem ipsum dolor",
        'example.txt': ("hello world this is a test. hello world :) " * 50).strip(),
        'test.bin': (b'7\x05{\xdc\xd7\xf2\xc3e\x98G\x07R5H"\xd9\x00\x94\xcd\xc9K\t%U\xdd\x96\x10\xd0\xd1\xa0\xdb\x96\xben\xf5\xafXB\xf5'
                     b'\xf8c\xc4"\x86l(\x0eyX\xbaK7\x03\x1dk\xc9\xfb\x05\x95\xc0\xbb\x08N\x93P/r_\xcc\\\x9c\xa0B\xc2l\xf0\x9a\xe1\xc8\xfb'
                     b'\xe7\x19\x8a\xfe;\xe2\xea\xdf\x99Z\x14\xd3\xbd\xa5\xbbG\xf0\x1e\xd0\xa2VAAH\x86\xb9\x14\xd2\x1f.\xdeo\x82Qr\x1d\xc0'
                     b'\xa68\xc3)\x9d\xb9p{eGa\xdb\x1c\x170\x9f\n+d\xa5w\xcb\x11\xc5(\x04\x0cE\xb3\xb6P=\xbcq\xbc_)\x80\xe8\xb2#\t\xce<\\('
                     b'ep\xa2@\xed\xdf\xd9\xeb\x1c\xd2o\xa0\xac\xb7\xe4\xd4y`\x87\x1f\x80\xf9U9>Q\x07ex\x18\xf5\x82\xb5$1B\x80\xf3\x87\x9c'
                     b'?\\\xb5\x87u\\$\x1f\xadwh\xa1\xb4\xa8\xffMI\xb1\x89"\xbb\xe0\xcc\xc5N\rg\x9b\xe9\xb2\xaa\'\x17\x04\xda=&\xd0\x1cT'
                     b'\x9d\xa5\x0bUS\xa4\xa5\xc3I~\xcb!7}\x9e\x7f\x9b\xeaXvB\xd6yR\x05{') * 50,
    }
    
    known_hashes = DictObject(
        #####
        # To generate Base64 encoded MD5 sums externally (i.e. using a third party tool for independent but compatible hashing),
        # you can use the 'openssl' command line tool, which can both generate the MD5 hash in binary format,
        # and encode binary data into Base64:
        #
        #     $ echo "hello world" | openssl dgst -md5 -binary | openssl enc -base64
        #     b1kCrCNwJL3QwXbLkwY9xA==
        #
        base64=DictObject(
            md5={
                'hello world\n':       'b1kCrCNwJL3QwXbLkwY9xA==',
                'lorem ipsum dolor\n': 'LbkwAQAkEE28U9IyabxwEA==',
            },
            sha1={
                'hello world\n':       'IlljY7PeQLBvmB+4XYIxLowO1RE=',
                'lorem ipsum dolor\n': 'm0xvrfMouEL06IikgQFuOdUQsAw=',
            },
            sha256={
                'hello world\n':       'qUiQTy8PR5uPgZdpSzAYSw0u0cHNKh7A+4XSmaGSpEc=',
                'lorem ipsum dolor\n': 'OgbBpkl8QgraZEvkl36ICpbYg/jsLSLbQFPF2myBJqo=',
            },
            sha512={
                'hello world\n':       '2zl0qX8kB7fK4a5jfAAwaHoRkTJ01XhJJVjjnBbAF96E6s3Ixi/jTuThK0sUKIF/Cbaidgw/imZM6ulNJDSlkw==',
                'lorem ipsum dolor\n': 'XqUh7v6FD5iwkSgzuW8VNUzi7sWwzT7ArN+zapxaJkvIfoDo2H2O9BRslTSUePkTwR+NEaw35x3JarR0qi5sRA==',
            },
        ),
        #####
        # To generate Base32 encoded MD5 sums externally, you can use the 'openssl' command line tool, along with the
        # 'base32' unix utility (pre-installed on OSX)
        #
        #     $ echo "lorem ipsum dolor" | openssl dgst -md5 -binary | base32
        #     FW4TAAIAEQIE3PCT2IZGTPDQCA======
        #     $ echo "hello world" | openssl dgst -md5 -binary | base32
        #     N5MQFLBDOASL3UGBO3FZGBR5YQ======
        #
        base32=DictObject(
            md5={
                'hello world\n':       'N5MQFLBDOASL3UGBO3FZGBR5YQ======',
                'lorem ipsum dolor\n': 'FW4TAAIAEQIE3PCT2IZGTPDQCA======',
            },
            sha1={
                'hello world\n':       'EJMWGY5T3ZALA34YD64F3ARRF2GA5VIR',
                'lorem ipsum dolor\n': 'TNGG7LPTFC4EF5HIRCSICALOHHKRBMAM',
            },
            sha256={
                'hello world\n':       'VFEJATZPB5DZXD4BS5UUWMAYJMGS5UOBZUVB5QH3QXJJTIMSURDQ====',
                'lorem ipsum dolor\n': 'HIDMDJSJPRBAVWTEJPSJO7UIBKLNRA7Y5QWSFW2AKPC5U3EBE2VA====',
            },
            sha512={
                'hello world\n':       '3M4XJKL7EQD3PSXBVZRXYABQNB5BDEJSOTKXQSJFLDRZYFWAC7PIJ2WNZDDC7Y2O4TQSWSYUFCA'
                                       'X6CNWUJ3AYP4KMZGOV2KNEQ2KLEY=',
                'lorem ipsum dolor\n': 'L2SSD3X6QUHZRMERFAZ3S3YVGVGOF3WFWDGT5QFM36ZWVHC2EZF4Q7UA5DMH3DXUCRWJKNEUPD4'
                                       'RHQI7RUI2YN7HDXEWVNDUVIXGYRA=',
            },
        ),
        md5=DictObject({
            'hello world\n':       '6f5902ac237024bdd0c176cb93063dc4',
            'lorem ipsum dolor\n': '2db930010024104dbc53d23269bc7010',
            'test.bin':            'a47e4f8f04a87cb4a1e1a82c48873170',
            'lorem.txt':           'bfab65d69198004a3981e11872ee1b17',
            'example.txt':         'a2ed54efa3bad6c2a25d7933d8edbb50',
        }),
        sha1=DictObject({
            'lorem ipsum dolor\n':  '9b4c6fadf328b842f4e888a481016e39d510b00c',
            'hello world\n':        '22596363b3de40b06f981fb85d82312e8c0ed511',
            'test.bin':             '1ef3516324fabe649eb67381c776b40a5a3533a5',
            'lorem.txt':            '75899ad8827a32493928903aecd6e931bf36f967',
            'example.txt': '18409430abe9e4ced4df55f62fa54314359a7c06',
    
        }),
        sha256=DictObject({
            'lorem ipsum dolor\n': '3a06c1a6497c420ada644be4977e880a96d883f8ec2d22db4053c5da6c8126aa',
            'hello world\n':       'a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447',
            'test.bin':            '5a61514c23e334d282b4683eb43e1b6fef31cc2b8a46a0efd40d2bf53dcf5f2c',
            'lorem.txt':           'ed03353266c993ea9afb9900a3ca688ddec1656941b1ca15ee1650a022616dfa',
            'example.txt': '0549f62480da468db22f8fed57a2478254bd38033c58b8d10d1a09ecf102433b',
    
        }),
        sha512=DictObject({
            'lorem ipsum dolor\n': '5ea521eefe850f98b0912833b96f15354ce2eec5b0cd3ec0acdfb36a9c5a264bc87e80e8d87d8ef4146c95349478f913'
                                   'c11f8d11ac37e71dc96ab474aa2e6c44',
            'hello world\n':       'db3974a97f2407b7cae1ae637c0030687a11913274d578492558e39c16c017de84eacdc8c62fe34ee4e12b4b1428817f'
                                   '09b6a2760c3f8a664ceae94d2434a593',
            'test.bin':            '6ab6efde61566e45cf6b9ec261756b67f0bab9788a0b7af2bdf55cc5a044e259f00f2f10b7a8665469e4bf96f8e1e498'
                                   'f6252d883ff658e6cde86ba22d738f4d',
            'lorem.txt':           'cd813e13d1d3919cdccc31c19d8f8b70bd25e9819f8770a011c8c7a6228536e6c9427b338cd732f2da3c0444dfebef83'
                                   '8b745cdaf3fd5dcba8db24fc83a3f6ef',
            'example.txt':         'f6ab6b096597c6339519fa3e8ecffc89e3af26942a3d13fd1b78f859c1b73052c3cdd6d83db891a7947fff7c72a5b41d'
                                   'd84e13273b10d6ca5be62e882c1b8cfd',
    
        }),
    )
    # def setUp(self) -> None:
    #     self.tempdir = tempfile.mkdtemp()
    #     # self.git = Git(repo=self.temp_repo1)
    #     self._create_test_file('testfile')
    #     self._create_test_file('testfile2')
    #     self._create_test_file('testfile3')
    #
    # def tearDown(self) -> None:
    #     shutil.rmtree(self.temp_repo1)
    #     self.git = None
    #     self.temp_repo1 = None
    
    def _check_hash(self, key: STRBYTES, algo: str = 'md5', b64=False, hexdigest=True):
        res = phash.calc_hash_sync(byteify(key), algo, b64=b64, hexdigest=hexdigest)
        self.assertEqual(res, self.known_hashes[algo][stringify(key)])

    def _check_hash_file(
            self, filename: str, algo: str = 'md5', b64=False, hexdigest=True,
            blocksize=FILE_BLOCK_SIZE, min_blocksize=MIN_BLOCK_SIZE, **kwargs
    ):
        orig_filename = str(filename)
        if not Path(filename).is_absolute():
            filename = str(self.tempdir / filename)
        res = run_coro_thread(
            phash.calc_hash_file, filename=filename, algo=algo, b64=b64, hexdigest=hexdigest,
            blocksize=blocksize, min_blocksize=min_blocksize, **kwargs
        )
        self.assertEqual(res, self.known_hashes[algo][orig_filename])
    
    def test_basic_md5(self):
        self._check_hash('hello world\n', 'md5')
        self._check_hash('lorem ipsum dolor\n', 'md5')
        # res = phash.calc_hash_sync(b"hello world\n", "md5", b64=False, hexdigest=True)
        # self.assertEqual(res, self.known_hashes.md5['hello world\n'])

    def test_basic_sha1(self):
        self._check_hash('hello world\n', 'sha1')
        self._check_hash('lorem ipsum dolor\n', 'sha1')

    def test_basic_sha256(self):
        self._check_hash('hello world\n', 'sha256')
        self._check_hash('lorem ipsum dolor\n', 'sha256')

    def test_basic_sha512(self):
        self._check_hash('hello world\n', 'sha512')
        self._check_hash('lorem ipsum dolor\n', 'sha512')

    def test_threaded_multi_md5(self):
        res = run_coro_thread(
            phash.calc_hashes_thread, "hello world\n", b"lorem ipsum dolor\n", self.temp_files_ct['test.bin'],
            algo='md5', b64=False, hexdigest=True
        )
        self.assertEqual(res[0], self.known_hashes.md5['hello world\n'])
        self.assertEqual(res[1], self.known_hashes.md5['lorem ipsum dolor\n'])
        self.assertEqual(res[2], self.known_hashes.md5['test.bin'])

    def test_threaded_multi_sha256(self):
        res = run_coro_thread(
            phash.calc_hashes_thread, "hello world\n", b"lorem ipsum dolor\n", self.temp_files_ct['test.bin'],
            algo='sha256', b64=False, hexdigest=True
        )
        self.assertEqual(res[0], self.known_hashes.sha256['hello world\n'])
        self.assertEqual(res[1], self.known_hashes.sha256['lorem ipsum dolor\n'])
        self.assertEqual(res[2], self.known_hashes.sha256['test.bin'])

    def test_bin_file_md5(self):
        self._check_hash_file('test.bin', 'md5')

    def test_bin_file_sha1(self):
        self._check_hash_file('test.bin', 'sha1')

    def test_bin_file_sha256(self):
        self._check_hash_file('test.bin', 'sha256')

    def test_bin_file_sha512(self):
        self._check_hash_file('test.bin', 'sha512')
    
    def test_lorem_file(self):
        self._check_hash_file('lorem.txt', 'md5')
        self._check_hash_file('lorem.txt', 'sha1')
        self._check_hash_file('lorem.txt', 'sha256')
        self._check_hash_file('lorem.txt', 'sha512')

    def test_example_file(self):
        self._check_hash_file('example.txt', 'md5')
        self._check_hash_file('example.txt', 'sha1')
        self._check_hash_file('example.txt', 'sha256')
        self._check_hash_file('example.txt', 'sha512')

    def test_threaded_bin_file_md5(self):
        res = run_coro_thread(
            phash.hash_files_threads,
            self.tempdir / 'lorem.txt', self.tempdir / 'example.txt', self.tempdir / 'test.bin',
            algo='md5', b64=False, hexdigest=True
        )
        self.assertEqual(res[0], self.known_hashes.md5['lorem.txt'])
        self.assertEqual(res[1], self.known_hashes.md5['example.txt'])
        self.assertEqual(res[2], self.known_hashes.md5['test.bin'])

    def test_threaded_bin_file_sha512(self):
        res = run_coro_thread(
            phash.hash_files_threads,
            self.tempdir / 'lorem.txt', self.tempdir / 'example.txt', self.tempdir / 'test.bin',
            algo='sha512', b64=False, hexdigest=True
        )
        self.assertEqual(res[0], self.known_hashes.sha512['lorem.txt'])
        self.assertEqual(res[1], self.known_hashes.sha512['example.txt'])
        self.assertEqual(res[2], self.known_hashes.sha512['test.bin'])

    def test_xhash_md5_hashlib(self):
        xh = phash.XHash.from_hashlib('md5', "hello world\n")
        self.assertEqual(xh.hexdigest(), self.known_hashes.md5['hello world\n'])
        self.assertEqual(xh.to_base64(), self.known_hashes.base64.md5['hello world\n'])
        self.assertEqual(xh.to_base32(), self.known_hashes.base32.md5['hello world\n'])

    def test_xhash_sha1_hashlib(self):
        xh = phash.XHash.from_hashlib('sha1', "hello world\n")
        self.assertEqual(xh.hexdigest(), self.known_hashes.sha1['hello world\n'])
        self.assertEqual(xh.to_base64(), self.known_hashes.base64.sha1['hello world\n'])
        self.assertEqual(xh.to_base32(), self.known_hashes.base32.sha1['hello world\n'])

    def test_xhash_sha256_hashlib(self):
        xh = phash.XHash.from_hashlib('sha256', "hello world\n")
        self.assertEqual(xh.hexdigest(), self.known_hashes.sha256['hello world\n'])
        self.assertEqual(xh.to_base64(), self.known_hashes.base64.sha256['hello world\n'])
        self.assertEqual(xh.to_base32(), self.known_hashes.base32.sha256['hello world\n'])

    def test_xhash_sha512_hashlib(self):
        xh = phash.XHash.from_hashlib('sha512', "hello world\n")
        self.assertEqual(xh.hexdigest(), self.known_hashes.sha512['hello world\n'])
        self.assertEqual(xh.to_base64(), self.known_hashes.base64.sha512['hello world\n'])
        self.assertEqual(xh.to_base32(), self.known_hashes.base32.sha512['hello world\n'])
        
    def test_wrappers(self):
        self.assertEqual(str(phash.md5("hello world\n")), self.known_hashes.md5['hello world\n'])
        self.assertEqual(str(phash.sha1("hello world\n")), self.known_hashes.sha1['hello world\n'])
        self.assertEqual(str(phash.sha256("hello world\n")), self.known_hashes.sha256['hello world\n'])
        self.assertEqual(str(phash.sha512("hello world\n")), self.known_hashes.sha512['hello world\n'])

# def test_basic_md5_two(self):
    #     self._check_hash('lorem ipsum dolor\n', 'md5')
    #
    #     # res = phash.calc_hash_sync(b"lorem ipsum dolor\n", "md5", b64=False, hexdigest=True)
    #     # self.assertEqual(res, self.known_hashes.md5['lorem ipsum dolor'])
