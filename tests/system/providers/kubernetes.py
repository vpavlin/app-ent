import os
import subprocess
import sys
import time
import urllib


def start():
    if not (os.path.exists('/usr/bin/kubectl') or
            os.path.exists('/usr/local/bin/kubectl')):
        print "No kubectl bin exists? Please install."
        return

    K8S_VERSION = '1.3.4'

    cmd = (
        "docker run "
        "--volume=/:/rootfs:ro "
        "--volume=/sys:/sys:ro "
        "--volume=/var/lib/docker/:/var/lib/docker:rw "
        "--volume=/var/lib/kubelet/:/var/lib/kubelet:rw "
        "--volume=/var/run:/var/run:rw "
        "--net=host "
        "--pid=host "
        "--privileged=true "
        "-d "
        "gcr.io/google_containers/hyperkube-amd64:v{k8s_version} "
        "/hyperkube kubelet " + (
            "--containerized "
            "--hostname-override=\"127.0.0.1\" "
            "--address=\"0.0.0.0\" "
            "--api-servers=http://localhost:8080 "
            "--config=/etc/kubernetes/manifests "
            "--cluster-dns=10.0.0.10 "
            "--cluster-domain=cluster.local "
            "--allow-privileged=true --v=2")
    ).format(k8s_version=K8S_VERSION)

    output = subprocess.check_output(cmd, shell=True)
    print output

    wait_until_k8s_is_up()


def stop():
    cmd = """
for run in {0..2}
do
  docker ps -a | grep 'k8s_' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f
  docker ps -a | grep 'gcr.io/google_containers/hyperkube-amd64' | awk '{print $1}' | xargs --no-run-if-empty docker rm -f
done"""
    output = subprocess.check_output(cmd, shell=True)
    print output


def answers():
    return """
[general]
provider = kubernetes
namespace = default
"""


def wait_until_k8s_is_up():
    while True:
        try:
            resp = urllib.urlopen('http://127.0.0.1:8080')
            if resp.getcode() == 200:
                break
        except IOError:
            pass
        print '...'
        time.sleep(1)
    time.sleep(5)

if __name__ == '__main__':
    exec(sys.argv[1] + '()')
