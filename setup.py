#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


setup(
    name='zops.requirements_directory',
    use_scm_version=True,

    author="Alexandre Andrade",
    author_email='kaniabi@gmail.com',

    url='https://github.com/zerotk/zops.requirements_directory',

    description="Handles Python requirements in a directory using pip-tools.",
    long_description="Handles Python requirements in a directory using pip-tools.",

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
    keywords='development environment, shell, operations',

    include_package_data=True,
    packages=['zops', 'zops.requirements_directory'],
    namespace_packages=['zops'],
    entry_points="""
        [zops.plugins]
        req=zops.requirements_directory.cli:req
    """,

    install_requires=[
        'zerotk.zops',
        'pip-tools',
    ],
    setup_requires=['setuptools_scm'],
    tests_require=[],

    license="MIT license",
)
