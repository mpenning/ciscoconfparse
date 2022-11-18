"""
A git wrapper to simplify git operations.
"""

from subprocess import Popen, PIPE, STDOUT
from argparse import ArgumentParser
import fileinput
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
    parse_required = parser.add_argument_group("required")

    ## Create a master subparser for all optional commands
    parse_optional = parser.add_argument_group("optional")

    parse_optional.add_argument(
        "-b",
        "--branch",
        action="store",
        type=str,
        default="main",
        required=False,
        help="git checkout to this branch string (default: '')",
    )

    parse_optional.add_argument(
        "-c",
        "--combine",
        action="store",
        type=str,
        default="",
        required=False,
        help="combine a git branch with the 'main' branch",
    )

    parse_optional.add_argument(
        "-d",
        "--debug",
        action="store",
        type=int,
        default=False,
        required=False,
        help="git_helper.py debug level",
    )

    # Add a boolean flag to store_true...
    parse_optional.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        required=False,
        help="Force a git push (using --force-with-lease)",
    )

    parse_optional.add_argument(
        "-I",
        "--increment_version",
        action="store",
        default=None,
        required=False,
        choices=[
            "major",
            "minor",
            "patch",
        ],
        help="Increment the version tag in pyproject.toml",
    )

    parse_optional.add_argument(
        "-m",
        "--message",
        action="store",
        default="",
        required=False,
        help="Add a push / merge message",
    )

    parse_optional.add_argument(
        "-M",
        "--method",
        action="store",
        default=None,
        required=False,
        choices=["merge", "rebase", "ff"],  # ff -> fast-forward
        help="Use this git method to combine pending branches: merge, rebase, or ff (fast-forward)",
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
        "-P",
        "--project",
        action="store",
        type=str,
        default="",
        required=False,
        help="name of project",
    )

    parse_optional.add_argument(
        "-s",
        "--status",
        action="store_true",
        default=False,
        required=False,
        help="return the git status",
    )

    parse_optional.add_argument(
        "-t",
        "--tag",
        action="store_true",
        default=False,
        required=False,
        help="git push with a git tag from pyproject.toml",
    )

    parse_optional.add_argument(
        "-u",
        "--user",
        action="store",
        type=str,
        default=os.environ.get("USER", ""),
        required=False,
        help="git username (default: $USER)",
    )

    args = parser.parse_args()

    if args.combine == "main":
        assert args.method is not None
        raise ValueError(
            "git_helper.py --combine cannot combine the 'main' branch with itself."
        )

    if args.combine != "":
        if args.method is None:
            raise ValueError("git_helper.py --combine requires use of -M / --method")

    if args.combine != "":
        if args.message == "":
            raise ValueError("git_helper.py --combine requires use of -m / --message")

    if args.push is True:
        if args.user == "":
            raise ValueError("git_helper.py --push requires use of -u / --user")

    if args.push is True:
        if args.project == "":
            raise ValueError("git_helper.py --push requires use of -P / --project")

    return args

def is_pyproject_version_in_origin(args):
    pyproject_version = get_pyproject_version(args)

def epoch_ts(commit_hash=None):
    """
    Return the number of integer epoch seconds for the commit hash.
    """
    assert isinstance(commit_hash, str)
    assert len(commit_hash) == 7 or len(commit_hash) == 40
    # 'git show' credit... https://stackoverflow.com/a/3815007/667301
    stdout, stderr = run_cmd("git show -s --format=%ct {0}".format(commit_hash))
    if len(stderr.strip()) > 0:
        return -1
    else:
        return int(stdout.strip())

