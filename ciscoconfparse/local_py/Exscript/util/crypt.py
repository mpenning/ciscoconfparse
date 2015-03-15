# Copyright (C) 2007-2010 Samuel Abels.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
Encryption related utilities.
"""
from Exscript.external.otp import generate

def otp(password, seed, sequence):
    """
    Calculates a one-time password hash using the given password, seed, and
    sequence number and returns it.
    Uses the MD4/sixword algorithm as supported by TACACS+ servers.

    @type  password: string
    @param password: A password.
    @type  seed: string
    @param seed: A username.
    @type  sequence: int
    @param sequence: A sequence number.
    @rtype:  string
    @return: A hash.
    """
    return generate(password, seed, sequence, 1, 'md4', 'sixword')[0]
