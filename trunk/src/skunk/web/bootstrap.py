"""

This module contains service-loading code.

It could also contain a bootstrap() method that would:

  1. load the configuration in some standard way
  2. load the services
  3. compose the middleware according to configuration
  4. start a server

I'll probably do this eventually, but right now I'm ok with
doing this manually in a module. 

"""
import logging

from skunk.config import Configuration
from skunk.util.importutil import import_from_string

log=logging.getLogger(__name__)

Configuration.setDefaults(services=[],
                          wsgiPipeline=(
    'skunk.web.context:ContextMiddleware',
    'skunk.web.routing:RoutingMiddleware',
    'skunk.web.controller:ControllerServer',
    'skunk.web.fileserver:DispatchingFileServer'
    )
                          )


def load_services():
    for service in Configuration.services:
        try:
            log.info("loading service '%s'", service)
            s=import_from_string(service)
            if callable(s):
                log.debug("service is callable, calling")
                s()
        except:
            exception("error loading service %s", service)
            raise


def make_app():
    """
    several problems here.

    1. an app might be specified other than as a string.
    2. this imposes a restriction on constructors (that's OK)
    3. this uses configuration, which isn't scoped if this itself
       creates the ContextMiddleware.  Perhaps that always must
       come first.
       
    """
    pipeline=Configuration.wsgiPipeline
    app=None
    for spec in reversed(pipeline):
        cls=import_from_string(spec)
        if app:
           app=cls(app)
        else:
            app=cls()
    return app
        