def ls_remote_origin(args):
    stdout, stderr = run_cmd("git ls-remote origin")
    short_hash = {
        "tag": {},
        "branch_head": {},
        "pull_head": {},
        "pull_merge": {},
        "hash_epoch_ts": {},
    }
    long_hash = {
        "tag": {},
        "branch_head": {},
        "pull_head": {},
        "pull_merge": {},
        "hash_epoch_ts": {},
    }
    for line in stdout.splitlines():
        parse_tag = re.search(r"^(\w+)\s+refs\Wtags\W(\S+?)\^\{\}\s*$", line.strip())
        # refs/heads/main
        parse_branch = re.search(r"^(\w+)\s+refs\Wheads\W(\S+?)\s*$", line.strip())
        # refs/pull/100/head refs/pull/100/head
        parse_pull_head = re.search(
            r"^(\w+)\s+refs\Wpull\W(\d+)\Whead\s*$", line.strip()
        )
        # refs/pull/100/head refs/pull/100/merge
        parse_pull_merge = re.search(
            r"^(\w+)\s+refs\Wpull\W(\d+)\Wmerge\s*$", line.strip()
        )
        parsed = False
        what = "N/A"
        if parse_tag is not None:
            git_commit_hash = parse_tag.group(1)
            git_ref = parse_tag.group(2)
            short_hash["tag"][git_ref] = git_commit_hash[0:7]
            long_hash["tag"][git_ref] = git_commit_hash
            what = "tag"
            parsed = True
        elif parse_branch is not None:
            git_commit_hash = parse_branch.group(1)
            git_ref = parse_branch.group(2)
            short_hash["branch_head"][git_ref] = git_commit_hash[0:7]
            long_hash["branch_head"][git_ref] = git_commit_hash
            what = "branch_head"
            parsed = True
        elif parse_pull_head is not None:
            git_commit_hash = parse_pull_head.group(1)
            git_ref = int(parse_pull_head.group(2))  # Pull Request number
            short_hash["pull_head"][git_ref] = git_commit_hash[0:7]
            long_hash["pull_head"][git_ref] = git_commit_hash
            what = "pull_head"
            parsed = True
        elif parse_pull_merge is not None:
            git_commit_hash = parse_pull_merge.group(1)
            git_ref = int(parse_pull_merge.group(2))  # Pull Request number
            short_hash["pull_merge"][git_ref] = git_commit_hash[0:7]
            long_hash["pull_merge"][git_ref] = git_commit_hash
            what = "pull_merge"
            parsed = True

        # Some Pull Request hash values don't have timestamps
        if parsed is True and (what == "tag" or what == "branch_head"):
            ts = epoch_ts(git_commit_hash)
            if ts > 0:
                short_hash["hash_epoch_ts"][git_commit_hash[0:7]] = ts
                long_hash["hash_epoch_ts"][git_commit_hash] = ts

    return short_hash, long_hash

def increment_tag_version(value=None):
    """
    Accept a string value and modify existing version tag tuple according
    to the string value input. Return the modified tag tuple.
    """
    assert isinstance(value, str)
    assert value in set({"major", "minor", "patch"})
    versions = get_version_list()
    assert len(versions) > 0
    this_version = versions[-1]
    assert len(this_version) == 3
    assert isinstance(this_version, tuple)
    this_version = (
        int(this_version[0]),
        int(this_version[1]),
        int(this_version[2]),
    )

    new_version = None
    if value == "patch":
        new_version = (this_version[0], this_version[1], this_version[2] + 1)

    elif value == "minor":
        new_version = (this_version[0], this_version[1] + 1, 0)

    elif value == "major":
        new_version = (this_version[0] + 1, 0, 0)
    else:
        raise ValueError(
            "increment_tag_version('{0}') cannot parse verion='{0}'".format(value)
        )

    return new_version

