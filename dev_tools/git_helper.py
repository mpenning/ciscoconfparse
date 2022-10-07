from subprocess import Popen, PIPE, STDOUT
from argparse import ArgumentParser
import shlex
import sys
import os

from loguru import logger as loguru_logger

def parse_args(input_str=""):
    """Parse CLI arguments, or parse args from the input_str variable"""

    ## input_str is useful if you don't want to parse args from the shell
    if input_str != "":
        # Example: parse_args("create -f this.txt -b")
        sys.argv = [input_str]  # sys.argv[0] is always the whole list of args
        sys.argv.extend(shlex.split(input_str))  # shlex adds the rest of argv

    parser = ArgumentParser(
        prog=os.path.basename(__file__),
        description="Manage a git workflow that uses git tags",
        add_help=True,
    )

    ## Create a master subparser for all commands
    parse_optional = parser.add_argument_group("optional")

    parse_optional.add_argument(
        "-c",
        "--checkout",
        help="git checkout to this branch string (default: '')",
        action="store",
        type=str,
        default="",
        required=False,
    )

    # Add a boolean flag to store_true...
    parse_optional.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        required=False,
        help="git push using --force-with-lease",
    )

    parse_optional.add_argument(
        "-t",
        "--tag",
        action="store_true",
        default=False,
        required=False,
        help="git push with a git tag",
    )

    args = parser.parse_args()
    return args

def LogIt(level=None, message=None):
    """Modest loguru hack to indent the log message based on log level."""

    message_indent = {
        "TRACE": 6,    # indent TRACE log message by 6 spaces
        "DEBUG": 5,    # indent DEBUG log message by 5 spaces
        "INFO": 4,
        "SUCCESS": 3,
        "WARNING": 2,
        "ERROR": 1,
        "CRITICAL": 0,
    }
    assert isinstance(level, str)
    assert level.upper() in set(message_indent.keys())
    assert isinstance(message, str)
    level = level.upper()

    indented_message = message_indent[level]*" " + message
    return loguru_logger.log(level, "|" + indented_message)

def run_cmd(
    # cmd takes a dictionary with a cmd key, or a string with a command in it
    cmd = None,
    cwd = os.getcwd(),
    colors = False,
    debug = 0,
):
    """run a shell command and return stdout / stderr strings
    To run a shell command, call like this...  a value in cwd is optional...
    ############
    # Call with a cmd string...
    ############
    cmd = "ls -la"
    stdout, stderr = run_cmd(cmd)
    """
    # ^ is a logical xor...
    #    -->   https://stackoverflow.com/a/432844/667301
    assert isinstance(cmd, str)
    assert sys.version_info >= (3, 6)  # Popen() encoding parameter requires 3.6
    args = parse_args()

    if debug > 0:
        LogIt("INFO", "Calling run_cmd(cmd='%s')".format(cmd))

    if debug > 1:
        LogIt("DEBUG", "Processing Popen() string cmd='{}'".format(cmd))
    assert cmd != ""
    assert cwd != ""
    cwd = os.path.expanduser(cwd)

    if debug > 1:
        LogIt("DEBUG", "Popen() started")

    process = Popen(
        shlex.split(cmd),
        shell=False,
        universal_newlines=True,
        cwd=cwd,
        stderr=PIPE,
        stdout=PIPE,
        # bufsize = 0  -> unbuffered
        # bufsize = 1  -> line buffered
        bufsize=0,
        # encoding parameter... https://stackoverflow.com/a/57970619/667301
        encoding="utf-8",
    )
    if debug > 1:
        LogIt("DEBUG", "Calling Popen().communicate()")
    stdout, stderr = process.communicate()
    if debug > 1:
        LogIt("DEBUG", "Popen().communicate() returned stdout=%s" % stdout)
    return (stdout, stderr)

def tag_git_version(args=None):
    # The VERSION environment variable should be set in a Makefile which calls
    # this script...
    VERSION = os.environ.get("VERSION")
    try:
        assert isinstance(VERSION, str)
    except AssertionError:
        LogIt("WARNING", "Could not find an env variable named 'VERSION'")
    except:
        raise NotImplementedError("")

    try:
        assert VERSION != "\${VERSION}"
    except AssertionError:
        LogIt("WARNING", "Env variable 'VERSION' assigned literal \${VERSION}")
    except:
        raise NotImplementedError("")

    if args.force is True:
        git_push_flag1 = "--force-with-lease"
    else:
        git_push_flag1 = ""

    if args.checkout != "":
        LogIt("DEBUG", "Checking out git branch: {}".format(args.checkout))
        stdout, stderr = run_cmd("git checkout {}".format(args.checkout))

    stdout, stderr = run_cmd("git remote remove origin")
    stdout, stderr = run_cmd('git remote add origin "git@github.com:mpenning/ciscoconfparse"')

    # TODO: build CHANGES.md management / edit tool... automate version change lists
    # TODO: support for push local tag to a remote 'git push origin 1.6.42'
    # TODO: support for delete remote tags 'git push origin ":refs/tags/waat"'
    # TODO: support for finding remote tags on a specific git hash 'git ls-remote -t <remote> | grep <commit-hash>'

    if args.tag is True:
        # Create a local git tag at git HEAD
        stdout, stderr = run_cmd('git tag -a {0} -m "Tag with {0}"'.format(VERSION))

    if args.force is True:
        stdout, stderr = run_cmd('git push {} git@github.com:mpenning/ciscoconfparse.git'.format(git_push_flag1))
    else:
        stdout, stderr = run_cmd('git push git@github.com:mpenning/ciscoconfparse.git')

    if args.force is True and args.tag is True:
        stdout, stderr = run_cmd('git push {} --tags origin +main'.format(git_push_flag1))
        stdout, stderr = run_cmd('git push {} --tags origin {}'.format(git_push_flag1, VERSION))

    elif args.force is False and args.tag is True:
        stdout, stderr = run_cmd('git push --tags origin +main')
        stdout, stderr = run_cmd('git push --tags origin {}'.format(VERSION))

    elif args.force is True and args.tag is False:
        stdout, stderr = run_cmd('git push {} origin +main'.format(git_push_flag1))
    elif args.force is False and args.tag is False:
        stdout, stderr = run_cmd('git push origin +main')

if __name__=="__main__":
    args = parse_args()
    tag_git_version(args)
