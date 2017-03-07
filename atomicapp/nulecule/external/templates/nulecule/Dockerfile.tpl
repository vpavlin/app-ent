FROM projectatomic/atomicapp:${atomicapp_version}

MAINTAINER Your Name <you@email.com>

LABEL io.projectatomic.nulecule.providers="kubernetes,docker,marathon" \
      io.projectatomic.nulecule.specversion="${nulecule_spec_version}"

ADD /Nulecule /Dockerfile README.md /application-entity/
ADD /artifacts /application-entity/artifacts
