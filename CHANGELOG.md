## Atomic App 0.6.4 (10-06-2016)

This release of Atomic App includes a large refactor of the "config" class as well as a minor change to our release script.

Features:
  - Config refactor
  - Release script fix
  - Test cases added to the config class

```
Charlie Drage <charlie@charliedrage.com> (1):
      Update release script regex

Ratnadeep Debnath <rtnpro@gmail.com> (3):
      Initial work on refactoring Nulecule config. #524
      Re implememt Config class to be more generic. Fixes #524
      Fixed tests for config refactor.
```

## Atomic App 0.6.3 (08-31-2016)

This release focuses on bug fixes, scripts as well as the Nulecule specification being merged into Atomic App.

Features:
  - The Nulecule spec is now located within the Atomic App repo / project
  - Bug fixes with the `atomicapp genanswers` command
  - Release script added

```
Charlie Drage <charlie@charliedrage.com> (7):
      Remove lifecycle for updated CLI doc
      Merge Nulecule specification into Atomic App
      Formatting error with anymarkup and genanswers
      Openshift to KubeShift conversion and improvements
      Add release script for Atomic App
      Fix typo in openshift.py provider
      Fixes mode argument with --mode=genanswers

Ratnadeep Debnath <rtnpro@gmail.com> (1):
      Use travis CI to run tests from tests/units dir.
```

## Atomic App 0.6.2 (07-27-2016)

This release of Atomic App introduces the new `atomicapp index` command.

