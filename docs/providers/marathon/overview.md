# Marathon

### Overview

The Marathon provider will deploy an application into Mesos cluster
using Marathon scheduler.

### Configuration 
This provider requires configuration (`provider-api`) to be able to connect to Marathon API.
If no `provider-api` is specified it will use `http://localhost:8080` as Marathon API url.
This configuration can be provided in the `answers.conf` file. 

Example:

    [general]
    provider=marathon
    provider-api=http://10.0.2.15:8080

#### Configuration values

Table 1. Marathon default configuration values

Keyword     | Required | Description                                 | Default value
------------|----------|---------------------------------------------|--------------------------
provider-api |   no     |  url for Marathon REST API                  | `http://localhost:8080`

### Operations

```
atomicapp run
```

This command creates app in Marathon.
The deploy process creates applications in order as enlisted in Nulecule Marathon artifacts.

```
atomicapp stop
```
This command deletes app from Marathon.

