"""
The otp module implements the RFC2289 (previously RFC1938) standard
for One-Time Passwords.

For details of RFC2289 adherence, module limitations, and a to-do list,
please see __init__.py 

<insert Python license here>
"""

__version__ = '$Revision: 1.4 $'

import string, random
from Crypto.Hash import MD4
try:
    from hashlib import sha1 as SHA
    from hashlib import md5 as MD5
except ImportError:
    from Crypto.Hash import SHA, MD5
from AppendixB import DefaultDictionary
from keywrangling import keyformat, convertkey

_VALIDSEEDCHARACTERS = string.letters + string.digits

_HASHMODULE = { 'md4': MD4, 'md5' : MD5, 'sha' : SHA }

def _fold_md5(digest):
    result = ''
    if len(digest)<16:
        print digest
        raise AssertionError
    for i in range(0,8):
        result = result + chr(ord(digest[i]) ^ ord(digest[i+8]))
    return result
    
def _fold_sha(hash):
    # BROKEN
    ordhash = map(ord, hash)
    result = [0, 0, 0, 0, 0, 0, 0, 0]
    
    result[3] = ordhash[0] ^ ordhash[8] ^  ordhash[16] 
    result[2] = ordhash[1] ^ ordhash[9] ^  ordhash[17]
    result[1] = ordhash[2] ^ ordhash[10] ^ ordhash[18]
    result[0] = ordhash[3] ^ ordhash[11] ^ ordhash[19]
    result[7] = ordhash[4] ^ ordhash[12]
    result[6] = ordhash[5] ^ ordhash[13]
    result[5] = ordhash[6] ^ ordhash[14]
    result[4] = ordhash[7] ^ ordhash[15]

    return ''.join(map(chr, result))

_FOLDFUNCTION = { 'md4': _fold_md5, 'md5' : _fold_md5, 'sha' : _fold_sha }

def generate(passphrase, seed,
             startkey=0, numkeys=499, hashfunction='md5',
             keyformat = 'hex'):
    """Generate a sequence of OTP keys from a pass phrase and seed
    using the specified hash function. Results are returned as a
    list of long integers suitable for conversion to six-word or
    hexadecimal one-time passwords. 
    
    passphrase   -- the shared secret pass phrase as supplied by the
                    user over a secure connection and stored by the
                    OTP server. 
    seed         -- the seed phrase used both to initialize keys and
                    sent in the clear by OTP servers as part of the
                    OTP challenge.
    startkey     -- the number of iterations to run before the first
                    key in the result list is taken.
    numkeys      -- the number of keys to return in the result list.
    hashfunction -- the hash function to use when generating keys.
    keyformat    -- the key format to generate
    """
    
    # check arguments for validity and standards compliance
    if hashfunction not in _HASHMODULE.keys():
        raise Exception, 'hashfunction'
    if len(passphrase) not in range(4,64):
        raise Exception, 'passphrase length'
    if len(seed) not in range(1,17):
        raise Exception, 'seed length'
    for x in seed:
        if not x in _VALIDSEEDCHARACTERS:
            raise Exception, 'seed composition'
    if startkey < 0:
        raise Exception, 'startkey'
    if numkeys < 1:
        raise Exception, 'numkeys'
    # not checked: argument types, startkey and numkeys out of range
    
    hashmodule = _HASHMODULE[hashfunction]
    folder = _FOLDFUNCTION[hashfunction]
    
    hash = folder(hashmodule.new(seed + passphrase).digest())
    
    # discard the first <startkey> keys    
    for iterations in range(0, startkey):
        hash = folder(hashmodule.new(hash).digest())
        
    # generate the results
    keylist = []
    
    for keys in range(0, numkeys):
        keylist.append(hash)
        hash = folder(hashmodule.new(hash).digest())
        
    return convertkey(keyformat,keylist)    

def generateseed(length=5):
    """Generate a random, valid seed of a given length."""
    # check standards compliance of arguments
    if length not in range(1,11):
        raise Exception, 'length'
    seed = ''
    vsclen = len(_VALIDSEEDCHARACTERS)
    bignum = 2L**32 - 1
    for i in range(0, length):
        index = long(random.random() * bignum) % vsclen
        seed = seed + _VALIDSEEDCHARACTERS[index]
    return seed