We add this command in order to give a quick overview of all available featured and tested Nuleculized applications on [github.com/projectatomic/nulecule-library](https://github.com/projectatomic/nulecule-library). The ability to generate your own list is available as well with the `atomicapp index generate` command.

The main features of this release are:

* Addition of the `atomicapp index` command
* Correct file permissions are now when extracting Nuleculized containers
* OpenShift connection issue bugfix


## `atomicapp index`

This release adds the addition of the `atomicapp index` command. By using the `atomicapp index list` command, Atomic App will retrieve a container containing a valid `index.yml` and output all available Nulecule containers. This index can also be updated by using `atomicapp index update`.


**atomicapp index list**

Outputs the list of available containers located at `~/.atomicapp/index.yml`.

```
▶ atomicapp index list
INFO   :: Atomic App: 0.6.2 - Mode: Index
ID                        VER      PROVIDERS  LOCATION                                             
postgresql-atomicapp      1.0.0    {D,O,K}    docker.io/projectatomic/postgresql-centos7-atomicapp 
flask_redis_nulecule      0.0.1    {D,K}      docker.io/projectatomic/flask-redis-centos7-atomicapp
redis-atomicapp           0.0.1    {D,O,K}    docker.io/projectatomic/redis-centos7-atomicapp      
gocounter                 0.0.1    {D,K}      docker.io/projectatomic/gocounter-scratch-atomicapp  
mariadb-atomicapp         1.0.0    {D,O,K}    docker.io/projectatomic/mariadb-centos7-atomicapp    
helloapache-app           0.0.1    {D,K,M}    docker.io/projectatomic/helloapache                  
mongodb-atomicapp         1.0.0    {D,O,K}    docker.io/projectatomic/mongodb-centos7-atomicapp    
etherpad-app              0.0.1    {D,O,K}    docker.io/projectatomic/etherpad-centos7-atomicapp   
apache-centos7-atomicapp  0.0.1    {D,K,M}    docker.io/projectatomic/apache-centos7-atomicapp     
wordpress-atomicapp       2.0.0    {D,O,K}    docker.io/projectatomic/wordpress-centos7-atomicapp  
skydns-atomicapp          0.0.1    {K}        docker.io/projectatomic/skydns-atomicapp             
guestbookgo-atomicapp     0.0.1    {O,K}      docker.io/projectatomic/guestbookgo-atomicapp        
mariadb-app               0.0.1    {D,K}      docker.io/projectatomic/mariadb-fedora-atomicapp     
gitlab-atomicapp          1.2.0    {D,K}      docker.io/projectatomic/gitlab-centos7-atomicapp 
```

**atomicapp index update**

Updates the `index.yml` file.

```
▶ atomicapp index update
INFO   :: Atomic App: 0.6.2 - Mode: Index
INFO   :: Updating the index list
INFO   :: Pulling latest index image...
INFO   :: Skipping pulling docker image: projectatomic/nulecule-library
INFO   :: Copying files from image projectatomic/nulecule-library:/index.yaml to /home/wikus/.atomicapp/index.yaml
INFO   :: Index updated
```

**atomicapp index generate**

Generates a valid `index.yml` file to use in listing all available containers.

```
▶ atomicapp index generate ./nulecule-library
INFO   :: Atomic App: 0.6.1 - Mode: Index
INFO   :: Generating index.yaml from ./nulecule-library
INFO   :: index.yaml generated
```

```
Abhishek <abhishek@dhcp35-217.lab.eng.blr.redhat.com> (3):
      incorrect_log_level
      Show help when no arguments given.
      raise DockerException for docker commands

Charlie Drage <charlie@charliedrage.com> (7):
      Remove warning in regards to application-entity
      Refactor extracting
      Fixes connecting issues with OpenShift
      Fix coverage
      Modifies asking for parameters to show app name
      When fetching or extracting, set the correct uid + guid
      Add "index" command to Atomic App

Shubham Minglani <shubham@linux.com> (1):
      collect only atomicapp tests
```

## Atomic App 0.6.1 (07-06-2016)

A minor release for Atomic App.

With this release, we merge a few bug fixes in relation to our Kubernetes provider as well as clean up documentation.

Features:
  - Fix inclusive rules issue with Kubernetes
  - Clean up CLI parsing documentation / help command 


```
Charlie Drage <charlie@charliedrage.com>::
      Fix link issue on CLI doc within start guide
      Clean up parsing
      False positive error out on docker pull

Khris Richardson <khris.richardson@intel.com>:
      more inclusive rules for adding es
```

## Atomic App 0.6.0 (06-14-2016)

A major release of Atomic App, we incorporate major changes to the **kubernetes** provider. With this release we replace the usage of kubectl with the *requests* Python library and the Kubernetes HTTP API end-point. This change results in faster deployment, smaller image sizes and detailed error messages.

The main features of this release are:
  - Kubectl to API conversion for the Kubernetes provider
  - Removal of ASCII art

```
Charlie Drage <charlie@charliedrage.com> (3):
      Ignore .swn vim temp files
      Remove ASCII art
      Add a new 'library' for k8s/openshift providers.

Khris Richardson <khris.richardson@intel.com> (2):
      add support for api-groups
      add precision to resource membership test
```

## Atomic App 0.5.2 (05-24-2016)

This release of Atomic App we include binary generation, a logging refactor/clean-up as well as a minor code refactor to the main Nulecule codebase.

The main features are:
  - Add support for generating a static binary of Atomic App
  - Logging clean-up
  - README.md removed from `atomicapp init` generation
  - Removal of dynamic module/class loading from providers in favour of static

```
Charlie Drage <charlie@charliedrage.com>:
      Ignore vim .swo files
      Change provider-config warning to debug
      Remove README.MD from init
      Makes Makefile faster using .PHONY && add default python location
      Modify TravisCI for updated Makefile
      Removes loading via .py files
      Hide container id output on container creation
      Change dir of /external to /nulecule/external
      Add binary generation
      Update to a cleaner logging output.
      Logging formatting

Suraj Deshmukh <surajssd009005@gmail.com>:
      Added elif to consecutive exclusive if statements
      Use filter to search in kubeconfig.py
      Now logs can show path to file under root atomicapp folder
      Updated the inContainer function doc string
      Removed unused function update from utils.py
      Replaced a for loop that initialized a dict
```

## Atomic App 0.5.1 (04-26-2016)

This is a minor release of Atomic App where we refactor, fix code bugs as well as deprecate an old feature. Due to the numerous issues of locking as well as the deprectation of the `lockfile` library we have remove the locking mechanism from Atomic App.

The main features of this release are:

  - The deprecation of locking
  - `atomicapp init` code and UI clean-up
  - Documentation updates
  - inContainer() function bug fix for Docker 1.10+

```
Charlie Drage <charlie@charliedrage.com>:
      Add Marathon to index
      Update README.md with correct installation instructions.
      Remove dockerenv and dockerinit check
      Remove locking from Atomic App

Dusty Mabe <dusty@dustymabe.com>:
      init: remove unnecessary message to the user
      init: remove number of return variables from NuleculeManager.init()
      init: add logic to properly cleanup tmp dir
      init: break a few long lines into shorter ones

Shubham Minglani <shubham@linux.com>:
      fix typo

Suraj Deshmukh <surajssd009005@gmail.com>:
      Moved a constant from openshift.py to constants.py
      Abstracted the way we get absolute path
```

## Atomic App 0.5.0 (04-12-2016)

This is a major release of Atomic App where we introduce a new CLI command as well as the renaming of multiple provider configuration parameters.

The main features of this release are:
  
  - Introduction of the `atomicapp init` CLI command
  - Renaming of provider configuration related parameters
  - --provider-auth added as a CLI command

Other:

  - Updated legal information
  - Bug fix on persistent storage initialization
  - Utility method to gather sudo user path and information
  - Improved detection if we're inside a Docker container
  - Improved readility on provider failed exceptions
  - docker inspect bugfix

## Atomic App Initialization

We've included support for initializing a basic Atomic App via the `atomicapp init` command. This creates a basic example that can be used on __Docker__ and __Kubernetes__ providers based on the [centos/httpd](https://hub.docker.com/r/centos/httpd/) docker image.

```bash
▶ atomicapp init helloworld
[INFO] - main.py - Action/Mode Selected is: init

Atomic App: helloworld initialized at ./helloworld

▶ vim ./helloworld/Nulecule # Make changes to the Nulecule file

▶ atomicapp run ./helloworld
[INFO] - main.py - Action/Mode Selected is: run
[INFO] - base.py - Provider not specified, using default provider - kubernetes
[WARNING] - plugin.py - Configuration option 'provider-config' not found
[WARNING] - plugin.py - Configuration option 'provider-config' not found
[INFO] - kubernetes.py - Using namespace default
[INFO] - kubernetes.py - trying kubectl at /usr/bin/kubectl
[INFO] - kubernetes.py - trying kubectl at /usr/local/bin/kubectl
[INFO] - kubernetes.py - found kubectl at /usr/local/bin/kubectl
[INFO] - kubernetes.py - Deploying to Kubernetes

Your application resides in ./helloworld
Please use this directory for managing your application

```

## New provider configuration parameter names

We've renamed the provider-specific parameters for better clarity by adding dashes in-between 'provider' and the specified function.

Major changes include the renaming of __accesstoken__ to __provider-auth__.

```
providerapi --> provider-api
accesstoken --> provider-auth
providertlsverify --> provider-tlsverify
providercafile --> provider-cafile
```

```ini
[general]
provider = openshift
namespace = mynamespace
provider-api = https://127.0.0.1:8443
provider-auth = sadfasdfasfasfdasfasfasdfsafasfd
provider-tlsverify = True
provider-cafile = /etc/myca/ca.pem
```

```sh
atomicapp run projectatomic/etherpad-centos7-atomicapp --provider openshift --provider-tlsverify False --provider-auth foo --provider-api "https://localhost:8443"
```

```
Charlie Drage <charlie@charliedrage.com>:
      Add more legal information
      Update year
      Requirements should retrieve from Nulecule object not graph
      Warn not error on missing requirement
      Util to gather what user is running Atomic App and which home dir it should use
      Check to see if it's a Docker container
      Update Dockerfile.pkgs testing repos
      Dashes added to CLI commands to distinguish provider config data
      Fix test params with the new dashes
      Add provider-auth as a CLI command and convert ACCESSTOKEN to provider-auth
      Modify accesstoken tests to provider-auth
      Change constant ACCESS_TOKEN_KEY to PROVIDER_AUTH_KEY
      Modify documentation to reflect changes in params
      Remove /host from provider config example path

Dusty Mabe <dusty@dustymabe.com>:
      init: modify docker template to publish to host port 80

Ratnadeep Debnath <rtnpro@gmail.com>:
      Added 'init' command to initialize a new atomic app.
      Make destination optional atomicapp init command
      Ask user if destination is not empty when initializting atomic app.
      Do not acquire lock for initializing atomicapp.
      Set default action as 'Y' when atomicapp init asks to clean dest directory.
      Include nulecule template files in package data.
      Add k8s service for initialized app.
      Moved Nulecule template files to external dir.
      Don't hard code atomicapp/nulecule versions in atomic app template.
      Show status message on atomicapp init run.
      Added doc strings for atomicapp init method.

Shubham Minglani <shubham@linux.com>:
      Handle ProviderFailedException, fix #627
      add pass for improved readability
      replace inspect with ps, fix #672

Suraj Deshmukh <surajssd009005@gmail.com>:
      Added OrderedDict so as to deploy application in given order
```

## Atomic App 0.4.5 (03-29-2016)

This is a minor release of Atomic App where we make some changes to the UI output as well as fix a few provider-specific bugs.

The main features of this release are:

  - Cleaner logging output
  - More prominent output when Atomic App asks for a missing answers variable
  - Multi-line artifact support for the Docker provider

Other:

  - Update documentation on cli comparison
  - Move kubeconfig parsing to a separate class
  - Refactor cli exceptions code

```
Charlie Drage <charlie@charliedrage.com>:
      Convert to epoch time
      Update docs / more clarity on cli comparison
      Change asking format
      Move kubeconfig parsing to a separate file
      Change kubeconfig testing name and move into a separate file
      Add weekly meeting information

Preeti Chandrashekar <preetipagad@gmail.com>:
      Minor edits to atomicapp_lifecycle.md

Shubham Minglani <shubham@linux.com>:
      handle docker error, raise instead of print, fix #570
      refactor exceptions, fix #621, fix #622

Suraj Deshmukh <surajssd009005@gmail.com>:
      Docker-run file with multi-line command supported
```

## Atomic App 0.4.4 (03-15-2016)

This release includes a major update to our documentation as well as the user experience when deploying an Atomic App.

The main features are:

  - Major update to documentation
  - Cleaner logging output
  - Error-out validation on JSON/YAML

UI:

  - Fix --version output on CLI
  - Handle docker exception errors
  - Inform on wrong provider name provided within answers.conf

Other:

  - Fix requirements on 'make test'

For a full list of changes between 0.4.4 and 0.4.3 please see the git shortlog below!

```
Charlie Drage <charlie@charliedrage.com> (10):
      Doc for current functions implemented by spec
      Fix minor markdown error in spec_coverage
      Major update to README and documentation
      Error cleanly on missing Nulecule or invalid formatted Nulecule
      Multiple problems with issuestats.com
      Add tests for missing Nulecule or wrongly formatted file for missing
      Change from ReadWrite to ReadWriteOnce in persistent storage tests
      Add Persistent Storage validation on ReadWriteOnce, etc.
      Remove time from default output
      Convert to epoch time

Dusty Mabe <dusty@dustymabe.com> (2):
      docs: fix broken link
      logging: fix duplicated log messages

Preeti Chandrashekar <preetipagad@gmail.com> (1):
      Minor edits to atomicapp_lifecycle.md

Shubham Minglani <shubham@linux.com> (2):
      Handle docker pull exception, improve #441, fix #568
      fix --version output, fix #481

Suraj Deshmukh <surajssd009005@gmail.com> (5):
      Install requirements before make test
      Wrong provider name in answers.conf, exits AtomicApp with readable error
      Typo in providers docs
      Instruction to skip travis CI
      Inform user when provider not specified
```

## Atomic App 0.4.3 (03-01-2016)

You'll now see pretty colors with logging / output!

With this release, we've refactored our logging formatter making it easier to decipher between information, debug, warning and errors.

You are now able to specify what logging format you'd like to output via the command line:

```
  --logtype {cockpit,color,nocolor,none}
                        Override the default logging output. The options are:
                        nocolor: we will only log to stdout; color: log to
                        stdout with color; cockpit: used with cockpit
                        integration; none: atomicapp will disable any logging.
                        If nothing is set and logging to file then 'nocolor'
                        by default. If nothing is set and logging to tty then
                        'color' by default.
```

The main features are:

  - A new logging mechanism that outputs color-coordinated logging messages
  - Added CLI commands for color, nocolor, cockpit and 'none' output

UI:

  - Failure on finding no artifacts

Other:

  - Readme updates / typo fixes

```
Charlie Drage <charlie@charliedrage.com> (3):
      Fail if unable to find artifact
      Change order of getting context
      Update readme

Dusty Mabe <dusty@dustymabe.com> (4):
      logging: Add in Atomic App Logging class
      logging: add cockpit logging output
      tests: fix test to look for output in stdout vs stderr

Shubham Minglani <shubham@linux.com> (1):
      Remove extra whitespaces from logging output.
```

## Atomic App 0.4.2 (02-18-2016)

As we start to get closer to a 1.0.0 release, we continue to focus on tests and user interaction. This weeks release focus on both as well as a minor feature.

The main features of this release are:
  - Meta data is now an optional requirement when building

UI:
  - Relative path support for provider ocnfig data
  - Raise on missing artifact or docker image failure

Bug fixes:
  - Label fixes against `atomic` cli master branch. We now pass our current working directory as a variable

Misc:
  - Remove uneeded test suite files (Dockerfiles, licenses, etc.)
  - All references to `install` have now been removed  within the code in favour of `fetch`


```
Charlie Drage <charlie@charliedrage.com>:
      Fail on missing artifacts within Nulecule file
      Add tests for failure of finding Nulecule artifacts
      Remove instances of install verb to fetch
      Remove unneeded files in test examples dirs
      Fix xpathing tests on missing files

Dusty Mabe <dusty@dustymabe.com>:
      providerconfig: support someone specifying a relative path
      cli: Print helpful error if no app_spec provided.
      Do not use artifacts dir to select provider.
      tests: update cli test
      labels: update run labels to no longer use backticks
      labels: no longer default to verbose output
      Add Tomas to MAINTAINERS
      Adds Atomicapp lifecycle definition. Closes #290
      nulecule: error if no artifacts in spec for inherited provider

Ratnadeep Debnath <rtnpro@gmail.com>:
      Update file handling doc. Fixes #285

Suraj Deshmukh <surajssd009005@gmail.com>:
      This makes `metadata` an optional argument
```

## Atomic App 0.4.1 (02-02-2016)

0.4.1 is a minor bug fix release.

```
Charlie Drage <charlie@charliedrage.com>:
      Remove roadmap in favour of wiki
      Remove symbolic link from Dockerfile

Dusty Mabe <dusty@dustymabe.com>:
      cli: Fix bug with atomic cli + genanswers
      openshift: Fix a few spelling mistakes.
      openshift: clean up scale function log message.
      If not given, don't populate namespace in answers.conf.gen.

Tomas Kral <tkral@redhat.com>:
      marathon: do not convert types when parsing json artifact
```

## Atomic App 0.4.0 (01-20-2016)

With this release we bump our version to 0.4.0 to coincide with our BETA-4 release as well as the change to our "install" verb.

The most significant new features are:
  - Renaming install to fetch
  - Allowing users to pass an answers file as a URL

For an extended list of changes, please see the git shortlog below.

```
Charlie Drage <charlie@charliedrage.com>:
      Change undeploy/deploy functions to run/stop
      Rename install to fetch
      Remove mention of uninstall function
      Fix test names
      Remove install label from Dockerfiles

Dusty Mabe <dusty@dustymabe.com>:
      docker: fix stopping for artifacts with '--name='
      cli: allow specifying target dir during atomic run
      cli: add --namespace option to cli
      Allow users to provide answers file as url.
      Create destination app_path dir if it doesn't exist yet.

Ratnadeep Debnath <rtnpro@gmail.com>:
      Support specifying default provider in Nulecule spec file. Fixes #378

Tomas Kral <tkral@redhat.com>:
      openshift provider: safer stop
      openshift provider: fix typos, add more explanation
      openshift provider: remove acronyms from comments
```

## Atomic App 0.3.1 (01-14-2016)

This release introduces some significant features to Atomic App as well as our first release since 0.3.0.

The outmost features include:
 - Persistent storage
 - HTTPS (TLS) verification and support for OpenShift
 - OpenShift stop support
 - Nested Nulecule application support for OpenShift.

For an extended list of changes, please see the git shortlog below.

```
Charlie Drage <charlie@charliedrage.com> (9):
      Merge pull request #457 from rtnpro/remove-docker-containers-on-stop
      Merge pull request #392 from kadel/marathon-provider
      0.3.0 Release
      Add persistent storage core
      Add Kubernetes persistent storage functionality
      Test requirements.py persistent storage
      Warn if no persistent volumes exist to claim
      Merge pull request #485 from kadel/issue484
      Stop Docker containers more gracefully

Dharmit Shah <shahdharmit@gmail.com> (10):
      Common place for list of Providers
      PEP8
      Adds Marathon provider data for `helloapache` example
      Nulecule for `helloapache` app now contains information about marathon artifacts
      CLI tests for marathon provider using `helloapache` atomic app
      Information about where to specify `providerapi` for Marathon provider
      Changes suggested in PR review
      Added try..except block for request
      Catch `AnyMarkupError` instead of `Exception` for invalid artifacts
      Use `ProviderFailedException` instead of `sys.exit`

Dusty Mabe <dusty@dustymabe.com> (40):
      Merge pull request #463 from kadel/make_rest_request
      Revert "Remove container on stopping on Docker provider. Fixes #389"
      Merge pull request #464 from projectatomic/revert-457-remove-docker-containers-on-stop
      Allow user to specify both source and destination as directories.
      Merge pull request #466 from dustymabe/dusty-src-dest
      cli: import argparse rather than specific items
      cli: Restructure argument parsers.
      cli: Add global options help text to toplevel parser.
      cli: Add in a --mode cli switch to select action.
      Merge pull request #468 from dustymabe/dusty-add-mode
      Fix yaml choice for --answers-format.
      utils: add rm_dir() function.
      Add --destination=none. Files don't persist after run.
      Update native openshift code to use dest=none.
      Add 'genanswers' action to generate answers.conf in cwd.
      Merge pull request #469 from dustymabe/dusty-add-genanswers-new
      cli: Fix the name of the genanswers subparser.
      cli: Clarify some of the app_spec help texts.
      Merge pull request #465 from projectatomic/openshift-unittests
      Merge pull request #473 from kadel/openshift-AttributeError
      Merge pull request #472 from dustymabe/dusty-update-stop-app-spec-help
      Merge pull request #474 from kadel/openshift-stop
      Merge pull request #460 from cdrage/persistent-storage
      Merge pull request #488 from cdrage/stop-more-gracefully
      cli: Add genanswers as a choice for --mode.
      Include port information in detected openshift api endpoint.
      Merge pull request #490 from dustymabe/allow-genanswers-for-mode
      Merge pull request #491 from dustymabe/dusty-add-port-to-providerapi
      Merge pull request #480 from kadel/openshift-ssl
      Merge pull request #489 from projectatomic/oc-new-app-with-nested-nulecules
      cli: allow overriding cmdline from env vars
      Merge pull request #504 from dustymabe/dusty-cli-overrides
      Add support for embedding answers file in application.
      Merge pull request #505 from dustymabe/dusty-allow-embedded-answers-file
      Add in cli options for some provider* answers.
      Merge pull request #506 from dustymabe/dusty-add-cli-overrides
      native openshift: move detection of provider information to provider.
      native openshift: Add in ssl verification.
      native openshift: respect it if user set tls_verify to False.
      Merge pull request #503 from dustymabe/dusty-ssl-in-native-openshift

Ratnadeep Debnath <rtnpro@gmail.com> (13):
      Remove container on stopping on Docker provider. Fixes #389
      Refactored openshift provider for testing. #459
      Refactor openshift provider: Move interaction with remote API from OpenShiftProvider
      Added tests for OpenshiftProvider.deploy.
      Refactor openshift _process_artifacts
      Added tests for openshift _process_artifact_data.
      Added tests for openshift to parse kube config
      Added docs for openshift provider unittests.
      Unpack image using Openshift API on Openshift provider.
      Fixed unittests for Nulecule and NuleculeComponent
      Fix using ssl connection options in websocket connection to Openshift.
      Wait for Openshift pod to run, before extracting content.
      Delete openshift pod irrespective of successful or failed extraction.

Tomas Kral <tkral@redhat.com> (24):
      move openshift._make_request() to Utils.make_rest_request()
      first draft of marathon provider
      change providerurl to providerapi
      fix dry-run for marathon
      empty marathon_artifacts array in init()
      marathon fixes
      add Marathon to list of supported providers
      raise exeption on AnyMarkupError in Marathon provider
      mention Mesos with Marathon in docs
      use Utils.make_rest_request in Marathon provider
      add more docs to functions in Marathon provider
      fix AttributeError OpenshiftClient.ssl_verify
      Implement stop for OpenShift provider.
      openshift provider: fix typos, add comments
      openshift provider: when deleting use selector from RC to get PODs
      openshift provider: update comments
      openshift provider: add option for skiping tls verification
      fix typos and flake8 errors
      openshift provider: doc of providertlsverify and providercafile
      openshift provider: break ssl_verify to provider_ca and provider_tls_verify
      openshift provider: use _requests_tls_verify() in undeploy
      openshift provider: check that required options are !None
      openshift provider: test connection to OpenShift     print nicer error message when invalid ttl/ssl certificate
      openshift provider: translate CA path to host path and check if exists
```

## Atomic App 0.3.0 (12-16-2015)

This release introduces a new provider (Mesos) as well as a major refactor of the OpenShift provider.

For an extended list of changes please see the git log below of the changes between 0.2.3 and 0.3.0

```
Aaron Weitekamp <aweiteka@redhat.com>:
      Update OpenShift docs to describe how native mode works

Charlie Drage <charlie@charliedrage.com>:
      Adds some more information when running --dry-run
      Default to a reasonable provider in /artifacts
      Minor fix in nulecule testing and flake8
      Add clean to Makefile

Dharmit Shah <shahdharmit@gmail.com>:
      Common place for list of Providers
      PEP8
      Adds Marathon provider data for `helloapache` example
      Nulecule for `helloapache` app now contains information about marathon artifacts
      CLI tests for marathon provider using `helloapache` atomic app
      Information about where to specify `providerapi` for Marathon provider
      Changes suggested in PR review
      Added try..except block for request
      Catch `AnyMarkupError` instead of `Exception` for invalid artifacts
      Use `ProviderFailedException` instead of `sys.exit`

Dusty Mabe <dusty@dustymabe.com>:
      Support for options anywhere on command line.
      Adds dockerignore file.
      Removes VOLUME from Dockerfiles.
      Update working dir to have broader permissions.
      Provider documentation update/re-organization.
      utils: adds function to detect if running in openshift pod.
      Act accordingly if run via `oc new-app`.
      Allow non-root in openshift pod to grab lockfile.
      Revert "Remove container on stopping on Docker provider. Fixes #389"

Ratnadeep Debnath <rtnpro@gmail.com>:
      Move global cli options to sub command level.
      Remove container on stopping on Docker provider. Fixes #389

Tomas Kral <tkral@redhat.com>:
      first attempt to use OpenShift api instead of oc command
      openshift - add pods and persistentvolumeclaims
      add requests as dependency
      openshift provider - fix duplicate deployment with composite apps
      openshift provider cleanup and working undeploy
      openshift-api refactoring
      openshift-api add template processing
      openshift-api keep types specified in json
      openshift-api fix issues raised in code review #420
      openshift-api validate artifact in _process_artifacts
      openshift-api add providerconfig support
      openshift-api fail if providerconfig and answers.conf are in conflict
      openshift-api handle timeouts when communicating with remote api
      openshift-api update docs
      openshift-api remove undeploy() for now as it is not working properly
      move openshift._make_request() to Utils.make_rest_request()
      first draft of marathon provider
      change providerurl to providerapi
      fix dry-run for marathon
      empty marathon_artifacts array in init()
      marathon fixes
      add Marathon to list of supported providers
      raise exeption on AnyMarkupError in Marathon provider
      mention Mesos with Marathon in docs
      use Utils.make_rest_request in Marathon provider
      add more docs to functions in Marathon provider
```

## Atomic App 0.2.3 (12-02-2015)

This release fixes numerous bugs as well as introduces some organizational changes to our main code-base.

Please see below for a summary of commits between 0.2.2 and 0.2.3

```
Charlie Drage <charlie@charliedrage.com>:
      Fix constants in nulecule dir
      Clean up CLI answers-format option
      Change tmp dir location
      Update README dependencies
      fix readme.md link blob
      Lib.py should load plugins in init
      Add roadmap doc
      Fix tests not removing answers.conf.gen
      Update requirements.md

Dusty Mabe <dusty@dustymabe.com>:
      Removes RHEL7 dockerfile.
      Dockerfiles: remove unnecessary line from Dockerfiles.
      Moves Dockerfiles to Dockerfiles.git/ directory.
      Adds Dockerfiles.pkgs/ directory.
      Updates fedora git Dockerfile to use Fedora 23.
      Updates git Dockerfiles to use env var for version.
      Updates git Dockerfiles to add reqs to the workdir location.
      Don't run container to extract files.

Swapnil Kulkarni <me@coolsvap.net>:
      Updated minor typos
```

## Atomic App 0.2.2 (11-17-2015)

This is our first release since our major refactor in 0.2.1.

This release fixes numerous bugs as well as introduces some refactoring to our Dockerfile's and how we handle dependencies.

Please see below for a summary of commits from 0.2.1 to 0.2.2.

```
Charlie Drage <charlie@charliedrage.com> (1):
      raise exception when running run --dry-run

Dusty Mabe <dusty@dustymabe.com> (7):
      Adds more checking for docker client/server sync issues.
      utils: Adds in AtomicAppUtilsException class.
      Reworks answers file processing.
      Removes dryrun from _write_answers() function.
      Remove specific versions from required libraries.
      Reworks testing Dockerfile and test requirements.
      Reworks Dockerfiles.

Ratnadeep Debnath <rtnpro@gmail.com> (4):
      Added docs for provider and adding a new provider
      Merge config sets value for key if it or it's value is missing at source.
      Fixes in README for provider:
      Removing docker-compose provider from supported providers list.

Subin M <subin@apache.org> (1):
      remove unused method printAnswerFile

Tomas Kral <tkral@redhat.com> (1):
      add  PROVIDERS constant
```

## Atomic App 0.2.1 (11-04-2015)

This is a major release for Atomic App that refactors most of the base code as well as adds numerous features.

  * Complete refactor of the Atomic App core codebase
  * JSON Pointer xpathing for artifacts
  * Integration of unpacking to /var/lib/atomicapp rather than `cwd`
  * Numerous bug fixes && improvements to integration tests


Please see the `git shortlog` summary below for all commits since the previous release.

```
Charlie Drage <charlie@charliedrage.com> (8):
      Remove dotfiles from tests
      Sync requirements with master. Fixes lockfile issue.
      add xpathing

Dusty Mabe <dusty@dustymabe.com> (15):
      Don't unpack files to cwd
      Enables running atomicapp from within a container again.
      Implement a few comments from code review #356.
      Remove Aaron from MAINTAINERS upon his request.
      Add Ratnadeep to MAINTAINERS :)
      Adds preferred email for Dusty to MAINTAINERS.
      Adds nice error message for Docker client/server out of sync. Closes #174
      Syncs up run labels in Dockerfiles.
      Fixes run label in Dockerfiles so that atomic run <image> works.

Jeroen van Meeuwen (Kolab Systems) <vanmeeuwen@kolabsys.com> (1):
      Use epel-release rather than echo'ing .repo config files

Ratnadeep Debnath <rtnpro@gmail.com> (19):
      Updated docs for file handling for artifact path. #143
      Added note on not supporting nested artifact dir. #143
      Added unittests for Nulecule class.
      Added tests for NuleculeComponent load
      Added tests for NuleculeComponent run.
      Added tests for stopping NuleculeComponent.
      Added tests for NuleculeComponent load_config.
      Added tests for loading external app in NuleculeComponent.
      Added tests for accessing components of a nulecule component.
      In NuleculeComponent, pass 'dryrun' param when calling render of external Nulecule.
      Added tests for rendering a NuleculeComponent
      Added tests for retrieving artifact paths for a NuleculeComponent.
      Added tests for rendering an artifact in NuleculeComponent.
      Reorganize and group code in each testcase for atomicapp/nulecule into
      Bugfix in merging config and updated tests for the same
      Fix unittest for Nulecule load config.
      Fix mocking 'open' in nulecule/base.py.
      Fixed test for rendering artifact.
      Fixed test for rendering local artifact for provider.

Tomas Kral <tkral@redhat.com> (1):
      do not create symlink if source doesn't exist
```

## Atomic App 0.1.12 (10-22-2015)

We have fixed many bugs as well as implemented more enhancements to the Atomic App life cycle with this release. 

Please see below for a summary of commits for the 0.1.12 release.

```
Aaron Weitekamp <aweiteka@redhat.com> (2):
      Add openshift LABELs
      Add OpenShift LABEL information

Charlie Drage <charlie@charliedrage.com> (10):
      update testing
      dup code
      add two new cool maintainers!
      fix artifact bug
      added makefile
      update travis
      add requirement doc
      docker stop terminology fix

Christoph Görn <goern@redhat.com> (13):
      add some issuestats.com stats
      prepared Atomic App 0.1.11 release
      added merge rules

Dusty Mabe <dusty@dustymabe.com> (4):
      Fixes handling of directory for answers argument.
      Reverts "artifact logic bugfix". Fixes #306
      Fixes broken builds bc of lockfile dependency.

Subin M <subin@apache.org> (1):
      add new method find_executable_binary

Swapnil Kulkarni <me@coolsvap.net> (1):
      Small fix for pep8 error

Václav Pavlín <vaclav.pavlin@gmail.com> (5):
      Generate provider config for kubernetes if it does not exist
      Do not use sudo in Docker provider
      Use DEFAULT_PROVIDER_CONFIG in exception message
      Mention config file generation in Kubes provider descripion
      Fix bad indentation issue
```

# Atomic App Base Container Image

Welcome to Atomic App, this is the reference implementation of the [Container
Application Specification](http://www.projectatomic.io/nulecule/spec/0.0.2/index.html) (aka the Nulecule Specification)

## Atomic App 0.1.11 (2015-Sept-23)

This is a hotfix to 0.1.10 and removed a bug we had in [Missing config file error (~/.kube/config) in 0.1.10](https://github.com/projectatomic/atomicapp/issues/280).

Author: Václav Pavlín <vaclav.pavlin@gmail.com>
 * Do not use sudo in Docker provider, Fixes #281

 * Generate provider config for kubernetes if it does not exist

    There is new unimplemented method in Plugin - generateConfigFile.
    This method is invoked in case a provider calls checkConfigFile
    and the file does not exist. If provider does not implement
    this method, error about missing configuration file will
    be printed out. Config file will be generated and used if the method
    is implemented.  
    Currently, it is implemented only by Kubernetes provider.
    Fixes #280

Author: Charlie Drage <charlie@charliedrage.com>

 * fix openshift import warning

## Atomic App 0.1.10 (2015-Sept-21)

With this releasewe have fixed many bugs and implemented many enhancements, please see the [Atomic App Issue tracker](https://github.com/projectatomic/atomicapp/issues/) for the past.

A summary of the major new features is given below.

Author: Charlie Drage <charlie@charliedrage.com>

 * More unit testing / restructure
 * undeploy added to docker provider
 * dont ask for missing artifacts if stopping
 * debian dockerfile support

Author: Ratnadeep Debnath <rtnpro@gmail.com>

 * Convert global params in Nulecule file to `Dict` rather than `List`, fixed #276

Author: Václav Pavlín <vaclav.pavlin@gmail.com>

 * Add `providerconfig` option to fix #266
 * Add Dockerfile for running tests, add How-to-test to CONTRIBUTION.md

Author: Navid Shaikh <nshaikh@redhat.com>
 * Add the right nodePort from allowed port range, reference <https://github.com/kubernetes/kubernetes/blob/master/docs/user-guide/services.md#type-nodeport>
 * Add tests for fix of issue #212
 * Fixes processing multiple k8s artifacts resources
      - Nulecule multiple resource artifacts defined per kind of resource can now be
      processed without overriding earlier artifacts
      - Modifies the methods names as per <https://www.python.org/dev/peps/pep-0008/#method-names-and-instance-variables>
      - Alters order of imports as per <https://www.python.org/dev/peps/pep-0008/#imports>
      - Adds docstring to methods
 * Adds support for resizing replicas if using kube v1 APIs   
      This patch adds provision for lookup of resource identity based on the API
      version under processing. Presently support for v1, v1beta3 and v1beta1 APIs
      are included.

Author: Aaron Weitekamp <aweiteka@redhat.com>

 * Fix typo in docs/cli.md
 * Add provider documentation
 * Add --provider option
    The --provider option is constrained to supported providers.
    Providers can be specified in answers.conf. If --provider opt
    is specified it will be overridden. Otherwise the default provider
    is used.

Author: Swapnil Kulkarni <me@coolsvap.net>

* Update tox.ini to execute the pep8 tests
    Currently if i do tox -e pep8
    - it does not run
    - fails to create the test env
    Updated following,
    - tox.ini to include testenv
    Added test-requirements for flake8


## Atomic App 0.1.3 (2015-Aug-17)

This is a hotfix to 0.1.2 and removed a bug we had in [all LABELs of the Dockerfiles](https://github.com/projectatomic/atomicapp/issues/217).


## Atomic App 0.1.2

With this release we have fixed many bugs and implemented many enhancements. To follow
the development in details, please have a look at the [Atomic App Issue tracker](https://github.com/projectatomic/atomicapp/issues/).

This release contains the changes support the deployment of Atomic Apps via [Cockpit web UI](http://cockpit-project.org/).

Starting with 0.1.2 a new LABEL has been added to the docker container image: `io.projectatomic.nulecule.atomicappversion` so that
an external entity can figure out what version of atomicapp is provided by that container image.

A short overview of the major new features is given below.

Author: Subin M <subin@apache.org>

 * add LABEL for atomicapp version to Atomic App Base Container Image

Author: Václav Pavlín <vaclav.pavlin@gmail.com>

 * Create a lock file and fail if it's already locked to prevent concurrent Atomic Apps running

 * Merge pull request #206 from goern/feature/travis-pep8
   [trivial] Feature/travis pep8

 * Merge pull request #169 from sub-mod/cockpit-integration, see https://github.com/cockpit-project/cockpit/pull/2474

 * Add dry-run checks to install

Author: Daniel Veillard <veillard@redhat.com>

 *  Fix a logic bug -  if the id is not found the exception won't be raised by the expected
    code for it but ny the access to the dict in the message before it

Author: Aaron Weitekamp <aweiteka@redhat.com>

 *  Update openshift provider command

 *  OpenShift is now using 'oc', formerly 'osc'.
    This updates the CLI string and also adds support
    for non-root usage. When non-root the oc symlink
    is broken inside the container. In this case we
    create a symlink inside the container.

Author: Christoph Görn <goern@redhat.com>

 * replaces GNU AGPL by GNU LGPL

 *  initial version of python unittest and coveralls based testing
    I removed shell based tests, as they are replaced by python based tests.

 *  using pytest and coverage, converted to a TestSuite
    added an sys.exit() to cli.main.run(), as a CLI should return something.

Author: Ian McLeod <imcleod@redhat.com>

 *  Initial drop of tests for Travis CI

    These two tests take advantage of the --dry-run option as well as the caching of
    previously extracted Docker image content.  If any element of this caching
    behavior is changed, these test will likely need to be recreated.

    The two tests Nulecules are borrowed from the nulecule spec examples here:

    https://github.com/projectatomic/nulecule/tree/master/examples

    I created this test content by doing a dry run on a system actually running
    Docker, then extracting the "external" directory.
