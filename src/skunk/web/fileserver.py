import errno
import httplib
import mimetypes
import os
import stat

import webob
import webob.exc

from skunk.components import stringcomp
from skunk.config import Configuration
import skunk.stml
from skunk.util.pathutil import translate_path, untranslate_path

# FileIterable and FileIterator stolen from Ian Bicking's nice WebOb
# file-serving example.  Thanks, Ian.

DEFAULT_HIDDEN_FILE_PATTERNS=[
    '$\.',
    '\.comp$',
    '\.pydcmp$',
    '\.pyinc$',
    '\.pycomp$',
    '\.inc$'
    ]

DEFAULT_INDEX_DOCUMENTS=[
    'index.html',
    'index.xml',
    'index.stml',
    'index.py'
    ]

Configuration.mergeDefaults(
    hiddenFilePatterns=DEFAULT_HIDDEN_FILE_PATTERNS,
    indexDocuments=DEFAULT_INDEX_DOCUMENTS,
    # options for serving static files with x-sendfile 
    staticFileUseXSendFile=False,
    staticFileXSendFileHeader='X-Sendfile',
    staticFileXSendFileHeaderPathTranslated=False
    )
                            

class FileIterable(object):
    
    def__init__(self, filename, start=None, stop=None):
        self.filename = filename
        self.start = start
        self.stop = stop

    def __iter__(self):
        return FileIterator(self.filename, self.start, self.stop)
    
    def app_iter_range(self, start, stop):
        return self.__class__(self.filename, start, stop)

class FileIterator(object):
    chunk_size = 4096

    def __init__(self, filename, start, stop):
        self.filename = filename
        self.fileobj = open(filename, 'rb')
        if start:
            self.fileobj.seek(start)
        if stop is not None:
            self.length = stop - start
        else:
            self.length = None
            
    def __iter__(self):
        return self
    
    def next(self):
        if self.length is not None and self.length <= 0:
            raise StopIteration
        chunk = self.fileobj.read(self.chunk_size)
        if not chunk:
            raise StopIteration
        if self.length is not None:
            self.length -= len(chunk)
            if self.length < 0:
                # Chop off the extra:
                chunk = chunk[:self.length]
        return chunk

class PuntingWSGIMiddleware(object):
    """
    a WSGI application that has a reference to another WSGI application
    to call if it can't handle the request.
    """

    def __init__(self, next_app=None):
        self.next_app=next_app

    def handle_response(self, response, environ, start_response):
        if response:
            return response(environ, start_response)
        if self.next_app:
            return self.next_app(environ, start_response)
        return self.handle_error(httplib.NOT_FOUND)
            
        
class FileServerMixin(object):

    def __call__(self, environ, start_response):
        request=webob.Response(environ)
        try:
            path, realpath, statinfo, status=self.check_path(request.path)
        except webob.exc.HTTPException, exc:
            return exc(environ, start_response)
            
        app=self.serve_file(path, realpath, statinfo, status)
        if app:
            return app(environ, start_response)
        # not sure how to handle "punting"
    
    def serve_file(self, path, realpath, statinfo, status):
        raise NotImplementedError

    def is_hidden(self, path, realpath, statinfo):
        """
        return True if the file in question (which should exist)
        is allowed to be seen.
        """
        return False

    def check_path(self, path):
        """
        takes a request path and looks for a real path related to it.
        returns the path (possibly corrected), the translated path,
        stat() info, and an http status code.
        """
        componentRoot=Configuration.componentRoot
        realpath=translate_path(componentRoot, path)
        try:
            s=os.stat(realpath)
        except IOError, oy:
            if oy.errno==errno.ENOENT:
                return path, realpath, (), httplib.NOT_FOUND
            elif oy.errno==errno.EACCES:
                raise webob.exc.HTTPForbidden()
            # anything else?
            else:
                # let a more general 500 handler clean up
                raise
        else:
            if stat.S_ISDIR(s.st_mode):
                # look for index files
                for ifile in Configuration.indexDocuments:
                    p=os.path.join(realpath, ifile)
                    if os.path.isfile(p):
                        
                        # we have an index document.  Did the url
                        # start with a slash?  If so, redirect to
                        # slashed url.  (We don't do this before the
                        # index document check so that users aren't
                        # given information about the existence of
                        # directories without index documents.)

                        if not path.endswith('/'):
                            raise webob.exc.HTTPMovedPermanently(add_slash=True)

                        return (untranslate_path(componentRoot, p),
                                p,
                                os.stat(p),
                                httplib.OK)
                    
            elif stat.S_ISFILE(s.st_mode):
                # is the file hidden?
                if self.is_hidden(path, realpath, s):
                    return path, realpath, s, httplib.NOT_FOUND
                return path, realpath, s, httplib.OK
            else:
                # don't know what the hell this is
                raise webob.exc.HTTPForbidden()

            
