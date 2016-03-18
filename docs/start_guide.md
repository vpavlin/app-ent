# Getting Started

This is a thorough start guide to show you each detail of an Atomic App. Teaching you the basic commands as well as the generation of your first Atomic App.

## Basic commands

The __four__ basic commands of atomicapp are:

__atomicapp fetch__: Retrieving a packaged container and exporting it to a directory.

ex. `atomicapp fetch projectatomic/helloapache`

__atomicapp run__: Running a packaged container on a specified provider. Unless a directory is specified, `run` will also perform `fetch`.

ex. `atomicapp run projectatomic/helloapache --provider=kubernetes`

__atomicapp stop__: Stopping a deployed Nulecule on a specified provider. Whether you're using Kubernetes, OpenShift or Docker, Atomic App will stop the containers.

ex. `atomicapp stop ./myappdir --provider=kubernetes`

__atomicapp genanswers__: By examing the `Nulecule` file. Atomic App will generate an `answers.conf` file to be used for non-interactive deployment.

ex. `atomicapp genanswers ./myappdir`

For more detailed information as well as a list of all parameters, use `atomicapp --help` on the command line. Alternatively, you can read our [CLI doc](docs/cli.md).

## Atomic App on Project Atomic hosts

If you are on a [Project Atomic host](https://projectatomic.io/download) you can interact with `atomicapp` via the `atomic` cli command.

Some commands for `atomicapp` on an atomic host are a bit different.

However. Regardless of the `atomic run` command, a `--mode` can be passed to change the functionality of the command. 

| Atomic App | Atomic CLI
|-----------|--------|
| `atomicapp fetch projectatomic/helloapache` | `atomic run projectatomic/helloapache --mode fetch`
| `atomicapp run projectatomic/helloapache` | `atomic run projectatomic/helloapache`
| `atomicapp stop ./myappdir` | `atomic stop projectatomic/helloapache ./myappdir`
| `atomicapp genanswers ./myappdir` | `atomic run projectatomic/helloapache ./myappdir --mode genanswers`

## Building your first Atomic App

A typical Atomic App or "Nulecule" container consists of the following files:
```sh
~/helloapache
▶ tree
.
├── answers.conf.sample
├── artifacts
│   ├── docker
│   │   └── hello-apache-pod_run
│   ├── kubernetes
│   │   └── hello-apache-pod.json
│   └── marathon
│       └── helloapache.json
├── Dockerfile
├── Nulecule
└── README.md
```

We will go through each file and folder as we build our first Atomic App container.

For this example, we will be using the [helloapache](https://github.com/projectatomic/nulecule-library/tree/master/helloapache) example from the [nulecule-library](https://github.com/projectatomic/nulecule-library) repo.

In order to follow along, fetch the container and `cd` into the directory:
```sh
atomicapp fetch --destination localdir projectatomic/helloapache
cd localdir
```

### ./localdir/Dockerfile
Atomic App itself is packaged as a container. End-users typically do not install the software from source, instead using the `atomicapp` container as the `FROM` line in a Dockerfile and packaging your application on top. For example:


```Dockerfile
FROM projectatomic/atomicapp

MAINTAINER Your Name <you@example.com>

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
```

Within `helloapache` we specify a bit more within our labels:
```Dockerfile
FROM projectatomic/atomicapp:0.4.2

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

LABEL io.projectatomic.nulecule.providers="kubernetes,docker,marathon" \
      io.projectatomic.nulecule.specversion="0.0.2"

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
```

__Optionally__, you may indicate what providers you specifically support via the Docker LABEL command.

__NOTE:__ The Dockerfile you supply here is for building a Nuleculized container image (often called an 'Atomic App'). It is not the Dockerfile you use to build your upstream Docker image. The actual `atomicapp` code should already be built at this time and imported in the `FROM projectatomic/atomicapp` line.

### ./localdir/Nulecule

This is the `Nulecule` file for Atomic App. The `Nulecule` file is composed of graph and metadata in order to link one or more containers for your application.
```yaml
---
specversion: 0.0.2
id: helloapache-app

metadata:
  name: Hello Apache App
  appversion: 0.0.1
  description: Atomic app for deploying a really basic Apache HTTP server

graph:
  - name: helloapache-app

    params:
      - name: image
        description: The webserver image
        default: centos/httpd
      - name: hostport
        description: The host TCP port as the external endpoint
        default: 80

    artifacts:
      docker:
        - file://artifacts/docker/hello-apache-pod_run
      kubernetes:
        - file://artifacts/kubernetes/hello-apache-pod.json
      marathon:
        - file://artifacts/marathon/helloapache.json
```

##### Spec and id information 
```yaml
---
specversion: 0.0.2
id: helloapache-app
```

Here we indicate the specversion of our Atomic App (similar to a `v1` or `v2` of an API) as well as our ID.

##### Metadata
```yaml
metadata:
  name: Hello Apache App
  appversion: 0.0.1
  description: Atomic app for deploying a really basic Apache HTTP server
```

__Optionally__, a good metadata section will indiciate to a user of your app what it does as well as what version it's on.

##### Graph

```yaml
graph:
  - name: helloapache-app

    params:
      - name: image
        description: The webserver image
        default: centos/httpd
      - name: hostport
        description: The host TCP port as the external endpoint
        default: 80

    artifacts:
      docker:
        - file://artifacts/docker/hello-apache-pod_run
      kubernetes:
        - file://artifacts/kubernetes/hello-apache-pod.json
      marathon:
        - file://artifacts/marathon/helloapache.json
```

__Graph__ is the most important section. In here we will indicate all the default parameters as well as all associated artifacts.

```yaml
params:
  - name: image
    description: The webserver image
    default: centos/httpd
```
There will likely be many parameters that need to be exposed at deployment. It's best to provide defaults whenever possible. Variable templating is used within artifact files. For example: `$image` within `artifacts/kubernetes/hello-apache-pod.json` becomes `centos/httpd`.

**NOTE:** Not providing a default variable will require Atomic App to ask the user. Alternatively, an `answers.conf` file can be provided.

```yaml
artifacts:
  docker:
    - file://artifacts/docker/hello-apache-pod_run
  kubernetes:
    - file://artifacts/kubernetes/hello-apache-pod.json
  marathon:
    - file://artifacts/marathon/helloapache.json
```
In order to use a particular provider, name as well as a file location required. Each file is a variable-subtituted template of how your Atomic App container is ran. We go more into detail below.

```yaml
kubernetes:
  - file://artifacts/kubernetes/hello-apache-pod.json
  - file://artifacts/kubernetes/hello-apache-service.json
```
Multiple files may also be specified. For example, specifying a pod, service and replication controller for the `kubernetes` provider.

### ./localdir/artifacts/docker/hello-apache-pod_run
```sh
docker run -d -p $hostport:80 $image
```
Each artifact uses variable replacement values. For our Docker provider, we substitute the port number with `$hostport` as indicated by our graph in our `Nulecule` file. The same as our `$image` variable.

### ./localdir/artifacts/kubernetes/hello-apache-pod.json
```json
"image": "$image",
"name": "helloapache",
"ports": [
    {
        "containerPort": 80,
        "hostPort": $hostport,
        "protocol": "TCP"
    }
```

Similarly, the kubernetes provider uses both `$image` and `$hostport` variables for pod deployment.

### ./localdir/answers.conf.sample

`answers.conf.sample` is an answers file generated while fetching. It is a generated ini file that provides parameter answers for non-interactive deployments.

```ini
[helloapache-app]
image = centos/httpd
hostport = 80

[general]
namespace = default
provider = kubernetes
```

Default values such as the provider as well as the namespace can be provided.

In order to use an answers file, simply specify the location of the file when deploying:
```sh
cp answers.conf.sample answers.conf
sudo atomicapp run -a answers.conf .
```

### Conclusion

Now you know how to build your very own first app! After you have created the necessary files go ahead and build/run it!

```sh
docker build -t myapp .
sudo atomicapp run myapp
```

Atomic App is portable and hence you can also deploy regardless of the host:
```sh
# Host 1
docker build -t myrepo/myapp .
docker push myrepo/myapp

# Host 2
docker pull myrepo/myapp
sudo atomicapp run myrepo/myapp
```

Although we have yet to cover every `atomicapp` command. Feel free to use `atomicapp [run/fetch/stop] --help` for a list of all options.

For an extended guide on the `Nulecule` file, read our [extended Nulecule doc](nulecule.md).
