FROM centos:7

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

ENV ATOMICAPPVERSION="0.4.3"

LABEL io.projectatomic.nulecule.atomicappversion=${ATOMICAPPVERSION} \
      io.openshift.generate.job=true \
      io.openshift.generate.token.as=env:TOKEN_ENV_VAR \
      RUN="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} run \${OPT3}" \
      STOP="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} stop \${OPT3}"

WORKDIR /opt/atomicapp

# Add the requirements file into the container
ADD requirements.txt ./

# Install needed requirements
RUN yum install -y epel-release && \
    yum update -y && \
    yum install -y --setopt=tsflags=nodocs docker && \
    yum install -y --setopt=tsflags=nodocs $(sed s/^/python-/ requirements.txt) && \
    yum clean all

WORKDIR /atomicapp

# If a volume doesn't get mounted over /atomicapp (like when running in 
# an openshift pod) then open up permissions so files can be copied into
# the directory by non-root.
RUN chmod 777 /atomicapp

# If a volume doesn't get mounted over /run (like when running in an
# openshift pod) then open up permissions so the lock file can be
# created by non-root.
RUN chmod 777 /run/lock

ENV PYTHONPATH  /opt/atomicapp/

# the entrypoint
ENTRYPOINT ["/usr/bin/python", "/opt/atomicapp/atomicapp/cli/main.py"]

# Add all of Atomic App's files to the container image
# NOTE: Do this last so rebuilding after development is fast
ADD atomicapp/ /opt/atomicapp/atomicapp/
