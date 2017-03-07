FROM centos:7

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

# Check https://bodhi.fedoraproject.org/updates/?packages=atomicapp
# for the most recent builds of atomicapp in epel
ENV ATOMICAPPVERSION="0.6.4"
ENV TESTING="--enablerepo=epel-testing"

LABEL io.projectatomic.nulecule.atomicappversion=${ATOMICAPPVERSION} \
      io.openshift.generate.job=true \
      io.openshift.generate.token.as=env:TOKEN_ENV_VAR \
      RUN="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e USER -e SUDO_USER -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} run \${OPT3}" \
      STOP="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e USER -e SUDO_USER -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} stop \${OPT3}"

WORKDIR /atomicapp

# If a volume doesn't get mounted over /atomicapp (like when running in 
# an openshift pod) then open up permissions so files can be copied into
# the directory by non-root.
RUN chmod 777 /atomicapp

RUN yum install -y epel-release && \
    yum install -y atomicapp-${ATOMICAPPVERSION} ${TESTING} --setopt=tsflags=nodocs && \
    yum clean all

# the entrypoint
ENTRYPOINT ["/usr/bin/atomicapp"]
