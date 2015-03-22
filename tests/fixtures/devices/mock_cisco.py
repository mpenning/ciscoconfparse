#!/usr/bin/python

"""
This is how it should be used:

hostname>en
Password:
hostname#conf t
Enter configuration commands, one per line. End with CNTL/Z
hostname(config)#username admin password secure
hostname(config)#exit
hostname#wr m
Building configuration...
[OK]
hostname#
"""

import time
import sys

import MockSSH

## Define some globals here
CRLF = '\r\n'
ENABLE_PASS = 'cisco123'
HOSTNAME = "MockSwitch"

INTF_BRIEF = """Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  unassigned      YES NVRAM  up                    down
Vlan10                  10.0.10.3      YES NVRAM  up                    up
GigabitEthernet0/1     unassigned      YES unset  up                    up
GigabitEthernet0/2     unassigned      YES unset  up                    up
GigabitEthernet0/3     unassigned      YES unset  down                  down
GigabitEthernet0/4     unassigned      YES unset  down                  down
GigabitEthernet0/5     unassigned      YES unset  up                    up
GigabitEthernet0/6     unassigned      YES unset  up                    up
GigabitEthernet0/7     unassigned      YES unset  up                    up
GigabitEthernet0/8     unassigned      YES unset  up                    up
Loopback0               192.0.2.1      YES unset  up                    up"""

VERSION = """Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 15.0(2)SE7, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2014 by Cisco Systems, Inc.
Compiled Thu 23-Oct-14 14:49 by prod_rel_team

ROM: Bootstrap program is C2960 boot loader
BOOTLDR: C2960 Boot Loader (C2960-HBOOT-M) Version 12.2(35r)SE2, RELEASE SOFTWARE (fc1)

sw3 uptime is 159 days, 17 hours, 6 minutes
System returned to ROM by power-on
System restarted at 17:36:44 CST Thu Nov 13 2014
System image file is "flash:c2960-lanbasek9-mz.150-2.SE7.bin"


This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

cisco WS-C2960G-8TC-L (PowerPC405) processor (revision A0) with 65536K bytes of memory.
Processor board ID FOC2222V77S
Last reset from power-on
2 Virtual Ethernet interfaces
8 Gigabit Ethernet interfaces
The password-recovery mechanism is enabled.

64K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : F4:AC:DE:AD:BE:EF
Motherboard assembly number     : 73-10613-08
Power supply part number        : 341-0208-01
Motherboard serial number       : FOC10010XZ1
Power supply serial number      : LIT13370000
Model revision number           : A0
Motherboard revision number     : B0
Model number                    : WS-C2960G-8TC-L
System serial number            : FOC2222V77S
Top Assembly Part Number        : 800-28133-01
Top Assembly Revision Number    : F0
Version ID                      : V01
CLEI Code Number                : COM7S00ARA
Hardware Board Revision Number  : 0x01


Switch Ports Model              SW Version            SW Image
------ ----- -----              ----------            ----------
*    1 8     WS-C2960G-8TC-L    15.0(2)SE7            C2960-LANBASEK9-M


Configuration register is 0xF
"""

def invalid_input(instance):
    #% Invalid input detected at '^' marker.
    errmsg1 = " "*len(instance.protocol.prompt.strip())+"""^"""
    errmsg2 = CRLF+"""% Invalid input detected at '^' marker."""
    errmsg = errmsg1+errmsg2
    instance.write(errmsg)

def incomplete_command(instance):
    #% Incomplte command
    errmsg = """% Incomplete command."""
    instance.write(errmsg)

def set_term_nopage(instance):
    instance.term_nopage = True

#
# command: enable
#
def enable_prompt(instance):
    instance.protocol.prompt = CRLF+"{0}#".format(HOSTNAME)
    instance.protocol.password_input = False

def en_password_denied(instance):
    #% Access denied
    instance.write("% Access denied")

#
# sh ip int brief
#
def sh_ip_int_brief(instance):
    for idx, line in enumerate(INTF_BRIEF.splitlines()):
        if idx==0:
            crlf = ""
        else:
            crlf = CRLF
        instance.write(crlf+line)

#
# sh ver (with paging)
#
def sh_ver(instance):
    more_str = " --More-- "
    for idx, line in enumerate(VERSION.splitlines()):
        if idx==0:
            crlf = ""
        elif idx==23:
            crlf = CRLF
            # FIXME: Implement paging here in the future
            if not getattr(instance, 'term_nopage', None):
                # FIXME: I can't figure out how to make this force paging
                #more_prompt(instance, instance)
                pass
        else:
            crlf = CRLF
        instance.write(crlf+line)

#
# configuration mode: username foo password bar
#
class command_username(MockSSH.SSHCommand):
    name = 'username'

    def start(self):
        if 'config' not in self.protocol.prompt:
            invalid_input(self)

        elif (not len(self.args)>3 or not self.args[1]=='password'):
            # Throw incomplete command if not enough args
            incomplete_command(self)

        elif (not len(self.args)==3 or not self.args[1]=='password'):
            # Throw invalid input if no pasword keyword
            invalid_input(self)

        self.exit()

