#!/usr/bin/env python
## Ref https://docs.python.org/2/distutils/introduction.html
## Ref https://the-hitchhikers-guide-to-packaging.readthedocs.org/en/latest/
## Ref http://www.ibm.com/developerworks/library/os-pythonpackaging/

from setuptools import setup as setuptools_setup
from setuptools import find_packages
import json
import sys
import re
import os

from loguru import logger

ENCODING = "latin-1"
ENCODING = "utf-8"

def log_format_string(record):
    """A loguru Helper method to format log strings"""
    assert isinstance(record, dict)
    keyname = "extra[classname]" if "classname" in record.get("extra") else "name"
    return (
            "<green>{time:YYYY-MM-DD_HH:mm:ss.SSS}</green> | <lvl>{level: <8}</lvl> | <c>%s:{function}:{line}</c> - <level>{message}</level>" % keyname
    )

def log_retention(files, max_log_size=20*1024**3):
    """Specify logfile retention policy, per file"""
    stats = [(_file, os.stat(_file)) for _file in files]
    stats.sort(key=lambda s: -s[1].st_mtime)  # Sort files from newest to oldest
    while sum(s[1].st_size for s in stats) > max_log_size:
        _file, _ = stats.pop()
        os.remove(_file)

logger.remove()  # Disable intrusive loguru defaults... ref
#     https://github.com/Delgan/loguru/issues/208
logger.add(
    sink=sys.stderr,
    colorize=True,
    diagnose=True,
    backtrace=True,
    enqueue=True,
    serialize=False,
    catch=True,
    level="DEBUG",
    # compression, encoding, and retention throw errors in logger.add()
    #compression="gzip",
    #encoding="utf-8",
    #retention="3 months",  # also see log_retention()
    # log_format_string(record)
    format=log_format_string,
)

CURRENT_PATH = os.path.join(os.path.dirname(__file__))
sys.path.insert(1, CURRENT_PATH)

@logger.catch(level="WARNING")
def read(fname):
    # Dynamically generate setup(long_description)
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


## Conditionally require the correct ipaddr package in Python2 vs Python3
# Ref Github issue #127 - sdist improvements
REQUIRES = ["colorama", "passlib", "dnspython", "loguru"]
EXTRAS = {
    ":python_version<'3'": ["ipaddr>=2.1.11"],
}


@logger.catch(level="WARNING")
def metadata_json_path():
    """Return the full filepath to metadata.json as a python string"""
    config_filename = "metadata.json"
    base_path = os.path.dirname(os.path.abspath(__file__))

    assert os.path.isdir(base_path) is True
    for current_path, directories, files in os.walk(base_path):
        for filename in files:
            if filename == config_filename:
                return os.path.join(current_path, config_filename)
    raise OSError("The file named {} was not found" % config_filename)


@logger.catch(level="WARNING")
def get_metadata(attr_name):
    """Open metadata.json and return attr_name (as a python string)"""
    return json.loads(open(metadata_json_path()).read()).get(attr_name)


@logger.catch(level="WARNING")
def setup_packages():
    setuptools_setup(
        name=get_metadata("name"),
        version=get_metadata("version"),
        description=get_metadata("description"),
        url=get_metadata("url"),
        author=get_metadata("author"),
        author_email=get_metadata("author_email"),
        license=get_metadata("license"),
        platforms=[get_metadata("platforms")],
        keywords=[get_metadata("keywords")],
        entry_points="",
        long_description=read("README.rst"),
        include_package_data=True,  # See MANIFEST.in for explicit rules
        packages=find_packages(),
        use_2to3=True,  # Reqd for Windows + Py3 - ref Github issue #32
        zip_safe=False,
        install_requires=REQUIRES,
        extras_require=EXTRAS,  # Conditional dependencies Github isssue #127
        # setup_requires=["setuptools_hg"],  # setuptools_hg must be installed as a python module
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Plugins",
            "Intended Audience :: Developers",
            "Intended Audience :: System Administrators",
            "Intended Audience :: Information Technology",
            "Intended Audience :: Telecommunications Industry",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python",
            "Topic :: Communications",
            "Topic :: Internet",
            "Topic :: System :: Networking",
            "Topic :: System :: Networking :: Monitoring",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )


if __name__ == "__main__":
    setup_packages()
