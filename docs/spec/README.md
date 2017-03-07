# Composite Container-based Application Specification

`\ˈnü-li-ˌkyül\` (n.) a made-up word meaning ["the mother of all atomic particles"](http://simpsons.wikia.com/wiki/Made-up_words).

**Your installer for container-based applications.** Replace your shell script and deployment instructions with some metadata.

**Change runtime parameters for different environments.** No need to edit files before deployment. Users can choose interactive or unattended deployment. Guide web interface users with parameter metadata to validate user input and provide descriptive help.

**Bridge between Enterprise IT and PaaS** With pluggable orchestration providers you can package your application to run on OpenShift, Kubernetes, Docker Compose, Helios, Panamax, Docker Machine, etc. and allow the user to choose the target when deployed.

**Compose applications from a catalog.** No need to re-package common services. Create composite applications by referencing other Nulecule-compliant apps. For example, adding a well-designed, orchestrated database is simply a reference to another container image.

## Problem Statement
Currently there is no standard way of defining a multi-container application's configuration without distributing instructions and files to the end-user. Additionally, these files must be managed and distributed via different systems than the containers themselves.

Containers in the OCI (Open Container Initiative) format derived from Docker offers a new approach for application packaging. OCI enables application-centric aggregate packaging, optimized for deployment into containers. However most applications will consist of multiple containers, which surfaces two issues: the relationships between containers need to be expressed in order to manage dependencies and orchestrate the deployment (e.g. set up network connections) with consideration of environmental factors, and this application-level meta-data needs to be distributed. OCI itself, however, stops at the individual container. Orchestration tools such as Kubernetes offer a generic description model for multi-container applications, however they do not define a transport model, nor a standard way to parameterize a generic template. The mindset of most, if not all, current container orchestration systems is to treat the aggregate, multi-container application as state of the cluster rather than an entity in it's own right and therefore they regress beyond the portability that OCI introduced. This means that it's very easy to put a individual service into a Docker-style Registry, however there is no way to represent a full application at the distribution level - I can create a single MariaDB container, but not a MariaDB/Galera cluster or even a full application such as [Kolab](https://kolab.org/). So what is missing? A standard way to describe and package a multi-container application.

## What is Nulecule?

Nulecule defines a pattern and model for packaging complex multi-container applications and services, referencing all their dependencies, including orchestration metadata in a container image for building, deploying, monitoring, and active management.

The Nulecule specification enables complex applications to be defined, packaged and distributed using standard container technologies. The resulting container includes dependencies, supports multiple orchestration providers, and has the ability to specify resource requirements. The Nulecule specification also supports the aggregation of multiple composite applications. The Nulecule specification is container and orchestration agnostic, enabling the use of any container and orchestration technology.

**[Glossary of terms](GLOSSARY.md)**

## Nulecule Specification Highlights

* Application description and context maintained in a single container through extensible metadata
* Composable definition of complex applications through inheritance and composition of containers into a single, standards-based, portable description.
* Simplified dependency management for the most complex applications through a directed graph to reflect relationships.
* Container and orchestration engine agnostic, enabling the use of any container technology and/or orchestration technology

Detailed explanation on the **Nulecule** file-format is explained at [NULECULE_FILE.md](NULECULE_FILE.md).

## “The Big Picture”

![Alt Nulecule specification high-level story.](/docs//images/logo.png "Nulecule specification high-level story")

## Deployment User Experience

The Nulecule specification has been implemented in the [Atomic App reference implementation](https://github.com/projectatomic/atomicapp).  Atomic App currently supports docker containers and kubernetes and docker orchestration providers.  The [atomic command](https://github.com/projectatomic/atomic) is used to run the container that contains the Nulecule specification and the Atomic App implementation.

This example is a single container application based on the centos/httpd image, but you can use your own.

You may wish to run the Nulecule from an empty directory as it will copy the Nulecule files to the working directory for inspection every time it is run.

### Option 1: Non-interactive defaults

Run the image. It will automatically use kubernetes as the orchestration provider.  This will become interactive and prompt for defaults if the Nulecule file doesn't provide defaults for all of the parameters.

```
[sudo] atomic run projectatomic/helloapache
```

### Option 2: Unattended

1. Create the file `answers.conf` with these contents:

    This sets up the values for the two configurable parameters (image and hostport) and indicates that kubernetes should be the orchestration provider.

        [general]
        provider = kubernetes

        [helloapache-app]
        image = centos/httpd # optional: choose a different image
        hostport = 80        # optional: choose a different port to expose
1. Run the application from the current working directory

        $ [sudo] atomic run projectatomic/helloapache
        ...
        helloapache


1. As an additional experiment, remove the kubernetes pod and change the provider to 'docker' and re-run the application to see it get deployed on native docker.

### Option 3: Install and Run

You may want to download the application, review the configuration and parameters as specified in the Nulecule file, and edit the answerfile before running the application.

1. Download the application files using `atomic install`

        [sudo] atomic install projectatomic/helloapache

1. Rename `answers.conf.sample`

        mv answers.conf.sample answers.conf

1. Edit `answers.conf`, review files if desired and then run

        $ [sudo] atomic run projectatomic/helloapache
        ...
        helloapache

## Test
Any of these approaches should create a kubernetes pod or a running docker container.

With a kubernetes pod, once its state is "Running" curl the minion it's running on.

```
$ kubectl get pod helloapache
POD                IP                  CONTAINER(S)       IMAGE(S)           HOST                LABELS              STATUS
helloapache        172.17.0.8          helloapache        centos/httpd       10.3.9.216/         name=helloapache   Running
$ curl 10.3.9.216
<bunches_of_html_goodness>
```

If you test the docker provider, once the container is running, curl the port on your localhost.

```
$ curl localhost
<bunches_of_html_goodness>
```

Additional examples that conform to the Nulecule spec can be found at [github.com/projectatomic/nulecule-library](https://github.com/projectatomic/nulecule-library).

## Developer User Experience

See the [Getting Started with Nulecule guide](GETTING_STARTED.md).

## Implementations

This is only a specification. Implementations may be written in any language. See [implementation guide](IMPLEMENTATION_GUIDE.md)

**Reference implementation** https://github.com/projectatomic/atomicapp

## Examples / Library

For a library of examples conforming to the current reference implementation [atomicapp](https://github.com/projectatomic/atomicapp) please visit [github.com/projectatomic/nulecule-library](https://github.com/projectatomic/nulecule-library)
