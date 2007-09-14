#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#   
import optparse
import os
from random import randint
import sha

class Authenticator(object):
    def _make_hash(self, user, password, salt=None):
        if salt is None:
            salt = "%04X" % randint(0,4095)
        chash = sha.sha('%s:%s%s' % (user, salt, password)).digest()
        return salt+''.join(["%02X" % ord(i) for i in chash])

    def authenticate(self, user, password):
        if not user or not password:
            return False
        t = self.get_hash_bits(user)
        if t==None:
            return False
        salt, hash = t[:4], t[4:]
        if not hash:
            return False
        if self._make_hash(user, password, salt) == (salt+hash):
            return True

    def get_hash_bits(self, user):
        raise NotImplementedError
    
class PreloadedAuthenticator(Authenticator):
    def __init__(self, authdict=None):
        self.authdict = authdict or {}
        
    def setUserPassword(self, user, password):
        self.authdict[user] = self._make_hash(user, password)

    def get_hash_bits(self, user):
        return self.authdict.get(user)

class FileAuthenticator(PreloadedAuthenticator):
    def __init__(self, filename, create=False):
        self.file = filename
        PreloadedAuthenticator.__init__(self)
        if (not create) or os.path.exists(filename)):
            self._load()

    def _load(self):
        for i in open(self.filename):
            i=i.strip()
            if not i or i[0] == '#':
                continue
            colidx = i.rfind(':')
            if colidx == -1:
                continue
            name = i[:colidx]
            self.authdict[name] = i[colidx+1:]

    def dump(self):
        f = open(self.file, 'w')
        for i in self.authdict.items():
            f.write('%s:%s\n' % i)
        f.close()

            
def authenticate(authfile, username, password):
    """
    check whether the given username and password match an entry in
    the given htpasswd style auth file.
    """
    return FileAuthenticator(authfile).authenticate(username, password)

def swpasswd(filename, username, password=None, create=False):
    pass
        

__all__=['authenticate', 'FileAuthenticator']
