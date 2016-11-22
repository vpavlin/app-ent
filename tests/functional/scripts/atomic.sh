#!/bin/bash

# NOTE, atomic 1.8 requires Docker 1.9
RELEASE="1.8"
LINK="https://github.com/projectatomic/atomic/archive/v1.8.tar.gz"
SOURCE=$2

# Install according to github docs 
# https://github.com/projectatomic/atomic/tree/master/docs/install
install_atomic() {
  echo "
  ##########
  INSTALLING ATOMIC CLI
  ##########
  "
  if [ "$SOURCE" == "rpm" ]; then
    yum install -y atomic
    return
  elif [ "$SOURCE" == "master" ]; then
    #clean this up later
    echo "Downloading master"
    git clone https://github.com/projectatomic/atomic atomic
    cd atomic
  else
    wget $LINK -O atomic.tar.gz
    tar --no-same-owner -xvf atomic.tar.gz
    cd atomic-$RELEASE
  fi
  
  # Use rhel yum, if not assume it's ubuntu / debian
  if [ -f /etc/redhat-release ]; then
    # Remove all previous builds of atomic (issue of upgrading 1.5 to 1.8)
    rm -rf /usr/lib/python2.7/site-packages/Atomic/ /usr/lib/python2.7/site-packages/atomic-*
    yum install -y epel-release python-pip pylint go-md2man
  else
    rm -rf /usr/local/lib/python2.7/site-packages/Atomic/ /usr/local/lib/python2.7/site-packages/atomic-*
    rm -rf /usr/local/lib/python2.7/dist-packages/Atomic/ /usr/local/lib/python2.7/dist-packages/atomic-*
    apt-get install -y make git python-selinux go-md2man python-pip python-dbus python-rpm pylint
    ln /usr/local/bin/pylint /usr/bin/pylint
  fi
 
  # Install all the requirements (usually done by make all)
  pip install -r requirements.txt

  # Ignore any PYLINT errors and make sure you're installing via Python 2
  PYLINT=true PYTHON=/usr/bin/python2 make install

  # Remove once completed
  cd ..
  rm -rf atomic-$RELEASE atomic.tar.gz
}

case "$1" in
        install)
            install_atomic
            ;;
        *)
            echo $"Usage: atomic.sh {install}"
            exit 1
 
esac
