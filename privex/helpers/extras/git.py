"""
Helper functions / classes for using ``git`` within a python application.

Quickstart with the aliases ``get_current_commit``, ``get_current_tag`` and ``get_current_branch``
--------------------------------------------------------------------------------------------------

To save you time, we pre-instantiate :class:`._AsyncGit` at :attr:`._cwd_git` within the module, using the current working
directory as the repo, allowing you to quickly call some of the most common Git functions without having to instantiate
a ``Git()`` instance::

    >>> from privex.helpers import get_current_tag, get_current_branch, get_current_commit
    >>> get_current_commit()
    '8418c964b35d76bcad984f5102ac605be0ae7b58'
    >>> get_current_branch()
    'master'
    >>> get_current_tag()
    '2.14.0'


Using the Git class ( :class:`._AsyncGit` )
-------------------------------------------

Basic usage of :class:`.Git` ( :class:`._AsyncGit` )
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For full functionality, you'll want to import ``Git`` and create an instance.

Despite the fact that the Git class methods are all async methods, they can be called from within a synchronous app or context, and
they'll generally work as if they were synchronous functions, thanks to the :func:`.awaitable_class` decorator.


    >>> from privex.helpers import Git
    >>> g = Git(repo='/home/user/projects/some_app')
    >>> g.get_current_commit()
    'e962f66650729e2f66395b45e1600f61d8461378'
    >>> g.add("docs", "README.md")
    >>> g.commit("1.2.3 - Added documentation and README.md")
    >>> g.tag('1.2.3')
    >>> g.get_current_tag()
    '1.2.3'

Using Git commands which don't have a method implemented
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The magic method :meth:`._AsyncGit.__getattr__` allows you to call Git sub-commands which aren't yet implemented as a method, simply
by calling the command's name as a method on the class instance.

If the sub-command contains ``-`` 's (dashes) in it's name, simply replace the dashes with underlines - ``__getattr__`` will
automatically rewrite the underlines (``_``) back into dashes (``-``).

For example, we can run ``git count-objects`` by calling the method ``count_objects``, even though ``count_objects`` isn't
implemented as a method. Just like normal methods, we can call it synchronously from non-async functions/methods, and use async ``await``
when using it within asynchronous code::

    >>> await g.count_objects()
    '2061 objects, 8880 kilobytes'
    >>> g.count_objects('-v')
    'count: 2061\nsize: 8880\nin-pack: 0\npacks: 0\nsize-pack: 0\nprune-packable: 0\ngarbage: 0\nsize-garbage: 0'



"""
from os import getcwd
from os.path import isabs, abspath, join
from typing import Tuple, Optional, Callable, Coroutine, Union, Any, AnyStr

from privex.helpers.common import stringify, empty, empty_if
from privex.helpers import STRBYTES
from privex.helpers.asyncx import call_sys_async, awaitable, awaitable_class
from privex.helpers.exceptions import SysCallError


async def _async_sys(proc, *args, write: STRBYTES = None, **kwargs) -> Tuple[str, str]:
    """Small async wrapper function for :func:`.call_sys_async` to simplify calling ``git``, including detecting git errors"""
    stderr_raise = kwargs.pop('stderr_raise', False)
    strip = kwargs.pop('strip', True)
    out, err = await call_sys_async(proc, *args, write=write, **kwargs)
    out, err = stringify(out, if_none=''), stringify(err, if_none='')
    if strip: out, err = out.strip(), err.strip()
    
    if len(err) > 1 and stderr_raise:
        raise SysCallError(f'Git returned an error: "{err}"')
    
    return out, err


def _repo(repo: str = None) -> str:
    """
    A very simple private helper function which ensures the passed ``repo`` is an absolute directory path. If ``repo`` is blank,
    then simply returns the current working directory. Converts relative paths into absolute paths by joining them to :func:`.getcwd`
    """
    repo = getcwd() if empty(repo) else repo
    return join(getcwd(), repo) if not isabs(repo) else repo


