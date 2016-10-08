FROM scratch 

### This is taken from Christopher Gorn's original 
### Example implementation of wordpress.
### https://github.com/goern/wordpress-atomicapp/.

MAINTAINER Jay Vyas <jvyas@redhat.com>
ENV container docker
LABEL INSTALL /bin/cat /application-entity/README.md

ADD / /application-entity

ENTRYPOINT [ "/application-entity/bin/cat", "/application-entity/README.md" ]