def check_exists_tag_local(tag_value=None):
    """Check 'git tag' for an exact string match for tag_value."""
    assert isinstance(tag_value, str)
    loguru_logger.log(
        "DEBUG",
        "|"
        + "Checking whether version '{}' is defined in pyproject.toml".format(
            tag_value
        ),
    )
    stdout, stderr = run_cmd("git tag")
    for line in stdout.splitlines():
        if tag_value.strip() == line.strip():
            loguru_logger.log(
                "DEBUG", "|" + "Tag '{}' already exists.".format(tag_value)
            )
            return True
    loguru_logger.log("DEBUG", "|" + "'{}' is a new git tag".format(tag_value))
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
        loguru_logger.log("INFO", "|" + "Calling run_cmd(cmd='{}')".format(cmd))

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
        bufsize=1,
        # encoding parameter... https://stackoverflow.com/a/57970619/667301
        encoding="utf-8",
    )
    if debug > 1:
        loguru_logger.log("DEBUG", "|" + "Calling Popen().communicate()")

    if debug >= 1:
        loguru_logger.log("INFO", "|" + "run_cmd('{}')".format(cmd))

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


def pyproject_filepath():
    filepath = os.path.join(git_root_directory(), "pyproject.toml")
    return filepath


def get_version_list():
    """Return a list of tuples; one tuple per version number tag"""
    versions = []
    stdout, stderr = run_cmd("git tag")
    for version in stdout.splitlines():
        vv = re.search(r"^v*(\d+\.\d+\.\d+)", version)
        if vv is not None:
            tt = [int(ii) for ii in vv.group(1).split(".")]
            versions.append(tuple(tt))
    return sorted(versions)


def get_pyproject_version(args):
    """Read the version from pyproject.toml"""
    version = None
    filepath = pyproject_filepath()
    assert os.path.isfile(filepath)
    for line in open(filepath).read().splitlines():
        if "version" in line:
            rr = re.search(r"\s*version\s*=\s*(\S+)$", line.strip())
            if rr is not None:
                version = rr.group(1).strip().strip("'").strip('"')
                loguru_logger.log(
                    "DEBUG",
                    "|"
                    + "Found version '{0}' defined in {1}".format(version, filepath),
                )
                return version
        else:
            continue

    if version is None:
        raise ValueError("FATAL: Cannot find a version defined in pyproject.toml")
    else:
        return True

def get_branch_name(args):
    stdout, stderr = run_cmd("git branch", debug=args.debug)
    #'* develop\n  main\n'
    retval = None
    for line in stdout.splitlines():
        if '*' in line:
            return line.replace('*', '').strip()
    raise ValueError("Could not find local git branch name")


def bump_pyproject_version(args):
    """
    Bump the version up, as required; write the version tag into pyproject.toml.
    """
    if args.increment_version is None:
        tag = ".".join([str(ii) for ii in get_version_list[-1]])
    else:
        tag = ".".join(
            [str(ii) for ii in increment_tag_version(args.increment_version)]
        )

    filepath = os.path.join(git_root_directory(), "pyproject.toml")
    assert os.path.isfile(filepath)

    # https://stackoverflow.com/a/290494/667301
    for line in fileinput.input(filepath, inplace=True):
        if re.search(r"^version", line) is not None:
            print('{} = "{}"{}'.format("version", tag, os.linesep), end="")
        else:
            print(line.strip(os.linesep))
    return True


def git_checkout_branch(args):
    assert isinstance(args.branch, str)
    loguru_logger.log("DEBUG", "|" + "Checking out git branch: {}".format(args.branch))
    stdout, stderr = run_cmd("git checkout {}".format(args.branch))


def git_tag_commit_version():
    """
    Tag the latest git commit with the version listed in pyproject.toml
    """
    stdout, stderr = run_cmd(
        'git tag -a {0} -m "Tag with {0}"'.format(get_pyproject_version())
    )


