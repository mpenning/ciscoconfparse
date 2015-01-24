from random import randint, choice
import sys

if sys.argv[1]=="1":
    print "!"
    print "!"
    for vlan in range(1, 4095):
        print "vlan {0}".format(vlan)
        print " name VLAN_{0}".format(vlan)
        print "!"
    print "!"
    for slot in range(1, 14):
        for port in range(1, 49):
            print "interface GigabitEthernet {0}/{1}".format(slot, port)
            mode = choice(['trunk', 'access'])
            if mode=='trunk':
                print " switchport"
                print " switchport trunk encapsulation dot1q"
                print " switchport mode trunk"
                print " switchport trunk allowed vlan 1-{0}".format(randint(2, 4094))
                print " switchport nonnegotiate"
                print " spanning-tree guard root"
                print "!"
            elif mode=='access':
                print " switchport"
                print " switchport access vlan {0}".format(randint(2, 4094))
                print " switchport mode access"
                print " switchport nonnegotiate"
                print " spanning-tree portfast"
                print "!"
    for vlan in range(1, 4095):
        print "interface Vlan {0}".format(vlan)
        print " no shutdown"
        mode = choice(['global', 'vrf'])
        if mode=='vrf':
            print "ip vrf forwarding VRF_{0}".format(vlan)
        print " description Layer3 SVI: vlan {0}".format(vlan)
        print " ip address {0}.{1}.{2}.0 255.255.255.0".format(randint(1, 224), 
            randint(1, 255), randint(1, 255))
        print "!"

elif sys.argv[1]=="5":
    print "!"
    print "!"
    print "!"
    for acl_number in range(0, 100):
        print "ip access-list extended ACL_{0}".format('%02i' % acl_number)
        for ace in range(0, randint(20, 254)):
            print " permit {0} any host 192.0.2.{1}".format(choice(['tcp', 'udp', 'ip']), ace)
        print "!"
