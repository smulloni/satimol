"""

Description goes here.

"""
from skunk.components.objects import *
from skunk.components.compileCache import *
from skunk.components.context import *
from skunk.components.exceptions import *
from skunk.components.handlers import *
from skunk.components.api import *

from skunk.config import Configuration 

Configuration.setDefaults(
    useCompileMemoryCache=True,
    compileCachePath=None,
    componentRoot='/',
    componentCache=':memory:',
    componentCacheDebugMemcached=False,
    componentExtraGlobals=None,
    componentFileSuffixMap=DEFAULT_FILE_COMPONENT_SUFFIX_MAP,
    componentHandlers=defaultComponentHandlers)

del Configuration
                      
