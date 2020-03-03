#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('docs/history.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='bikram',
    version='2.1.0',
    description="Utilities to work with Bikram/Vikram Samwat dates.",
    long_description=readme + '\n\n' + history,
    author="keshaB Paudel",
    author_email='self@keshab.net',
    url='https://github.com/poudel/bikram',
    packages=[
        'bikram',
    ],
    package_dir={'bikram':
                 'bikram'},
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='bikram',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
