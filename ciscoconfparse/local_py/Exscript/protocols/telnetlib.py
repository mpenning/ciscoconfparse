"""TELNET client class.

Based on RFC 854: TELNET Protocol Specification, by J. Postel and
J. Reynolds

Example:

>>> from telnetlib import Telnet
>>> tn = Telnet('www.python.org', 79)   # connect to finger port
>>> tn.write('guido\r\n')
>>> print tn.read_all()
Login       Name               TTY         Idle    When    Where
guido    Guido van Rossum      pts/2        <Dec  2 11:10> snag.cnri.reston..

>>>

Note that read_all() won't read until eof -- it just reads some data
-- but it guarantees to read at least one byte unless EOF is hit.

It is possible to pass a Telnet object to select.select() in order to
wait until more data is available.  Note that in this case,
read_eager() may return '' even if there was data on the socket,
because the protocol negotiation may have eaten the data.  This is why
EOFError is needed in some cases to distinguish between "no data" and
"connection closed" (since the socket also appears ready for reading
when it is closed).

Bugs:
- may hang when connection is slow in the middle of an IAC sequence

To do:
- option negotiation
- timeout should be intrinsic to the connection object instead of an
  option on one of the read calls only

"""


# Imported modules
import sys
import time
import socket
import select
import struct
from cStringIO import StringIO

__all__ = ["Telnet"]

# Tunable parameters
DEBUGLEVEL = 0

# Telnet protocol defaults
TELNET_PORT = 23

# Telnet protocol characters (don't change)
IAC  = chr(255) # "Interpret As Command"
DONT = chr(254)
DO   = chr(253)
WONT = chr(252)
WILL = chr(251)
SB   = chr(250)
SE   = chr(240)
theNULL = chr(0)

# Telnet protocol options code (don't change)
# These ones all come from arpa/telnet.h
BINARY = chr(0) # 8-bit data path
ECHO = chr(1) # echo
RCP = chr(2) # prepare to reconnect
SGA = chr(3) # suppress go ahead
NAMS = chr(4) # approximate message size
STATUS = chr(5) # give status
TM = chr(6) # timing mark
RCTE = chr(7) # remote controlled transmission and echo
NAOL = chr(8) # negotiate about output line width
NAOP = chr(9) # negotiate about output page size
NAOCRD = chr(10) # negotiate about CR disposition
NAOHTS = chr(11) # negotiate about horizontal tabstops
NAOHTD = chr(12) # negotiate about horizontal tab disposition
NAOFFD = chr(13) # negotiate about formfeed disposition
NAOVTS = chr(14) # negotiate about vertical tab stops
NAOVTD = chr(15) # negotiate about vertical tab disposition
NAOLFD = chr(16) # negotiate about output LF disposition
XASCII = chr(17) # extended ascii character set
LOGOUT = chr(18) # force logout
BM = chr(19) # byte macro
DET = chr(20) # data entry terminal
SUPDUP = chr(21) # supdup protocol
SUPDUPOUTPUT = chr(22) # supdup output
SNDLOC = chr(23) # send location
TTYPE = chr(24) # terminal type
EOR = chr(25) # end or record
TUID = chr(26) # TACACS user identification
OUTMRK = chr(27) # output marking
TTYLOC = chr(28) # terminal location number
VT3270REGIME = chr(29) # 3270 regime
X3PAD = chr(30) # X.3 PAD
NAWS = chr(31) # window size
TSPEED = chr(32) # terminal speed
LFLOW = chr(33) # remote flow control
LINEMODE = chr(34) # Linemode option
XDISPLOC = chr(35) # X Display Location
OLD_ENVIRON = chr(36) # Old - Environment variables
AUTHENTICATION = chr(37) # Authenticate
ENCRYPT = chr(38) # Encryption option
NEW_ENVIRON = chr(39) # New - Environment variables
# the following ones come from
# http://www.iana.org/assignments/telnet-options
# Unfortunately, that document does not assign identifiers
# to all of them, so we are making them up
TN3270E = chr(40) # TN3270E
XAUTH = chr(41) # XAUTH
CHARSET = chr(42) # CHARSET
RSP = chr(43) # Telnet Remote Serial Port
COM_PORT_OPTION = chr(44) # Com Port Control Option
SUPPRESS_LOCAL_ECHO = chr(45) # Telnet Suppress Local Echo
TLS = chr(46) # Telnet Start TLS
KERMIT = chr(47) # KERMIT
SEND_URL = chr(48) # SEND-URL
FORWARD_X = chr(49) # FORWARD_X
PRAGMA_LOGON = chr(138) # TELOPT PRAGMA LOGON
SSPI_LOGON = chr(139) # TELOPT SSPI LOGON
PRAGMA_HEARTBEAT = chr(140) # TELOPT PRAGMA HEARTBEAT
EXOPL = chr(255) # Extended-Options-List

