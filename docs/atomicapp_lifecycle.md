Atomicapp Lifecycle Definition
==============================

`fetch`
-------
Will download and combine artifacts from the target application and any 
dependent applications including sample answers.conf file into a local 
directory for inspection and/or modification. Same for all providers.


`install`
---------
Peform actions to prepare application to run. Performs validation 
of Nulecule as well as some provider specific implementation:

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Run the command embedded in the INSTALL label in the container image. |
| Kubernetes    | Deploy artifacts to Kubernetes with replica count = 0 |
| Openshift     | Deploy artifacts to Openshift with replica count = 0 OR Upload template if artifact is a template. |


`run`
-----
Run an application. Provider specific implementation:

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Run requested containers on local machine. |
| Kubernetes    | Increase replica count from 0 to >0. |
| Openshift     | Increase replica count from 0 to >0 OR Instantiate template. |

`stop` - (opposite of `run`)
----------------------------
Stop an application. Provider specific implementation:

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Stop requested containers on local machine. |
| Kubernetes    | Decrease replica counts to 0. |
| Openshift     | Decrease replica counts to 0. |


`uninstall` - (opposite of `install`)
-------------------------------------
Remove deployment configuration from platform. Provider specific implementation:

| Provider      | Implementation |
| ------------- | -------------- |
| Docker        | Run the command embedded in the UNINSTALL label in the container image. |
| Kubernetes    | Remove artifacts from Kubernetes. |
| Openshift     | Remove artifacts from Openshift. Delete template from openshift. |


`clean` - (opposite of `fetch`)
-------------------------------
Remove artifacts files from local system and clean up directory. Same for all providers.

