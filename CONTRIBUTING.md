# Contributing to Atomic App (atomicapp)

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

## Submitting a Pull Request
Before you submit your pull request consider the following guidelines:

* Make your changes in a new git branch:

     ```shell
     git checkout -b bug/my-fix-branch master
     ```

* Create your patch, **including appropriate test cases**.
* Commit your changes using a descriptive commit message.
* Push your branch to GitHub:

    ```shell
    git push origin bug/my-fix-branch
    ```

* In GitHub, send a pull request to `atomicapp:master`.
* If we suggest changes then:
  * Make the required updates.
  * Rebase your branch and force push to your GitHub repository (this will update your Pull Request):

    ```shell
    git rebase master -i
    git push origin bug/my-fix-branch -f
    ```

That's it! Thank you for your contribution!

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
* Use the imperative mood ("Move cursor to..." not "Moves cursor to..."):wq
* Reference issues and pull requests liberally
