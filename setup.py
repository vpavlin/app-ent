#!/usr/bin/env python

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

setup(name='containerapp',
      version='0.1',
      description='A tool to install and run Nulecule apps',
      author='Vaclav Pavlin',
      author_email='vpavlin@redhat.com',
      url='https://github.com/vpavlin/atomicapp-run',
      license="MIT",
      entry_points={
          'console_scripts': ['containerapp=containerapp.cli.main:main'],
      },
      packages=find_packages(),
      install_requires=_install_requirements(),
)
