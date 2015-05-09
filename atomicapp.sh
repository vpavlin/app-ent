#!/usr/bin/bash

if [ "$1" == "-h" -o "$1" == "--help" ]; then
    echo "This script let's you to run the atomicapp container as a tool."
    echo "All arguments are passed to docker run command for image projectatomic/atomicapp"
    echo "Current directory (`pwd`) is mounted to the container as /atomicapp"
fi

docker run -it --rm --net=host --privileged -v /run:/run -v /:/host -v `pwd`:/atomicapp projectatomic/atomicapp $@
