

from skunk.web.fileserver import *
from skunk.web.context import *
from skunk.web.controller import *
from skunk.web.routing import *
from skunk.web.buffet import *

from skunk import __version__
from skunk.config import Configuration
from skunk.web.routing import _redirect

Configuration.setDefaults(
    serverIdentification='Skunkweb %s' % __version__,
    defaultCharset='utf-8',
    defaultContentType='text/html',
    # this overrides variable set in skunk.stml
    redirectFunc=_redirect
    )

del Configuration, __version__, _redirect
from skunk.web.bootstrapper import *

