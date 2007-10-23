import cPickle as pickle
import datetime
import time

import pydo

from skunk.config import Configuration
from skunk.web.sessions.base import SessionStore

class PyDOSessionTable(pydo.PyDO):
    connectionAlias='pydosessions'
    table='skunksessions'
    fields=(pydo.Unique('id'),
            'data',
            'modified_at')

class PyDOSessionStore(SessionStore):
    
    def save(self, session_id, data):
        obj=PyDOSessionTable.getUnique(id=session_id)
        d=dict(modified_at=datetime.datetime.now(),
               data=pickle.dumps(data))
        if obj:
            obj.update(d)
        else:
            obj=PyDOSessionTable.new(id=session_id,
                                     **d)
        obj.commit()
            

    def get_session(self, session_id):
        obj=PyDOSessionTable.getUnique(id=session_id)        
        if obj:
            mtime=time.mktime(obj.modified_at.timetuple())
            data=pickle.loads(obj.data)
            return mtime, data

    def touch(self, session_id):
        obj=PyDOSessionTable.getUnique(id=session_id)
        obj.modified_at=datetime.datetime.now()
        obj.commit()
        
        
    def delete_session(self, session_id):
        PyDOSessionTable.deleteSome(id=session_id)
        PyDOSessionTable.commit()

    def purge(self):
        delta=datetime.timedelta(seconds=Configuration.sessionTimeout)
        when=datetime.datetime.now() - delta
        PyDOSessionTable.deleteSome('modified_at < %s', when)
        PyDOSessionTable.commit()

__all__=['PyDOSessionStore']
