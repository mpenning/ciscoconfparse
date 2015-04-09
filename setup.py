#!/usr/bin/env python
## Ref https://docs.python.org/2/distutils/introduction.html
## Ref https://the-hitchhikers-guide-to-packaging.readthedocs.org/en/latest/
## Ref http://www.ibm.com/developerworks/library/os-pythonpackaging/

from setuptools import setup, find_packages
import sys
import os
CURRENT_PATH=os.path.join(os.path.dirname(__file__))
sys.path.insert(1,CURRENT_PATH)

## Using version_info/version.py as a workaround for
##   Github issue #24 (recursive import dependencies)
from version_info.version import __version__ as __ccpversion__

def read(fname):
    # Dynamically generate setup(long_description)
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


## Conditionally require the correct ipaddr package in Python2 vs Python3
if sys.version_info[0]<3:
    IPADDR = "ipaddr>=2.1.11"
else:
    IPADDR = "ipaddress"

setup(name='ciscoconfparse',
      version=__ccpversion__,
      description='Parse, Audit, Query, Build, and Modify Cisco IOS-style configurations',
      url='http://www.pennington.net/py/ciscoconfparse/',
      author='David Michael Pennington',
      author_email='mike /|at|\ pennington.net',
      license='GPLv3',
      platforms='any',
      keywords='Parse audit query modify Cisco IOS configuration',
      entry_points = "",
      long_description=read('README.rst'),
      include_package_data=True, # See MANIFEST.in for explicit rules
      packages=find_packages(),
      use_2to3=True,             # Reqd for Windows + Py3 - ref Github issue #32
      zip_safe=False,
      install_requires = [IPADDR],       # Package dependencies here
      setup_requires=["setuptools_hg"],  # setuptools_hg must be installed as a python module
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Plugins',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Information Technology',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Communications',
          'Topic :: Internet',
          'Topic :: System :: Networking',
          'Topic :: System :: Networking :: Monitoring',
          'Topic :: Software Development :: Libraries :: Python Modules',
          ],
     )
