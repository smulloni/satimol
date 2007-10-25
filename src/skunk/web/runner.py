"""
an interface for running wsgi servers in various ways according to
configuration, with daemonization and pid file support.

TODO: add configuration for logging.

"""

import errno
import logging
import os
import signal

try:
    import grp
    import pwd
    have_unix=1
except ImportError:
    have_unix=0

try:
    from flup.server.scgi_fork import WSGIServer as SCGIServer
    from flup.server.fcgi_fork import WSGIServer as FCGIServer
    from flup.server.scgi import WSGIServer as SCGIThreadServer
    from flup.server.fcgi import WSGIServer as FCGIThreadServer
    haveflup=True
except ImportError:
    haveflup=False

try:
    from cherrypy.wsgiserver import CherryPyWSGIServer as httpserver
except ImportError:
    httpserver=None

from skunk.config import Configuration

Configuration.setDefaults(
    # for scgi and fcgi; currently the only http alternatives
    # are threaded
    useThreads=False, 
    serverProtocol='http',
    maxThreads=None,
    maxSpare=None,
    minSpare=None,
    maxChildren=None,
    maxRequests=None,
    pidfile=None,
    daemonize=False,
    umask=None,
    user=None,
    group=None,
    bindAddress='TCP:127.0.0.1:7777',
    serverName=None,
    sslCertificate=None,
    sslPrivateKey=None)
    
log=logging.getLogger(__name__)



class _BindAddress(object):
    def __init__(self,
                 sockettype,
                 file=None,
                 umask=None,
                 interface=None,
                 port=None):
        """this is a private constructor.
        Come to think of it, the whole class is private.
        Don't use it."""
        self.sockettype=sockettype
        self.file=file
        self.umask=umask
        self.interface=interface
        self.port=port

    @property
    def addr(self):
        if self.sockettype=='unix':
            return self.file
        return (self.interface, self.port)

    @classmethod
    def from_string(cls, spec):
        """
        parses two kinds of strings:

        TCP:[host|*]:[port]

        and

        UNIX:path:[umask|]
        """
        interface=port=file=umask=None
        bits=spec.split(':', 2)
        sockettype=bits.pop(0).lower()
            
        if sockettype=='tcp':
            if len(bits) != 2:
                raise ValueError("invalid address specification")
            interface=bits[0]
            port=int(bits[1])
            
        elif sockettype=='unix':
            file=bits.pop(0)
            if bits:
                # should be an octal value
                umask=bits[0]
                if umask:
                    umask=int(umask, 8)
        else:
            raise ValueError('unsupported socket type: %s' % sockettype)
        return cls(sockettype=sockettype,
                   file=file,
                   umask=umask,
                   interface=interface,
                   port=port)

def _get_run_func(app):
    addr=_BindAddress.from_string(Configuration.bindAddress)
    if (Configuration.serverProtocol=='https' and
        None in (Configuration.sslCertificate,
                 Configuration.sslPrivateKey)):
        raise ConfigurationError("https requested, but certificate or "
                                 "private key not specified")    
    if Configuration.serverProtocol in ('http','https'):
        if not httpserver:
            raise RuntimeError("to serve http directly you need to install CherryPy.")
        def runfunc():
            log.debug('in runfunc for cherrypy http server')
            server=httpserver((addr.interface, addr.port),
                              app,
                              server_name=Configuration.serverName)
            log.debug('server instance created')
            if Configuration.serverProtocol=='https':
                server.ssl_certificate=Configuration.sslCertificate
                server.ssl_private_key=Configuration.sslPrivateKey
            try:
                server.start()
            finally:
                server.stop()
                
        return runfunc
    else:
        threads=Configuration.useThreads
        if Configuration.serverProtocol == 'fcgi':
            serverclass=FCGIThreadServer if threads else FCGIServer
        elif Configuration.serverProtocol == 'scgi':
            serverclass=SCGIThreadServer if threads else SCGIServer
        def runfunc():
            if threads:
                kw=dict(maxSpare=Configuration.maxSpare,
                        minSpare=Configuration.minSpare,
                        maxThreads=Configuration.maxThreads)
            else:
                kw=dict(maxSpare=Configuration.maxSpare,
                        minSpare=Configuration.minSpare,
                        maxChildren=Configuration.maxChildren,
                        maxRequests=Configuration.maxRequests)
            # clean out Nones
            kw=dict(i for i in kw.items() if not i[1] is None)
            server=serverclass(app,
                               bindAddress=addr.addr,
                               umask=addr.umask,
                               **kw)
            server.run()
        return runfunc

def _change_user_group():
    user=Configuration.user
    group=Configuration.group    
    if not have_unix:
        if user or group:
            log.warn("no dropping of credentials implemented on non-UNIX platforms")
        return

    if user or group:
        # in case we are seteuid something else, which would
        # cause setuid or getuid to fail, undo any existing
        # seteuid. (The only reason to do this is for the case
        # os.getuid()==0, AFAIK).
        try:
            seteuid=os.seteuid
        except AttributeError:
            # the OS may not support seteuid, in which
            # case everything is hotsy-totsy.
            pass
        else:
            seteuid(os.getuid())
        if group:
            gid=grp.getgrnam(group)[2]
            os.setgid(gid)
        if user:
            uid=pwd.getpwnam(user)[2]
            os.setuid(uid)

def _run_server(func):
    daemonize=Configuration.daemonize
    pidfile=Configuration.pidfile
    log.debug("daemonize: %s, pidfile: %s", daemonize, pidfile)
    if daemonize:
        try:
            os.fork
        except NameError:
            log.info("not daemonizing, as the fork() call is not available")
            daemonize=False
    if daemonize:
        if os.fork():
            os._exit(0)
        if os.fork():
            os._exit(0)
        os.setsid()
        os.chdir('/')
        os.umask(0)
        os.open(os.devnull, os.O_RDWR)
        os.dup2(0,1)
        os.dup2(0,2)
        if pidfile:
            pidfp=open(pidfile, 'w')
            pidfp.write('%s' % os.getpid())
            pidfp.close()
            

    _change_user_group()
    starting_pid=os.getpid()
    try:
        try:
            func()
        except (SystemExit, KeyboardInterrupt):
            pass
    finally:
        if daemonize and pidfile and os.getpid()==starting_pid:
            log.debug('removing pidfile')
            try:
                os.unlink(pidfile)
            except OSError, oy:
                if oy.errno!=errno.ENOENT:
                    log.exception("error unlinking pidfile")


def run(wsgiapp):
    func=_get_run_func(wsgiapp)
    _run_server(func)

__all__=['run']
