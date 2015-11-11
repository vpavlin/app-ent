# Atomicapp Workflow

Atomicapp is used to manage the lifecycle of Nulecule applications.  Atomicapp allows you to install, run and stop Nulecule applications from both Nulecule container images and Nulecule metadata.  This document demonstrates how to use `atomicapp` to interact with Nulecule applications.

The general workflow is:

1. Install the application, typically from an image.
2. Configure the application.
3. Run the application, typically from installed metadata.
4. Stop the application.

## Installing a Nulecule Application

Atomicapp allows you to install Nulecule applications on your system from Nulecule container images. The install process consists of fetching the specified Nulecule container image and extracting Nulecule metadata from it to a default location or a specified location.

### Installing From an Image

The installation process will download the Nulecule application container and extract the Nulecule metadata.  By default, this metadata is saved to a directory inside of `/var/lib/atomicapp`.

    $ sudo atomicapp install projectatomic/helloapache
    ...
    Your application resides in /var/lib/atomicapp/projectatomic-helloapache-071c3cc24417
    Please use this directory for managing your application

The installation location can be overridden with the `--destination` command line option:

    $ sudo atomicapp install --destination path/to/some/dir projectatomic/helloapache
    ...
    Your application resides in path/to/some/dir
    Please use this directory for managing your application

The destination path can be a relative path or an absolute path.  The directory will be created if it does not already exist.

**NOTE:** `--dry-run` does not work when installing a Nulecule application from an image because it requires making changes to the underlying host system.

### Installing From a local path

If a Nulecule application's metadata has already been extracted to a local directory, there is no installation operation to be performed.  Therefore, this is a `noop` command.  You cannot use the `--destination` command line option with this form of installation.

    $ sudo atomicapp install some_projectatomic_helloapache
    ...
    Your application resides in some_project_helloapache
    Please use this directory for managing your application

## Configuring the Nulecule Application

Installing a Nulecule application generates an `answers.conf.sample` file.  This file can be used as the template for your application configuration by copying/renaming it to `answers.conf`.  The `answers.conf` file should be edited as required to run your application.

## Running a Nulecule Application

Atomicapp allows you to run a Nulecule application from local Nulecule
metadata or directly from a Nulecule container image.

### Running from Local Metadata

    $ sudo atomicapp run /var/lib/atomicapp/projectatomic-helloapache-0b6aec7c9c41

Running a Nulecule application generates a `answers.conf.gen` file in the Nulecule application directory with configuration generated from the `answers.conf` file supplied by the user and any other defaults and configuration supplied by the application.  The `answers.conf.gen` file is the configuration that is used to start and stop the Nulecule application.

See below for additional options.

#### Running from an Image

This will, in one step, download the Nulecule application, extract the Nulecule  metadata, and run the application using the default configuration.

    $ sudo atomicapp run projectatomic/helloapache

See below for additional options.

**NOTE:** The `--dry-run` option does not work when running a Nulecule application from a container image.

### Other Options

`atomicapp run` supports the following optional arguments:

- `-a` or `--answers`: By default, `atomicapp run` looks for the `answers.conf` file in the installation directory. This option overrides this behavior and allows you to specify another file that contains the answers data.
- `-write-answers`: By default, `atomicapp run` writes the `answers.conf.gen` file to the installation directory. This option overrides this behavior and allows you to specify another file that should be used.
- `--provider`: This option lets you override the default provider and the prpvider, if any, specified in `answers.conf` file.
- `--ask`: This causes `atomicapp` to prompt the user for values for parameters that have default values and are not specified in ``answers`` file.
- ``-destination``: Specifies the path to install Nulecule metadata to when running a Nulecule application directly from a container image.


### 3. Stop
A Nulecule application can be stopped using the ``atomicapp stop`` command.
Stop uses the ``answers.conf.gen`` file created during installation/execution
of the Nulecule application.

``sudo atomicapp stop /var/lib/atomicapp/projectatomic-helloapache-0b6aec7c9c41``
