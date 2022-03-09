from subprocess import getstatusoutput as gso

def find_version_from_pyproject():
    """Find the current version in pyproject.toml"""
    with open("pyproject.toml") as fh:
        for line in fh.read().splitlines():
            if "version" in line:
                version = line.strip().split()[-1]
    return version

def do_git_version_tag(version):
    gso("git remote remove origin")
    gso('git remote add origin "git@github.com:mpenning/ciscoconfparse"')
    gso('git tag -a {0} -m "Tag with {0}"'.format(version))
    gso('git push --force-with-lease --tags origin +main')
    gso('git push --force-with-lease --tags origin "{0}"'.format(version))


if __name__=="__main__":
    version = find_version_from_pyproject()
    do_git_version_tag(version)
