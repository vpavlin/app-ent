FROM centos:centos7

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

LABEL io.projectatomic.nulecule.atomicappversion="0.1.3" \
      RUN="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} run \${OPT3} /atomicapp" \
      STOP="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} stop \${OPT3} /atomicapp" \
      INSTALL="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run  --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} install \${OPT3} --destination /atomicapp /application-entity"

WORKDIR /opt/atomicapp

# add all of Atomic App's files to the container image
ADD atomicapp/ /opt/atomicapp/atomicapp/
ADD setup.py VERSION NULECULE requirements.txt /opt/atomicapp/

# add EPEL repo for pip
RUN echo -e "[epel]\nname=epel\nenabled=1\nbaseurl=https://dl.fedoraproject.org/pub/epel/7/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/epel.repo

# lets install pip, and gcc for the native extensions
# and remove all after use
RUN yum install -y --setopt=tsflags=nodocs python-pip python-setuptools docker gcc
RUN python setup.py install
RUN yum remove -y gcc cpp glibc-devel glibc-headers kernel-headers libmpc mpfr python-pip && \
    yum clean all

WORKDIR /atomicapp
VOLUME /atomicapp

# the entrypoint
ENTRYPOINT ["/usr/bin/atomicapp"]
