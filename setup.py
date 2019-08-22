# -*- coding: utf-8 -*-
"""
kingdomlib
~~~~~~~~~~
"""
from __future__ import with_statement

import os

from setuptools import setup
from setuptools.command.test import test

__dir__ = os.path.dirname(__file__)
about = {}
with open(os.path.join(__dir__, 'kingdomlib', '__about__.py')) as f:
    exec(f.read(), about)


def requirements(filename):
    """Reads requirements from a file."""
    with open(filename) as f:
        return [x.strip() for x in f.readlines() if x.strip()]


def run_tests(self):
    raise SystemExit(__import__('pytest').main(['-v']))


test.run_tests = run_tests

setup(
    name='kingdomlib',
    version=about['__version__'],
    license=about['__license__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    description=about['__description__'],
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    packages=['kingdomlib'],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Programming Language :: Python :: 3.7',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Programming Language :: Python :: Implementation :: Jython',
                 'Programming Language :: Python :: Implementation :: PyPy',
                 'Topic :: Games/Entertainment',
                 'Topic :: Scientific/Engineering :: Mathematics'],
    install_requires=requirements('requirements.txt'),
    tests_require=requirements('test/requirements.txt'),
    test_suite='...',
)
