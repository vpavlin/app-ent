## Using Atomic App

Prerequisite: Before proceeding, make sure you either have a Kubernetes, OpenShift or Docker environment setup and ready.

You can either use Atomic App on your own OS or in a container via the `atomic` command on Atomic hosts.

In order to use Atomic App on Project Atomic hosts we use the `INSTALL` and `RUN` label functionality with [atomic cli](https://github.com/projectatomic/atomic).

With the exception of the `atomic stop` command all functionality is essentially the same.

### Quickstart: Atomic App on bare metal

__Running Apache on Docker:__
```sh
▶ sudo atomicapp run projectatomic/helloapache --provider=docker
2016-02-25 16:06:38,298 - [INFO] - main.py - Action/Mode Selected is: run
2016-02-25 16:06:38,299 - [INFO] - base.py - Unpacking image: projectatomic/helloapache to /var/lib/atomicapp/projectatomic-helloapache-7c32c1632a7b
2016-02-25 16:06:41,904 - [INFO] - container.py - Skipping pulling Docker image: projectatomic/helloapache
2016-02-25 16:06:41,904 - [INFO] - container.py - Extracting nulecule data from image: projectatomic/helloapache to /var/lib/atomicapp/projectatomic-helloapache-7c32c1632a7b
20af2e6e33d10d26aa98d6e63c70de5fd55bfe14b9cc782e1312afe441ef7130
2016-02-25 16:06:42,231 - [INFO] - docker.py - Deploying to provider: Docker
5d6938439d50c21251507b26c73f5e65f102f2b99e183002ef2ec21414c4ee78

Your application resides in /var/lib/atomicapp/projectatomic-helloapache-7c32c1632a7b
Please use this directory for managing your application

▶ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                NAMES
5d6938439d50        centos/httpd        "/run-httpd.sh"          3 seconds ago       Up 1 seconds        0.0.0.0:80->80/tcp   default_centos-httpd_ec75a2fe2a50
```

__Runnning Apache on Kubernetes:__
```sh
▶ sudo atomicapp run projectatomic/helloapache
2016-02-25 15:03:04,341 - [INFO] - main.py - Action/Mode Selected is: run
2016-02-25 15:03:04,343 - [INFO] - base.py - Unpacking image: projectatomic/helloapache to /var/lib/atomicapp/projectatomic-helloapache-c0dd79b5e757
2016-02-25 15:03:07,983 - [INFO] - container.py - Skipping pulling Docker image: projectatomic/helloapache
2016-02-25 15:03:07,984 - [INFO] - container.py - Extracting nulecule data from image: projectatomic/helloapache to /var/lib/atomicapp/projectatomic-helloapache-c0dd79b5e757
886e10a3244f982f3302ab9058ab7b377c6f83e2cf63f001e1ba011358d0b471
2016-02-25 15:03:08,332 - [INFO] - kubernetes.py - Using namespace default
2016-02-25 15:03:08,332 - [INFO] - kubernetes.py - trying kubectl at /usr/bin/kubectl
2016-02-25 15:03:08,332 - [INFO] - kubernetes.py - trying kubectl at /usr/local/bin/kubectl
2016-02-25 15:03:08,332 - [INFO] - kubernetes.py - found kubectl at /usr/local/bin/kubectl
2016-02-25 15:03:08,332 - [INFO] - kubernetes.py - Deploying to Kubernetes
...

Your application resides in /var/lib/atomicapp/projectatomic-helloapache-c0dd79b5e757
Please use this directory for managing your application

▶ kubectl get po
NAME                   READY     STATUS    RESTARTS   AGE
helloapache            1/1       Running   0          2m
k8s-etcd-127.0.0.1     1/1       Running   0          1d
k8s-master-127.0.0.1   4/4       Running   0          1d
k8s-proxy-127.0.0.1    1/1       Running   0          1d
```

__Fetch, edit and run Apache on Kubernetes:__
```sh
▶ mkdir ./localdir

▶ sudo atomicapp fetch projectatomic/helloapache --destination ./localdir/
2016-02-25 15:35:41,439 - [INFO] - main.py - Action/Mode Selected is: fetch
2016-02-25 15:35:41,440 - [INFO] - base.py - Unpacking image: projectatomic/helloapache to helloapache
2016-02-25 15:35:45,067 - [INFO] - container.py - Skipping pulling Docker image: projectatomic/helloapache
2016-02-25 15:35:45,067 - [INFO] - container.py - Extracting nulecule data from image: projectatomic/helloapache to helloapache
c12d2047fab44f2906b9cbee3ac86c6c6499921ce33a90085e8765491b44f447

Your application resides in localdir
Please use this directory for managing your application

▶ cd localdir

▶ cat Nulecule
...
      - name: hostport
        description: The host TCP port as the external endpoint
        default: 80
...

▶ vim Nulecule # edit port 80 to 8080

▶ cat Nulecule 
...
      - name: hostport
        description: The host TCP port as the external endpoint
        default: 8080
...

▶ sudo atomicapp run .

OR

▶ docker build -t myapp
▶ sudo atomicapp run myapp
```

### Quickstart: Atomic App on Atomic Host

__Running Apache on Docker:__
```sh
▶ sudo atomic run projectatomic/helloapache --provider=docker
docker run -it --rm  --privileged -v /home/wikus:/atomicapp -v /run:/run -v /:/host --net=host --name helloapache -e NAME=helloapache -e IMAGE=projectatomic/helloapache projectatomic/helloapache  run  --provider=docker
docker run -it --rm  --privileged -v /home/wikus:/atomicapp -v /run:/run -v /:/host --net=host --name helloapache -e NAME=helloapache -e IMAGE=projectatomic/helloapache projectatomic/helloapache  run  --provider=docker
2016-03-01 20:54:37,617 - [INFO] - main.py - Action/Mode Selected is: run
2016-03-01 20:54:37,618 - [INFO] - base.py - Unpacking image: projectatomic/helloapache to /host/var/lib/atomicapp/projectatomic-helloapache-a68057164f09
2016-03-01 20:54:38,357 - [INFO] - container.py - Skipping pulling Docker image: projectatomic/helloapache
2016-03-01 20:54:38,358 - [INFO] - container.py - Extracting nulecule data from image: projectatomic/helloapache to /host/var/lib/atomicapp/projectatomic-helloapache-a68057164f09
6eedd332f9938c7b4bacca694fdc77309ca5b43aabb05a1cb644ff8a0b713012
2016-03-01 20:54:38,558 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:54:38,558 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:54:38,602 - [INFO] - docker.py - Deploying to provider: Docker
a98d9a3305496803c38a90a9ef65c52030dc23dae4b04f36ce167ff98335395f

Your application resides in /var/lib/atomicapp/projectatomic-helloapache-a68057164f09
Please use this directory for managing your application
```

__Runnning Apache on Kubernetes:__
```sh
▶ sudo atomic run projectatomic/helloapache
docker run -it --rm  --privileged -v /home/wikus:/atomicapp -v /run:/run -v /:/host --net=host --name helloapache -e NAME=helloapache -e IMAGE=projectatomic/helloapache projectatomic/helloapache  run  
docker run -it --rm  --privileged -v /home/wikus:/atomicapp -v /run:/run -v /:/host --net=host --name helloapache -e NAME=helloapache -e IMAGE=projectatomic/helloapache projectatomic/helloapache  run  
2016-03-01 20:58:03,396 - [INFO] - main.py - Action/Mode Selected is: run
2016-03-01 20:58:03,397 - [INFO] - base.py - Unpacking image: projectatomic/helloapache to /host/var/lib/atomicapp/projectatomic-helloapache-89e975ea7438
2016-03-01 20:58:04,153 - [INFO] - container.py - Skipping pulling Docker image: projectatomic/helloapache
2016-03-01 20:58:04,153 - [INFO] - container.py - Extracting nulecule data from image: projectatomic/helloapache to /host/var/lib/atomicapp/projectatomic-helloapache-89e975ea7438
c85cbb2d28857f2b283e23a72a70e077daceeb2b72f6964605af6f7efa8fbc2f
2016-03-01 20:58:04,387 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:58:04,388 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:58:04,388 - [INFO] - kubernetes.py - Using namespace default
2016-03-01 20:58:04,388 - [INFO] - kubernetes.py - trying kubectl at /host/usr/bin/kubectl
2016-03-01 20:58:04,388 - [INFO] - kubernetes.py - trying kubectl at /host/usr/local/bin/kubectl
2016-03-01 20:58:04,388 - [INFO] - kubernetes.py - found kubectl at /host/usr/local/bin/kubectl
2016-03-01 20:58:04,388 - [INFO] - kubernetes.py - Deploying to Kubernetes

Your application resides in /var/lib/atomicapp/projectatomic-helloapache-89e975ea7438
Please use this directory for managing your application
```

__Stopping Apache on Kubernetes:__
```sh
▶ sudo atomic stop projectatomic/helloapache /var/lib/atomicapp/projectatomic-helloapache-89e975ea7438
docker run -it --rm  --privileged -v /home/wikus:/atomicapp -v /run:/run -v /:/host --net=host --name helloapache -e NAME=helloapache -e IMAGE=projectatomic/helloapache projectatomic/helloapache  stop  /var/lib/atomicapp/projectatomic-helloapache-89e975ea7438 
2016-03-01 20:59:57,067 - [INFO] - main.py - Action/Mode Selected is: stop
2016-03-01 20:59:57,075 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:59:57,075 - [WARNING] - plugin.py - Configuration option 'providerconfig' not found
2016-03-01 20:59:57,075 - [INFO] - kubernetes.py - Using namespace default
2016-03-01 20:59:57,075 - [INFO] - kubernetes.py - trying kubectl at /host/usr/bin/kubectl
2016-03-01 20:59:57,075 - [INFO] - kubernetes.py - trying kubectl at /host/usr/local/bin/kubectl
2016-03-01 20:59:57,075 - [INFO] - kubernetes.py - found kubectl at /host/usr/local/bin/kubectl
2016-03-01 20:59:57,075 - [INFO] - kubernetes.py - Undeploying from Kubernetes
```
