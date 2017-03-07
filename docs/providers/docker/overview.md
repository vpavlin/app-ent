# Docker Provider

### Overview

Applications started using the Docker provider will simply result
in Docker containers being started on the host where the Atomic App
commands were executed.

Atomic App will generate a name for the containers based on the
namespace within the answers file and the name of the image the
containers are based on. If `--name` is provided with the docker
artifacts file, that will be used instead, but a warning will be
given.


### Configuration

#### namespace

The psuedo namespace to use when naming docker containers. Docker
does not properly support namespacing so this is done by naming
containers in a predictable manner with the value of the namespace as
part of the name.

The namespace can be changed in the `[general]` section of the
answers.conf file. An example is below:

```
[general]
namespace: mynamespace
```

#### provider-config
This communicates directly with the docker daemon on the host. It does
not use the `provider-config` option.

#### Configuration Value Defaults

Table 1. Docker default configuration values

Keyword  | Required | Description                                           | Default value
---------|----------|-------------------------------------------------------|--------------
namespace|   no     |   namespace to use when deploying docker containers   | default\*

\*The naming convention used when deploying is: `NAMESPACE_IMAGENAME_HASHVALUE`


### Operations

```
atomicapp run
```

This command deploys the application in Docker containers. The deployment uses 
the value of `namespace` option within `answers.conf` and deploys with
a naming convention. If a previous deployment with the same name is detected, 
it will fail and warn the user.

```
atomicapp stop
```

This command undeploys the app in Docker by stopping any containers
that were starting during the run.
