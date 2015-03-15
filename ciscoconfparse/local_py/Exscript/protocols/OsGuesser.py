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
from Exscript.protocols.drivers import drivers

class OsGuesser(object):
    """
    The OsGuesser monitors everything that happens on a Protocol,
    and attempts to collect data out of the network activity.
    It watches for specific patterns in the network traffic to decide
    what operating system a connected host is running.
    It is completely passive, and attempts no changes on the protocol
    adapter. However, the protocol adapter may request information
    from the OsGuesser, and perform changes based on the information
    provided.
    """

    def __init__(self):
        self.info        = {}
        self.debug       = False
        self.auth_os_map = [d._check_head for d in drivers]
        self.os_map      = [d._check_response for d in drivers]
        self.auth_buffer = ''
        self.set('os', 'unknown', 0)

    def reset(self):
        self.__init__()

    def set(self, key, value, confidence = 100):
        """
        Defines the given value with the given confidence, unless the same
        value is already defined with a higher confidence level.
        """
        if value is None:
            return
        if key in self.info:
            old_confidence, old_value = self.info.get(key)
            if old_confidence >= confidence:
                return
        self.info[key] = (confidence, value)

    def set_from_match(self, key, regex_list, string):
        """
        Given a list of functions or three-tuples (regex, value, confidence),
        this function walks through them and checks whether any of the
        items in the list matches the given string.
        If the list item is a function, it must have the following
        signature::

            func(string) : (string, int)

        Where the return value specifies the resulting value and the
        confidence of the match.
        If a match is found, and the confidence level is higher
        than the currently defined one, the given value is defined with
        the given confidence.
        """
        for item in regex_list:
            if hasattr(item, '__call__'):
                self.set(key, *item(string))
            else:
                regex, value, confidence = item
                if regex.search(string):
                    self.set(key, value, confidence)

    def get(self, key, confidence = 0):
        """
        Returns the info with the given key, if it has at least the given
        confidence. Returns None otherwise.
        """
        if key not in self.info:
            return None
        conf, value = self.info.get(key)
        if conf >= confidence:
            return value
        return None

    def data_received(self, data, app_authentication_done):
        # If the authentication procedure is complete, use the normal
        # "runtime" matchers.
        if app_authentication_done:
            # Stop looking if we are already 80 percent certain.
            if self.get('os', 80) in ('unknown', None):
                self.set_from_match('os', self.os_map, data)
            return

        # Else, check the head that we collected so far.
        self.auth_buffer += data
        if self.debug:
            print "DEBUG: Matching buffer:", repr(self.auth_buffer)
        self.set_from_match('os', self.auth_os_map, self.auth_buffer)
        self.set_from_match('os', self.os_map,      self.auth_buffer)
