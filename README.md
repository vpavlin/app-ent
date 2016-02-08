# Atomic App

Atomic App is a reference implementation of the [Nulecule Specification](http://www.projectatomic.io/docs/nulecule/). It can be used to bootstrap container applications and to install and run them. Atomic App is designed to be run in a container context. Examples using this tool may be found in the [Nulecule examples directory](https://github.com/projectatomic/nulecule/tree/master/examples).

## Getting Started

Atomic App is packaged as a container. End-users typically do not install the software from source. Instead use the atomicapp container as the `FROM` line in a Dockerfile and package your application on top. For example:

```
FROM projectatomic/atomicapp:0.4.1

MAINTAINER Your Name <you@example.com>

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
```

For more information see the [Atomic App getting started guide](http://www.projectatomic.io/docs/atomicapp/).

## Developers

See CONTRIBUTING.md for development.

## Providers

Providers represent various deployment targets. They can be added by placing a file called `provider_name.py` in `providers/`. This file needs to implement the interface explained in (providers/README.md). For a detailed description of all providers available see the [Provider description](docs/providers.md).

## Dependencies

Please see [REQUIREMENTS](https://github.com/projectatomic/atomicapp/blob/master/docs/requirements.md) for current Atomic App dependencies.

##Communication channels

* IRC: #nulecule (On Freenode)
* Mailing List: [container-tools@redhat.com](https://www.redhat.com/mailman/listinfo/container-tools)

# The Badges

[![Code Health](https://landscape.io/github/projectatomic/atomicapp/master/landscape.svg?style=flat)](https://landscape.io/github/projectatomic/atomicapp/master)
[![Build Status](https://travis-ci.org/projectatomic/atomicapp.svg?branch=master)](https://travis-ci.org/projectatomic/atomicapp)
[![Coverage Status](https://coveralls.io/repos/projectatomic/atomicapp/badge.svg?branch=master&service=github)](https://coveralls.io/github/projectatomic/atomicapp?branch=master)
[![Issue Stats](http://issuestats.com/github/projectatomic/atomicapp/badge/pr)](http://issuestats.com/github/projectatomic/atomicapp)
[![Issue Stats](http://issuestats.com/github/projectatomic/atomicapp/badge/issue)](http://issuestats.com/github/projectatomic/atomicapp)

# Copyright

Copyright (C) 2015 Red Hat Inc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

The GNU Lesser General Public License is provided within the file lgpl-3.0.txt.
