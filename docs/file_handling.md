## Fetch

Fetching an Atomic App means to download the metadata files: artifacts and
sample answerfile for an Atomic App. By default, it downloads the metadata
files for the atomicapp to a directory of the form
``/var/lib/atomicapp/<atomic app name>-<uuid>``. If needed,
you can also specify a target directory to download the metadata for the
Atomic App using the ``--destination`` option.

## Developing and Debugging

Image developers may run the root container and point to a Nulecule directory on the local system.

## Directories

* `/var/lib/atomicapp/<atomic app name>-<uuid>`: This is where an Atomic App
    and it's dependencies are fetched when fetching or running the Atomic App,
    unless, a specific destination is specified.
* `/var/lib/atomicapp/<atomic app name>-<uuid>/external`:
    External Atomic Apps, if any, for the given Atomic App are
    fetched into ``external`` directory inside the directory of
    the Atomic App, during, fetching the Atomic App with
    dependencies or running the Atomic App.

## Artifact path

Local path to an artifact file or a directory containing artifact files as its
immediate children.

## Runtime answers file

When running an Atomic App, it asks the users for missing values for
parameters defined in the Atomic App and it's child Atomic Apps. This
aggregated answers data is used to run the Atomic App, and is dumped
to a file: ``answers.conf.gen`` in the Atomic App's directory, to be
used later when stopping the Atomic App.

## Rendered artifact files

Artifact files are rendered with runtime answers data along side the original
artifact files, but with the filenames prefixed with a `.` (dot), to make
them hidden.

