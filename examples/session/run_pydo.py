import atexit
import os
import logging
import shutil
import tempfile

from skunk.config import Configuration
from skunk.web import Context, bootstrap, expose
from skunk.web.sessions.pydostore import PyDOSessionStore, initDB

log=logging.getLogger(__name__)

dbdir=tempfile.mkdtemp()
dbpath=os.path.join(dbdir, 'sessions.db')

initSQL="""CREATE TABLE skunksessions (id TEXT, data BLOB, modified_at TIMESTAMP)"""

initDB('sqlite3', dbpath, verbose=True, init=initSQL)


def cleanup():
    log.info('cleaning up session db')
    shutil.rmtree(dbdir)
    
atexit.register(cleanup)

Configuration.load_kw(
    logConfig={'level' : 'debug'},
    sessionEnabled=True,
    sessionStore=PyDOSessionStore(),
    sessionCookieSalt='fudgemeaweatherby',
    services=['skunk.web.sessions'],
    controllers=dict(main=__name__),
    routes=[
    (('index', '/'),
     dict(controller='main',
          action='dopage'))
    ])

@expose()
def dopage():
    session=Context.session
    number=session.get('number', 0)
    session['number']=number+1
    session.save()
    return '<em>Your number is %d</em>' % number


if __name__=='__main__':
    bootstrap()
    
