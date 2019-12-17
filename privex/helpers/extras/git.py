from os import getcwd
from os.path import isabs, abspath, join
from typing import Tuple, Optional, Coroutine, Union, Any

from privex.helpers.common import stringify, empty, empty_if
from privex.helpers import STRBYTES
from privex.helpers.asyncx import call_sys_async, awaitable, awaitable_class
from privex.helpers.exceptions import SysCallError


async def _async_sys(proc, *args, write: STRBYTES = None, **kwargs) -> Tuple[str, str]:
    stderr_raise = kwargs.pop('stderr_raise', False)
    strip = kwargs.pop('strip', True)
    out, err = await call_sys_async(proc, *args, write=write, **kwargs)
    out, err = stringify(out, if_none=''), stringify(err, if_none='')
    if strip: out, err = out.strip(), err.strip()
    
    if len(err) > 1 and stderr_raise:
        raise SysCallError(f'Git returned an error: "{err}"')
    
    return out, err


def _repo(repo):
    repo = getcwd() if empty(repo) else repo
    return join(getcwd(), repo) if not isabs(repo) else repo


@awaitable_class
class AsyncGit:
    """
    This class uses the :func:`.awaitable_class` decorator to make the class work both synchronously and asynchronously, without needing
    to duplicate code.
    
    The :func:`.awaitable_class` decorator detects whether the methods are being called from a synchronous, or an asynchronous
    function/method.
    
    * If they're being called from an async function, then a coroutine will be returned, and must be ``await``'ed.
    
    * If they're being called from a synchronous function, then it will spin up an event loop, run the method in
      the event loop, then return the result transparently.
    
    
    **Synchronous usage**::
        
        >>> g = Git()   # Git is an alias for AsyncGit, there is no difference between them
        >>>
        >>> def some_func():
        ...     current_commit = g.get_current_commit()
        ...     print(current_commit)
        'ac52b28f551825160785f9ea7e96f86ccc869cc1'
    
    **Asynchronous usage**::
        
        >>> g = Git()    # Git is an alias for AsyncGit, there is no difference between them
        >>>
        >>> async def some_func():
        ...     current_commit = await g.get_current_commit()
        ...     print(current_commit)
        'ac52b28f551825160785f9ea7e96f86ccc869cc1'

    """
    repo: Optional[str]
    default_version: str
    
    def __init__(self, repo: str = None, default_version: str = 'HEAD', **kwargs):
        self.repo = None
        self.repo = _repo(repo)
        self.default_version = default_version
    
    def _repo(self, repo=None) -> str:
        return self.repo if empty(repo) and not empty(self.repo) else _repo(repo)

    async def _git(self, *args, repo: str = None, strip=True) -> str:
        repo = self._repo(repo)
        out, _ = await _async_sys("git", *args, cwd=repo, strip=strip)
        return out
    
    async def init(self, *args, repo: str = None) -> str:
        return await self._git("init", *args, repo=repo)

    async def add(self, *args, repo: str = None) -> str:
        return await self._git("add", *args, repo=repo)

    async def branch(self, *args, repo: str = None) -> str:
        return await self._git("branch", *args, repo=repo)

    async def commit(self, message: str, *args, repo: str = None) -> str:
        return await self._git("commit", "-m", stringify(message), *args, repo=repo)

    async def checkout(self, branch: str, *args, repo: str = None, new: bool = False) -> str:
        args = ['-b', branch] + list(args) if new else [branch] + list(args)
        return await self._git("checkout", *args, repo=repo)
    
    async def status(self, *args, repo: str = None, concise=True) -> str:
        if concise: args = ['-s'] + list(args)
        return await self._git("status", *args, repo=repo, strip=False)

    async def tag(self, *args, repo: str = None) -> str:
        return await self._git("tag", *args, repo=repo)
    
    async def get_current_commit(self, version: str = None, repo: str = None) -> str:
        """
        Get current commit hash. Optionally specify ``version`` to get the current commit hash for a branch or tag.
        
        **Examples**::
        
            >>> g = Git()
            >>> await g.get_current_commit()
            'ac52b28f551825160785f9ea7e96f86ccc869cc1'
            >>> await g.get_current_commit('2.0.0')    # Get the commit hash for the tag 2.0.0
            '598584a447ba63212ac3fe798c01941badf1c194'
        
        
        :param str version:  Optionally specify a branch / tag to get the current commit hash for.
        :param str repo:     Optionally specify a specific local repository path to run ``git`` within.
        :return str commit_hash: The current Git commit hash
        """
        return await self._git("rev-parse", empty_if(version, self.default_version), repo=repo)
    
    async def get_current_branch(self, repo: str = None) -> str:
        """
        Get current active branch/tag.

        **Examples**::

            >>> g = Git()
            >>> await g.get_current_branch()
            'master'
            >>> await g.checkout('testing', new=True)    # Create and checkout the branch 'testing'
            >>> await g.get_current_branch()
            'testing'
        

        :param str repo:     Optionally specify a specific local repository path to run ``git`` within.
        :return str current_branch: The name of the current checked out branch or tag
        """
        return await self._git("rev-parse", "--abbrev-ref", 'HEAD', repo=repo)

    async def get_current_tag(self, version: str = None, repo: str = None) -> str:
        """
        Get the latest tag on this branch - useful for detecting current version of your python application.

        **Examples**::

            >>> g = Git()
            >>> await g.get_current_tag()          # Get the latest tag on the active branch
            '2.5.0'
            >>> await g.get_current_tag('develop') # Get the latest tag on the branch 'develop'
            '2.5.3'

        :param str version:  Optionally specify a branch / tag to get the latest tag for.
        :param str repo:     Optionally specify a specific local repository path to run ``git`` within.
        :return str current_tag: The name of the latest tag on this branch.
        """
        return await self._git("describe", "--abbrev=0", "--tags", empty_if(version, self.default_version), repo=repo)
    
    async def log(self, *args, repo: str = None, concise=True):
        if concise: args = ['--oneline'] + list(args)
        return await self._git("--no-pager", "log", *args, repo=repo)


Git = AsyncGit
_cwd_git = AsyncGit()

get_current_commit = _cwd_git.get_current_commit
get_current_branch = _cwd_git.get_current_branch
get_current_tag = _cwd_git.get_current_tag

__all__ = [
    'AsyncGit', 'Git', 'get_current_commit', 'get_current_branch', 'get_current_tag', '_repo',
]
