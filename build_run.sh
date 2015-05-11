#!/bin/bash

WHAT=$1

# TODO sanity check that we got docker >= 1.6

[ -z "${WHAT}" ] && echo "Need to provide a distro you want to build for (fedora|centos|rhel7)" && exit
IMAGE_NAME=atomicapp-${WHAT}

if [ -z "$USERNAME" ]; then
    echo "setting USERNAME to " `whoami` 
    USERNAME=`whoami`
fi

echo docker build $USERNAME/$IMAGE_NAME
if [ "$WHAT" == "centos" ]; then
    docker build --rm --tag $USERNAME/$IMAGE_NAME --file Dockerfile .
else
    docker build --rm --tag $USERNAME/$IMAGE_NAME --file Dockerfile.${WHAT} .
fi

#end.
