#!/bin/bash
set -ex

LINK="https://github.com/projectatomic/atomicapp"
UPSTREAM="projectatomic/atomicapp"

install_atomicapp() {
  echo "
  ##########
  INSTALLING ATOMICAPP CLI
  
  This will install atomicapp to /bin
  as well as build an atomicapp container named
  atomicapp:build
  ##########
  "
  git clone $LINK
  cd atomicapp

  if [ "$1" ]
    then
      echo "USING PR: $1"
      git fetch origin pull/$1/head:PR_$1
      git checkout PR_$1
  fi

  # Install
  make install

  # Build docker container
	docker pull centos:7
  docker build -t atomicapp:build .

  cd ..
  rm -rf atomicapp
}

case "$1" in
        install)
            install_atomicapp $2
            ;;
        *)
            echo $"Usage: atomicpp.sh {install}"
            exit 1
esac
