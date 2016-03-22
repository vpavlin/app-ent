#!/usr/bin/env python

"""
 Copyright 2014-2016 Red Hat, Inc.

 This file is part of Atomic App.

 Atomic App is free software: you can redistribute it and/or modify
 it under the terms of the GNU Lesser General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Atomic App is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public License
 along with Atomic App. If not, see <http://www.gnu.org/licenses/>.
"""

import re

from setuptools import setup, find_packages


def _get_requirements(path):
    try:
        with open(path) as f:
            packages = f.read().splitlines()
    except (IOError, OSError) as ex:
        raise RuntimeError("Can't open file with requirements: %s", repr(ex))
    packages = (p.strip() for p in packages if not re.match("^\s*#", p))
    packages = list(filter(None, packages))
    return packages


def _install_requirements():
    requirements = _get_requirements('requirements.txt')
    return requirements

setup(
    name='atomicapp',
    version='0.4.3',
    description='A tool to install and run Nulecule apps',
    author='Red Hat, Inc.',
    author_email='container-tools@redhat.com',
    url='https://github.com/projectatomic/atomicapp',
    license="LGPL3",
    entry_points={
        'console_scripts': ['atomicapp=atomicapp.cli.main:main'],
    },
    packages=find_packages(),
    package_data={'atomicapp': ['providers/external/kubernetes/*.yaml']},
    include_package_data=True,
    install_requires=_install_requirements()
)
