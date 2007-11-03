import atexit
import os
import logging
import random
import shutil
import tempfile

from skunk.config import Configuration
from skunk.web import Context, bootstrap, expose
from skunk.web.sessions.diskstore import DiskSessionStore

log=logging.getLogger(__name__)
sessiondir=tempfile.mkdtemp()

def cleanup():
    log.info('cleaning up temporary session directory')
    shutil.rmtree(sessiondir)

atexit.register(cleanup)

Configuration.load_kw(
    logConfig={'level' : 'debug'},
    sessionEnabled=True,
    sessionStore=DiskSessionStore(sessiondir),
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
    
