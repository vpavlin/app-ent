all:
	python -m pytest -vv

install:
	python setup.py install

test:
	python -m pytest -vv

image:
	docker build -t $(tag) .

syntax-check:
	flake8 atomicapp

clean:
	python setup.py clean --all

develop:
	source `which virtualenvwrapper.sh`; \
	mkvirtualenv atomicapp; \
	python setup.py develop; \
	echo "alias atomicapp=~/.virtualenvs/atomicapp/bin/atomicapp" >> ~/.virtualenvs/atomicapp/bin/postactivate; \
	echo "alias sudo='sudo '" >> ~/.virtualenvs/atomicapp/bin/postactivate; \
	echo "unalias atomicapp && unalias sudo" >> ~/.virtualenvs/atomicapp/bin/postdeactivate