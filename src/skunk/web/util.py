from skunk.config import Configuration

def get_http_exception(status, *args, **kwargs):
    handlerclass=Configuration.errorHandlers[status]
    handler=handlerclass(*args, **kwargs)
    return handler

def handle_error(status, environ, start_response, *args, **kwargs):
    handler=get_http_exception(status, *args, **kwargs)
    # this is not Context.response
    if not handler.server:
        handler.server=Configuration.serverIdentification
    return handler(environ, start_response)

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
