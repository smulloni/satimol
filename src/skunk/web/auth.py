"""
authorization / authentication services, with support for common
auth schemes like file-based basic auth, and extensible
mechanisms for custom auth schemes.
"""
import base64
import logging

from skunk.config import Configuration
from skunk.util.armor import armor, dearmor
from skunk.util.authenticator import authenticate
from skunk.web.buffet import template
from skunk.web.context import Context
from skunk.web.exceptions import get_http_exception

log=logging.getLogger(__name__)

Configuration.setDefaults(authorizer=None,
                          defaultUser=None,
                          authCookieName='skunkauth')

def enable():
    """
    install the auth service.  
    """
    from skunk.web.context import InitContextHook
    if not _auth_hook in InitContextHook:
        InitContextHook.append(_auth_hook)
    
def _auth_hook(*args, **kwargs):
    authorizer=Configuration.authorizer
    if authorizer:
        authorizer()

class AuthorizerBase(object):
    """
    An abstract base class for authorizers.  Subclasses should be
    mixed in with implementations of AuthStorageBase.
    """

    def get_logged_in_user(self):
        """
        examines the credentials available to determine
        which user is currently logged in.  If there is one,
        that user's username is returned.
        """
        raise NotImplementedError

    def process_login(self):
        """
        examines the request to see if there is login information in
        it, and processes it if so, returning a 2-tuple (username,
        errordata).  If username is a true value, errors will be ignored;
        otherwise, errordata should consist of data that can be consumed
        by handle_unauthorized().
        """
        raise NotImplementedError

    def add_user_to_context(self, username, user):
        """
        store the username and/or user object in the request context.
        """
        raise NotImplementedError

    def handle_unauthorized(self, errordata):
        """
        take appropriate action if the request is unauthorized.
        errordata is any data produced by a login attempt in the
        current request that a login mechanism may wish to capture.
        """
        raise NotImplementedError

    def store_credentials(self, username, user):
        """
        store the user credentials as needed
        """
        pass

    def __call__(self):
        # look at the request, see if there is a user already logged
        username=self.get_logged_in_user()
        if not username:
            # is there login information in the request to process?
            username, errordata=self.process_login()
        if username:
            # get a User object, if any. 
            user=self.get_user_by_username(username) or username
            Context.request.remote_user=username
            Context.user=user
            # persist the login info as needed
            self.store_credentials(username, user)
        else:
            self.handle_unauthorized(errordata)

class AuthStorageBase(object):

    def check_password(self, username, password):
        """
        return True if the password is valid,
        otherwise False.
        """
        raise NotImplementedError

    def get_user_by_username(self, username):
        """
        return the user object for this username.  
        """
        raise NotImplementedError


class SimpleFileStorage(AuthStorageBase):
    def __init__(self, authfile):
        self.authfile=None
        
    def check_password(self, username, password):
        return authenticate(self.authfile, username, password)

    def get_user_by_username(self, username):
        return username

    
class BasicAuthorizerBase(AuthorizerBase):

    def __init__(self, realm):
         self.realm=realm

    def get_logged_in_user(self):
        req=Context.request
        authhead=req.headers.get('Authorization',
                                 req.headers.get('Proxy-Authorization'))
        if authhead:
            scheme, authtoken = authhead.split(' ',1)
            if scheme.lower() != 'basic':
                return
            decoded = base64.decodestring(authtoken.strip())
            try:
                username, password=decoded.split(':', 1)
            except ValueError:
                return
            else:
                if self.check_password(username, password):
                    return username
        
    def process_login(self):
        # I don't return anything here, but always
        # raise a 401
        exc=get_http_exception(401)
        exc.headers['WWW-Authenticate']='Basic: realm=' % self.realm
        raise exc


class BasicFileAuthorizer(BasicAuthorizerBase, SimpleFileStorage):
    def __init__(self, authfile, realm):
        BasicAuthorizerBase.__init__(self, realm)
        SimpleFileStorage.__init__(self, authfile)

class _default:
    pass

class CookieAuthorizerBase(object):

    def __init__(self, nonce):
        self.nonce=nonce

    def get_logged_in_user(self):
        req=Context.request
        cval=req.cookies.get(Configuration.authCookieName)
        if cval:
            user=dearmor(self.nonce, cval)
            if user:
                return user
            
    def store_credentials(self, username, user):
        """
        store the user credentials as needed
        """
        rsp=Context.response
        value=armor(self.nonce, username)
        rsp.set_cookie(Configuration.authCookieName,
                       value,
                       **Configuration.authCookieAttributes)

class LoginPageMixin(object):

    def __init__(self,
                 template,
                 username_field='username',
                 password_field='password',
                 template_opts=None):
        self.template=template
        self.username_field=username_field
        self.password_field=password_field
        self.template_opts=template_opts or {}

    def process_login(self):
        params=Context.request.mixed()
        username=params.get(self.username_field)
        password=params.get(self.password_field)
        if not (username or password):
            return None, {}
        elif self.check_password(username, password):
            return username, None
        else:
            return None, dict((self.username_field, username),
                              (self.password_field, password))

    def handle_unauthorized(self, errordata):
        @template(self.template, **self.template_opts)          
        def tmp():
            return errordata
        return tmp()

    
        
class CookieLoginAuthBase(CookieAuthorizerBase,
                          LoginPageMixin,
                          AuthorizerBase):
    def __init__(self,
                 nonce,
                 template,
                 username_field='username',
                 password_field='password',
                 template_opts=None):
        CookieAuthorizerBase.__init__(self, nonce)
        LoginPageMixin.__init__(self,
                                template,
                                username_field,
                                password_field,
                                template_opts)

         