def wait_for_more(instance):
    while True:
        time.sleep(0.1)

class more_prompt(MockSSH.SSHCommand):

    def start(self):
        prompt = ' --More-- '
        self.protocol.password_input = True
        self.callbacks = [wait_for_more, wait_for_more]

    def lineReceived(self, line):
        pass

#
# command: conf
#
def conf_output_error(instance):
    invalid_input(instance)


def conf_output_success(instance):
    usermsg1 = "Enter configuration commands, one per line.  End with CNTL/Z."
    instance.write(usermsg1)

def conf_change_protocol_prompt(instance):
    instance.protocol.prompt = CRLF+"{0}(config)#".format(HOSTNAME)


#
# command: quit
#
def quit_command_success(instance):
    if 'config' in instance.protocol.prompt:
        # We are exiting config mode, and quit isn't a valid command
        invalid_input(instance)
    else:
        instance.protocol.call_command(
            instance.protocol.commands['_exit'])
#
# command: exit
#
def exit_command_success(instance):
    if 'config' in instance.protocol.prompt:
        # We are exiting config mode
        instance.protocol.prompt = CRLF+"{0}#".format(HOSTNAME)
    else:
        instance.protocol.call_command(
            instance.protocol.commands['_exit'])

#
# command: end
#
def end_command_success(instance):
    if 'config' in instance.protocol.prompt:
        # We are exiting config mode
        instance.protocol.prompt = CRLF+"{0}#".format(HOSTNAME)
    else:
        invalid_input(instance)

#
# command: wr
#
def wr_build_config(instance):
    instance.terminal.session.conn.transport.transport.setTcpNoDelay(True)
    instance.write("Building configuration...")
    ## In a perfect world, we would sleep here to pretend
    ##    that the router is building the configuration; however,
    ##    there isn't a good way to make Twisted flush the TCP buffer
    ##    so the client sees a delay between "Building configuration..." 
    ##    and "[OK]"
    #time.sleep(1.2)
    instance.write(CRLF+"[OK]")

command_en = MockSSH.PromptingCommand(
    'en',         # the enable command
    ENABLE_PASS,  # enable password
    'Password: ', # enable password prompt
    success_callbacks=[enable_prompt],
    failure_callbacks=[en_password_denied])

command_enable = MockSSH.PromptingCommand(
    'enable',     # the enable command
    ENABLE_PASS,  # enable password
    'Password: ', # enable password prompt
    success_callbacks=[enable_prompt],
    failure_callbacks=[en_password_denied])

command_conf = MockSSH.ArgumentValidatingCommand(
    'conf',
    [conf_output_success, conf_change_protocol_prompt],
    [invalid_input],
    *["t"])

command_wr = MockSSH.ArgumentValidatingCommand(
    'wr',
    [wr_build_config],
    [invalid_input],
    *["m"])

command_term_len = MockSSH.ArgumentValidatingCommand(
    'term',
    [set_term_nopage],
    [invalid_input],
    *['len', '0'])

command_sh_ip_int_brief = MockSSH.ArgumentValidatingCommand(
    'sh',
    [sh_ip_int_brief],
    [invalid_input],
    *['ip', 'int', 'brief'])

command_sh_ver = MockSSH.ArgumentValidatingCommand(
    'show',
    [sh_ver],
    [invalid_input],
    *['ver'])

command_quit = MockSSH.ArgumentValidatingCommand(
    'quit',
    [quit_command_success],
    [invalid_input],
    *[])

command_end = MockSSH.ArgumentValidatingCommand(
    'end',
    [end_command_success],
    [invalid_input],
    *[])

command_exit = MockSSH.ArgumentValidatingCommand(
    'exit',
    [exit_command_success],
    [invalid_input],
    *[])

def start_cisco_mock(initial_prompt='>'):
    """This is where we define everything that is emulated"""

    # List of commands to emulate... see definitions above
    commands = [
        command_en,
        command_enable,
        command_term_len,
        command_sh_ip_int_brief,
        command_sh_ver,
        command_conf,
        command_username,
        command_wr,
        command_quit,
        command_end,
        command_exit,
    ]

    users = {'admin': 'cisco'}
    MockSSH.startThreadedServer(commands,
                                prompt=CRLF+"{0}{1}".format(HOSTNAME, initial_prompt),
                                interface="localhost",
                                port=2222,
                                **users)

def stop_cisco_mock():
    MockSSH.stopThreadedServer()

if __name__=='__main__':
    print("Connect with 'ssh -p 2222 admin@localhost'")
    start_cisco_mock()

    # Force the user to type stop if this was run from the CLI
    input = ''
    try:
        while (input!='stop'):
            input = raw_input('Type stop to stop: ').lower()
        stop_cisco_mock()
    except KeyboardInterrupt:
        stop_cisco_mock()
