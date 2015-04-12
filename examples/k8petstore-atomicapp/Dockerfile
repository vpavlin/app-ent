FROM scratch 

MAINTAINER Christoph Görn <goern@redhat.com>

ENV container docker
LABEL INSTALL /bin/cat /application-entity/README.md

ADD / /application-entity

ENTRYPOINT [ "/application-entity/bin/cat", "/application-entity/README.md" ]
