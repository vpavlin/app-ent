<pre>
              __                              
              \ \___     .__                  
            .--""___\..--"/                   
        .__.|-"""..... ' / ____                   
________\_______________/_/ O  \___/
 <_/_\_/_\_/_\_/_\_/_\_/_______/   \  
</pre>

# shipy

shipy is a python library which runs the `docker` commands using [`docker-py`](github.com/docker/docker-py) and returns parseable output.

This is useful when you need to take `docker` commands as an input from the user, but you do not want to shell out to run those commands, because that would require a lot of grep, sed, awk on the returned output, and the next release of docker might as well change the output and your application comes crashing down.

## Using shipy

##### Installation

shipy will soon be made into a python package on `pip`, `.rpm` and `.deb`, keep an eye out.

Till then just clone this repository,
`git clone https://github.com/containscafeine/shipy.git` and you have it.

You need to have a `docker-py` version that is compatible with your docker engine.

##### Usage
Clone the repository in your project root and you should be able to import it and run as follows:

###### as a library

```python
from shipy.dpyexec import Shipy
shipy = Shipy()
command = 'run --name batman  -v /tmp:/tmp centos:latest ping 8.8.8.8'
shipy.shipy(command.split())
```


###### as a command line tool

```
$ python shipy run --name batman -p 8080:8080 centos ping 8.8.8.8
INFO:root:Running container 512f9e5a9143a10306e5f6a17438e0412daac859ae2b6057b3bde58918f4e53b.
```

```
$ python shipy ps
INFO:root:Name: batman, ID: 55ef260d
INFO:root:Name: jolly_jennings, ID: 17661ba7
INFO:root:Name: agitated_cori, ID: 6d20c974
...
```

## Supported commands

The following commands are supported right now, and more are being added rapidly.

#### run
```
usage: shipy run [-h] [--name NAME] [--entrypoint ENTRYPOINT] [-d]
                 [--hostname HOSTNAME] [-u USER] [-e ENVIRONMENT]
                 [--cpu-shares CPU_SHARES] [-w WORKING_DIR]
                 [--mac-address MAC_ADDRESS] [-l LABELS]
                 [--stop-signal STOP_SIGNAL] [-v BINDS] [-p PORT_BINDINGS]
                 [-P] [--link LINKS] [--privileged] [--dns DNS]
                 [--dns-search DNS_SEARCH] [--volumes-from VOLUMES_FROM]
                 [--net NETWORK_MODE]
                 image ...

positional arguments:
  run
  image                 the image to run
  command               the command to be run in the container

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           a name for the container
  --entrypoint ENTRYPOINT
                        an entrypoint
  -d, --detach          detached mode, run container in the background
  --hostname HOSTNAME   optional hostname for the container
  -u USER, --user USER  sets the username or UID used and optionally the
                        groupname or GID for the specified command
  -e ENVIRONMENT, --env ENVIRONMENT
                        set environment variables
  --cpu-shares CPU_SHARES
                        CPU shares (relative weight)
  -w WORKING_DIR, --workdir WORKING_DIR
                        working directory inside the container
  --mac-address MAC_ADDRESS
                        container MAC address (e.g. 92:d0:c6:0a:29:33)
  -l LABELS, --label LABELS
                        set metadata on the container (e.g., --label
                        com.example.key=value)
  --stop-signal STOP_SIGNAL
                        signal to stop a container. Default is SIGTERM
  -v BINDS, --volume BINDS
                        bind mount a volume
  -p PORT_BINDINGS, --publish PORT_BINDINGS
                        port bindings
  -P, --publish-all     publish all exposed ports to random ports on the host
                        interfaces
  --link LINKS          add link to another container in the form of <name or
                        id>:alias or just <name or id> in which case the alias
                        will match the name
  --privileged          give extended privileges to this container
  --dns DNS             set custom DNS servers
  --dns-search DNS_SEARCH
                        set custom DNS search domains
  --volumes-from VOLUMES_FROM
                        mount volumes from the specified container(s)
  --net NETWORK_MODE    set the Network mode for the container
```

#### ps
```
usage: shipy ps [-h] [-a]

positional arguments:
  ps

optional arguments:
  -h, --help  show this help message and exit
  -a, --all   show all containers
```

#### kill
```
usage: shipy kill [-h]  container

positional arguments:
  kill        kill a container
  container   the container to kill

optional arguments:
  -h, --help  show this help message and exit
```
 
#### stop
```
usage: shipy stop [-h]  container

positional arguments:
  stop        stop a running container
  container   the container to stop

optional arguments:
  -h, --help  show this help message and exit
```
 
#### rm
```
 usage: shipy rm [-h] [-f] [-v] [-l]  container

positional arguments:
  rm            remove a container
  container     the container to remove

optional arguments:
  -h, --help    show this help message and exit
  -f, --force   force the removal of a running container
  -v, --volume  remove the volumes associated with the container
  -l, --link    remove the specified link and not the underlying container
```

#### pull
```
usage: shipy pull [-h]  image

positional arguments:
  pull        pull a container image
  image       the container image to pull

optional arguments:
  -h, --help  show this help message and exit
```

#### restart
```
usage: shipy restart [-h]  container

positional arguments:
  restart     restart a container
  container   the container image to pull

optional arguments:
  -h, --help  show this help message and exit
```

### version
```
usage: shipy version [-h]

positional arguments:
  version     show the docker version information

optional arguments:
  -h, --help  show this help message and exit
```
