#!/bin/bash

##############################################################################
# Change into your virtualenv before running the script                      #
##############################################################################

# Print very verbose debugging info to STDOUT
# functionally, '-o functrace' is the same as the -T option above...
set -xT

# -v: Print STDIN lines as they are read
# -e: Stop this script if a command exits w/ a non-zero code
# -u: Stop this script if a variable has an error
set -veu

# -o pipefail: Stop this script if a pipeline has an error
set -o pipefail

# IFS is "Initial Field Seperator"...
#     By default, bash sets $IFS to $' \n\t' - space, newline, tab
#     bash $IFS default to split on spaces can cause unexpected problems
IFS=$'\n\t'


declare -a all_tests=("test_CiscoConfParse.py" "test_Ccp_Util.py" "test_Models_Cisco.py" "test_Models_Asa.py" "test_Models_Junos.py")
# bash loop syntax...
#     https://stackoverflow.com/a/8880633/667301
for test_filename in "${all_tests[@]}"
do
   pytest -r=fE --exitfirst --durations=5 --strict-config --cache-clear --capture=sys --show-capture=all --tb=short --strict-config --color=yes --code-highlight=yes --showlocals "$test_filename"
   sleep 0.05
done
