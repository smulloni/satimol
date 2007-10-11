#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
#

import getpass
import optparse
import os
from random import randint
import sha
import sys

class Authenticator(object):

    def __init__(self, authdict=None):
        self.authdict = authdict or {}
        
    def setUserPassword(self, user, password):
        self.authdict[user] = self._make_hash(user, password)

    def get_hash_bits(self, user):
        return self.authdict.get(user)

    def _make_hash(self, user, password, salt=None):
        if salt is None:
            salt = "%04X" % randint(0,4095)
        chash = sha.sha('%s:%s%s' % (user, salt, password)).digest()
        return salt+''.join(["%02X" % ord(i) for i in chash])

    def authenticate(self, user, password):
        if not user or not password:
            return False
        t = self.get_hash_bits(user)
        if t is None:
            return False
        salt, hash = t[:4], t[4:]
        if not hash:
            return False
        if self._make_hash(user, password, salt) == (salt+hash):
            return True


class FileAuthenticator(Authenticator):
    def __init__(self, filename, create=False):
        self.filename = filename
        Authenticator.__init__(self)

        if not create:
            if not os.path.exists(filename):
                raise ValueError, "file does not exist: %s" % filename
            self.load()

    def reload(self):
        self.authdict.clear()
        self.load()

    def load(self):
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
        f = open(self.filename, 'w')
        for i in self.authdict.items():
            f.write('%s:%s\n' % i)
        f.close()

            
def authenticate(authfile, username, password):
    """
    check whether the given username and password match an entry in
    the given htpasswd style auth file.
    """
    return FileAuthenticator(authfile).authenticate(username, password)

def swpasswd(filename, username, password=None, create=False, delete=False):
    auth=FileAuthenticator(filename, create)
    if not delete:
        while not password:
            password=getpass.getpass("Password: ")
        auth.setUserPassword(username, password)
    else:
        try:
            del auth.authdict[username]
        except KeyError:
            print >> sys.stderr, "no such user"
            sys.exit(1)
    auth.dump()
    sys.exit(0)
        
def main(args=None):
    if args is None:
        args=sys.argv[1:]
    p=optparse.OptionParser(usage="usage: %prog [options] password_file username")
    p.add_option('-c', '--create',
                 dest='create', action='store_true',
                 default=False,
                 help="create or truncate the password file")
    p.add_option('-d', '--delete',
                 dest='delete', action='store_true',
                 default=False,
                 help="delete the given user")
    opts, args=p.parse_args(args)
    if opts.delete and opts.create:
        p.error('delete and create options do not make sense together')
    if len(args)!=2:
        p.error("expected two arguments")
    filename, username=args
    swpasswd(filename, username, create=opts.create, delete=opts.delete)

__all__=['authenticate', 'FileAuthenticator']
