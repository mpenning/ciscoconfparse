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
from Exscript.util        import crypt
from Exscript.stdlib.util import secure_function

@secure_function
def otp(scope, password, seed, seqs):
    """
    Calculates a one-time password hash using the given password, seed, and
    sequence number and returns it.
    Uses the md4/sixword algorithm as supported by TACACS+ servers.

    @type  password: string
    @param password: A password.
    @type  seed: string
    @param seed: A username.
    @type  seqs: int
    @param seqs: A sequence number, or a list of sequence numbers.
    @rtype:  string
    @return: A hash, or a list of hashes.
    """
    return [crypt.otp(password[0], seed[0], int(seq)) for seq in seqs]
