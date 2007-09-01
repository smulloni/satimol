import sys

# FileIterable and FileIterator stolen from Ian Bicking's nice WebOb
# file-serving example.  Thanks, Ian.

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

# I probably will not use this and use some sort of cascade scheme like
# paste has (although I may want to provide some way of forcing the cascade
# to stop even if returning an error code)
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
