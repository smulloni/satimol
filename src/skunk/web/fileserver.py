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
from skunk.web.context import Context
from skunk.web.exceptions import handle_error, get_http_exception
from skunk.web.util import FileIterable

log=logging.getLogger(__name__)

__all__=['DispatchingFileServer', 'StaticFileServer']


DEFAULT_HIDDEN_FILE_PATTERNS=[
    '^\.',                                   # UNIX hidden files
    '\.(comp|pydcmp|pyinc|pycomp|inc)$',     # skunk components
    '~$',          # backup file
    '\.conf$'      # configuration files
    ]

DEFAULT_INDEX_DOCUMENTS=[
    'index.html',
    'index.stml',
    'index.xml',    
    'index.py'
    ]

DEFAULT_FILE_DISPATCHERS=[('.*\.(stml|html|py)$',
                           'skunk.web.fileserver:serve_stml')]

Configuration.setDefaults(
    hiddenFilePatterns=DEFAULT_HIDDEN_FILE_PATTERNS,
    indexDocuments=DEFAULT_INDEX_DOCUMENTS,
    
    # options for serving static files with x-sendfile 
    staticFileUseXSendFile=False,
    staticFileXSendFileHeader='X-Sendfile',
    staticFileXSendFileHeaderPathTranslated=True,
    
    staticFileAddEtag=False,
    
    # whether to guess the character encoding of static text files
    # with chardet, if available
    staticFileUseChardet=True,

    # for dispatching server, a list of (pattern, handler) pairs
    fileDispatchers=DEFAULT_FILE_DISPATCHERS
    
    )

class FileServerBase(object):

    def get_request(self, environ):
        try:
            return Context.request
        except AttributeError:
            return webob.Request(environ)

    def __call__(self, environ, start_response):
        try:
            request=self.get_request(environ)
            path, realpath, statinfo=self.check_path(request.path)
            app=self.serve_file(path, realpath, statinfo, request)
            if app:
                return app(environ, start_response)
            exc=get_http_exception(httplib.NOT_FOUND)
            return exc(environ, start_response)
        except webob.exc.HTTPException, exc:
            return exc(environ, start_response)
        except:
            log.exception("error in serving file")
            return handle_error(httplib.INTERNAL_SERVER_ERROR,
                                environ,
                                start_response)
    
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
            elif re.search(h, path):
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
        except (OSError, IOError), oy:
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
        return serve_static(path, realpath, statinfo, request)

def serve_stml(path, realpath, statinfo, request):
    """
    handler for stml and Component files.
    """
    try:
        response=Context.response
    except AttributeError:
        response=webob.Response(content_type=Configuration.defaultContentType,
                                charset=Configuration.defaultCharset)
    body=stringcomp(path, REQUEST=request, RESPONSE=response)
    # if you set the body of the response yourself, that will
    # replace anything output by the component.  Normally you
    # won't be doing that in this context.
    if not response.body:
        response.body=body
    return response

def serve_static(path, realpath, statinfo, request):
    if request.method not in ('GET', 'HEAD'):
            return get_http_exception(httplib.METHOD_NOT_ALLOWED)
    type, contentenc=mimetypes.guess_type(realpath)

    if not type:
        type='application/octet-stream'

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

    if contentenc:
        res.content_encoding=contentenc
        
    if type.startswith('text/'):
        if Configuration.defaultCharset:
            res.charset=Configuration.defaultCharset
        elif chardet and Configuration.staticFileUseChardet:
            res.charset=chardet.detect(open(realpath).read(1024))['encoding']

    # Other custom header munging is left for middleware, or
    # something else
    return res

        

class DispatchingFileServer(FileServerBase):
    """
    a file server that dispatches to different handlers on the basis
    of filename (usually extension).  
    """

    _handlercache={}

    def _default_handler(self, path, realpath, statinfo, request):
        return serve_static(path, realpath, statinfo, request)

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
            return self._default_handler
        if isinstance(handler, basestring):
            try:
                return self._handlercache[handler]
            except KeyError:
                handler=import_from_string(handler)
                self._handlercache[handler]=handler
                return handler
        else:
            return handler
        
    
    def serve_file(self, path, realpath, statinfo, request):
        handler=self.get_handler(path)
        assert handler, "get_handler didn't return a handler"
        return handler(path, realpath, statinfo, request)


def _test():
    import sys
    logging.basicConfig(level=logging.DEBUG)
    args=sys.argv[1:]
    if args:
        Configuration.load_kw(componentRoot=args[0])
    from wsgiref.simple_server import make_server
    from skunk.web.context import ContextMiddleware
    make_server('localhost', 7777,
                ContextMiddleware(DispatchingFileServer())).serve_forever()

if __name__=='__main__':
    _test()


__all__=['DispatchingFileServer', 'StaticFileServer',
         'DEFAULT_HIDDEN_FILE_PATTERNS',
         'DEFAULT_INDEX_DOCUMENTS',
         'DEFAULT_FILE_DISPATCHERS'
         ]
