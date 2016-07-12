# This can be overriden (for eg):
# make install PYTHON=/usr/bin/python2.7
PYTHON ?= /usr/bin/python
DOCKER ?= /usr/bin/docker

.PHONY: all
all:
	$(PYTHON) -m pytest -vv --cov atomicapp

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: test
test:
	pip install -qr requirements.txt
	pip install -qr test-requirements.txt
	$(PYTHON) -m pytest -vv --cov atomicapp

.PHONY: image
image:
	$(DOCKER) build -t $(tag) .

.PHONY: syntax-check
syntax-check:
	flake8 atomicapp

.PHONY: clean
clean:
	$(PYTHON) setup.py clean --all

.PHONY: binary
binary:
	./script/binary.sh
