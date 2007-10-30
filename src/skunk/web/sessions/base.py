from UserDict import DictMixin
import logging
import sha
import time
import uuid

from skunk.config import Configuration
from skunk.web.context import Context, InitContextHook, CleanupContextHook
from skunk.util.importutil import import_from_string

log=logging.getLogger(__name__)

# set configuration variables

Configuration.setDefaults(
    sessionEnabled=False,
    sessionCookieName='skunksession',
    sessionCookiePath='/',
    sessionCookieExtras=None,
    sessionTimeout=18000, # in seconds: 30 minutes
    sessionStaleAction=None,
    )

# hook to enable sessions and put them in the context 

def _init_session_hook(ctxt, env):
    if Configuration.sessionEnabled:
        ctxt.session=Session()

def _session_cleanup_hook(ctxt, env):
    if Configuration.sessionEnabled:
        Context.session.save()
        
def enable():
    if not _init_session_hook in InitContextHook:
        InitContextHook.append(_init_session_hook)
    if not _session_cleanup_hook in CleanupContextHook:
        CleanupContextHook.append(_session_cleanup_hook)

init_service=enable        

class Session(DictMixin):

    def __init__(self):
        self._data=None
        self._session_id=None
        self._dirty=False
        
    def load(self):
        # get cookie and IP from environ
        # if no cookie, create new one and start a new session
        # otherwise, look for cookie in storage
        # if it exists, check whether it is still valid (age and IP)
        # if not, invalidate it and start a new session
        # otherwise, load the session data and touch the session
        cookiename=Configuration.sessionCookieName
        cookieval=Context.request.cookies.get(cookiename)
        if cookieval:
            session_id=self._check_cookie(cookieval)
            if not session_id:
                log.warn("something wrong with session cookie: %s", cookieval)
                Context.request.delete_cookie(cookiename)
            else:
                self._session_id=session_id
                sess=self._get_session()
                if sess:
                    self._data=sess
                else:
                    # perhaps this should never happen?
                    log.warn('creating new session dictionary with old cookie')
                    self._data={}
        else:
            log.info("creating new session")
            cookieval=self._make_cookie()
            Context.response.set_cookie(cookiename,
                                        cookieval,
                                        path=Configuration.sessionCookiePath,
                                        **(Configuration.sessionCookieExtras or {}))
            self._data={}

    def _get_session(self):
        session_data, mtime=Configuration.sessionStore.get_session(self._session_id)
        if not session_data:
            return
        if time.time() - mtime >= Configuration.sessionTimeout:

            staleAction=Configuration.sessionStaleAction
            if staleAction:
                if isinstance(staleAction, str):
                    staleAction=import_from_string(staleAction)
                if isinstance(staleAction, Exception) or issubclass(staleAction, Exception):
                    raise staleAction
                elif callable(staleAction):
                    res=staleAction(self._session_id)
                    if res and isinstance(res, Exception):
                        raise res
                else:
                    log.warn(("don't know what to do with "
                              "Configuration.sessionStaleAction %s" % staleAction))
        else:
            return session_data
        return None
    
    def _get_cookie_salt(self):
        try:
            salt=Configuration.sessionCookieSalt
        except AttributeError:
            salt=None
        if not salt:
            raise RuntimeError, "sessions require the configuration variable sessionCookieSalt to be defined"
        return salt
                
    def _check_cookie(self, cookieval):
        digest, val=cookieval.split(' ', 1)
        salt=self._get_cookie_salt()
        realdigest=sha.sha('%s%s' % (salt, val)).hexdigest()
        if realdigest!=digest:
            log.warn('cookie digest does not match, tossing')
            return None
        try:
            session_id, ip = val.split('|', 1)
        except ValueError:
            log.warn("malformed cookie: %s", val)
            return None
        if ip != Context.request.remote_addr:
            log.warn("ip of cookie, %s, does not match request's (%s)",
                     ip,
                     Context.request.remote_addr)
            return None
        return session_id

    def _make_cookie(self):
        if not self._session_id:
            self._session_id=str(uuid.uuid4())
        ip=Context.request.remote_addr
        val="%s|%s" % (self._session_id,
                       ip)
        salt=self._get_cookie_salt()
        digest=sha.sha('%s%s' % (salt, val)).hexdigest()
        return "%s %s" % (digest, val)
    

    def __getitem__(self, key):
        if self._data is None:
            self.load()
        return self._data[key]

    def __setitem__(self, key, value):
        if self._data is None:
            self.load()
        self._data[key]=value
        self._dirty=True

    def __delitem__(self, key):
        if self._data is None:
            self.load()
        del self._data[key]
        self._dirty=True

    def keys(self):
        if self._data is None:
            self.load()
        return self._data.keys()

    def update(self, d, **kw):
        if self._data is None:
            self.load()
        self._data.update(d, **kw)
        self._dirty=True    

    def save(self):
        if self._dirty:
            Configuration.sessionStore.save(self._session_id, self._data)
            self._dirty=False

    
            
class SessionStore(object):

    def save(self, session_id, data):
        raise NotImplementedError

    def get_session(self, session_id):
        raise NotImplementedError

    def touch(self, session_id):
        raise NotImplementedError

    def delete_session(self, session_id):
        raise NotImplementedError

    def purge(self):
        """delete any sessions that are timed out."""
        raise NotImplementedError

__all__=['Session', 'SessionStore', 'init_service']
