
from skunk import __version__

from skunk.config import Configuration

Configuration.setDefaults(
    serverIdentification='Skunkweb %s' % __version__,
    defaultCharset='utf-8',
    defaultContentType='text/html'
    )

del Configuration

from skunk.web.fileserver import *
from skunk.web.context import *
from skunk.web.controller import *
try:
    from skunk.web.routing import *
except ImportError:
    pass
