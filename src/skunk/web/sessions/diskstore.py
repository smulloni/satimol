import cPickle as pickle
import errno
import logging
import os
import tempfile
import time

from skunk.web.sessions.base import SessionStore

log=logging.getLogger(__name__)

class DiskSessionStore(SessionStore):

    def __init__(self, session_directory):
        self._session_directory=session_directory

    def touch(self, session_id):
        filename=self._get_filename(session_id)
        os.utime(filename)

    def get_session(self, session_id):
        filename=self._get_filename(session_id)
        try:
            fp=open(filename)
        except IOError, e:
            if e.errno==errno.ENOENT:
                return None, None
            raise
        else:
            data=pickle.load(fp)
            mtime=os.path.getmtime(filename)
            return data, mtime
        
                
    def _get_filename(self, session_id):
        parts=[self._session_directory]
        parts.extend(session_id.split('-'))
        filename=os.path.normpath(os.path.join(*parts))
        if filename.startswith(self._session_directory):
            return filename

    def _get_session_id(self, filename):
        if not filename.startswith(self._session_directory):
            return None
        f=filename[:len(self._session_directory)]
        parts=filter(None, f.split(os.path.sep))
        return '-'.join(parts)

    def save(self, session_id, data):
        t=time.time()
        filename=self._get_filename(session_id)
        if not filename:
            log.warn("invalid session id?: %s", session_id)
        dir=os.path.dirname(filename)
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except IOError, oy:
                if oy.errno!=errno.EEXIST:
                    log.exception('error creating session directory')
                    return
        try:
            fd, name=tempfile.mkstemp(suffix='.tmp', dir=dir)
            fp=os.fdopen(fd,  'wb')
            pickle.dump(data, fp)
            fp.close()
            os.rename(name, filename)
        except (IOError, SystemError):
            log.exception('error saving session')

        
    def delete_session(self, session_id):
        filename=self._get_filename(session_id)
        if filename:
            try:
                os.unlink(filename)
            except IOError, e:
                if e.errno==errno.ENOENT:
                    pass
                else:
                    log.exception('error deleting session: %s', filename)
        
__all__=['DiskSessionStore']
