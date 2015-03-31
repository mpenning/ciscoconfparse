#!/usr/bin/python

################################################################################
#             First approach of my auditing script                             #
################################################################################

import ciscoconfparse

parser = ciscoconfparse.CiscoConfParse("/Users/mlanger/ownCloud/Downloads/449090_network.txt", factory=True, syntax="asa")
#parser = ciscoconfparse.CiscoConfParse("/Users/mlanger/ownCloud/Downloads/449093_network.txt", factory=True, syntax="asa")

interfaces = parser.find_objects(r"^interface ")
print "---------------------------------------------------------------------------"
print "                           INTERFACES                                      "
print "---------------------------------------------------------------------------"

for interface in interfaces:
    print "---------------------------------------------------------------------------"
    print "Object       : ", interface
    print "Intf Name    : ", interface.name
    print "Intf Alias   : ", interface.intf_name
    print "Is Interface : ", interface.is_intf
    print "Intf IP      : ", interface.ipv4_addr
    print "Intf Netmask : ", interface.ipv4_netmask, " => ", interface.ipv4_masklength

acls = parser.find_objects(r"^access-list ")

print "---------------------------------------------------------------------------"
print "                              ACLs                                         "
print "---------------------------------------------------------------------------"

for acl in acls:
    print "---------------------------------------------------------------------------"
    if acl.is_remark:
        print "ACL Object: ", acl
        print "ACL Config: ", acl.text
        print "ACL Name  : ", acl.acl_name
        print "ACL Type  : ", acl.acl_type
        print "ACL Remark: ", acl.acl_remark
    else:
        print "ACL Object   : ", acl
        print "ACL Config   : ", acl.text
        print "ACL Name     : ", acl.acl_name
        print "ACL Type     : ", acl.acl_type
        print "ACL Action   : ", acl.acl_action
        print "ACL Protocol : ", acl.acl_protocol
        print "ACL Matchtype: ", acl.acl_matchtype
        print "ACL src      : ", acl.acl_srcmatchobject
