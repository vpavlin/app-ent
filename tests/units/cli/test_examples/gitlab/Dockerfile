FROM projectatomic/atomicapp:0.1.3

MAINTAINER Navid Shaikh <nshaikh@redhat.com>

LABEL io.projectatomic.nulecule.specversion 0.0.2
LABEL io.projectatomic.nulecule.providers "kubernetes"

LABEL Build docker build --rm --tag swordphilic/gitlab-centos7-atomicapp .

ADD /Nulecule /Dockerfile /application-entity/
ADD /artifacts /application-entity/artifacts
