FROM debian:jessie

MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

ENV ATOMICAPPVERSION="0.6.4"

LABEL io.projectatomic.nulecule.atomicappversion=${ATOMICAPPVERSION} \
      RUN="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e USER -e SUDO_USER -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} run \${OPT3}" \
      STOP="docker run -it --rm \${OPT1} --privileged -v \${PWD}:/atomicapp -v /run:/run -v /:/host --net=host --name \${NAME} -e USER -e SUDO_USER -e NAME=\${NAME} -e IMAGE=\${IMAGE} \${IMAGE} \${OPT2} stop \${OPT3}"

WORKDIR /opt/atomicapp

# Add the requirements file into the container
ADD requirements.txt ./

# add jessie-backports for Docker package
RUN echo "deb http://http.debian.net/debian jessie-backports main" > /etc/apt/sources.list.d/backports.list

# lets install pip, and gcc for the native extensions
# and remove all after use
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io python-pip gcc && \
    pip install -r /opt/atomicapp/requirements.txt && \
    apt-get remove --purge -y gcc && \
    apt-get autoremove -y && \
    apt-get clean -y

WORKDIR /atomicapp

# If a volume doesn't get mounted over /atomicapp (like when running in 
# an openshift pod) then open up permissions so files can be copied into
# the directory by non-root.
RUN chmod 777 /atomicapp

ENV PYTHONPATH  /opt/atomicapp/

# the entrypoint
ENTRYPOINT ["/usr/bin/python", "/opt/atomicapp/atomicapp/cli/main.py"]

# Add all of Atomic App's files to the container image
# NOTE: Do this last so rebuilding after development is fast
ADD atomicapp/ /opt/atomicapp/atomicapp/
