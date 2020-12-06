from argparse import ArgumentParser
import shlex
import csv
import sys
import re
import os

from ciscoconfparse import CiscoConfParse

assert sys.version_info>=(3, 0, 0), "Error.  Please install Python 3"

"""
Author: David Michael Pennington <mike@pennington.net>
License: GPLv3

portmover.py:
Move ports from an 'old' switch to a new switch:
    Read a Cisco IOS config and a csv containing port mappings; 
    output a new switch config
"""

def parse_args(input_str=""):
    """Parse CLI arguments, or parse args from the input_str variable"""

    ## input_str is useful if you don't want to parse args from the shell
    if input_str!="":
        # Example: parse_args("create -f this.txt -b")
        sys.argv = [input_str]   # sys.argv[0] is always the whole list of args
        sys.argv.extend(shlex.split(input_str))   # shlex adds the rest of argv

    parser = ArgumentParser(prog=os.path.basename(__file__), 
        description='Move ports in a new switch configuration', add_help=True)

    parser_required = parser.add_argument_group('required')
    parser_required.add_argument('-o', '--old', required=True, 
        help='Old config filename')
    parser_required.add_argument('-n', '--new', required=True, 
        help='New config filename')
    parser_required.add_argument('-m', '--map', required=True, 
        help='CSV file which maps old to new ports')

    return parser.parse_args()


def main(args):
    """Read a old Cisco IOS config and a csv containing port mappings; output a new config"""
    parse = CiscoConfParse(args.old) # parse the old config
    config = list()  # Initialize a container for the new config

    # Open the csv... 
    with open(args.map) as csvfh:
        reader = csv.reader(csvfh)

        # iterate over the port mappings in the csv...
        for idx, row in enumerate(reader):
            if idx==0:  # Skip the CSV header row
                continue
            elif row==[]:  # Skip empty CSV rows
                continue

            # Ensure there are two columns on this csv row
            assert len(row)==2, "CSV row: '{0}' must have two columns".format(
                row)

            ## Read the old & new interface info from the csv file
            oldport, newport = row[0], row[1]

            ## Parse out the interface class & number via regex...
            mm = re.search(r'^(\w+?)\s*(\d\S+)$', oldport.strip())
            if mm is not None:
                # We correctly parsed the old port name into parts
                oldclass, oldnum = mm.group(1), mm.group(2)
            else:
                # We can't parse the old port name into parts...
                error = "Cannot parse '{0}' in the csv".format(
                    oldport)
                raise ValueError(error)
            try:
                # Find the old interface...
                intfobj = parse.find_objects('^interface\s+{0}\s*{1}$'.format(
                    oldclass, oldnum))[0]
            except IndexError:
                raise ValueError('Cant find "{0}" in the old config'.format(
                    oldport))

            ## Default the new interface to prevent any potential problems...
            config.append('default interface {0}'.format(newport))
            ## Add the new interface configuration...
            config.append('interface {0}'.format(newport))
            ## Copy all the old configuration to the new interface...
            for child in intfobj.all_children:
                config.append(child.text)
            config.append('!')

    ## Write the new config file
    with open(args.new, 'w') as newconffh:
        for line in config:
            newconffh.write(line+os.linesep)

if __name__=='__main__':
    """Read a Cisco IOS config and a csv containing port mappings; output a new config"""
    args = parse_args()
    main(args)
