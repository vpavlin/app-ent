# Providers
This chapter describes how to use and configure the providers included with Atomic App. It gives you a short overview of all available providers and how to use them.


Not all Atomic Apps must support each provider: one Atomic App may only include deployment information for OpenShift3 while another does support OpenShift3 and Kubernetes.

## List of providers
Atomic App 0.1.3 includes three providers:

  * Docker

  * Kubernetes

  * OpenShift 3


All providers assume that you install and run the Atomic App on a host that is part of the backend cluster or runs docker directly. By now we do not support remote deployments.

## Choosing a provider
While deploying an Atomic App you can choose one of the providers by setting it in `answers.conf`:

```
[general]
provider: openshift
```

Providers may need additional configuration.

### Docker

**Features**

The Docker provider will simply start a Docker container on the host the Atomic App is deployed.


Atomic App will use the name within namespace and append it with `atomic` and a hash value. If --name is provided within the Docker artifacts file, this will be used but the user will be given a warning.

**Configuration values**

Table 1. Docker default configuration values

Keyword  | Required | Description                                           | Default value
---------|----------|-------------------------------------------------------|--------------
namespace|   no     |   namespace to use when deploying docker containers   | default\*

\*The naming convention used when deploying is: atomic\_APPNAME\_HASHVALUE

**Operations**

```
atomicapp run
```

This command deploys the app in Docker. The deployment uses the name provided within `answers.conf` and deploys with the naming convention `atomic_APPNAME_HASHVALUE`. If a previous deployment with the same name is detected, it will fail and warn the user.

```
atomicapp stop
```

This command undeploys the app in Docker. For the given namespace, the undeploy:

  1. Greps `docker ps` for the namespace

  2. Kills all Docker containers that match

If --name was provided in the Docker artifacts file, this command will not work.

### Kubernetes

**Features**

The Kubernetes Provider supports namespaces, this will deploy an application into a given namespace. All components of the applications will be created in that namespace. The `namespace` defined in the Kubernetes artifacts. If any are defined, they must match the namespace value in configuration.


The default value of `namespace` is `default` unless otherwise defined in the Kubernetes manifest.

**Configuration values**

Table 1. Kubernetes default configuration values

Keyword  | Required | Description                                 | Default value
---------|----------|---------------------------------------------|--------------
namespace|   no     |   namespace to use with each kubectl call   | default

**Operations**

```
atomicapp run
```

This command deploys the app in Kubernetes cluster in a specified namespace. For the given namespace, the deploy process creates objects (pods, replicas, services) in order as enlisted in Nulecule Kubernetes artifacts.

```
atomicapp stop
```
This command undeploys the app in Kubernetes cluster in specified namespace. For the given namespace, the undeploy process consist of:

  1. Scaling down all replicas to 0

  2. Deleting all objects (pods, replicas, services)

### Openshift3

**Features**

The OpenShift3 Provider will deploy and run an Atomic App on an OpenShift3 instance provided via an OpenShift3 configuration file. An OpenShift3 configuration file is written to a disk provided that you have logged in see [osc login announcement](http://lists.openshift.redhat.com/openshift-archives/users/2015-March/msg00014.html)


You need to provide a copy of `.config/openshift/.config` so that the provider may use this configuration to deploy and run the Atomic App.


As of 0.1.3 of Atomic App, OpenShift3 templates will only be processed by Atomic App during the run phase. The names of the parameters supplied by the OpenShift3 template file will be replaced by the parameters supplied to Atomic App.

**Configuration values**

Table 1. OpenShift3 default configuration values

Keyword         | Required | Description                                 | Default value
----------------|----------|---------------------------------------------|--------------
openshiftconfig |   no     |   path to OpenShift3 configuration file     | none

