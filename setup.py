#!/usr/bin/env python
import os

from setuptools import setup, find_packages
import sys
sys.path.insert(0,os.getcwd()+'/ciscoconfparse')

def read(fname):
    # Dynamically generate setup(long_description)
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='ciscoconfparse',
      version=__import__("ciscoconfparse").__version__,
      url='http://github.com/mpenning/ciscoconfparse',
      author='David Michael Pennington',
      author_email='mike /|at|\ pennington.net',
      license='GPL',
      include_package_data=True,
      zip_safe=False,
      platforms='any',
      keywords='Parse audit query modify Cisco IOS configuration',
      description='Parse, Audit, Query, Build, and Modify Cisco IOS-style configurations',
      long_description=read('README.rst'),
      packages=find_packages('ciscoconfparse'),
      package_dir = {'': 'ciscoconfparse'},
      #namespace_packages=['ciscoconfparse'],
      #py_modules=['ciscoconfparse'],
      use_2to3=False,
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
