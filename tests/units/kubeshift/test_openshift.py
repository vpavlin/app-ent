import mock
from atomicapp.providers.lib.kubeshift.openshift import KubeOpenshiftClient

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
        return ['Pod', 'template', 'Route']

    def get_groups(self, *args):
        return {}

    def request(self, method, url, data=None):
        return None, 200

    @property
    def cluster(self):
        return {'server': 'https://foobar'}


@mock.patch("atomicapp.providers.lib.kubeshift.openshift.KubeBase")
def test_k8s_create(mock_class):
    # Mock the API class
    mock_class.return_value = FakeClient()
    mock_class.get_resources.return_value = ['Pod']
    mock_class.kind_to_resource_name.return_value = 'Pod'

    k8s_object = {"apiVersion": "v1", "kind": "Pod", "metadata": {"labels": {"app": "helloapache"}, "name": "helloapache"}, "spec": {
        "containers": [{"image": "$image", "name": "helloapache", "ports": [{"containerPort": 80, "hostPort": 80, "protocol": "TCP"}]}]}}

    a = KubeOpenshiftClient(config)
    a.create(k8s_object, "foobar")

@mock.patch("atomicapp.providers.lib.kubeshift.openshift.KubeBase")
def test_oc_create(mock_class):
    mock_class.return_value = FakeClient()
    mock_class.get_resources.return_value = ['Route']
    mock_class.kind_to_resource_name.return_value = 'Route'

    oc_object = {"apiVersion": "v1", "kind": "Route", "metadata": {"labels": {"name": "helloapache-route"}, "name": "helloapache-route"}, "spec": {
        "host": "$endpoint", "to": [{"kind": "Service", "name": "helloapache-svc"}]}}
    a = KubeOpenshiftClient(config)
    a.create(oc_object, "foobar")

@mock.patch("atomicapp.providers.lib.kubeshift.openshift.KubeBase")
def test_oc_delete(mock_class):
    mock_class.return_value = FakeClient()
    mock_class.kind_to_resource_name.return_value = 'Route'

    oc_object = {"apiVersion": "v1", "kind": "Route", "metadata": {"labels": {"name": "helloapache-route"}, "name": "helloapache-route"}, "spec": {
        "host": "$endpoint", "to": [{"kind": "Service", "name": "helloapache-svc"}]}}
    a = KubeOpenshiftClient(config)
    a.delete(oc_object, "foobar")

@mock.patch("atomicapp.providers.lib.kubeshift.openshift.KubeBase")
def test_k8s_delete(mock_class):
    # Mock the API class
    mock_class.return_value = FakeClient()
    mock_class.kind_to_resource_name.return_value = 'Pod'

    k8s_object = {"apiVersion": "v1", "kind": "Pod", "metadata": {"labels": {"app": "helloapache"}, "name": "helloapache"}, "spec": {
        "containers": [{"image": "$image", "name": "helloapache", "ports": [{"containerPort": 80, "hostPort": 80, "protocol": "TCP"}]}]}}

    a = KubeOpenshiftClient(config)
    a.delete(k8s_object, "foobar")


class FakeOpenshiftTemplateClient():

    def __init__(self, *args):
        pass

    def test_connection(self, *args):
        pass

    def get_resources(self, *args):
        return ['Pod', 'template']

    def get_groups(self, *args):
        return {}

    def request(self, method, url, data=None):
        openshift_object = {}
        openshift_object['objects'] = [{"kind": "Service", "apiVersion": "v1", "metadata": {"name": "cakephp-mysql-example", "annotations": {"description": "Exposes and load balances the application pods"}}, "spec": {"ports": [{"name": "web", "port": 8080, "targetPort": 8080}], "selector": {"name": "cakephp-mysql-example"}}}]
        return openshift_object, 200

    @property
    def cluster(self):
        return {'server': 'https://foobar'}


@mock.patch("atomicapp.providers.lib.kubeshift.openshift.KubeBase")
def test_process_template(mock_class):
    # Mock the API class
    mock_class.return_value = FakeOpenshiftTemplateClient()
    mock_class.kind_to_resource_name.return_value = 'template'

    openshift_template = {"kind": "Template", "apiVersion": "v1", "metadata": {"name": "foobar"}, "objects": [{"kind": "Service", "apiVersion": "v1", "metadata": {"name": "cakephp-mysql-example", "annotations": {
        "description": "Exposes and load balances the application pods"}}, "spec": {"ports": [{"name": "web", "port": 8080, "targetPort": 8080}], "selector": {"name": "cakephp-mysql-example"}}}]}

    a = KubeOpenshiftClient(config)
    a.create(openshift_template, "foobar")
    a.delete(openshift_template, "foobar")
