import csv
import re
import os

from ciscoconfparse import CiscoConfParse

"""
Author: David Michael Pennington <mike@pennington.net>
License: GPLv3
"""

def main(configpath, newconfigpath, csvpath):
    parse = CiscoConfParse(configpath)
    config = list()
    with open(csvpath) as csvfh:
        reader = csv.reader(csvfh)
        for idx, line in enumerate(reader):
            if idx==0:  # Skip the header line
                continue
            elif line==[]:  # Skip empty lines
                continue
            ## Parse out the old interface info from the csv file
            oldport, newport = line[0], line[1]
            try:
                ## Parse out the interface class & number via regex...
                mm = re.search(r'^(\w+?)\s*(\d\S+?)$', oldport.strip())
                if mm is not None:
                    # We correctly parsed the old port name into parts
                    oldclass, oldnum = mm.group(1), mm.group(2)
                else:
                    # We can't parse the old port name into parts...
                    error = "Cannot parse '{0}' in the csv".format(
                        oldport)
                    raise ValueError(error)
                # Find the old interface line...
                intfobj = parse.find_objects('^interface\s+{0}\s*{1}'.format(
                    oldclass, oldnum))[0]
            except IndexError:
                raise ValueError('Cant find "{0}" in the old config'.format(
                    oldport))

            ## Default the new interface to prevent any potential problems...
            config.append('default interface {0}'.format(newport))
            ## Add the new configuration...
            config.append('interface {0}'.format(newport))
            ## Add all the configuration for this interface...
            for child in intfobj.all_children:
                config.append(child.text)
            config.append('!')

    ## Write the new config
    with open(newconfigpath, 'w') as outfh:
        for line in config:
            outfh.write(line+os.linesep)

if __name__=='__main__':
    """Read a Cisco IOS config and a csv containing port mappings; output a new config"""
    configpath = raw_input('Path to the old config: ')
    newconfigpath = raw_input('Path to the new config: ')
    ## See example port_move.csv in this directory
    csvpath = raw_input('Path to the csv port mapping old -> new config: ')
    main(configpath, newconfigpath, csvpath)
    
