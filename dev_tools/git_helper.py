from subprocess import Popen, PIPE, STDOUT
from argparse import ArgumentParser
import shlex
import sys
import os
import re

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
        "-p",
        "--push",
        action="store_true",
        default=False,
        required=False,
        help="git push",
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
    if args.force is True:
        args.push = True
    # args.tag_value = get_version()

    return args


def check_exists_tag_value(tag_value=None):
    """Check 'git tag' for an exact string match for tag_value."""
    assert isinstance(tag_value, str)
    loguru_logger.log(
        "INFO",
        "|"
        + "Checking whether version '{}' is defined in pyproject.toml".format(
            tag_value
        ),
    )
    stdout, stderr = run_cmd("git tag")
    for line in stdout.splitlines():
        if tag_value.strip() == line.strip():
            loguru_logger.log(
                "INFO", "|" + "Tag '{}' already exists.".format(tag_value)
            )
            return True
    loguru_logger.log("INFO", "|" + "'{}' is a new git tag".format(tag_value))
    return False


def LogItDeprecated(level=None, message=None):
    """Modest loguru hack to indent the log message based on log level."""

    message_indent = {
        "TRACE": 6,  # indent TRACE log message by 6 spaces
        "DEBUG": 5,  # indent DEBUG log message by 5 spaces
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

    indented_message = message_indent[level] * " " + message
    return loguru_logger.log(level, "|" + indented_message)


def run_cmd(
    # cmd takes a dictionary with a cmd key, or a string with a command in it
    cmd=None,
    cwd=os.getcwd(),
    colors=False,
    debug=0,
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
        loguru_logger.log("INFO", "|" + "Calling run_cmd(cmd='%s')".format(cmd))

    if debug > 1:
        loguru_logger.log(
            "DEBUG", "|" + "Processing Popen() string cmd='{}'".format(cmd)
        )
    assert cmd != ""
    assert cwd != ""
    cwd = os.path.expanduser(cwd)

    if debug > 1:
        loguru_logger.log("DEBUG", "|" + "Popen() started")

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
        loguru_logger.log("DEBUG", "|" + "Calling Popen().communicate()")
    stdout, stderr = process.communicate()
    if debug > 1:
        loguru_logger.log(
            "DEBUG", "|" + "Popen().communicate() returned stdout=%s" % stdout
        )
    return (stdout, stderr)


def git_root_directory():
    """
    return a string with the path name of the git root directory.
    """
    stdout, stderr = run_cmd("git rev-parse --show-toplevel")
    retval = None
    for line in stdout.splitlines():
        if line.strip() != "":
            retval = line.strip()
            return retval
    raise OSError()


def get_version():
    """Read the version from pyproject.toml"""
    filepath = os.path.join(git_root_directory(), "pyproject.toml")
    assert os.path.isfile(filepath)
    for line in open(filepath).read().splitlines():
        if "version" in line:
            rr = re.search(r"\s*version\s*=\s*(\S+)$", line.strip())
            if rr is not None:
                return rr.group(1).strip().strip("'").strip('"')
        else:
            continue
    raise ValueError()


def git_tag_and_push(args):
    version = get_version()
    loguru_logger.log("DEBUG", "|" + "Tagging this repo with '{}'".format(version))

    if args.checkout != "":
        loguru_logger.log(
            "DEBUG", "|" + "Checking out git branch: {}".format(args.checkout)
        )
        stdout, stderr = run_cmd("git checkout {}".format(args.checkout))

    stdout, stderr = run_cmd("git remote remove origin")
    stdout, stderr = run_cmd(
        'git remote add origin "git@github.com:mpenning/ciscoconfparse"'
    )

    # TODO: build CHANGES.md management / edit tool... automate version change lists
    # TODO: support for push local tag to a remote 'git push origin 1.6.42'
    # TODO: support for delete remote tags 'git push origin ":refs/tags/waat"'
    # TODO: support for finding remote tags on a specific git hash 'git ls-remote -t <remote> | grep <commit-hash>'

    version = get_version()  # Get the version from pyproject.toml
    assert isinstance(version, str)

    print("ARGS push", args.push)
    print("ARGS tag", args.tag)
    print("ARGS force", args.force)

    if check_exists_tag_value(tag_value=version) is True:
        loguru_logger.log(
            "INFO",
            "|"
            + "The -t argument is rejected; the '{0}' tag already exists in this local git repo".format(
                version
            ),
        )

    else:
        # args.tag is a new tag value...
        if args.tag is True:
            # Create a local git tag at git HEAD
            stdout, stderr = run_cmd('git tag -a {0} -m "Tag with {0}"'.format(version))

    stdout, stderr = run_cmd("git checkout main")

    if args.force is False and args.push is True and args.tag is False:
        # Do NOT force push
        loguru_logger.log(
            "SUCCESS", "|" + "git push (without tags) to the main branch at git origin."
        )
        stdout, stderr = run_cmd("git push git@github.com:mpenning/ciscoconfparse.git")
        stdout, stderr = run_cmd("git push origin +main")

    elif args.force is False and args.push is True and args.tag is True:
        loguru_logger.log(
            "SUCCESS", "|" + "git push (with tags) to the main branch at git origin."
        )
        stdout, stderr = run_cmd("git push --tags origin +main")
        stdout, stderr = run_cmd("git push --tags origin {}".format(version))

    elif args.force is True and args.tag is True:
        # Force push and tag
        loguru_logger.log(
            "SUCCESS",
            "|" + "git push FORCED (with tags) to the main branch at git origin.",
        )
        stdout, stderr = run_cmd(
            "git push --force-with-lease --tags git@github.com:mpenning/ciscoconfparse.git"
        )
        stdout, stderr = run_cmd("git push --force-with-lease --tags origin +main")
        stdout, stderr = run_cmd(
            "git push --force-with-lease --tags origin {}".format(version)
        )

    elif args.force is True and args.tag is False:
        loguru_logger.log(
            "SUCCESS",
            "|" + "git push FORCED (without tags) to the main branch at git origin.",
        )
        stdout, stderr = run_cmd("git push --force-with-lease origin +main")

    else:
        ValueError("Found an invalid combination of CLI options")


if __name__ == "__main__":
    args = parse_args()
    git_tag_and_push(args)
    # sys.exit(1)
