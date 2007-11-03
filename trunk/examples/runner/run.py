import os
import sys

from skunk.config import Configuration
from skunk.web import ContextMiddleware, RoutingMiddleware, ControllerServer, expose, bootstrap

@expose(content_type='text/plain')
def helloworld():
    return "Hello World"


Configuration.load_kw(
    logConfig={'level' : 'debug', 'filename' : os.path.abspath('debug.log')},
    daemonize=True,
    useThreads=True,
    pidfile=os.path.abspath('simplerunner.pid'),
    controllers=dict(hello=__name__),
    routes=[(('index', '/'),
             {'controller' : 'hello',
              'action' : 'helloworld'})],
    bindAddress='TCP:0.0.0.0:7777')

app=ContextMiddleware(RoutingMiddleware(ControllerServer()))
bootstrap(app)