class StaticFileServer(FileServerMixin):

    def serve_file(self, path, realpath, statinfo, status):
        if status==httplib.OK:
            type, encoding=mimetypes.guess_type(realpath)
            if not type:
                type='application/octet-stream'
            if type.startswith('text/') and encoding:
                type+='; charset=%s' % encoding

            if Configuration.staticFileUseXSendFile:
                header=Configuration.staticFileXSendFileHeader
                if Configuration.staticFileXSendFilePathTranslated:
                    xpath=realpath
                else:
                    xpath=path
                    
                # I don't think I need conditional_response here.
                res=webob.Response(content_type=type,
                                   content_length=statinfo.st_size,
                                   last_modified=statinfo.st_mtime)
                res.headers.add(header, xpath)
            else:
                res=webob.Response(content_type=type,
                                   conditional_response=True,
                                   app_iter=FileIterable(realpath),
                                   content_length=statinfo.st_size,
                                   last_modified=statinfo.st_mtime)
                
            # optionally add etag.... @TBD
            # optionally add custom headers for some things.... @TBD

            return res
        elif status==httplib.NOT_FOUND:
            # we should special case this .... @TBD
            # depending on how it is done, it could be moved
            # into the FileServerMixin
            return webob.exc.HTTPNotFound()


class STMLFileServer(FileServerMixin):
    """
    """

    def serve_file(self, path, realpath, statinfo, status):
        pass
    

class DispatchingFileServer(FileServerMixin):
    """
    a file server that dispatches to different handlers on the basis
    of filename (usually extension).
    """

    def serve_file(self, path, realpath, statinfo, status):
        # precondition: either it is 404 or the audio exists and it is OK to serve it

        handler=self.get_handler(path, realpath)
        if not handler:
            # punt somehow
            return None
        
        
            
## class STMLActivePageApp(object):

##     def _check_path(self, path):
##         realpath=translate_path(Configuration.componentRoot, path)
##         try:
##             s=os.stat(realpath)
##         except IOError, oy:
##             if oy.errno==errno.ENOENT:
##                 return None
##             else:
##                 raise
##         else:
##             if stat.S_ISDIR(s.st_mode):
##                 # look for index files
##                 for ifile in Configuration.indexDocuments:
##                     p=os.path.join(realpath, ifile)
##                     if os.path.isfile(p):
##                         return untranslate_path(Configuration.componentRoot, p)
##             elif stat.S_ISFILE(s.st_mode):
##                 return path
##             else:
##                 return None
            

##     def _is_component(self, path):
##         p, ext=os.path.splitext(path)
##         if ext and ext in 
            
        
    
##     def __call__(self, environ, start_response):
##         request=webob.Request(environ)
##         path=request.path
##         effective_path=self._check_path(path)
##         if not effective_path:
##             return webob.exc.HTTPNotFound()
##         try:
##             res=stringcomp(path)
##         except IOError, oy:
            
##             return [res]
        
        


