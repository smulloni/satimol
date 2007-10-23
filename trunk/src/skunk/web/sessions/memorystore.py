import logging
import time

from skunk.config import Configuration
from skunk.web.sessions.base import SessionStore

log=logging.getLogger(__name__)

# since this is only useful in a single process environment,
# this should have locking. @TBD
class InMemorySessionStore(SessionStore):

    def __init__(self):
        self._sessions={}

    def save(self, session_id, data):
        self._sessions[session_id]=(data, time.time())

    def touch(self, session_id):
        try:
            data, t=self._sessions[session_id]
        except KeyError:
            log.warn('no such session, cannot touch')
        else:
            self._sessions[session_id]=data, time.time()
        
    def get_session(self, session_id):
        return self._sessions.get(session_id)

    def delete_session(self, session_id):
        try:
            del self._sessions[session_id]
        except KeyError:
            pass

    def purge(self):
        now=time.time()
        timeout=Configuration.sessionTimeout
        for sid in self._sessions:
            d,t=self._sessions[sid]
            if now-t >= timeout:
                del self._sessions[sid]
        

__all__=['InMemorySessionStore']


