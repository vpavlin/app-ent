# Contributing to Atomic App

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines (not rules) for contributing to Atomic App,
which is hosted in the [Project Atomic Organization](https://github.com/projectatomic) on GitHub.
These are just guidelines, not rules, use your best judgment and feel free to
propose changes to this document in a pull request.

## Submitting Issues

* You can create an issue [here](https://github.com/projectatomic/atomicapp/issues/new), include as many details as possible with your report.
* Include the version of Atomic App you are using, have a look at the docker container image tag.
* Include the behavior you expected and maybe other places you've seen that behavior
* Perform a [cursory search](https://github.com/issues?utf8=%E2%9C%93&q=is%3Aissue+repo%3Aprojectatomic%2Fatomicapp)
  to see if a similar issue has already been submitted

## Developers

First of all, fork the [repository](https://github.com/projectatomic/atomicapp) and clone your github repository:

```shell
$ git clone https://github.com/<your-username>/atomicapp
```

### Install this project for development

Goto cloned repo and Simply run following commands

```shell
$ sudo pip install virtualenvwrapper
$ cd atomicapp
$ make develop
```

Goto the Nuleculized app directory and run

```shell
$ workon atomicapp
$ sudo atomicapp run .
```

### Build
```
docker build -t [TAG] .
```

Just a call to Docker to package up the application and tag the resulting image.

### Install and Run
```
atomicapp [--dry-run] [-a answers.conf] install|run [--recursive] [--update] [--destination DST_PATH] APP|PATH
```

Pulls the application and it's dependencies. If the last argument is
existing path, it looks for `Nulecule` file there instead of pulling anything.

* `--recursive yes|no` Pull whole dependency tree
* `--update` Overwrite any existing files
* `--destination DST_PATH` Unpack the application into given directory instead of current directory
* `APP` Name of the image containing the application (f.e. `vpavlin/wp-app`)
* `PATH` Path to a directory with installed (i.e. result of `atomicapp install ...`) app

Action `run` performs `install` prior its own tasks are executed if `APP` is given. When `run` is selected, providers' code is invoked and containers are deployed.

## Submitting a Pull Request
Before you submit your pull request consider the following guidelines:

* Make your changes in a new git branch:

     ```shell
     git checkout -b bug/my-fix-branch master
     ```

* Create your patch, **including appropriate test cases**. Do not forget to add a copyright notice to your files, pls read along the line 625 of gpl-3.txt
* Please test your changes locally for conformance of coding guidelines with following command

     ```shell
     $ tox
     ```

* Include documentation that either describe a change to a behavior of atomicapp or the changed capability to an end user of atomicapp.
* Commit your changes using **a descriptive commit message**. If you are fixing an issue please include something like 'this closes issue #xyz'.
* Additionally think about implementing a git hook, as flake8 is part of the [travis-ci tests](https://travis-ci.org/projectatomic/atomicapp) it will help you pass the CI tests.

    ```shell
    $ cat .git/hooks/pre-push
    #!/bin/bash

    flake8 -v atomicapp
    ```

* Push your branch to GitHub:

    ```shell
    git push origin bug/my-fix-branch
    ```

* In GitHub, send a pull request to `atomicapp:master`.
* If we suggest changes then:
  * Make the required updates.
  * Rebase your branch and force push to your GitHub repository (this will update your Pull Request):

    ```shell
    git commit --amend
    git rebase master -i
    git push origin bug/my-fix-branch -f
    ```

That's it! Thank you for your contribution!

### Merge Rules

* Include unit or integration tests for the capability you have implemented
* Include documentation for the capability you have implemented
* If you are fixing an issue within Atomic App,
 * include the issue number you are fixing

### After your pull request is merged

After your pull request is merged, you can safely delete your branch and pull the changes
from the upstream repository:

* Delete the remote branch on GitHub either through the GitHub web UI or your local shell as follows:

    ```shell
    git push origin --delete bug/my-fix-branch
    ```

* Check out the master branch:

    ```shell
    git checkout master -f
    ```

* Delete the local branch:

    ```shell
    git branch -D bug/my-fix-branch
    ```

* Update your master with the latest upstream version:

    ```shell
    git pull --ff upstream master
    ```


## Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Reference issues and pull requests liberally

## How to Test

[Functional tests](tests/test_cli.py) and [unit tests](tests/units/) are part
of this repository. We prepared a [Dockerfile](Dockerfile.test) which creates
an image able to run these tests. To build it, run:

```
docker build -t atomicapp-test -f Dockerfile.test .
```

In case you want to test code which is currently in repository, run:

```
docker run -t --rm atomicapp-test
```

To test your changes in code you have two options:

1. rebuild the image every time you save a file
2. add a volume to the `docker run` command as follows

```
docker run -t --rm -v $PWD/atomicapp:/opt/atomicapp/atomicapp atomicapp-test
```

You can use following command to run tests you added:

```
docker run -t --rm -v $PWD/tests/:/opt/atomicapp/tests atomicapp-test
```
