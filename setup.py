#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='zops.requirements_directory',
    version='0.1.0',
    description="Handles Python requirements in a directory using pip-tools.",
    long_description="Handles Python requirements in a directory using pip-tools.",
    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',
    url='https://github.com/zerotk/zops.requirements_directory',
    packages=['zops', 'zops.requirements_directory'],
    namespace_packages=['zops'],
    entry_points="""
        [zops.plugins]
        req=zops.requirements_directory.cli:req
    """,
    include_package_data=True,
    install_requires=[
        'zerotk.zops',
        'pip-tools',
    ],
    license="MIT license",
    zip_safe=False,
    keywords='operations',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=[]
)
