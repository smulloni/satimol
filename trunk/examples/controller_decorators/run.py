import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer

from skunk.config import Configuration
from skunk.web import (expose,
                       template,
                       ContextMiddleware,
                       RoutingMiddleware,
                       ControllerServer)

logging.basicConfig(level=logging.DEBUG)

@expose(content_type='text/plain')
def helloworld(name):
    return 'Hello, World, and furthermore, hi there %s' % name

@template('/witch.comp')
@expose()
def dingdong():
    return dict(witch='Brenda',
                status='dead or missing')

Configuration.load_kw(
    componentRoot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files'),
    routes=[
    (('hi', 'helloworld/:name'),
     dict(controller='daone', action='helloworld')),
    (('ding', 'dingdong'),
     dict(controller='daone', action='dingdong')),
    ],
    controllers={'daone' : 'run'},
    showTracebacks=True,
    MvcOn=True)

# no file server needed in this case
app=ContextMiddleware(RoutingMiddleware(ControllerServer())) #DispatchingFileServer())))

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')

if __name__=='__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
