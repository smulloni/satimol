"""
This example shows how to do resource management for a db connection.
The ORM PyDO is used, and it is initialized globally in the start script.
A function that rolls back any existing transactions is added to the
CleanupContextHook.

"""

import datetime
import logging
import os

import pydo

from skunk.config import Configuration
from skunk.web import InitContextHook, CleanupContextHook, Context, bootstrap, expose
from skunk.util.pathutil import relpath

def initDB():
    pydo.initAlias('hitcounter', 'sqlite3', dict(database='hit.db'),
                   pool=False)
    if not os.path.exists('hit.db'):
        create_sql="""CREATE TABLE hits (
        id INTEGER NOT NULL PRIMARY KEY,
        path TEXT NOT NULL,
        hit_at TIMESTAMP,
        remote_ip VARCHAR(15)
        )"""
        dbi=pydo.getConnection('hitcounter')
        c=dbi.cursor()
        c.execute(create_sql)
        c.close()
        dbi.commit()
    
initDB()

class Hits(pydo.PyDO):
    connectionAlias='hitcounter'
    fields=(pydo.Sequence('id'),
            'path',
            'hit_at',
            'remote_ip')

    @classmethod
    def register(cls, environ):
        return cls.newfetch(remote_ip=environ['REMOTE_ADDR'],
                            path=environ['PATH_INFO'],
                            hit_at=datetime.datetime.now())

class HitController(object):

    @expose()
    def show_hits(self):
        allhits=Hits.getSome(order='id ASC')
        if allhits:
            yield """<html><head><title>Hits</title></head><body><table>
            <tr><th>Id</th><th>Time</th><th>Path</th><th>Remote Ip</th></tr>"""
            for hit in allhits:
                yield "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    hit.id, hit.hit_at.isoformat(), hit.path, hit.remote_ip)
            yield "</body></html>"
        else:
            yield "no hits"
        


log=logging.getLogger(__name__)

def rollbackConnection(*args, **kwargs):
    db=pydo.getConnection('hitcounter', False)
    if db:
        log.debug("rolling back hitcounter connection")
        db.rollback()
        
def record_hit(Context, environ):
    Hits.register(environ).commit()

CleanupContextHook.append(record_hit)        
CleanupContextHook.append(rollbackConnection)

comproot=os.path.join(os.path.dirname(__file__), 'files')
Configuration.load_kw(componentRoot=comproot,
                      logConfig=dict(level='debug'),
                      routes=[
    (('hits', '/hits'), {'controller' : 'hits', 'action' : 'show_hits'}),
    ],
                      controllers={'hits' : HitController()})



if __name__=='__main__':
    bootstrap()

