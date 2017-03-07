import pytest
from atomicapp.providers.lib.kubeshift.kubebase import KubeBase
from atomicapp.providers.lib.kubeshift.exceptions import KubeConnectionError


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
kubebase = KubeBase(config)


def test_get_resources(httpserver):
    content = '{"kind":"APIResourceList","groupVersion":"v1","resources":[{"name":"bindings","namespaced":true,"kind":"Binding"},{"name":"componentstatuses","namespaced":false,"kind":"ComponentStatus"}]}'
    httpserver.serve_content(content, code=200, headers=None)
    kubebase.get_resources(httpserver.url)


def test_get_groups(httpserver):
    content = '{"kind":"APIGroupList","groups":[{"name":"autoscaling","versions":[{"groupVersion":"autoscaling/v1","version":"v1"}],"preferredVersion":{"groupVersion":"autoscaling/v1","version":"v1"},"serverAddressByClientCIDRs":[{"clientCIDR":"0.0.0.0/0","serverAddress":"192.168.1.156:443"}]},{"name":"batch","versions":[{"groupVersion":"batch/v1","version":"v1"}],"preferredVersion":{"groupVersion":"batch/v1","version":"v1"},"serverAddressByClientCIDRs":[{"clientCIDR":"0.0.0.0/0","serverAddress":"192.168.1.156:443"}]},{"name":"extensions","versions":[{"groupVersion":"extensions/v1beta1","version":"v1beta1"}],"preferredVersion":{"groupVersion":"extensions/v1beta1","version":"v1beta1"},"serverAddressByClientCIDRs":[{"clientCIDR":"0.0.0.0/0","serverAddress":"192.168.1.156:443"}]}]}'
    httpserver.serve_content(content, code=200, headers=None)
    kubebase.get_groups(httpserver.url)


def test_connection(httpserver):
    httpserver.serve_content(content="OK", code=200, headers=None)
    kubebase.test_connection(httpserver.url)


def test_kind_to_resource_name():
    assert kubebase.kind_to_resource_name("Pod") == "pods"
    assert kubebase.kind_to_resource_name("buildconfig") == "buildconfigs"
    assert kubebase.kind_to_resource_name("policy") == "policies"
    assert kubebase.kind_to_resource_name("petset") == "petsets"
    assert kubebase.kind_to_resource_name("componentstatus") == "componentstatuses"
    assert kubebase.kind_to_resource_name("Ingress") == "ingresses"


def test_request_methods_failures():
    with pytest.raises(KubeConnectionError):
        kubebase.request("get", "http://localhost")
    with pytest.raises(KubeConnectionError):
        kubebase.request("post", "http://localhost")
    with pytest.raises(KubeConnectionError):
        kubebase.request("put", "http://localhost")
    with pytest.raises(KubeConnectionError):
        kubebase.request("delete", "http://localhost")
    with pytest.raises(KubeConnectionError):
        kubebase.request("patch", "http://localhost")


def test_request_timeout(httpserver):
    httpserver.serve_content(content="Time out", code=408, headers=None)
    with pytest.raises(KubeConnectionError):
        kubebase.request("get", httpserver.url)


def test_request_ok(httpserver):
    httpserver.serve_content(content="OK", code=200, headers=None)
    kubebase.request("get", httpserver.url)


def test_websocket_request_without_ssl():
    # Should get an attribute error if there is no "cert_ca" to the base config
    with pytest.raises(AttributeError):
        kubebase.websocket_request("http://foobar")
