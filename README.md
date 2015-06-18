# Atomicapp

Atomicapp is a reference implementation of the [Nulecule Specification](https://github.com/projectatomic/nulecule). It can be used to bootstrap container applications and to install and run them. Atomicapp is designed to be run in a container context. Examples using this tool may be found in the [Nulecule examples directory](https://github.com/projectatomic/nulecule/tree/master/examples).

## Getting Started

Atomicapp is packaged as a container. End-users typically do not install the software from source. Instead use the atomicapp container as the `FROM` line in a Dockerfile and package your application on top. For example:

```
FROM projectatomic/atomicapp:0.1.1

MAINTAINER Your Name <you@example.com>

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
```

For more information see the [Nulecule getting started guide](https://github.com/projectatomic/nulecule/blob/master/docs/getting-started.md).

## Developers

First of all, clone the github repository: `git clone https://github.com/projectatomic/atomicapp`.

### Install this project
Simply run

```
pip install .
```

If you want to do some changes to the code, I suggest to do:

```
cd atomicapp
export PYTHONPATH=`pwd`:$PYTHONPATH
alias atomicapp="`pwd`/atomicapp/cli/main.py"
```

### Build
```
atomicapp [--dry-run] build [TAG]
```

Calls Docker build to package up the application and tags the resulting image.

### Install and Run
```
atomicapp [--dry-run] [-a answers.conf] install|run [--recursive] [--update] [--destination DST_PATH] APP|PATH
```

Pulls the application and it's dependencies. If the last argument is
existing path, it looks for `Nulecule` file there instead of pulling anything.

* `--recursive yes|no` Pull whole dependency tree
* `--update` Overwrite any existing files
* `--destination DST_PATH` Unpack the application into given directory instead of current directory
* `APP` Name of the image containing the application (f.e. `vpavlin/wp-app`)
* `PATH` Path to a directory with installed (i.e. result of `atomicapp install ...`) app

Action `run` performs `install` prior it's own tasks are executed if `APP` is given. When `run` is selected, providers' code is invoked and containers are deployed.

## Providers

Providers represent various deployment targets. They can be added by placing a file called `provider_name.py` in `providers/`. This file needs to implement the interface explained in (providers/README.md). For a detailed description of all providers available see the [Provider description](Providers.asciidoc).

## Dependencies

As of Version 0.1.1 Atomicapp uses [Python 2.7.5](https://docs.python.org/2/) and [Anymarkup](https://github.com/bkabrda/anymarkup).

##Communication channels

* IRC: #nulecule (On Freenode)
* Mailing List: [container-tools@redhat.com](https://www.redhat.com/mailman/listinfo/container-tools)

# The Badges

[![Code Health](https://landscape.io/github/projectatomic/atomicapp/master/landscape.svg?style=flat)](https://landscape.io/github/projectatomic/atomicapp/master)
[![Build Status](https://travis-ci.org/projectatomic/atomicapp.svg?branch=master)](https://travis-ci.org/projectatomic/atomicapp)

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
