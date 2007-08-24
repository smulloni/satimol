"""

WSGI applications for serving active STML pages (or Python skunk components)
and static documents.



"""


import errno
import httplib
import logging
import md5
import mimetypes
import os
import re
import stat

try:
    import chardet
except ImportError:
    chardet=None
    
import webob
import webob.exc

from skunk.components import stringcomp
from skunk.config import Configuration
import skunk.stml
from skunk.util.importutil import import_from_string
from skunk.util.pathutil import translate_path, untranslate_path

log=logging.getLogger(__name__)

__all__=['DispatchingFileServer', 'StaticFileServer']

# FileIterable and FileIterator stolen from Ian Bicking's nice WebOb
# file-serving example.  Thanks, Ian.

DEFAULT_HIDDEN_FILE_PATTERNS=[
    '$\.',         # UNIX hidden files
    '\.comp$',     # skunk component
    '\.pydcmp$',   # skunk data component
    '\.pyinc$',    # skunk include
    '\.pycomp$',   # skunk component
    '\.inc$',      # skunk include
    '~$'           # backup file
    ]

DEFAULT_INDEX_DOCUMENTS=[
    'index.html',
    'index.stml',
    'index.xml',    
    'index.py'
    ]

DEFAULT_FILE_DISPATCHERS=[('.*\.(stml|html|py)$',
                           'skunk.web.fileserver:STMLFileHandler')]

Configuration.mergeDefaults(
    hiddenFilePatterns=DEFAULT_HIDDEN_FILE_PATTERNS,
    indexDocuments=DEFAULT_INDEX_DOCUMENTS,
    
    # options for serving static files with x-sendfile 
    staticFileUseXSendFile=False,
    staticFileXSendFileHeader='X-Sendfile',
    staticFileXSendFileHeaderPathTranslated=True,
    
    # HTTPException classes 
    errorHandlers=webob.exc.status_map,
    staticFileAddEtag=False,
    defaultCharset='utf-8',
    
    # whether to guess the character encoding of static text files
    # with chardet, if available
    staticFileUseChardet=True,

    # for dispatching server, a list of (pattern, handler) pairs
    fileDispatchers=DEFAULT_FILE_DISPATCHERS
    
    )

def get_http_exception(status, *args, **kwargs):
    handlerclass=Configuration.errorHandlers[status]
    handler=handlerclass(*args, **kwargs)
    return handler

def handle_error(status, environ, start_response, *args, **kwargs):
    handler=get_http_exception(status, *args, **kwargs)
    return handler(environ, start_response)

class FileIterable(object):
    
    def __init__(self, filename, start=None, stop=None):
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

class Punter(object):
    """
    a WSGI application that may have a reference to another WSGI
    application to punt to if it can't handle the request itself.  If
    the application wants to punt, it calls self.punt(); if it has an attribute
    called "next_app" it should be a WSGI application, which will be used to
    handle the request.  If it does not, or if the attribute is None, a 404
    response will be returned instead.
    """

    def punt(self, environ, start_response):
        next_app=getattr(self, 'next_app', None)
        if next_app:
            return next_app(environ, start_response)
        return handle_error(httplib.NOT_FOUND, environ, start_response)
        
class FileServerBase(Punter):

    def __call__(self, environ, start_response):
        request=webob.Request(environ)
        try:
            path, realpath, statinfo=self.check_path(request.path)
        except webob.exc.HTTPException, exc:
            return exc(environ, start_response)
            
        app=self.serve_file(path, realpath, statinfo, request)
        if app:
            return app(environ, start_response)
        self.punt(environ, start_response)
    
    def serve_file(self, path, realpath, statinfo, request):
        raise NotImplementedError

    def is_hidden(self, path, realpath, statinfo):
        """
        return True if the file in question (which should exist)
        is allowed to be seen.

        by default, this matches each pattern in
        Configuration.hiddenFilePatterns against the path and returns
        True if one of them matches.  The patterns can either be
        callables that take three positional arguments (path,
        realpath, statinfo) or regexes (either strings or compiled).
        """
        for h in Configuration.hiddenFilePatterns:
            if callable(h) and h(path, realpath, statinfo):
                return True
            elif re.match(h, path):
                return True
        return False

    def check_path(self, path):
        """
        takes a request path and looks for a real path related to it.
        returns the path (possibly corrected), the translated path, and
        stat() info. If is can be determined that the correct status code
        for this resource is not 200, it will raise a webob.exc.HTTPException
        here.
        """
        componentRoot=Configuration.componentRoot
        realpath=translate_path(componentRoot, path)
        try:
            s=os.stat(realpath)
        except IOError, oy:
            if oy.errno==errno.ENOENT:
                raise get_http_exception(httplib.NOT_FOUND)
            elif oy.errno==errno.EACCES:
                raise get_http_exception(httplib.FORBIDDEN)
            # anything else?
            else:
                # let a more general 500 handler clean up.
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
                            raise get_http_exception(httplib.MOVED_PERMANENTLY,
                                                     add_slash=True)
                            
                        return (untranslate_path(componentRoot, p),
                                p,
                                os.stat(p))
                raise get_http_exception(httplib.NOT_FOUND)
            elif stat.S_ISREG(s.st_mode):
                # is the file hidden?
                if self.is_hidden(path, realpath, s):
                    raise get_http_exception(httplib.NOT_FOUND)
                return path, realpath, s
            else:
                # don't know what the hell this is
                raise get_http_exception(httplib.FORBIDDEN)

            
