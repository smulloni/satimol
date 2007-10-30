import os
import logging
import random

from skunk.config import Configuration
from skunk.web import Context, bootstrap, expose
from skunk.web.sessions.diskstore import DiskSessionStore

logging.basicConfig(level=logging.DEBUG)

Configuration.load_kw(
    sessionEnabled=True,
    sessionStore=DiskSessionStore('/tmp/satimolsessions'),
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
    
