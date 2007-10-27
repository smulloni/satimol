"""

This example use the lower-level run() function rather than bootstrap().

"""

import logging
import os
import sys

from skunk.config import Configuration
from skunk.web import ContextMiddleware, RoutingMiddleware, ControllerServer, expose
from skunk.web.runner import run

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

@expose(content_type='text/plain')
def helloworld():
    return "Hello World"


Configuration.load_kw(
    daemonize=True,
    useThreads=True,
    serverProtocol='fcgi',
    pidfile=os.path.abspath('simplerunner.pid'),
    controllers=dict(hello=__name__),
    routes=[(('index', '/'),
             {'controller' : 'hello',
              'action' : 'helloworld'})],
    MvcOn=True,
    bindAddress='TCP:0.0.0.0:7777')

app=ContextMiddleware(RoutingMiddleware(ControllerServer()))
run(app)
