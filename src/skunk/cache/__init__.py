#

"""

A library for the memoization of functions and other callables.

"""

from skunk.cache.exceptions import *
from skunk.cache.base import *
from skunk.cache.policy import *
from skunk.cache.memoryCache import *
from skunk.cache.diskCache import *
from skunk.cache.decorator import *
from skunk.cache.log import *

from skunk.config import Configuration as _c
_c.setDefaults(defaultCacheExpiration='30s',
               defaultCachePolicy=YES,
               defaultCacheOndefer=None)
del _c