class StaticFileServer(FileServerBase):
    """
    WSGI application that serves static files.
    """

    def serve_file(self, path, realpath, statinfo, request):

        type, dontbother=mimetypes.guess_type(realpath)
        if not type:
            type='application/octet-stream'
        if type.startswith('text/'):
            if Configuration.defaultCharset:
                res.charset=Configuration.defaultCharset
            elif chardet and Configuration.staticFileUseChardet:
                res.charset=chardet.detect(open(realpath).read(1024))['encoding']
            
        if Configuration.staticFileUseXSendFile:
            header=Configuration.staticFileXSendFileHeader
            if Configuration.staticFileXSendFilePathTranslated:
                xpath=realpath
            else:
                xpath=path

            # I don't think I need conditional_response here; if you
            # are using X-Sendfile your web server should be able to
            # deal (at least it can it later versions of lighttpd)
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

            if Configuration.staticFileAddEtag:
                # this can be more efficient than generating an Etag
                # from the response body, so we're making it possible
                # to do here rather than in middleware
                etag='%s|%d|%d' % (realpath, statinfo.st_size, statinfo.st_mtime)
                etag=md5.md5(etag).hexdigest()
                res.headers['etag']=etag

        # Other custom header munging is left for middleware.
        return res

class STMLFileHandler(FileServerBase):
    """
    a file server that specializes in STML and skunk component files.

    This treats everything like a skunk component, so you don't want
    to use this directly; you want the DispatchingFileServer.
    """

    def serve_file(self, path, realpath, statinfo, request):
        """
        """
        response=webob.Response(content_type='text/html',
                                charset=Configuration.defaultCharset)
        body=stringcomp(path, REQUEST=request, RESPONSE=response)
        # if you set the body of the response yourself, that will
        # replace anything output by the component.  Normally you
        # won't be doing that in this context.
        if not response.body:
            response.body=body
        return response
        

class DispatchingFileServer(FileServerBase):
    """
    a file server that dispatches to different handlers on the basis
    of filename (usually extension).  
    """

    _default=StaticFileServer()
    _handlercache={}

    def get_handler(self, path):

        handler=None 
        for pat, h in Configuration.fileDispatchers:
            if callable(pat):
                matcher=pat
            elif isinstance(pat, basestring):
                matcher=re.compile(pat).match
            elif hasattr(pat, 'match'):
                matcher=pat.match
            m=matcher(path)
            if m:
                log.debug("found match against path %s: %s ", path, m)
                handler=h
                break
        log.debug('handler: %s', handler)
        if not handler:
            # return static file handler
            return self._default
        if isinstance(handler, basestring):
            try:
                return self._handlercache[handler]
            except KeyError:
                handlerclass=import_from_string(handler)
                handlerinstance=handlerclass()
                self._handlercache[handler]=handlerinstance
                return handlerinstance
        else:
            return handler
        

    
    def serve_file(self, path, realpath, statinfo, request):
        handler=self.get_handler(path)
        assert handler, "get_handler didn't return a handler"
        return handler.serve_file(path, realpath, statinfo, request)


def _test():
    import sys
    logging.basicConfig(level=logging.DEBUG)
    args=sys.argv[1:]
    if args:
        Configuration.load_kw(componentRoot=args[0])
    from wsgiref.simple_server import make_server
    make_server('localhost', 7777, DispatchingFileServer()).serve_forever()

if __name__=='__main__':
    _test()
