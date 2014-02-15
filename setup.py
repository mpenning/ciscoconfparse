#!/usr/bin/env python
import os

from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='ciscoconfparse',
      version='0.9.17',
      description='Parse, Query, Build, and Modify Cisco IOS-style configurations',
      url='http://www.pennington.net/py/ciscoconfparse/',
      author='David Michael Pennington',
      author_email='mike /|at|\ pennington.net',
      license='GPL',
      platforms='any',
      keywords='Parse query Cisco IOS configuration',
      entry_points = "",
      long_description=read('README.rst'),
      include_package_data=True,
      packages = find_packages(),
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
