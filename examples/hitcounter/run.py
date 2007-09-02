import logging
import os

from cherrypy.wsgiserver import CherryPyWSGIServer
import pydo

from skunk.config import Configuration
from skunk.web.context import ContextMiddleware, InitContextHook, CleanupContextHook
from skunk.web.controller import expose, ControllerServer
from skunk.web.fileserver  import DispatchingFileServer
from skunk.web.routing import RoutingMiddleware

from someControllers import *

logging.basicConfig(level=logging.DEBUG)
log=logging.getLogger(__name__)

def rollbackConnection(*args, **kwargs):
    db=pydo.getConnection('fumanchu', False)
    if db:
        db.rollback()
        
def record_hit(Context, environ):
    hit=Hits.register(environ)
    if hit:
        hit.commit()

CleanupContextHook.append(record_hit)        

CleanupContextHook.append(rollbackConnection)


Configuration.load_kw(componentRoot=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files'),
                      routes=[
    (('robots', '/robots/:color'), {'controller' : 'home',
                                    'action' : 'robots'}),
    (('wsgi','/wsgi'), {'controller' : 'home', 'action' : 'wsgi'}),
    (('hello', '/hello'), {'controller' : 'home'}),
    (('hits', '/hits'), {'controller' : 'home', 'action' : 'hits'}),
    ],
                      controllers={'home' : HomeController()},
                      MvcOn=True)

app=ContextMiddleware(RoutingMiddleware(ControllerServer(DispatchingFileServer())))

server=CherryPyWSGIServer(('localhost', 7777), app, server_name='localhost')


if __name__=='__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
