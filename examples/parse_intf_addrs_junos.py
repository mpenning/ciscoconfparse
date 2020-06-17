from ciscoconfparse import CiscoConfParse

## Define an example configuration to parse...
config = """interfaces {                                                 
    xe-0/0/0 {                                               
        unit 0 {                                             
            family inet {                                    
                address 1.1.1.6/31;                     
            }                                                
            family inet6 {                                   
                address FD00:DEAD:CAFE:6000::4/127;         
            }                                                
        }                                                    
    }                                                        
    xe-0/0/1 {                                               
        unit 0 {                                             
            family inet {                                    
                address 2.2.2.10/31;                    
            }                                                
            family inet6 {                                   
                address FD00:DEAD:CAFE:7903::2/64;             
            }                                                
        }                                                    
    }                                                        
    xe-0/0/2 {                                               
        mtu 9192;                                            
        unit 0 {                                             
            family inet {                                    
                address 3.3.3.14/31;                    
            }                                                
            family inet6 {                                   
                address FD00:DEAD:CAFE:6000::26/127;        
            }                                                
        }                                                    
    }                                                        
}""".splitlines()

## Parse the list of config lines here...
parse = CiscoConfParse(config, syntax='junos', comment='#')

## Define a set of regular expressions starting with the 'root' object and
## iterating over each object's children until we get to the address object.
##
## This winds up matching a whole 'branch' of a family...
branchspec = (
    r'interfaces',
    r'^\s+(\S+)',               # Detect any intf name...
    r'^\s+unit\s+(\d+)',        # Detect intf's unit
    r'^\s+family\s+(inet\d*)',  # Detect intf's inet family
    r'^\s+address\s+(\S+)',     # Detect intf's address
)
for params in parse.find_object_branches(branchspec):

    ## Assign object names here based on the order in `branchspec` (above)
    ## Numbering starts and zero and ends with four.  We don't need to use
    ## `branchspec[0]`...
    intf_obj, intf_unit_obj, intf_family_obj, addr_obj = params[1], params[2], \
        params[3], params[4]

    ## We included regex `match groups` in the `branchspec` regular expressions
    ## so we can assign the text matched by each match group to a unique
    ## variable name
    intf_name      = intf_obj.re_match_typed(branchspec[1])
    intf_unit      = intf_unit_obj.re_match_typed(branchspec[2])
    intf_family    = intf_family_obj.re_match_typed(branchspec[3])
    addr           = addr_obj.re_match_typed(branchspec[4])

    print("{}.{} {} {}".format(intf_name, intf_unit, intf_family, addr))
