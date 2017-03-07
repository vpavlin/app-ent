import mock
from atomicapp.providers.lib.kubeshift.kubernetes import KubeKubernetesClient

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

    def test_connection(self, *args):
        pass

    def get_resources(self, *args):
        return ['Pod', 'pod', 'pods']

    def get_groups(self, *args):
        return {}

    def request(self, method, url, data=None):
        return None, 200

    @property
    def cluster(self):
        return {'server': 'https://foobar'}


@mock.patch("atomicapp.providers.lib.kubeshift.kubernetes.KubeBase")
def test_create(mock_class):
    # Mock the API class
    mock_class.return_value = FakeClient()
    mock_class.kind_to_resource_name.return_value = 'Pod'

    k8s_object = {"apiVersion": "v1", "kind": "Pod", "metadata": {"labels": {"app": "helloapache"}, "name": "helloapache"}, "spec": {
        "containers": [{"image": "$image", "name": "helloapache", "ports": [{"containerPort": 80, "hostPort": 80, "protocol": "TCP"}]}]}}

    a = KubeKubernetesClient(config)
    a.create(k8s_object, "foobar")


@mock.patch("atomicapp.providers.lib.kubeshift.kubernetes.KubeBase")
def test_delete(mock_class):
    # Mock the API class
    mock_class.return_value = FakeClient()
    mock_class.kind_to_resource_name.return_value = 'Pod'

    k8s_object = {"apiVersion": "v1", "kind": "Pod", "metadata": {"labels": {"app": "helloapache"}, "name": "helloapache"}, "spec": {
        "containers": [{"image": "$image", "name": "helloapache", "ports": [{"containerPort": 80, "hostPort": 80, "protocol": "TCP"}]}]}}

    a = KubeKubernetesClient(config)
    a.delete(k8s_object, "foobar")
