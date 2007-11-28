"""

A session that uses client-side cookie storage; hence, just a
wrapper around an armored cookie.

Issues:

* session expiration needs to be implemented; needs to be stored in cookie.
* session store (for large session) needs interface/implementation(s).
* what is the max cookie size?

"""

from UserDict import DictMixin
import cPickle
from hashlib import sha256
import random
import time
from uuid import uuid4

from skunk.config import Configuration
from skunk.web.context import Context

Configuration.setDefaults(
    sessionTimeout=18000, # in seconds (30 minutes)
    sessionTouchInterval=20, # seconds
    sessionCookieMaxSize=3900, # bytes
    sessionCookieName='skunksession',
    sessionCookieNonce='',
    sessionEnabled=True,
    sessionServerStore=None,
    sessionStaleAction=None
    )

DIGESTSIZE=64
SALTSIZE=4

class Session(object, DictMixin):
    def __init__(self):
        self.dirty=False
        self._data=None
        self._session_id=None
        self._mtime=0

    def session_id():
        def fget(self):
            if not self._session_id:
                self._session_id=str(uuid4())
            return self._session_id
        def fset(self, v):
            self._session_id=v
        def fdel(self):
            self._session_id=None
        return fget, fset, fdel
    session_id=property(*session_id())

    def __getitem__(self, key):
        if self._data is None:
            self.load()
        return self._data[key]

    def __setitem__(self, key, value):
        if self._data is None:
            self.load()
        self._data[key]=value
        self.dirty=True

    def __delitem__(self, key):
        if self._data is None:
            self.load()
        del self._data[key]
        self.dirty=True

    def keys(self):
        if self._data is None:
            self.load()
        return self._data.keys()

    def update(self, d, **kw):
        if self._data is None:
            self.load()
        self._data.update(d, **kw)
        self.dirty=True

    def save(self):
        if not self.dirty:
            return
        dumped=None
        maxCookieSize=Configuration.sessionCookieMaxSize
        if maxCookieSize > 0:
            dumped=cPickle.dumps(self._data, cPickle.HIGHEST_PROTOCOL)
            mtime=int(time.time())
            smtime=str(mtime)
            cookielen=len(smtime)+1+DIGESTSIZE+SALTSIZE+len(dumped)
            if cookielen <= maxCookieSize:
                self._write_cookie(dumped, smtime)
                self.dirty=False
                return
        # we must use session store
        sess_id=self.session_id
        self._write_cookie(cPickle.dumps(sess_id))
        # the store may or may not use pickled data (which may or
        # may not be provided)
        self.sessionStore.save(sess_id, self._data, dumped)
        self.dirty=False

    def _write_cookie(self, pickled, timestring):
        salt=''.join([chr(random.randrange(0, 256)) for x in range(SALTSIZE)])
        val=''.join([timestring,
                     '|',
                     salt,
                     pickled])
        hasher=sha256(val)
        hasher.update(Configuration.sessionCookieNonce)

        Context.response.set_cookie(
            Configuration.sessionCookieName,
            '%s%s' % (hasher.hexdigest(), val),
            Configuration.sessionCookiePath,
            **(Configuration.sessionCookieExtras or {}))
        
    def handle_expired_session(self):
        # add a hook here for alternate behavior

        staleAction=Configuration.sessionStaleAction
        if staleAction:
            if isinstance(staleAction, str):
                staleAction=import_from_string(staleAction)
            if isinstance(staleAction, Exception) or issubclass(staleAction, Exception):
                raise staleAction
            elif callable(staleAction):
                res=staleAction(self)
                if res and isinstance(res, Exception):
                    raise res
        
        self._data={}
        self.dirty=True
        
    def load(self):
        # get info from cookie
        cookieval=Context.request.cookies.get(Configuration.sessionCookieName)
        if cookieval:
            # possibly situations:
            # 1. cookie is invalid (wrong hash, wrong ip, out of date, etc.)
            # 2. cookie has session data
            # 3. cookie has a session id, but no data; must be retrieved elsewhere
            mtime, session_data, session_id=self._read_cookie(cookieval)
            
            if ((Configuration.sessionTimeout > 0)
                and time.time() - mtime > Configuration.sessionTimeout):
                log.warn('session is expired')
                self.handle_expired_session()
                return
        
            if session_data:
                self._data=session_data
            elif session_id:
                self._session_id=session_id
                self._data=self.sessionStore.get_data(session_id)
            else:
                # cookie wasn't valid
                log.warn('invalid session cookie')
                #self._clear_cookie()
                self._data={}
                self.dirty=True
            
        else:
            log.info('creating new session')
            self._data={}
            self.dirty=True

        self._data.setdefault('__mtime__', mtime)

    def _clear_cookie(self):
        Context.response.delete_cookie(
            Configuration.sessionCookieName,
            path=Configuration.sessionCookiePath,
            domain=(Configuration.sessionCookieExtras or {}).get('domain'))
        
    def touch(self):
        if not self._mtime:
            # nasty, involves loading all the session data.
            # add a load variant that doesn't do a remote load or an unpickle?
            # store mtime separately from the session itself?
            self.load()
        if time.time() - self._mtime >= Configuration.sessionTouchInterval:
            self.dirty=True
            self.save()
            

    def _read_cookie(self, cookieval):
        """
        internal method that takes a cookie value and returns a 3-tuple:

        timestamp, session_data, session_id

        If the cookie is valid, exactly one of session_data and session_id will be not None.
        Otherwise, all will be None.
        
        """

        # parse cookie. 
        
        digest, stuff=cookieval[:DIGESTSIZE], cookieval[DIGESTSIZE:]
        hasher=sha256(stuff)
        hasher.update(Configuration.sessionCookieNonce)
        realdigest=hasher.hexdigest()
        if realdigest != digest:
            log.warn("bad digest for session cookie")
            return None, None, None
        try:
            timestring, stuff=stuff.split('|', 1)
        except ValueError:
            log.warn("couldn't get timestamp from session cookie")
            return None, None, None
        else:
            try:
                timestamp=int(timestring)
            except ValueError:
                log.warn("got bad timestamp from session cookie")
                return None, None, None
            
        try:
            data=cPickle.loads(stuff[SALTSIZE:])
        except cPickle.PickleError:
            log.warn('bad pickle for session cookie')
            return None, None, None
        if isinstance(data, str):
            return timestamp, None, data
        else:
            return timestamp, data, None