def git_tag_and_push(args):
    version = get_pyproject_version()
    loguru_logger.log(
        "DEBUG", "|" + "Using tag '{}' for this git transaction".format(version)
    )

    stdout, stderr = run_cmd("git remote remove origin")
    stdout, stderr = run_cmd(
        'git remote add origin "git@github.com:{0}/{1}"'.format(args.user, args.project)
    )

    # TODO: build CHANGES.md management / edit tool... automate version change lists
    # TODO: support for push local tag to a remote 'git push --tags origin 1.6.42'
    # TODO: support for delete remote tags 'git push origin ":refs/tags/waat"'
    # TODO: support for finding remote tags on a specific git hash 'git ls-remote -t <remote> | grep <commit-hash>'

    version = get_pyproject_version()  # Get the version from pyproject.toml
    assert isinstance(version, str)

    if check_exists_tag_local(tag_value=version) is True:
        loguru_logger.log(
            "DEBUG",
            "|"
            + "The -t argument is rejected; the '{0}' tag already exists in this local git repo".format(
                version
            ),
        )

    else:
        # args.tag is a new tag value...
        if args.tag is True:
            # Create a local git tag at git HEAD
            git_tag_commit_version(args)

    assert args.branch == "main"
    git_checkout_branch(args)

    if args.combine != "":
        assert (
            args.combine != "main"
        ), "FATAL: we are currently on the main branch and cannot combine it with itself"
        assert args.message != "", "FATAL: A {0} message is required".format(
            args.message
        )
        stdout, stderr = run_cmd(
            "git {0} {1} -m'{2}'".format(args.method, args.combine, args.message)
        )

    if args.force is False and args.push is True and args.tag is False:
        # Do NOT force push
        loguru_logger.log(
            "SUCCESS", "|" + "git push (without tags) to the main branch at git origin."
        )
        stdout, stderr = run_cmd(
            "git push git@github.com:{0}/{1}.git".format(args.user, args.project)
        )
        stdout, stderr = run_cmd("git push origin +{0}".format(args.branch))

    elif args.force is False and args.push is True and args.tag is True:
        loguru_logger.log(
            "SUCCESS", "|" + "git push (with tags) to the main branch at git origin."
        )
        stdout, stderr = run_cmd("git push origin +{0}".format(args.branch))
        stdout, stderr = run_cmd("git push --tags origin {}".format(version))

    elif args.force is True and args.tag is True:
        # Force push and tag
        loguru_logger.log(
            "SUCCESS",
            "|" + "git push FORCED (with tags) to the main branch at git origin.",
        )
        stdout, stderr = run_cmd(
            "git push --force-with-lease --tags git@github.com:{0}/{1}.git".format(
                args.user, args.project
            )
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

def main(args):

    if args.status is True:
        stdout, stderr = run_cmd("git status", debug=args.debug)
        print(stdout)

    elif args.combine != "":
        original_branch_name = get_branch_name(args)
        assert original_branch_name != "main"

        loguru_logger.debug(original_branch_name)
        # This is used for 'git merge <branch_name>' situations...
        assert args.combine != "main", "FATAL merging main with {} is not supported".format(original_branch_name)

        # checkout the main branch...
        args.branch = "main"
        git_checkout_branch(args)

        if args.tag is True:
            tag_value = git_tag_commit_version()     # Read version from pyproject.toml...
            if check_exists_tag_local(tag_value=tag_value) is False:
                git_tag_commit_version() 
            else:
                raise ValueError("FATAL tag {} already exists".format(tag_value))

        assert get_branch_name(args) == "main"
        ## FIXME git merge command below does NOT merge anything...
        raise NotImplementedError("git merge functionality is broken... it cannot merge the develop branch into main")
        stdout, stderr = run_cmd("git merge {0} -m '{1}'".format(original_branch_name, args.message), debug=args.debug)
        stdout, stderr = run_cmd("git push origin main", debug=args.debug)

        if args.tag is True:
            stdout, stderr = run_cmd("git push origin main --tags", debug=args.debug)

        if original_branch_name != "main":
            args.branch = original_branch_name
            git_checkout_branch(args)


if __name__ == "__main__":
    args = parse_args()
    main(args)
    # Lots of work to do before calling git_tag_and_push()
    # git_tag_and_push(args)
