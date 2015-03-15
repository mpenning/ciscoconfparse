"""
PyOTP, the Python One-Time Password module.

keywrangling.py: key handling routines for the otp module. 

<insert Python license here>
"""

__version__ = '$Revision: 1.4 $'

import types
from AppendixB import DefaultDictionary, WordFromNumber, NumberFromWord

def keyformat(key):
    """Return the type of a key or list of keys (all of which must
    be in the same format).
    
    Result: 'sixword', 'hex', 'long', 'raw', or None for an
    unrecognised key format.
    
    LIMITATIONS: This routine doesn't go to nearly enough effort
    to double- and triple-check key types. For example, any string
    of length 16 will be treated as a hex key. More checks should
    be added in the future."""
    
    if type(key) == types.ListType:
        return keyformat(key[0])
    if type(key) == types.LongType:
        return 'long'
    elif type(key) == types.StringType:
        if len(key) == 8:
            return 'raw'
        elif len(key) == 19 and len(key.split(' ')) == 4:
            return 'hex'
        elif len(key.split(' ')) == 6:
            return 'sixword'
        else:
            return None
    else:
        return None

def long_from_raw(hash):
    """Fold to a long, a digest supplied as a string."""
    
    hashnum = 0L
    for h in hash:
        hashnum <<= 8
        hashnum |= ord(h)
        
    return hashnum

def sixword_from_raw(key, dictionary=DefaultDictionary):
    return sixword_from_long(long_from_raw(key), dictionary)

def sixword_from_hex(key, dictionary=DefaultDictionary):
    return sixword_from_long(long_from_hex(key), dictionary)

def hex_from_long(key):
    k = '%016x' % key
    return ' '.join( [ k[0:4], k[4:8], k[8:12], k[12:16] ] ).upper()

def hex_from_raw(key):
    return hex_from_long(long_from_raw(key))

def hex_from_sixword(key):
    return hex_from_long(long_from_sixword(key))

def long_from_hex(key):
    return long(''.join(key.split(' ')).lower(), 16)

def checksummed_long(key):
    sum, k = 0, key
    for i in range(0, 32):
        sum = sum + ( k % 4 )
        k = k >> 2
    return ( key << 2 ) | ( sum % 4 )
    
def sixword_from_long(key, dictionary=DefaultDictionary):
    key = checksummed_long(key)
    
    words = []
    for i in range(0,6):
        words = [dictionary[key % 2048]] + words
        key = key >> 11
    return ' '.join(words)

def long_from_sixword(key):
    # no alternative dictionary format yet! 
    words = key.split(' ')
    for w in words:
        wordIndex = NumberFromWord(w)
        try:
            wordCheck = WordFromNumber(wordIndex)
        except:
            wordCheck = None
        print wordIndex, wordCheck

_KEYCONVERSIONTABLE = {
    'sixword' : { 'raw'     : sixword_from_raw ,
                  'long'    : sixword_from_long ,
                  'hex'     : sixword_from_hex }, 
    'long' :    { 'raw'     : long_from_raw ,
                  'sixword' : long_from_sixword,
                  'hex'     : long_from_hex },
    'hex' :     { 'raw'     : hex_from_raw ,
                  'sixword' : hex_from_sixword,
                  'long'    : hex_from_long }
    }

def convertkey(format, key_or_keylist):
    """Convert a key or a list of keys from one format to another.

    format         -- 'sixword', 'hex', or 'long'
    key_or_keylist -- either a key, or a list of keys ALL OF THE
                      SAME FORMAT."""
    
    originalformat = keyformat(key_or_keylist)
    if originalformat == format: # just in case! 
        return key_or_keylist
    
    conversionfunction = _KEYCONVERSIONTABLE[format][originalformat]
    if type(key_or_keylist) == types.ListType:
        return map(conversionfunction, key_or_keylist)
    else:
        return conversionfunction(key_or_keylist)
