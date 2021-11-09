#!/usr/bin/env python
## Ref https://docs.python.org/2/distutils/introduction.html
## Ref https://the-hitchhikers-guide-to-packaging.readthedocs.org/en/latest/
## Ref http://www.ibm.com/developerworks/library/os-pythonpackaging/

from setuptools import setup as setuptools_setup
from setuptools import find_packages
import locale
import json
import sys
import re
import os

from loguru import logger

ENCODING = "utf-8"

r""" setup.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
     Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corp.
     Copyright (C) 2007-2011 David Michael Pennington

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""

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
ENCODING = locale.getpreferredencoding()

@logger.catch(level="WARNING")
def read(fname):
    # Dynamically generate setup(long_description)
    filepath = os.path.join(os.path.dirname(__file__), fname)
    return open(filepath, encoding=ENCODING).read()


## Conditionally require the correct ipaddr package in Python2 vs Python3
# Ref Github issue #127 - sdist improvements
REQUIRES = ["passlib", "dnspython", "loguru"]
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
    return json.loads(open(metadata_json_path(), encoding=ENCODING).read()).get(attr_name)


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
        python_requires='>=3.5',
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
