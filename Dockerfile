FROM centos:centos7

MAINTAINER Vaclav Pavlin <vpavlin@redhat.com>

WORKDIR /opt/atomicapp

# add all of Atomic App's files to the container image
ADD atomicapp/ /opt/atomicapp/atomicapp/
ADD setup.py /opt/atomicapp/
ADD requirements.txt /opt/atomicapp/

# add EPEL repo for pip
RUN echo -e "[epel]\nname=epel\nenabled=1\nbaseurl=https://dl.fedoraproject.org/pub/epel/7/x86_64/\ngpgcheck=0" > /etc/yum.repos.d/epel.repo

# lets install pip, and gcc for the native extensions
# and remove all after use
RUN yum install -y --setopt=tsflags=nodocs python-pip docker gcc && \
    python setup.py install && \
    pip install -r ./requirements.txt && \
    yum remove -y gcc cpp glibc-devel glibc-headers kernel-headers libmpc mpfr python-pip && \
    yum clean all

WORKDIR /atomicapp
VOLUME /atomicapp

LABEL RUN  docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} run \${OPT3} /atomicapp
LABEL STOP docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} stop \${OPT3} /atomicapp
LABEL INSTALL docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run  --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} install \${OPT3} --destination /atomicapp /application-entity

# expose port 5000/tcp for Cockpit integration, see also https://github.com/cockpit-project/cockpit/wiki/Feature:-Kubernetes:-Application-Entities
EXPOSE 5000

# the entrypoint 
ENTRYPOINT ["/usr/bin/atomicapp"]
