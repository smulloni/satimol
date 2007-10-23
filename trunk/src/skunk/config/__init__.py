"""
skunk.config contains a global, thread-local configuration object
that can be scoped according to some environment (in particular,
according to a WSGI/CGI environ).

"""
from skunk.config.obj import Configuration
from skunk.config.scopes import *

class ConfigurationError(Exception):
    pass
