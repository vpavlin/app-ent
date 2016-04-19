
The Dockerfiles.git directory is the place where Dockerfiles that are
used to create containers that use the upstream git code live. These
Dockerfiles are meant to be used to build an atomicapp base container
for a number of different base operating systems.

For example, if you want to build an Atomic App container for Debian
that uses the upstream git code then you would run the following command
from the root of the git repo:

```
docker build -t debian-atomicapp-git -f ./Dockerfiles.git/Dockerfile.debian .
```

If you want to do the same thing for Fedora you would:

```
docker build -t fedora-atomicapp-git -f ./Dockerfiles.git/Dockerfile.fedora .
```

Or Alpine:
```
docker build -t alpine-atomicapp-git -f ./Dockerfiles.git/Dockerfile.alpine .
```