class _AsyncGit:
    """
    Git CLI wrapper class - methods can be used both synchronously and async via ``AsyncGit`` / ``Git`` (aliases, both are the same)
    
    This class uses the :func:`.awaitable_class` decorator to make the class work both synchronously and asynchronously, without needing
    to duplicate code.
    
    The :func:`.awaitable_class` decorator detects whether the methods are being called from a synchronous, or an asynchronous
    function/method.
    
    * If they're being called from an async function, then a coroutine will be returned, and must be ``await``'ed.
    
    * If they're being called from a synchronous function, then it will spin up an event loop, run the method in
      the event loop, then return the result transparently.
    
    
    **Synchronous usage**::
        
        >>> from privex.helpers import Git
        >>> g = Git()   # Git is an alias for AsyncGit, there is no difference between them
        >>>
        >>> def some_func():
        ...     current_commit = g.get_current_commit()
        ...     print(current_commit)
        'ac52b28f551825160785f9ea7e96f86ccc869cc1'
    
    **Asynchronous usage**::
        
        >>> from privex.helpers import Git
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

    async def git(self, *args, repo: str = None, strip=True, stderr=False) -> Union[str, Tuple[str, str]]:
        """
        Wrapper async method for calling ``git`` executable command against a repo - casts args to :class:`str`.
        
        This is intended for use internally by :class:`._AsyncGit` methods, but is under a non-private method name to allow you to call
        Git commands semi-directly if the class methods are getting in the way.
        
        Example::
        
            >>> Git().git('commit', '--amend', '-a', '-m', 'lorem ipsum dolor')
        
        
        :param AnyStr|int|float|object|Any args: Positional command line arguments to pass to ``git``. Most formats are fine, as long
                                                 as they can be casted into a :class:`str`
        
        :param str|None repo: The repository to run the command against. When ``None``, uses the value of :attr:`.repo`
        
        :param bool strip: (Default: ``True``) Whether to run :meth:`str.strip` on the string outputs of the command
        
        :param bool stderr: (Default: ``False``) When ``True``, includes the stderr output in the response like so: ``(stdout, stderr)``
                            When ``False``, simply returns ``stdout`` directly as a :class:`str`
          
        :return str stdout: (when ``stderr=False``) The text outputted to stdout by the command
        :return Tuple[str,str] stdout_err: (when ``stderr=True``) A :class:`tuple` containing ``(stdout: str, stderr: str)``
        """
        repo = self._repo(repo)
        out, err = await _async_sys("git", *[stringify(a) for a in args], cwd=repo, strip=strip)
        
        return (out, err) if stderr else out
    
    _git = git
    
    async def init(self, *args, repo: str = None) -> str:
        """
        Use like ``git init``

        **Example**::

            >>> Git().init()
        
        **Initialise a different repo from the one passed in the constructor**::
        
            >>> Git().init(repo="/home/user/myproject")

        """
        return await self.git("init", *args, repo=repo)

    async def add(self, *args, repo: str = None) -> str:
        """
        Use like ``git add``
        
        Example:
            
            >>> Git().add("docs/", "README.md")
        
        """
        return await self.git("add", *args, repo=repo)

    async def branch(self, *args, repo: str = None) -> str:
        return await self.git("branch", *args, repo=repo)

    async def commit(self, message: Optional[Union[str, bool]], *args, repo: Optional[str] = None) -> str:
        """
        Calls ``git commit`` with the arguments ``-m "message" [args]``, where each positional argument passed after the message
        is passed as a command line argument.
        
        To disable prepending ``-m`` to the arguments, pass ``None`` as the ``message`` and only your specified ``args`` will be
        passed along to ``git commit``.
        
        You may also set ``message`` to ``False`` which will call ``git commit --allow-empty-message [args]`` instead of
        prepending ``-m``.
        
        
        **Basic Usage**
        
        Standard commit with a message, plus the argument '-a'::
        
            >>> g = Git()
            >>> g.commit("added example.txt", "-a")
        
        Pass ``None`` as the message to disable prepending ``-m`` to the git arguments. For example, the following call commits
        the current staged changes, while re-using the commit message/author info/timestamp from the previous
        commit ``9e27d7233ac5bc59bc37c0572a401068fbd5e6be``::
        
            >>> g.commit(None, "-C", "9e27d7233ac5bc59bc37c0572a401068fbd5e6be")
        
        Pass ``False`` as the message for an easy way to call ``git commit --allow-empty-message``, plus any additional
        arguments you might pass::
        
            >>> g.commit(False, '-a')
        
        
        :param str|bool message: The git commit message to commit with. Alternatively ``None`` to remove the default ``-m``, or
                                 ``False`` as a shortcut for ``--allow-empty-message`` instead of ``-m``.
        :param args: Additional CLI arguments to pass to ``git commit``
        :param str repo: (as a kwarg only!) An absolute path to a Git repository to run ``git commit`` within. By default, this is
                         ``None`` which results in the repo passed in the constructor ( :attr:`.repo` ) being used.
        :return str stdout: The string text printed to stdout by ``git commit`` while running the command.
        """
        if message is None:
            return await self.git("commit", *args, repo=repo)
        if message is False:
            return await self.git("commit", "--allow-empty-message", *args, repo=repo)
        return await self.git("commit", "-m", stringify(message), *args, repo=repo)

    async def checkout(self, branch: str, *args, repo: str = None, new: bool = False) -> str:
        args = ['-b', branch] + list(args) if new else [branch] + list(args)
        return await self.git("checkout", *args, repo=repo)
    
    async def status(self, *args, repo: str = None, concise=True) -> str:
        if concise: args = ['-s'] + list(args)
        return await self.git("status", *args, repo=repo, strip=False)

    async def tag(self, *args, repo: str = None) -> str:
        return await self.git("tag", *args, repo=repo)
    
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
        return await self.git("rev-parse", empty_if(version, self.default_version), repo=repo)
    
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
        return await self.git("rev-parse", "--abbrev-ref", 'HEAD', repo=repo)

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
        return await self.git("describe", "--abbrev=0", "--tags", empty_if(version, self.default_version), repo=repo)
    
    async def log(self, *args, repo: str = None, concise=True):
        if concise: args = ['--oneline'] + list(args)
        return await self.git("--no-pager", "log", *args, repo=repo)

    def __getattr__(self, item: str) -> Union[Callable[[Any, Any, Any, Any, Any], Coroutine], callable, Any]:
        """
        If an attribute doesn't exist, this method will return a :func:`.awaitable` function that simply calls :meth:`.git` with the
        attribute name as the first argument, followed by any additional positional/keyword arguments.
        
        Since a lot of git commands have ``-`` in their name, but Python doesn't support attributes containing ``-``, non-existent
        attributes will have ``_`` replaced with ``-`` when calling :meth:`.git` with their name.
        
        For example, ``git.count_objects('-v')`` would become ``git count-objects -v``
        
        This allows most unimplemented ``git`` sub-commands to function when called as a method, for example, at the
        current point in time, neither the ``describe`` command, nor ``count-objects`` are implemented as a method, but both can still be
        called synchronously or asynchronously and it will work::
        
            >>> from privex.helpers import Git
            >>> g = Git()
            >>> g.describe('--tags')
            '2.14.0-1-g8418c96'
            >>> await g.describe('--tags')
            '2.14.0-1-g8418c96'
            >>> g.count_objects()
            '2061 objects, 8880 kilobytes'
            >>> await g.count_objects()
            '2061 objects, 8880 kilobytes'
        
        
        """
        try:
            value = super().__getattribute__(item)
            return value
        except AttributeError:
            @awaitable
            def _git(*args, **kwargs):
                return self.git(item.replace('_', '-'), *args, **kwargs)
            return _git


AsyncGit = awaitable_class(_AsyncGit)

Git = AsyncGit
_cwd_git = AsyncGit()
"""
:attr:`._cwd_git` is a pre-instantiated :class:`._AsyncGit` instance which uses the current working directory as the current git repo.

This instance is used by global instance method aliases :attr:`.get_current_commit`, :attr:`.get_current_branch`, :attr:`.get_current_tag`,
to allow developers to easily call methods such as :meth:`._AsyncGit.get_current_tag` without having to instantiate the
:class:`.Git` class.
"""

get_current_commit = _cwd_git.get_current_commit
"""Alias for :meth:`.AsyncGit.get_current_commit` (using pre-instantiated AsyncGit at :attr:`._cwd_git`)"""

get_current_branch = _cwd_git.get_current_branch
"""Alias for :meth:`.AsyncGit.get_current_branch` (using pre-instantiated AsyncGit at :attr:`._cwd_git`)"""

get_current_tag = _cwd_git.get_current_tag
"""Alias for :meth:`.AsyncGit.get_current_tag` (using pre-instantiated AsyncGit at :attr:`._cwd_git`)"""

__all__ = [
    'AsyncGit', 'Git', 'get_current_commit', 'get_current_branch', 'get_current_tag', '_repo',
]
