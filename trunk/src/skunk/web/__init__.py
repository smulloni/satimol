
from skunk import __version__

from skunk.config import Configuration

Configuration.setDefaults(
    serverIdentification='Skunkweb %s' % __version__,
    defaultCharset='utf-8',
    defaultContentType='text/html'
    )

del Configuration


