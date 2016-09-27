# This can be overriden (for eg):
# make install PYTHON=/usr/bin/python2.7
PYTHON ?= /usr/bin/python
DOCKER ?= /usr/bin/docker

.PHONY: all
all:
	$(PYTHON) -m pytest -vv

.PHONY: install
install:
	$(PYTHON) setup.py install

.PHONY: test
test:
	pip install -qr requirements.txt
	pip install -qr test-requirements.txt
	$(PYTHON) -m pytest tests/units/ -vv --cov atomicapp

.PHONY: functional-test
functional-test:
	pip install -qr requirements.txt
	pip install -qr test-requirements.txt
	./tests/functional/scripts/atomic.sh install
	./tests/functional/scripts/prepare.sh install
	$(DOCKER) build -t atomicapp:build .
	$(PYTHON) -m pytest tests/functional/ -vv --cov atomicapp

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
