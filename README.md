# ContainerApp
ContainerApp tool is a reference implementation of [Container Application Specification](https://github.com/aweiteka/atomicapp-spec). It can be used to bootstrap container application and to install and run them.

Example applications consist of [MariaDB](https://github.com/vpavlin/atomicapp-mariadb) and [Wordpress](https://github.com/vpavlin/atomicapp-wordpress) applications, where Wordpress depends on MariaDB.

## How To

### Install this project
Simply run

```
python setup.py install
```

If you want to do some changes to the code, I suggest to do:

```
cd atomicapp-run
export PYTHONPATH=$PWD/atomicapp:$PYTHONPATH
alias atomicapp="$PWD/atomicapp/cli/main.py"
```

### Create
```
atomicapp [--dry-run] create --schema PATH|URL APP_NAME
```

Constructs directory structure and fills Atomicfile with application name and id.
### Build
```
atomicapp [--dry-run] build [TAG]
```
Calls Docker build to package up the application and tags the resulting image.
### Install and Run
```
atomicapp [--dry-run] [-a answers.conf] install|run [--recursive] [--update] [--path PATH] APP|PATH 
```
Pulls the application and it's dependencies. If the last argument is existing path, it looks for Atomicfile there instead of pulling anything.
* `--recursive yes|no` Pull whole dependency tree
* `--update` Overwrite any existing files
* `--path PATH` Unpack the application into given directory instead of current directory

Action `run` performs `install` prior it's own tasks are executed. When `run` is selected, providers' code is invoked and containers are deployed.

## Providers

Providers represent various deployment targets. They are based on yapsy plugin system and can be added by implementing interface explained in [Providers](providers/README.md)

## Examples

### Mariadb App

### Wordpress App


