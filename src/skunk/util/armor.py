"""

This module contains two functions, armor and dearmor, which can be
used to ensure that data sent over a network has not been tampered
with.

"""
#  
#  Copyright (C) 2001 Andrew T. Csillag <drew_csillag@geocities.com>
#  
#      You may distribute under the terms of either the GNU General
#      Public License or the SkunkWeb License, as specified in the
#      README file.
   

import base64
import random
import sha

def armor(nonce, value):
    buff=[chr(random.randrange(0,256)) for x in range(4)]
    salt=''.join(buff)
    digest = sha.sha(''.join([salt, value,nonce])).digest()
    return base64.encodestring(''.join([salt, value, digest]))

def dearmor(nonce, value):
    try:
        value = base64.decodestring(value)
    except: #value string is bogus
        return None
    
    salt = value[:4]
    digest = value[-20:]
    value = value[4:-20]

    ndigest = sha.sha(''.join([salt, value, nonce])).digest()
    if ndigest != digest:
        return None
    return value
                   
__all__=['armor', 'dearmor']
