# Atomic App Command Line Interface (CLI)

The Atomic App software allows for several actions to be applied to
specified applications. The four actions that exist today are briefly
described below.

## CLI Commands

`genanswers`
------------
Will download and combine artifacts from the target application in a
temporary directory and then take the generated sample answers.conf
file and populate it in the users working directory. The temporary 
directory is then cleaned up.

`init`
----------
Initialize a directory with an example Atomic App application using
the `centos/httpd` container image. This is a templated file structure including
Docker and Kubernetes artifact examples.

`index`
---------
Use an `index.yaml` file located within `~/.atomicapp/index.yaml` for outputting a
series of featured Nuleculized applications

```
ID                        VER      PROVIDERS  LOCATION                                             
postgresql-atomicapp      1.0.0    {D,O,K}    docker.io/projectatomic/postgresql-centos7-atomicapp 
flask_redis_nulecule      0.0.1    {D,K}      docker.io/projectatomic/flask-redis-centos7-atomicapp
redis-atomicapp           0.0.1    {D,O,K}    docker.io/projectatomic/redis-centos7-atomicapp      
...
```

`fetch`
-------
Will download and combine artifacts from the target application and any 
dependent applications including sample answers.conf file into a local 
directory for inspection and/or modification. This is the same for all providers.

`run`
-----
Will run an application.

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Run application containers on local machine. |
| Kubernetes    | Run requested application in Kubernetes target environment. |
| Openshift     | Run requested application in OpenShift target environment. |
| Marathon      | Run requested application in Marathon target environment. |

`stop`
------
Will stop an application. 

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Stop application containers on local machine. |
| Kubernetes    | Stop requested application in Kubernetes target environment. |
| Openshift     | Stop requested application in OpenShift target environment. |
| Marathon      | Stop requested application in Marathon target environment. |

## Providers

Providers may be specified using the `answers.conf` file or the `--provider <provider>` option. 
If a provider is not explicitly implied and only one provider exists within the Nulecule container, Atomic App will use said provider.
If neither are detected, Atomic App will use Kubernetes by default.

Sample `answers.conf` file specifying provider

```
[general]
provider = openshift
```

Using the `--provider <provider>` option will override the provider in the answerfile.

### Supported providers

* kubernetes (default)
* openshift
* docker

