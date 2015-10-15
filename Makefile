BASE_IMAGE_NAME = atomicapp
TAG = atomicapp:dev
DOCKERFILE = Dockerfile

# https://www.gnu.org/software/make/manual/html_node/Phony-Targets.html
.PHONY: install syntax-check rmi

ifeq ($(TARGET), rhel7)
	OS := rhel7
	DOCKERFILE := Dockerfile.rhel7
else ifeq ($(TARGET), centos7)
	OS := centos7
	DOCKERFILE := Dockerfile
else ifeq ($(TARGET), debian8)
  OS := debian
	DOCKERFILE := Dockerfile.debian
else
  OS := fedora
	DOCKERFILE := Dockerfile.fedora
endif

all: test

install:
	python setup.py install

test: syntax-check
	python -m pytest -vv

image: syntax-check
	docker build -t $(TAG) -f $(DOCKERFILE) .

syntax-check:
	flake8 atomicapp

rmi:
	docker rmi $(TAG)