SEND_TTYPE = chr(1)

class Telnet:
    """Telnet interface class.

    An instance of this class represents a connection to a telnet
    server.  The instance is initially not connected; the open()
    method must be used to establish a connection.  Alternatively, the
    host name and optional port number can be passed to the
    constructor, too.

    Don't try to reopen an already connected instance.

    This class has many read_*() methods.  Note that some of them
    raise EOFError when the end of the connection is read, because
    they can return an empty string for other reasons.  See the
    individual doc strings.

    read_all()
        Read all data until EOF; may block.

    read_some()
        Read at least one byte or EOF; may block.

    read_very_eager()
        Read all data available already queued or on the socket,
        without blocking.

    read_eager()
        Read either data already queued or some data available on the
        socket, without blocking.

    read_lazy()
        Read all data in the raw queue (processing it first), without
        doing any socket I/O.

    read_very_lazy()
        Reads all data in the cooked queue, without doing any socket
        I/O.
    """

    def __init__(self, host=None, port=0, **kwargs):
        """Constructor.

        When called without arguments, create an unconnected instance.
        With a hostname argument, it connects the instance; a port
        number is optional.

        """
        self.debuglevel = DEBUGLEVEL
        self.can_naws = False
        self.host = host
        self.port = port
        self.sock = None
        self.cancel_expect = False
        self.rawq = ''
        self.irawq = 0
        self.cookedq = StringIO()
        self.eof = 0
        self.init_timetout        = kwargs.get('init_timeout',     None)
        self.window_size          = kwargs.get('termsize')
        self.stdout               = kwargs.get('stdout',           sys.stdout)
        self.stderr               = kwargs.get('stderr',           sys.stderr)
        self.termtype             = kwargs.get('termtype',         'dumb')
        self.data_callback        = kwargs.get('receive_callback', None)
        self.data_callback_kwargs = {}
        if host:
            self.open(host, port)

    def open(self, host, port=0):
        """Connect to a host.

        The optional second argument is the port number, which
        defaults to the standard telnet port (23).

        Don't try to reopen an already connected instance.

        """
        self.eof = 0
        if not port:
            port = TELNET_PORT
        self.host = host
        self.port = port
        msg = "getaddrinfo returns an empty list"
        for res in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
                self.sock.settimeout(self.init_timetout)
                self.sock.connect(sa)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg

    def msg(self, msg, *args):
        """Print a debug message, when the debug level is > 0.

        If extra arguments are present, they are substituted in the
        message using the standard string formatting operator.

        """
        if self.debuglevel > 0:
            self.stderr.write('Telnet(%s,%d): ' % (self.host, self.port))
            if args:
                self.stderr.write(msg % args)
            else:
                self.stderr.write(msg)
            self.stderr.write('\n')

    def set_debuglevel(self, debuglevel):
        """Set the debug level.

        The higher it is, the more debug output you get (on stdout).

        """
        self.debuglevel = debuglevel

    def close(self):
        """Close the connection."""
        if self.sock:
            self.sock.close()
        self.sock = 0
        self.eof = 1

    def get_socket(self):
        """Return the socket object used internally."""
        return self.sock

    def fileno(self):
        """Return the fileno() of the socket object used internally."""
        return self.sock.fileno()

    def write(self, buffer):
        """Write a string to the socket, doubling any IAC characters.

        Can block if the connection is blocked.  May raise
        socket.error if the connection is closed.

        """
        if type(buffer) == type(0):
            buffer = chr(buffer)
        elif isinstance(buffer, str) and IAC in buffer:
            buffer = buffer.replace(IAC, IAC+IAC)
        self.msg("send %s", `buffer`)
        self.sock.send(buffer)

    def read_all(self):
        """Read all data until EOF; block until connection closed."""
        self.process_rawq()
        while not self.eof:
            self.fill_rawq()
            self.process_rawq()
        buf = self.cookedq.getvalue()
        self.cookedq.seek(0)
        self.cookedq.truncate()
        return buf

    def read_some(self):
        """Read at least one byte of cooked data unless EOF is hit.

        Return '' if EOF is hit.  Block if no data is immediately
        available.

        """
        self.process_rawq()
        while self.cookedq.tell() == 0 and not self.eof:
            self.fill_rawq()
            self.process_rawq()
        buf = self.cookedq.getvalue()
        self.cookedq.seek(0)
        self.cookedq.truncate()
        return buf

    def read_very_eager(self):
        """Read everything that's possible without blocking in I/O (eager).

        Raise EOFError if connection closed and no cooked data
        available.  Return '' if no cooked data available otherwise.
        Don't block unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        while not self.eof and self.sock_avail():
            self.fill_rawq()
            self.process_rawq()
        return self.read_very_lazy()

    def read_eager(self):
        """Read readily available data.

        Raise EOFError if connection closed and no cooked data
        available.  Return '' if no cooked data available otherwise.
        Don't block unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        while self.cookedq.tell() == 0 and not self.eof and self.sock_avail():
            self.fill_rawq()
            self.process_rawq()
        return self.read_very_lazy()

    def read_lazy(self):
        """Process and return data that's already in the queues (lazy).

        Raise EOFError if connection closed and no data available.
        Return '' if no cooked data available otherwise.  Don't block
        unless in the midst of an IAC sequence.

        """
        self.process_rawq()
        return self.read_very_lazy()

    def read_very_lazy(self):
        """Return any data available in the cooked queue (very lazy).

        Raise EOFError if connection closed and no data available.
        Return '' if no cooked data available otherwise.  Don't block.

        """
        buf = self.cookedq.getvalue()
        self.cookedq.seek(0)
        self.cookedq.truncate()
        if not buf and self.eof and not self.rawq:
            raise EOFError, 'telnet connection closed'
        return buf

    def set_receive_callback(self, callback, *args, **kwargs):
        """The callback function called after each receipt of any data."""
        self.data_callback        = callback
        self.data_callback_kwargs = kwargs

    def set_window_size(self, rows, cols):
        """
        Change the size of the terminal window, if the remote end supports
        NAWS. If it doesn't, the method returns silently.
        """
        if not self.can_naws:
            return
        self.window_size = rows, cols
        size = struct.pack('!HH', cols, rows)
        self.sock.send(IAC + SB + NAWS + size + IAC + SE)

    def process_rawq(self):
        """Transfer from raw queue to cooked queue.

        Set self.eof when connection is closed.  Don't block unless in
        the midst of an IAC sequence.
        """
        buf = ''
        try:
            while self.rawq:
                # Handle non-IAC first (normal data).
                char = self.rawq_getchar()
                if char != IAC:
                    buf = buf + char
                    continue

                # Interpret the command byte that follows after the IAC code.
                command = self.rawq_getchar()
                if command == theNULL:
                    self.msg('IAC NOP')
                    continue
                elif command == IAC:
                    self.msg('IAC DATA')
                    buf = buf + command
                    continue

                # DO: Indicates the request that the other party perform,
                # or confirmation that you are expecting the other party
                # to perform, the indicated option.
                elif command == DO:
                    opt = self.rawq_getchar()
                    self.msg('IAC DO %s', ord(opt))
                    if opt == TTYPE:
                        self.sock.send(IAC + WILL + opt)
                    elif opt == NAWS:
                        self.sock.send(IAC + WILL + opt)
                        self.can_naws = True
                        if self.window_size:
                            self.set_window_size(*self.window_size)
                    else:
                        self.sock.send(IAC + WONT + opt)

                # DON'T: Indicates the demand that the other party stop
                # performing, or confirmation that you are no longer
                # expecting the other party to perform, the indicated
                # option.
                elif command == DONT:
                    opt = self.rawq_getchar()
                    self.msg('IAC DONT %s', ord(opt))
                    self.sock.send(IAC + WONT + opt)

                # SB: Indicates that what follows is subnegotiation of the
                # indicated option.
                elif command == SB:
                    opt = self.rawq_getchar()
                    self.msg('IAC SUBCOMMAND %d', ord(opt))

                    # We only handle the TTYPE command, so skip all other
                    # commands.
                    if opt != TTYPE:
                        while self.rawq_getchar() != SE:
                            pass
                        continue

                    # We also only handle the SEND_TTYPE option of TTYPE,
                    # so skip everything else.
                    subopt = self.rawq_getchar()
                    if subopt != SEND_TTYPE:
                        while self.rawq_getchar() != SE:
                            pass
                        continue

                    # Mandatory end of the IAC subcommand.
                    iac = self.rawq_getchar()
                    end = self.rawq_getchar()
                    if (iac, end) != (IAC, SE):
                        # whoops, that's an unexpected response...
                        self.msg('expected IAC SE, but got %d %d', ord(iac), ord(end))
                    self.msg('IAC SUBCOMMAND_END')

                    # Send the next supported terminal.
                    ttype = self.termtype
                    self.msg('indicating support for terminal type %s', ttype)
                    self.sock.send(IAC + SB + TTYPE + theNULL + ttype + IAC + SE)
                elif command in (WILL, WONT):
                    opt = self.rawq_getchar()
                    self.msg('IAC %s %d',
                             command == WILL and 'WILL' or 'WONT', ord(opt))
                    if opt == ECHO:
                        self.sock.send(IAC + DO + opt)
                    else:
                        self.sock.send(IAC + DONT + opt)
                else:
                    self.msg('IAC %d not recognized' % ord(command))
        except EOFError: # raised by self.rawq_getchar()
            pass
        self.cookedq.write(buf)
        if self.data_callback is not None:
            self.data_callback(buf, **self.data_callback_kwargs)

    def rawq_getchar(self):
        """Get next char from raw queue.

        Block if no data is immediately available.  Raise EOFError
        when connection is closed.

        """
        if not self.rawq:
            self.fill_rawq()
            if self.eof:
                raise EOFError
        c = self.rawq[self.irawq]
        self.irawq = self.irawq + 1
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        return c

    def fill_rawq(self):
        """Fill raw queue from exactly one recv() system call.

        Block if no data is immediately available.  Set self.eof when
        connection is closed.

        """
        if self.irawq >= len(self.rawq):
            self.rawq = ''
            self.irawq = 0
        # The buffer size should be fairly small so as to avoid quadratic
        # behavior in process_rawq() above.
        buf = self.sock.recv(64)
        self.msg("recv %s", `buf`)
        self.eof = (not buf)
        self.rawq = self.rawq + buf

    def sock_avail(self):
        """Test whether data is available on the socket."""
        return select.select([self], [], [], 0) == ([self], [], [])

    def interact(self):
        """Interaction function, emulates a very dumb telnet client."""
        if sys.platform == "win32":
            self.mt_interact()
            return
        while 1:
            rfd, wfd, xfd = select.select([self, sys.stdin], [], [])
            if self in rfd:
                try:
                    text = self.read_eager()
                except EOFError:
                    print '*** Connection closed by remote host ***'
                    break
                if text:
                    self.stdout.write(text)
                    self.stdout.flush()
            if sys.stdin in rfd:
                line = sys.stdin.readline()
                if not line:
                    break
                self.write(line)

    def mt_interact(self):
        """Multithreaded version of interact()."""
        import thread
        thread.start_new_thread(self.listener, ())
        while 1:
            line = sys.stdin.readline()
            if not line:
                break
            self.write(line)

    def listener(self):
        """Helper for mt_interact() -- this executes in the other thread."""
        while 1:
            try:
                data = self.read_eager()
            except EOFError:
                print '*** Connection closed by remote host ***'
                return
            if data:
                self.stdout.write(data)
            else:
                self.stdout.flush()

    def _wait_for_data(self, timeout):
        end = time.time() + timeout
        while True:
            readable, writeable, excp = select.select([self.sock], [], [], 1)
            if readable:
                return True
            if time.time() > end:
                return False

    def _waitfor(self, list, timeout=None, flush=False, cleanup=None):
        re = None
        list = list[:]
        indices = range(len(list))
        search_window_size = 150
        head_loockback_size = 10
        for i in indices:
            if not hasattr(list[i], "search"):
                if not re: import re
                list[i] = re.compile(list[i])
        self.msg("Expecting %s" % [l.pattern for l in list])
        incomplete_tail = ''
        clean_sw_size = search_window_size
        while 1:
            self.process_rawq()
            if self.cancel_expect:
                self.cancel_expect = False
                self.msg('cancelling expect()')
                return -2, None, ''
            qlen = self.cookedq.tell()
            if cleanup:
                while 1:
                    self.cookedq.seek(qlen - clean_sw_size - len(incomplete_tail) - head_loockback_size)
                    search_window = self.cookedq.read()
                    search_window, incomplete_tail = cleanup(search_window)
                    if clean_sw_size > qlen or len(search_window) >= search_window_size:
                        search_window = search_window[-search_window_size:]
                        if len(search_window) > search_window_size:
                            clean_sw_size = clean_sw_size - search_window_size
                        break
                    else:
                        clean_sw_size = clean_sw_size + search_window_size
            else:
                self.cookedq.seek(qlen - search_window_size)
                search_window = self.cookedq.read()
            for i in indices:
                m = list[i].search(search_window)
                if m is not None:
                    e    = len(m.group())
                    e    = qlen - e + 1
                    self.cookedq.seek(0)
                    text = self.cookedq.read(e)
                    if flush:
                        self.cookedq.seek(0)
                        self.cookedq.truncate()
                        self.cookedq.write(search_window[m.end():])
                    else:
                        self.cookedq.seek(qlen)
                    return i, m, text
            if self.eof:
                break
            if timeout is not None:
                if not self._wait_for_data(timeout): # Workaround for the problem with select() below.
                    break
                # The following will sometimes lock even if data is available
                # and I have no idea why. Do NOT reverse this unless you are sure
                # that you found the reason. The error is rare, but it does happen.
                #r, w, x = select.select([self.sock], [], [], timeout)
                #if not r:
                #    break
            self.fill_rawq()
        text = self.read_very_lazy()
        if not text and self.eof:
            raise EOFError
        return -1, None, text

    def waitfor(self, list, timeout=None, cleanup=None):
        """Read until one from a list of a regular expressions matches.

        The first argument is a list of regular expressions, either
        compiled (re.RegexObject instances) or uncompiled (strings).
        The optional second argument is a timeout, in seconds; default
        is no timeout.

        Return a tuple of three items: the index in the list of the
        first regular expression that matches; the match object
        returned; and the text read up till and including the match.

        If EOF is read and no text was read, raise EOFError.
        Otherwise, when nothing matches, return (-1, None, text) where
        text is the text received so far (may be the empty string if a
        timeout happened).

        If a regular expression ends with a greedy match (e.g. '.*')
        or if more than one expression can match the same input, the
        results are undeterministic, and may depend on the I/O timing.
        """
        return self._waitfor(list, timeout, False, cleanup)

    def expect(self, list, timeout=None, cleanup=None):
        """
        Like waitfor(), but removes the matched data from the incoming
        buffer.
        """
        return self._waitfor(list, timeout, True, cleanup = cleanup)


def test():
    """Test program for telnetlib.

    Usage: python telnetlib.py [-d] ... [host [port]]

    Default host is localhost; default port is 23.

    """
    debuglevel = 0
    while sys.argv[1:] and sys.argv[1] == '-d':
        debuglevel = debuglevel+1
        del sys.argv[1]
    host = 'localhost'
    if sys.argv[1:]:
        host = sys.argv[1]
    port = 0
    if sys.argv[2:]:
        portstr = sys.argv[2]
        try:
            port = int(portstr)
        except ValueError:
            port = socket.getservbyname(portstr, 'tcp')
    tn = Telnet()
    tn.set_debuglevel(debuglevel)
    tn.open(host, port)
    tn.interact()
    tn.close()

if __name__ == '__main__':
    test()
