"""
Requirements / distutils "extras" helpers


Example usage for requirements/extras helpers
---------------------------------------------

Examples::

    >>> extensions = ['cache', 'crypto', 'django']
    # Loads ``extras/{extension}.txt`` for each extension, then returns a dictionary mapping each extension
    # to their requirements
    >>> extras_require(extensions)
    {'cache': ['redis'], 'crypto': ['cryptography>=2.8'], 'django': ['Django']}

    # Load ``example.txt`` and merge sub-requirement lists.
    >>> reqs('example.txt')
    ['privex-loghelper>=1.0', 'privex-jsonrpc', 'requests']



License note
------------

The following functions were taken from Celery's ``setup.py`` file. Since the time of writing
this comment block, they may have been further modified from their originals.

 * strip_comments
 * pip_requirement
 * _reqs
 * reqs
 * extras

Celery is licensed under The BSD License (3 Clause, also known as the new BSD license). The license is an
OSI approved Open Source license and is GPL-compatible(1).

The BSD license text can also be found here: http://www.opensource.org/licenses/BSD-3-Clause

Celery LICENSE file: https://github.com/celery/celery/blob/master/LICENSE

"""
import logging
import os
from privex.helpers.settings import EXTRAS_FOLDER
from typing import Union, Dict

log = logging.getLogger(__name__)


def strip_comments(l: str) -> str:
    """
    Strip any ``#`` comments from a line.
    
    :param str l: A string line, which may contain ``#`` comments
    :return str clean_line: The line ``l`` - stripped of any comments and excess whitespace.
    """
    return l.split('#', 1)[0].strip()


def pip_requirement(req: str) -> list:
    """Check a requirement line for imports ``-r some/path/requirements.txt`` and import them if found."""
    if req.startswith('-r '):
        _, path = req.split()
        return reqs(*path.split('/'))
    return [req]


def _reqs(*f: str) -> list:
    lines = (strip_comments(l) for l in open(os.path.join(os.getcwd(), *f)).readlines())
    return [pip_requirement(r) for r in lines if r]


def reqs(*f: str) -> list:
    """
    Parse requirement file.
    
    Example:
        reqs('default.txt')          # $PWD/default.txt
        reqs('extras', 'redis.txt')  # $PWD/extras/redis.txt
    Returns:
        List[str]: list of requirements specified in the file.
    """
    return [req for subreq in _reqs(*f) for req in subreq]


def extras(*p) -> list:
    """Parse requirement in the extras/ directory."""
    return reqs(EXTRAS_FOLDER, *p)


def extras_require(extra: Union[list, set, tuple]) -> Dict[str, list]:
    """Get map of all extra requirements."""
    return {x: extras(x + '.txt') for x in extra}
