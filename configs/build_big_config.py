from random import randint, choice

print "!"
print "!"
print "!"
for acl_number in range(0, 100):
    print "ip access-list extended ACL_{0}".format('%02i' % acl_number)
    for ace in range(0, randint(20, 254)):
        print " permit {0} any host 192.0.2.{1}".format(choice(['tcp', 'udp', 'ip']), ace)
    print "!"
