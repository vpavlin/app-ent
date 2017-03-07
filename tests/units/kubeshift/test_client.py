import mock
import pytest
from atomicapp.providers.lib.kubeshift.client import Client
from atomicapp.providers.lib.kubeshift.exceptions import KubeClientError

config = {
    "kind": "Config",
    "preferences": {},
    "current-context": "dev",
    "contexts": [
            {
                "name": "dev",
                "context": {
                    "cluster": "dev",
                    "user": "default"
                }
            }
    ],
    "clusters": [
        {
            "cluster": {
                "server": "http://localhost:8080"
            },
            "name": "dev"
        }
    ],
    "apiVersion": "v1",
    "users": [
        {
            "name": "default",
            "user": {
                    "token": "foobar"
            }
        }
    ]
}


class FakeClient():

    def __init__(self, *args):
        pass


@mock.patch("atomicapp.providers.lib.kubeshift.client.KubeKubernetesClient")
def test_client_kubernetes(FakeClient):
    Client(config, "kubernetes")


@mock.patch("atomicapp.providers.lib.kubeshift.client.KubeOpenshiftClient")
def test_client_openshift(FakeClient):
    Client(config, "openshift")


def test_client_load_failure():
    with pytest.raises(KubeClientError):
        Client(config, "foobar")


# TODO
def test_client_create():
    pass


# TODO
def test_client_delete():
    pass


# TODO
def test_client_namespaces():
    pass
