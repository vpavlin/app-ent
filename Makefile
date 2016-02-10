all:
	python -m pytest -vv

docs:
	install -d /usr/share/man/man1
	install -m 644 docs/man/atomicapp.1 /usr/share/man/man1

install: docs
	python setup.py install

test:
	python -m pytest -vv

image:
	docker build -t $(tag) .

syntax-check:
	flake8 atomicapp

clean:
	python setup.py clean --all
