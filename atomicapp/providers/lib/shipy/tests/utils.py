import docker
import pytest
from random import randint
from shipy.dpyexec import Shipy


@pytest.fixture
def shipy():
    return Shipy()


@pytest.fixture(scope='function')
def client(request):
    client = docker.Client(base_url='unix://var/run/docker.sock')
    images = []
    for image in client.images():
        images.append(image['RepoTags'][0].split('/')[-1])

    if 'busybox:latest' not in images:
        client.pull('busybox:latest')

    def container_fin():
        for container in client.containers(all=True):
            name = str(container['Names'][0])[1:]
            if name.startswith('bruce') and \
                    name.endswith('wayne'):
                try:
                    client.remove_container(name, force=True)
                except docker.errors.NotFound:
                    pass

    request.addfinalizer(container_fin)
    return client


def cinput(cmd):
    return cmd.split()


def container_name():
    prefix = 'bruce'
    suffix = 'wayne'
    return '{}-{}-{}'.format(prefix, randint(1, 10000000), suffix)


def test_docker_run_template(client,
                             shipy,
                             farg=' ',
                             fval=' ',
                             sarg=' ',
                             sval=' ',
                             cimage='busybox',
                             cargs='ping 127.0.0.1',
                             cn=None):

    arg_val = ''

    if cn is None:
        cn = container_name()

    for value in fval:
        arg_val = '{} {} {}'.format(arg_val, farg, value)

    container = shipy.shipy(
        cinput('run {} {} {} --name {} {} {}'
               .format(arg_val, sarg, sval, cn, cimage, cargs)))
    return container
