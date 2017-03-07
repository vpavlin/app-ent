# Nulecule file

Atomic App implements version `0.0.2` of the [Nulecule specification](https://github.com/projectatomic/nulecule/tree/master/spec).

A `Nulecule` file format can either be `json` or `yaml`.

### Data types 

Common Name | `type`    | `format`    | Comments
----------- | --------- | ----------- | --------------
integer     | `integer` | `int32`     | signed 64 bits
float       | `number`  | `float`     |
string      | `string`  |             |
byte        | `string`  | `byte`      |
boolean     | `boolean` |             |
date        | `string`  | `date`      | As defined by `full-date` - [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14)
dateTime    | `string`  | `date-time` | As defined by `date-time` - [RFC3339](http://xml2rfc.ietf.org/public/rfc/html/rfc3339.html#anchor14)
password    | `string`  | `password`  | Used to hint UIs the input needs to be obscured.
URL         | `URL`     | `URL`       | As defined by `URL` - [RFC3986 Section 1.1.3](https://tools.ietf.org/html/rfc3986#section-1.1.3)

### Nulecule file schema

#### Container Application Object
This is the root object for the specification.

Field Name  | Type                | Description
----------  | :-----------------: | ------------
id          | `string`            | **Required.** The machine readable id of the Container Application.
specversion | `string`            | **Required.** The semantic version string of the Container Application Specification used to describe the app. The value MUST be `"0.0.2"` (current version of the spec).
metadata    | `Metadata Object`   | **Optional** An object holding optional metadata related for the Container Application, this may include license information or human readable information.
graph       | `Graph Object`      | **Required.** A list of depending containerapps. Strings may either match a local sub directory or another containerapp-spec compliant containerapp image that can be pulled via docker.
requirements|`Requirements Object`| **Optional.** A list of requirements of this containerapp.


#### Metadata Object

Metadata for the Container Application.

##### Fields

Field Name     | Type            | Description
---------------|:---------------:| ------------
name           | `string`        | **Optional.** A human readable name of the containerapp.
appversion     | `string`        | **Optional.** The semantic version string of the Container Application.
description    | `string`        | **Optional.** A human readable description of the Container Application. This may contain information for the deployer of the containerapp.
license        | `License Object`| **Optional.** The license information for the containerapp.
arbitrary_data | `string`        | **Optional.** Arbitrary `key: value` pair(s) of metadata. May contain nested objects.

##### Metadata Object Example

```yaml
metadata:
  name: myapp
  appversion: 1.0.0
  description: description of myapp
  foo: bar
  othermetadata:
    foo: bar
    files: file://path/to/local/file
...
```

#### License Object

License information for the Container Application.

##### Fields

Field Name | Type     | Description
-----------|:--------:|---
name       | `string` | **Required.** The human readable license name used for the Container Application, no format imposed.
url        | `string` | **Optional.** A URL to the license used for the API. MUST be in the format of a URL.

##### License Object Example

```yaml
license:
  - name: Apache 2.0
    url: http://www.apache.org/licenses/LICENSE-2.0.html
```

#### Graph Object

The graph is a list of items (containerapps) the Container Application depends on.

##### Fields

Field Name| Type              | Description
----------|:-----------------:|-------------
name      | `string`          | **Required.** The name of the depending Container Application.
source    | `docker://`       | **Optional.** `docker://` source location of the Container Application, the source MUST be prefixed by `docker://`. If source is present, all other fields SHALL be ignored.
params    | `Params Object`   | **Optional.** A list of `Params Objects` that contain provider specific information. If params is present, source field SHALL be ignored.
artifacts | `Artifact Object` | **Optional.** A list of `Artifact Objects` that contain provider specific information. If artifacts is present, source field SHALL be ignored.

##### Graph Item Object Example:

```yaml
params:
  - name: mariadb-centos7-atomicapp
    source: docker://projectatomic/mariadb-centos7-atomicapp
  ...
```

If no `artifacts` are specified, then an external Atomic App is pulled and installed from the `docker://` source.

#### Parameters Object

A list of Parameters the containerapp requires. Defaults may be set, otherwise user input is required.

##### Fields

Field Name  | Type              | Description
------------|:-----------------:|-------------
name        | `string`          | **Required.** The name of the parameter.
description | `string`          | **Required.** A human readable description of the parameter.
default     | `string`          | **Optional.** An optional default value for the parameter.

##### Parameters Object Example:

```yaml
params:
  - name: image
    description:  wordpress image
    default: wordpress
  ...
```

#### Requirements Object

The list of requirements of the Container Application. 

Field Name       | Type                      | Description
---------------- | :-----------------------: | ------------
persistentVolume | `Persisent Volume Object` | **Optional.** An object that holds an array of persistent volumes.

#### Persistent Volume Object

This describes a requirement for persistent, read-only or read-write storage that should be available to the containerapp on runtime. The name of this object MUST be `"persistentVolume"`.

Despite the name, within __Kubernetes__ and __OpenShift__ this acts as a [PersistentVolumeClaim](http://kubernetes.io/v1.1/docs/user-guide/persistent-volumes.html).

Persistent Volume is only available for the following providers: __kubernetes__

##### Fields

Field Name       | Type      | Description
---------------- | :-------: | ------------
name             | `string`  | **Required.** A name associated with the storage requirement.
accessMode       | `string`  | **Required.** Must be either: __ReadWriteOnce__, __ReadOnlyMany__ or __ReadWriteMany__.
size             | `integer` | **Required.** Size of the volume claim.

##### Persistent Volume Example

```yaml
requirements:
  - persistentVolume:
      name: "var-log-http"
      accessMode: "ReadWriteOnce"
      size: 4
  - persistentVolume:
      name: "var-log-https"
      accessMode: "ReadOnlyMany"
      size: 4
  ...
```

#### Artifacts Object

The Artifacts Object describes a list of provider specific artifact items. These artifact items will be used during the installation of the containerapp to deploy to the provider. Each provider key contains a list of artifacts. 

Each artifact is a file location relative to the `Nulecule` file.

__Optionally,__ you may _inherit_ from another compatible provider.

##### Artifacts Example:

```yaml
graph:
    ...
    artifacts:
      docker:
        - file://artifacts/docker/hello-apache-pod_run
      kubernetes:
        - file://artifacts/kubernetes/hello-apache-pod.json
      openshift:
        - inherit:
          - kubernetes
    ...
```

# Full example

This is a full example of __all__ features of the Nulecule file. This is only used as an example and _does not necessarily work as intended_.

```yaml
---
specversion: 0.0.2
id: helloworld

metadata:
  name: Hello World
  appversion: 0.0.1
  description: Hello earth!
  license:
    - name: Apache 2.0
      url: http://www.apache.org/licenses/LICENSE-2.0.html
  foo: bar
  othermetadata:
    foo: bar
    files: file://path/to/local/file

graph:
  - name: mariadb-centos7-atomicapp
    source: docker://projectatomic/mariadb-centos7-atomicapp

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
      openshift:
        - inherit:
          - kubernetes
      marathon:
        - file://artifacts/marathon/helloapache.json

requirements:
  - persistentVolume:
      name: "var-log-httpd"
      accessMode: "ReadWriteOnce"
      size: 4
```
