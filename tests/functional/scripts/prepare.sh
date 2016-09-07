#!/bin/bash


do_redhat() {
    echo "Prepare for Red Hat"
    # hyperkube causes avc denials
    setenforce 0
    # make sure wget is installed
    yum install -y wget
    # Make sure docker is installed/started
    yum install -y docker
    systemctl start docker
    # Make sure kubernetes client is installed/started
    yum install -y kubernetes-client
}

do_debian() {
    echo "Prepare for Debian"

}

case "$1" in
    install)
        if [ -f /etc/redhat-release ]; then
	    do_redhat
	else
	    do_debian
	fi
    ;;
    *)
        echo $"Usage: prepare.sh {install}"
        exit 1
esac
