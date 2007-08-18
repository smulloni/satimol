"""

Description goes here.

"""
from skunk.components.objects import *
from skunk.components.compileCache import *
from skunk.components.handlers import *
from skunk.components.api import *

from skunk.config import Configuration 

Configuration.mergeDefaults(
    useCompileMemoryCache=True,
    compileCachePath=None,
    componentRoot='/',
    defaultCacheExpiration='30s',
    componentCache=None,
    componentExtraGlobals=None,
    componentFileSuffixMap=DEFAULT_FILE_COMPONENT_SUFFIX_MAP,
    componentHandlers=defaultComponentHandlers)

del Configuration
                      
