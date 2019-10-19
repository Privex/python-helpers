"""
This file exists to allow for ``python3 -m tests`` to work, as python's module execution option
attempts to load ``__main__`` from a package.
"""
from tests import *

if __name__ == '__main__':
    unittest.main()
