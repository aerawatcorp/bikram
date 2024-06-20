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
    version='2.1.3',
    description="Utilities to work with Bikram/Vikram Samwat dates.",
    long_description=readme + '\n\n' + history,
    authors=["keshaB Paudel", "aerawatcorp", "acpmasquerade"],
    author_email='aerawatcorp@gmail.com',
    url='https://github.com/aerawatcorp/bikram',
    packages=[
        'bikram',
    ],
    package_dir={'bikram':
                 'bikram'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='bikram bikram samwat vikram samwat nepali date',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
