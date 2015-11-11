FROM centos:centos7

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

LABEL io.projectatomic.nulecule.atomicappversion="0.2.1" \
      io.openshift.generate.job=true \
      io.openshift.generate.token.as=env:TOKEN_ENV_VAR \
      RUN="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} run \${OPT3} \${IMAGE}" \
      STOP="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} stop \${OPT3}" \
      INSTALL="docker run -it --rm \${OPT1} --privileged -v `pwd`:/atomicapp -v /run:/run -v /:/host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} -v \${OPT2} install \${OPT3} \${IMAGE}"

WORKDIR /opt/atomicapp

# add all of Atomic App's files to the container image
ADD atomicapp/ /opt/atomicapp/atomicapp/
ADD setup.py requirements.txt /opt/atomicapp/

# lets install pip, and gcc for the native extensions
# and remove all after use
RUN yum -y install epel-release && \
    yum install -y --setopt=tsflags=nodocs GitPython python-pip python-setuptools docker gcc && \
    python setup.py install && \
    yum remove -y gcc cpp glibc-devel glibc-headers kernel-headers libmpc mpfr python-pip && \
    yum clean all

WORKDIR /atomicapp
VOLUME /atomicapp

# the entrypoint
ENTRYPOINT ["/usr/bin/atomicapp"]
