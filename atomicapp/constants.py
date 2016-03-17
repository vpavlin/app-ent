__ATOMICAPPVERSION__ = '0.4.4'
__NULECULESPECVERSION__ = '0.0.2'

EXTERNAL_APP_DIR = "external"
GLOBAL_CONF = "general"
APP_ENT_PATH = "application-entity"
CACHE_DIR = "/var/lib/atomicapp"

PARAMS_KEY = "params"
RESOURCE_KEY = "resource"
INHERIT_KEY = "inherit"
ARTIFACTS_KEY = "artifacts"
ARTIFACTS_FOLDER = "artifacts"
NAME_KEY = "name"
DEFAULTNAME_KEY = "default"
PROVIDER_KEY = "provider"
NAMESPACE_KEY = "namespace"
REQUIREMENTS_KEY = "requirements"

# Nulecule spec terminology vs the function within /providers
REQUIREMENT_FUNCTIONS = {
    "persistentVolume": "persistent_storage"
}

MAIN_FILE = "Nulecule"
ANSWERS_FILE = "answers.conf"
ANSWERS_RUNTIME_FILE = "answers.conf.gen"
ANSWERS_FILE_SAMPLE = "answers.conf.sample"
ANSWERS_FILE_SAMPLE_FORMAT = 'ini'
WORKDIR = ".workdir"
LOCK_FILE = "/run/lock/atomicapp.lock"

LOGGER_DEFAULT = "atomicapp"
LOGGER_COCKPIT = "cockpit"

HOST_DIR = "/host"

DEFAULT_PROVIDER = "kubernetes"
DEFAULT_CONTAINER_NAME = "atomic"
DEFAULT_NAMESPACE = "default"
DEFAULT_ANSWERS = {
    "general": {
        "namespace": DEFAULT_NAMESPACE
    }
}

PROVIDERS = ["docker", "kubernetes", "openshift", "marathon"]
PROVIDER_API_KEY = "providerapi"
ACCESS_TOKEN_KEY = "accesstoken"
PROVIDER_CONFIG_KEY = "providerconfig"
PROVIDER_TLS_VERIFY_KEY = "providertlsverify"
PROVIDER_CA_KEY = "providercafile"

# Persistent Storage Formats
PERSISTENT_STORAGE_FORMAT = ["ReadWriteOnce", "ReadOnlyMany", "ReadWriteMany"]
