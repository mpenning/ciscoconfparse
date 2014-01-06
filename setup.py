#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='ciscoconfparse',
      version='0.9.6',
      description='Parse through Cisco IOS-style configurations and retrieve portions of the config using a variety of query methods',
      author='David Michael Pennington',
      author_email='mike /|at|\ pennington.net',
      license='GPL',
      keywords='Parse query Cisco IOS configuration',
      url='http://www.pennington.net/py/ciscoconfparse/',
      entry_points = "",
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
