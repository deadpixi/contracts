#!/usr/bin/env python

import sys

if sys.version_info[:2] < (3, 5):
    sys.stderr.write(
        'This version of dpcontracts requires Python 3.5 - either upgrade '
        'to a newer version of pip that handles this automatically, or '
        'explicitly "pip install dpcontracts<0.6".'
    )
    sys.exit(1)

from setuptools import setup
import dpcontracts

setup(name="dpcontracts",
      version="0.6.0",
      author="Rob King",
      author_email="jking@deadpixi.com",
      url="https://github.com/deadpixi/contracts",
      description="A simple implementation of contracts for Python.",
      py_modules=['dpcontracts'],
      python_requires='>=3.5',
      long_description=dpcontracts.__doc__,
      license="https://www.gnu.org/licenses/lgpl.txt",
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 3",
                   "Topic :: Software Development :: Libraries"])
