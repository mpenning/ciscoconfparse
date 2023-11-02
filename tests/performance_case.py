#!/usr/bin/env python
import argparse
import time

from cProfile import run
import sys
import os

THIS_DIR = os.path.dirname(__file__)
# sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))
sys.path.insert(0, "..")

from ciscoconfparse import CiscoConfParse

def parse_cli_args(sys_argv1):
    """
    Reference: https://docs.python.org/3/library/argparse.html
    """
    if isinstance(sys_argv1, (list, tuple)):
        pass
    else:
        raise ValueError("`sys_argv1` must be a list or tuple with CLI options from `sys.argv[1:]`")


    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description="Run CiscoConfParse() performance tests",
        add_help=True,
    )
    parser_optional = parser.add_argument_group("optional")
    parser_optional.add_argument(
        "-s",
        "--small",
        default=False,
        action="store_true",
        help="Run a performance profile against a modest Cisco IOS configuration.",
    )
    parser_optional.add_argument(
        "-a",
        "--acls",
        default=False,
        action="store_true",
        help="Run a performance profile against a Cisco IOS configuration with large ACLs.",
    )
    parser_optional.add_argument(
        "-v",
        "--vlans",
        default=False,
        action="store_true",
        help="Run a performance profile against a Cisco IOS configuration with over 4000 Switched Vlan Interfaces.",
    )

    args = parser.parse_args()
    return args

if __name__=="__main__":
    args = parse_cli_args(sys.argv[1:])
    if any([args.small, args.acls, args.vlans]):
        time.sleep(0.25)
        if args.small is True:
            run("CiscoConfParse('fixtures/configs/sample_01.ios')", sort=2)
        elif args.acls is True:
            run("CiscoConfParse('fixtures/configs/sample_05.ios')", sort=2)
        elif args.vlans is True:
            run(
                "CiscoConfParse('fixtures/configs/sample_06.ios', syntax='ios', factory=True)", sort=2
            )
    else:
        error = f"Could not find a valid argument in {args}"
        logger.error(error)
        raise ValueError(error)
