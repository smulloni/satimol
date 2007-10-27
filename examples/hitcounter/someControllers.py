import datetime
import os

import pydo

from skunk.web.controller import expose
from skunk.web.context import Context

def initDB():
    pydo.initAlias('fumanchu', 'sqlite3', dict(database='hit.db'),
                   pool=False)
    if not os.path.exists('hit.db'):
        create_sql="CREATE TABLE hits (id INTEGER NOT NULL PRIMARY KEY, hit_at TIMESTAMP, remote_ip VARCHAR(15))"
        dbi=pydo.getConnection('fumanchu')
        c=dbi.cursor()
        c.execute(create_sql)
        c.close()
        dbi.commit()
    
initDB()

class Hits(pydo.PyDO):
    connectionAlias='fumanchu'
    fields=(pydo.Sequence('id'),
            'hit_at',
            'remote_ip')

    @classmethod
    def register(cls, environ):
        remote_ip=environ.get('REMOTE_ADDR')
        if remote_ip:
            instance=cls.newfetch(remote_ip=remote_ip,
                                  hit_at=datetime.datetime.now())
            return instance
        

class HomeController(object):

    @expose()
    def index(self):
        return """
        <html>
        <head>
        <titleHome Page</title>
        </head>
        <body>
        <h1>Welcome to skunk.web</h1>
        </body>
        </html>
        """

    @expose()
    def robots(self, color):
        Context.response.content_type='text/plain'
        return "Your robots are about to turn " + color

    @expose()
    def hits(self):
        allhits=Hits.getSome(order='id ASC')
        if allhits:
            yield """<html><head><title>Hits</title></head><body><table>
            <tr><th>Id</th><th>Time</th><th>Remote Ip</th></tr>"""
            for hit in allhits:
                yield "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                    hit.id, hit.hit_at.isoformat(), hit.remote_ip)
            yield "</body></html>"
        else:
            yield "no hits"
        

    
    @expose()
    def wsgi(self):
        def an_app(environ, start_response):
            start_response('200 OK', [('Content-Type' , 'text/plain')])
            return ['Hello from a WSGI application']
        return an_app
