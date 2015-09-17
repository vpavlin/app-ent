# Docker Compose

### Overview

The Docker Compose provider: ``docker-compose``
will start a set of docker containers for a multi-tier application as
specified in a Docker Compose YAML file on the host the Atomic App is
deployed. Since, a docker compose YAML file will represent
the entire graph of applications in a Nulecule file, you don't need to run
docker compose on each application in the Nulecule graph. However, since
each provider for an application must point to an artifact file, you can
point to an empty ``artifacts/docker-compose/noop-compose.yaml`` artifact
file for applications you want to skip running docker compose on.

### Configuration

#### namespace

The psuedo namespace to use when naming docker containers. Docker does not properly support namespacing so this is done by naming containers in a predictable manner with the value of the namespace as part of the name.

The namespace can be changed in the [general] section of the answers.conf file. An example is below:

```
[general]
namespace: mynamespace
```

#### providerconfig
This communicates directly with the docker daemon on the host. It does not use the i``providerconfig`` option.


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

This command deploys the set of docker containers for a multi-tier application
as specified in the ``docker-compose`` artifact file. The deployment uses
the value of `namespace` option within `answers.conf` and deploys with
a naming convention. If a previous deployment with the same name is detected,
it will fail and warn the user.

```
atomicapp stop
```

This command undeploys all the containers for the multi-tier application
in Docker run by Docker ``compose`` during running atomicapp.

