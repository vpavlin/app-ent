# Kubernetes Provider

### Overview

Applications started using the Kubernetes provider will result in the
application being started inside of a kubernetes environment. This
typically means a pod/replication controller/service, etc.. will be
created and started.

Unlike Docker, kubernetes supports namespaces. Namespaces allow you to
deploy an application into a given namespace and allow for separation
from other components started in different namespaces. For an Atomic
App deployed in kubernetes, all components of the application will be
deployed into the namespace from the configuration in answers.conf.


### Configuration

#### namespace

As mentioned above, kubernetes supports namespaces. The default
namespace for an application is set to `default` unless otherwise
specified in the answers.conf. It can be changed in the `[general]`
section of the answers.conf file. An example is below:

```
[general]
namespace: mynamespace
```

#### provider-config

For Kubernetes the configuration file as specified by `provider-config`
is optional. Hosts that have kubernetes set up and running on them
may not need a `provider-config` to be specified because kubernetes
services are listening on default ports/addresses. However, if
kubernetes was set up to listen on different ports, or you wish to
connect to a remote kubernetes environment, then you will need to
specify a location for a provider config file.

One example of specifying a `provider-config` is below:

```
[general]
provider: kubernetes
provider-config: /home/foo/.kube/config
```

#### Configuration Value Defaults

Table 1. Kubernetes default configuration values

Keyword  | Required | Description                                             | Default value
---------|----------|---------------------------------------------------------|--------------
namespace|   no     | namespace to use with each kubectl call                 | default
provider-config| no  | config file that specifies how to connect to kubernetes | none


### Operations

```
atomicapp run
```

This command deploys the app in Kubernetes cluster in a specified namespace.
For the given namespace, the deploy process creates objects (pods, replicas,
services) in order as enlisted in Nulecule Kubernetes artifacts.

```
atomicapp stop
```
This command undeploys the app in the Kubernetes cluster in a specified namespace.
For the given namespace, the undeploy process consist of:

  1. Scaling down all replicas to 0

  2. Deleting all objects (pods, replicas, services)
