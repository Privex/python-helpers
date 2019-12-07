"""
Various helper functions/classes which depend on a certain package being installed.

This constructor file attempts to load each extras module individually, each wrapped with a try/catch
for :class:`ImportError` so that one unavailable package doesn't cause problems.

"""
import logging

log = logging.getLogger(__name__)

__all__ = ['HAS_ATTRS']
HAS_ATTRS = False

try:
    from privex.helpers.extras.attrs import *
    HAS_ATTRS = True
    __all__ += ['AttribDictable']
except ImportError:
    log.debug('privex.helpers.extras __init__ failed to import "attrs", not loading attrs library helpers')

try:
    from privex.helpers.extras.git import __all__ as _git_all
    from privex.helpers.extras.git import *
    __all__ += _git_all
except ImportError:
    log.debug('privex.helpers.extras __init__ failed to import "git", not loading Git helpers')


