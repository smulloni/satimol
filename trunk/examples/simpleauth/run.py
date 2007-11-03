import os

from skunk.config import Configuration, GlobMatcher
from skunk.util.pathutil import relpath
from skunk.web.auth import CookieFileAuthorizer
from skunk.web import ContextMiddleware, DispatchingFileServer, bootstrap

Configuration.load_kw(componentRoot=_relpath(__file__, 'files'),
                      services=['skunk.web.auth'],
                      logConfig=dict(level='debug')
                      )
Configuration.addMatcher(GlobMatcher('path', '/protected/*',
                                     authorizer=CookieFileAuthorizer(
    _relpath(__file__, 'auth.conf'),
    'nancynonce',
    '/login.comp')))

app=ContextMiddleware(DispatchingFileServer())

if __name__=='__main__':
    bootstrap(app)

                                     

    
    


