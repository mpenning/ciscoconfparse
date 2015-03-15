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
Cisco IOS emulator.
"""
import re
from Exscript.emulators import VirtualDevice

iosbanner = '''
Connected to %s.
Escape character is '^]'.


Unauthorized access prohibited!


%s line 2 


at '%s' port '/dev/vty0' from '12.34.56.78'
'''

def show_diag(data):
    slot = re.search(r'(\d+)', data).groups()[0]
    return """
SLOT %s  (RP/LC 0 ): 16 Port ISE Packet Over SONET OC-3c/STM-1 Single Mode/IR LC connector
  MAIN: type 79,  800-19733-08 rev A0
        Deviation: 0
        HW config: 0x01    SW key: 00-00-00
  PCA:  73-7614-07 rev A0 ver 1
        Design Release 1.0  S/N SAL1026SSZX
  MBUS: Embedded Agent
        Test hist: 0x00    RMA#: 00-00-00    RMA hist: 0x00
  DIAG: Test count: 0x00000000    Test results: 0x00000000
  FRU:  Linecard/Module: 16OC3X/POS-IR-LC-B=
        Processor Memory: MEM-LC-ISE-1024=
        Packet Memory: MEM-LC1-PKT-512=(Non-Replaceable)
  L3 Engine: 3 - ISE OC48 (2.5 Gbps)
  MBUS Agent Software version 2.68 (RAM) (ROM version is 3.66)
  ROM Monitor version 18.0
  Fabric Downloader version used 7.1 (ROM version is 7.1)
  Primary clock is CSC 1
  Board is analyzed 
  Board State is Line Card Enabled (IOS  RUN )
  Insertion time: 00:00:30 (36w1d ago)
  Processor Memory size: 1073741824 bytes
  TX Packet Memory size: 268435456 bytes, Packet Memory pagesize: 16384 bytes
  RX Packet Memory size: 268435456 bytes, Packet Memory pagesize: 16384 bytes
  0 crashes since restart
""" % slot

commands = (
('show version', """
Cisco Internetwork Operating System Software 
IOS (tm) GS Software (C12KPRP-P-M), Version 12.0(32)SY6c, RELEASE SOFTWARE (fc3)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2008 by cisco Systems, Inc.
Compiled Mon 08-Sep-08 15:31 by leccese
Image text-base: 0x00010000, data-base: 0x055CD000

ROM: System Bootstrap, Version 12.0(20040128:214555) [assafb-PRP1P_20040101 1.8dev(2.83)] DEVELOPMENT SOFTWARE
BOOTLDR: GS Software (C12KPRP-P-M), Version 12.0(32)SY6c, RELEASE SOFTWARE (fc3)

 S-EA1 uptime is 36 weeks, 1 day, 15 hours, 9 minutes
Uptime for this control processor is 36 weeks, 1 day, 14 hours, 30 minutes
System returned to ROM by reload at 03:32:54 MET Mon Feb 16 2009
System restarted at 03:25:22 MET Tue Mar 10 2009
System image file is "disk0:c12kprp-p-mz.120-32.SY6c.bin"

cisco 12416/PRP (MPC7457) processor (revision 0x00) with 1048576K bytes of memory.
MPC7457 CPU at 1263Mhz, Rev 1.1, 512KB L2, 2048KB L3 Cache
Last reset from power-on
Channelized E1, Version 1.0.

2 Route Processor Cards
2 Clock Scheduler Cards
3 Switch Fabric Cards
4 T1/E1 BITS controllers
1 Quad-port OC3c ATM controller (4 ATM).
2 16-port OC3 POS controllers (32 POS).
2 four-port OC12 POS controllers (8 POS).
2 twelve-port E3 controllers (24 E3).
1 Four Port Gigabit Ethernet/IEEE 802.3z controller (4 GigabitEthernet).
4 OC12 channelized to STS-12c/STM-4, STS-3c/STM-1 or DS-3/E3 controllers
4 ISE 10G SPA Interface Cards (12000-SIP-601)
3 Ethernet/IEEE 802.3 interface(s)
56 FastEthernet/IEEE 802.3 interface(s)
14 GigabitEthernet/IEEE 802.3 interface(s)
111 Serial network interface(s)
4 ATM network interface(s)
50 Packet over SONET network interface(s)
2043K bytes of non-volatile configuration memory.

250880K bytes of ATA PCMCIA card at slot 0 (Sector size 512 bytes).
65536K bytes of Flash internal SIMM (Sector size 256K).
Configuration register is 0x2102
""".lstrip()),

(r'sh\S* ip int\S* brie\S*', """
Interface     IP-Address     OK?  Method  Status                  Protocol
Ethernet0     10.108.00.5    YES  NVRAM   up                      up      
Ethernet1     unassigned     YES  unset   administratively down   down    
Loopback0     10.108.200.5   YES  NVRAM   up                      up      
Serial0       10.108.100.5   YES  NVRAM   up                      up      
Serial1       10.108.40.5    YES  NVRAM   up                      up      
Serial2       10.108.100.5   YES  manual  up                      up      
Serial3       unassigned     YES  unset   administratively down   down 
""".lstrip()),

('show interface.*', """
FastEthernet0/2 is administratively down, line protocol is down 
  Hardware is i82545, address is 0001.c9f4.c418 (bia 0001.c9f4.c418)
  MTU 1500 bytes, BW 100000 Kbit, DLY 100 usec, rely 255/255, load 1/255
  Encapsulation ARPA, loopback not set
  Keepalive set (10 sec)
  Half-duplex, Auto Speed
  ARP type: ARPA, ARP Timeout 04:00:00
  Last input never, output never, output hang never
  Last clearing of "show interface" counters never
  Input queue: 0/75/0/0 (size/max/drops/flushes); Total output drops: 0
  Queueing strategy: fifo
  Output queue: 0/40 (size/max)
  5 minute input rate 0 bits/sec, 0 packets/sec
  5 minute output rate 0 bits/sec, 0 packets/sec
     0 packets input, 0 bytes
     Received 0 broadcasts, 0 runts, 0 giants, 0 throttles
     0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored
     0 watchdog, 0 multicast
     0 input packets with dribble condition detected
     0 packets output, 0 bytes, 0 underruns
     1 output errors, 0 collisions, 0 interface resets
     0 babbles, 0 late collision, 0 deferred
     1 lost carrier, 0 no carrier
     0 output buffer failures, 0 output buffers swapped out
"""),

(r'show diag \d+', show_diag),

(r'^!.*', '')
)

class IOSEmulator(VirtualDevice):
    def __init__(self,
                 hostname,
                 echo       = True,
                 login_type = VirtualDevice.LOGIN_TYPE_BOTH,
                 strict     = True,
                 banner     = None):
        thebanner = iosbanner % (hostname, hostname, hostname)
        VirtualDevice.__init__(self,
                               hostname,
                               echo       = echo,
                               login_type = login_type,
                               strict     = strict,
                               banner     = banner or thebanner)
        self.user_prompt     = 'Username: '
        self.password_prompt = 'Password: '
        self.prompt          = hostname + '#'
        for command, handler in commands:
            self.add_command(command, handler)
