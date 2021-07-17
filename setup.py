#!/usr/bin/env python
## Ref https://docs.python.org/2/distutils/introduction.html
## Ref https://the-hitchhikers-guide-to-packaging.readthedocs.org/en/latest/
## Ref http://www.ibm.com/developerworks/library/os-pythonpackaging/

from setuptools import setup as _setup
from setuptools import find_packages
import json
import sys
import re
import os

from loguru import logger

logger.add(
    sys.stdout,
    colorize=True,
    diagnose = True,
    backtrace = True,
    level = "DEBUG",
    format="<green>{time}</green> <level>{message}</level>",
)

CURRENT_PATH = os.path.join(os.path.dirname(__file__))
sys.path.insert(1, CURRENT_PATH)


def read(fname):
    # Dynamically generate setup(long_description)
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


## Conditionally require the correct ipaddr package in Python2 vs Python3
# Ref Github issue #127 - sdist improvements
REQUIRES = ["colorama", "passlib", "dnspython"]
EXTRAS = {
    ":python_version<'3'": ["ipaddr>=2.1.11"],
}


def metadata_json_path():
    """Return the PATH to metadata.json as a python string"""
    base_path = os.path.dirname(os.path.abspath(__file__))
    for current_path, directories, files in os.walk(base_path):
        for filename in files:
            if filename == "metadata.json":
                return os.path.join(current_path, "metadata.json")
    raise OSError("metadata.json not found")


def get_metadata(attr_name):
    """Open metadata.json and return attr_name (as a python string)"""
    return json.loads(open(metadata_json_path()).read()).get(attr_name)

@logger.catch(level="CRITICAL")
def main(var=""):
    return var

## Setup ciscoconfparse
main()

_setup(
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
