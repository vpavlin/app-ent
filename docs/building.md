# Building the Atomic App base image

A Makefile is provided to support the process of testing and building Atomic App.
This Makefile includes three major targets:

* `test` - this will syntax check the source code and run all tests
* `install` - to install atomicapp locally
* `image` - to create a docker container image for Atomic App

Some default values are set within the Makefile:

* `BASE_IMAGE_NAME` - the base image name to use for the build
* `DOCKERFILE` - the (os depending) dockerfile to use for building the image
* `TAG` - a tag to use for the build

## Usage example

To generate a Debian GNU/Linux Jessie based Atomic App base image, simply use
the command line `make image TARGET=debian8`.
