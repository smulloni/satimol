"""

This example demonstrates dispatch based on method. 

"""
import datetime
import logging
import os

import pydo

from skunk.config import Configuration
from skunk.web import (bootstrap,
                       expose,
                       template,
                       Context,
                       CleanupContextHook)


log=logging.getLogger(__name__)

CREATE_SQL="""\
CREATE TABLE wikipage (
title TEXT UNIQUE NOT NULL,
body TEXT NOT NULL DEFAULT '',
edited_at TIMESTAMP NOT NULL
)
"""

def initDB():
    pydo.initAlias('littlewiki',
                   'sqlite3',
                   'littlewiki.db')
    if not os.path.exists('littlewiki.db'):
        conn=pydo.getConnection('littlewiki')
        cursor=conn.cursor()
        cursor.execute(CREATE_SQL)
        conn.commit()

initDB()    

class WikiPage(pydo.PyDO):
    connectionAlias='littlewiki'
    fields=(pydo.Unique('title'),
            'edited_at',
            'body')

@expose()
@template('/littlewiki.comp')
def wikipage_GET(title, message=None):
    page=WikiPage.getUnique(title=title)
    if page:
        return dict(message=message,
                    title=title,
                    body=page.body)
    else:
        return dict(message="This page does not exist yet",
                    title=title,
                    body=None)
    

@expose()
@template('/littlewiki.comp')
def wikipage_POST(title):
    args=Context.request.postvars
    newbody=args.get('body', '').strip()
    if not newbody:
        return show_page(title, "Edit aborted")
    
    page=WikiPage.getUnique(title=title)
    if not page:
        page=WikiPage.newfetch(title=title,
                               edited_at=datetime.datetime.now(),
                               body=newbody)
    else:
        page.body=newbody
        page.edited_at=datetime.datetime.now()
    page.commit()
    return dict(message="Edit saved",
                title=title,
                body=page.body)

routes=[
    (('littlewiki', '*title'),
     dict(controller='littlewiki',
          action='wikipage'))
    ]

controllers=dict(littlewiki=__name__)

comproot=os.path.join(os.path.dirname(__file__), 'files')

Configuration.load_kw(routes=routes,
                      componentRoot=comproot,
                      controllers=controllers,
                      logConfig=dict(level='debug'),
                      showTraceback=True)

def rollbackConnection(*args, **kwargs):
    db=pydo.getConnection('littlewiki', False)
    if db:
        log.debug("rolling back littlewiki connection")
        db.rollback()

CleanupContextHook.append(rollbackConnection)    

if __name__=='__main__':
    bootstrap()
