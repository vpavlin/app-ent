import base64
import os
import subprocess
import sys
import time
import urllib2


def start():
    print "Stopping existing origin container, if any..."
    try:
        subprocess.check_call('docker rm -f origin', shell=True)
    except subprocess.CalledProcessError:
        pass
    if not (os.path.exists('/usr/bin/kubectl') or
            os.path.exists('/usr/local/bin/kubectl')):
        print "No kubectl bin exists? Please install."
        sys.exit(1)

    cmd = """
docker run -d --name "origin" \
  --privileged --pid=host --net=host \
  -v /:/rootfs:ro -v /var/run:/var/run:rw -v /sys:/sys -v /var/lib/docker:/var/lib/docker:rw \
  -v /var/lib/origin/openshift.local.volumes:/var/lib/origin/openshift.local.volumes \
  openshift/origin start"""
    output = subprocess.check_output(cmd, shell=True)
    print output
    wait_for_os()


def answers():
    req = urllib2.Request(
        'https://localhost:8443/oauth/authorize?'
        'response_type=token&client_id=openshift-challenging-client',
        headers={'X-CSRF-Token': 1}
    )
    base64string = base64.encodestring('openshift:openshift').replace(
        '\n', '')
    req.add_header('Authorization', 'Basic %s' % base64string)
    f = urllib2.urlopen(req)
    api_key = f.geturl().split('access_token=')[1].split('&')[0]
    subprocess.check_call('docker exec -i origin oc config set-credentials openshift --token={api_key}'.format(api_key=api_key), shell=True)
    subprocess.check_call(
        'docker exec -i origin oc config set-cluster openshift1 '
        '--server=https://localhost:8443 --insecure-skip-tls-verify=true',
        shell=True)
    subprocess.check_call(
        'docker exec -i origin oc config set-context openshift '
        '--cluster=openshift1 --user=openshift', shell=True)
    subprocess.check_call(
        'docker exec -i origin oc config use-context openshift', shell=True)
    subprocess.check_call(
        'docker exec -i origin oc config set contexts.openshift.namespace foo',
        shell=True)

    time.sleep(3)
    subprocess.check_call(
        'docker exec -i origin oc new-project foo', shell=True)
    time.sleep(3)

    answers = """
[general]
provider = openshift
provider-api = https://localhost:8443
provider-auth = {api_key}
namespace = foo
provider-tlsverify = False""".format(api_key=api_key)
    print answers
    return answers


def stop():
    try:
        subprocess.check_output('docker rm -f origin', shell=True)
    except subprocess.CalledProcessError:
        return


def wait_for_os():
    while True:
        try:
            resp = urllib2.urlopen('https://127.0.0.1:8443')
            if resp.getcode() == 200:
                break
        except IOError:
            pass
        print '...'
        time.sleep(1)
    time.sleep(5)


def wait():
    cmd = """
  echo "Waiting for oc po/svc/rc to finish terminating..."
  docker exec -i origin oc get po,svc,rc
  sleep 3 # give kubectl chance to catch up to api call
  while [ 1 ]
  do
    oc=`docker exec -i origin oc get po,svc,rc | grep Terminating`
    if [[ $oc == "" ]]
    then
      echo "oc po/svc/rc terminated!"
      break
    else
      echo "..."
    fi
    sleep 1
  done"""
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        pass

if __name__ == '__main__':
    exec(sys.argv[1] + '()')
