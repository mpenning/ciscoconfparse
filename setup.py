#!/usr/bin/env python
import os

from setuptools import setup, find_packages
import sys
CURRENT_PATH=os.getcwd()+'/ciscoconfparse'
sys.path.insert(1,CURRENT_PATH)

def read(fname):
    # Dynamically generate setup(long_description)
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='ciscoconfparse',
      # TODO: Fix automagic version parsing
      #version=__import__("ciscoconfparse").__version__,
      version="1.1.4",
      description='Parse, Audit, Query, Build, and Modify Cisco IOS-style configurations',
      url='http://www.pennington.net/py/ciscoconfparse/',
      author='David Michael Pennington',
      author_email='mike /|at|\ pennington.net',
      license='GPL',
      platforms='any',
      keywords='Parse audit query modify Cisco IOS configuration',
      entry_points = "",
      long_description=read('README.rst'),
      include_package_data=True,
      packages=find_packages(),
      use_2to3=True,
      zip_safe=False,
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
