#!/bin/bash

#use this to build a docker container to run the application
if [ -z "$USERNAME" ]; then
    echo "setting USERNAME to " `whoami` 
    USERNAME=`whoami`
fi

DIR=$( dirname "${BASH_SOURCE[0]}" )
echo $DIR

pushd $DIR
ln -sf Dockerfile.fedora Dockerfile
docker build --rm -t $USERNAME/atomicapp-run .
popd

COMMAND="\"docker run --rm -it --privileged -v /run:/run -v /:/host -v \\\`pwd\\\`:/application-entity $USERNAME/atomicapp-run\" "

echo The application is now built as a command line executable docker container. 
echo
echo You can run it using:
echo $COMMAND
echo or, you can create an alias:
echo alias nulecule=$COMMAND
echo
echo If you aren\'t sure what to do next, try \(after creating the alias\):
echo nulecule --help
echo

