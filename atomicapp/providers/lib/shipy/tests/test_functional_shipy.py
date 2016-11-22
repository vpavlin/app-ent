import pytest
from utils import cinput, client, shipy, container_name as cn,\
    test_docker_run_template as run_template
from hurry.filesize import size

cimage = 'busybox'
cargs = 'ping 127.0.0.1'


def test_input_sanitization(shipy):
    test_input = {'test_mode': True, 'sanitized_input': True,
                  'isverbose': False, 'mode': 'test_mode'}

    assert {'sanitized_input': True} == shipy._sanify(test_input)


def test_malformed_docker_file_input(shipy, tmpdir):
    tmp_path = tmpdir.mkdir('shipy_temp').join('shipy_test')
    tmp_path.write('dckr run {} {}'.format(cimage, cargs))

    args = ['--file', str(tmp_path)]
    with pytest.raises(SyntaxError):
        shipy.shipy(args)


def test_docker_run_basic(client, shipy):
    container = shipy.shipy(
        cinput('run --name {} {} {}'.format(cn(), cimage, cargs)))
    assert 1 == len(client.containers(
        filters={'id': container, 'status': 'running'}))


def test_docker_run_name(client, shipy):
    cn = 'bruce-batman-wayne'
    run_template(client, shipy, cn=cn)

    assert 1 == len(client.containers(filters={'name': cn}))


def test_docker_run_args(client, shipy):
    cargs = 'ping -v -c 100 127.0.0.1'
    container = run_template(client, shipy, cargs=cargs)

    assert cargs == '{} {}'.format(
        client.inspect_container(container)['Path'],
        ' '.join(client.inspect_container(container)['Args']))


def test_docker_run_entrypoint(client, shipy):
    cargs = '-c 100 127.0.0.1'
    farg = '--entrypoint'
    fval = ('ping',)
    container = run_template(client, shipy, farg=farg, fval=fval, cargs=cargs)

    assert fval[0] == \
           client.inspect_container(container)['Config']['Entrypoint'][0]


def test_docker_run_hostname(client, shipy):
    farg = '--hostname'
    fval = ('batman',)
    container = run_template(client, shipy, farg, fval=fval)
    assert fval[0] == \
           client.inspect_container(container)['Config']['Hostname']


def test_docker_run_user(client, shipy):
    argument = ('-u', '--user')
    fval = ('root',)

    for farg in argument:
        container = run_template(client, shipy, farg=farg, fval=fval)
        assert fval[0] == \
               client.inspect_container(container)['Config']['User']


def test_docker_run_env(client, shipy):
    argument = ('-e', '--env')
    fval = ('bat=man', 'bruce=wayne')

    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg, fval=fval)

        for env in fval:
            assert env in \
               client.inspect_container(container)['Config']['Env']


def test_docker_run_cpu_shares(client, shipy):
    farg = '--cpu-shares'
    fval = (5,)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['CpuShares']


def test_docker_run_workdir(client, shipy):
    argument = ('-w', '--workdir')
    fval = ('/tmp',)
    for farg in argument:
        container = run_template(client, shipy, farg=farg, fval=fval)
        assert fval[0] == \
               client.inspect_container(container)['Config']['WorkingDir']


def test_docker_run_mac_address(client, shipy):
    farg = '--mac-address'
    fval = ('aa:aa:aa:aa:aa:aa',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['NetworkSettings']['MacAddress']


def test_docker_run_labels(client, shipy):
    argument = ('-l', '--label')
    fval = ('batman=begins', 'thedarkknight=rises')
    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg, fval=fval)

        for label in fval:
            l = label.split('=')
            assert l[1] == \
                client.inspect_container(container)['Config']['Labels'][l[0]]


def test_docker_run_stop_signal(client, shipy):
    farg = '--stop-signal'
    fval = ('SIGKILL',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['Config']['StopSignal']


def test_docker_run_volumes(client, shipy):
    argument = ('-v', '--volume')
    fval = ('/test_dir1:/test_dir_mount1:ro', '/test_dir2:/tmp')

    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg, fval=fval)

        binding_list = []
        for binding in fval:
            if len(binding) > 1:
                binding_list.append(binding)

        assert binding_list == \
               client.inspect_container(container)['HostConfig']['Binds']

        # this is asserting if the volumes are exposed on the container or not
        # a bit different from docker run, but can be called ideal
        assert_dict = {}
        for value in fval:
            assert_dict.update({value.split(':')[0]: {}})

        assert assert_dict == \
               client.inspect_container(container)['Config']['Volumes']


def test_docker_run_publish(client, shipy):
    argument = ('-p', '--publish')
    fval = ('13370:23370/udp', '13371:23371', '127.0.0.1:13372:23372',
            '23373', '127.0.0.1::23374')
    ext_fval = []
    only_ports = []

    for value in fval:
        container_port = value.split(':')[-1]
        host_params = value.split(':')[:-1]
        if container_port[-3:] not in ('tcp', 'udp'):
            ext_fval.append('{}:{}/tcp'.format(host_params, container_port))
        else:
            ext_fval.append('{}:{}'.format(host_params, container_port))

    for value in ext_fval:
        only_ports.append(value.split(':')[-1])

    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg, fval=fval)

        exposed_ports = \
            client.inspect_container(
                container)['Config']['ExposedPorts'].keys()
        exposed_ports.sort()
        # print ext_fval, exposed_ports
        assert only_ports == exposed_ports

        for cport, ncport in \
                client.inspect_container(
                    container)['HostConfig']['PortBindings'].items():

            if ncport[0]['HostIp']:
                host_conf = '[\'{}\', \'{}\']'.format(
                    ncport[0]['HostIp'], ncport[0]['HostPort'])
            elif ncport[0]['HostPort']:
                host_conf = '[\'{}\']'.format(ncport[0]['HostPort'])
            else:
                host_conf = []

            assert '{}:{}'.format(host_conf, cport) in ext_fval

        client.remove_container(container, force=True)


def test_docker_run_publish_all(client, shipy):
    argument = ('-P', '--publish-all')

    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg)

        assert client.inspect_container(
            container)['HostConfig']['PublishAllPorts']


def test_docker_run_links(client, shipy):
    farg = '--link'
    fval = []

    for _ in range(2):
        fval.append(cn())

    fval[1] += ':alias'

    fval = tuple(fval)

    ext_fval = []

    for linked_to in fval:
        run_template(client, shipy, cn=linked_to.split(':')[0])

        if len(linked_to.split(':')) == 1:
            linked_to += ':{}'.format(linked_to)
        ext_fval.append(linked_to)

    container = run_template(client, shipy, farg=farg, fval=fval)

    links = client.inspect_container(container)['HostConfig']['Links']

    assert len(fval) == len(links)

    for link in links:
        name, _, alias = ''.join(link.split(':')).split('/')[1:]

        assert '{}:{}'.format(name, alias) in ext_fval


def test_docker_run_privileged(client, shipy):
    farg = '--privileged'

    container = run_template(client, shipy, farg=farg)

    assert client.inspect_container(container)['HostConfig']['Privileged']


def test_docker_run_dns(client, shipy):
    farg = '--dns'
    fval = ('8.8.8.8', '8.8.4.4')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['Dns']


def test_docker_run_dns_search(client, shipy):
    farg = '--dns-search'
    fval = ('batman.com', 'brucewayne.com')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['DnsSearch']


def test_docker_run_volumes_from(client, shipy):
    farg = '--volumes-from'
    fval = []

    for _ in range(2):
        fval.append(cn())

    for volume_container in fval:
        run_template(client, shipy, cn=volume_container)

    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval == \
           client.inspect_container(container)['HostConfig']['VolumesFrom']


def test_docker_run_network_mode(client, shipy):

    reuse_network_container = cn()
    run_template(client, shipy, cn=reuse_network_container)

    for mode in ['bridge', 'none', 'container:{}'.format(
            reuse_network_container), 'host']:
        farg = '--net'
        fval = (mode,)

        container = run_template(client, shipy, farg=farg, fval=fval)

        assert fval[0] == \
               client.inspect_container(container)['HostConfig']['NetworkMode']


def test_docker_run_detach(client, shipy):
    argument = ('-d', '--detach')

    for farg in argument:
        container = run_template(client, shipy,
                                 farg=farg)

        assert not client.inspect_container(
            container)['Config']['AttachStdout']


def test_docker_run_restart_policy_on_failure(client, shipy):
    farg = '--restart'
    for fval in (('no',), ('on-failure',), ('on-failure:4',), ('always',), ('unless-stopped',)):
        container = run_template(client, shipy, farg=farg, fval=fval)
        inspect_output = client.inspect_container(container)['HostConfig']['RestartPolicy']
        fval_split = fval[0].split(':')

        assert fval_split[0] == inspect_output['Name']

        if fval_split[0] == 'on-failure' and len(fval_split) == 2:
            assert int(fval_split[1]) == inspect_output['MaximumRetryCount']


def test_docker_run_cap_add(client, shipy):
    farg = '--cap-add'
    fval = ('SYS_ADMIN', 'SYS_TIME')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['CapAdd']


def test_docker_run_cap_drop(client, shipy):
    farg = '--cap-drop'
    fval = ('SYS_ADMIN', 'SYS_TIME')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['CapDrop']


def test_docker_run_add_host(client, shipy):
    farg = '--add-host'
    fval = ('batman.example:10.0.0.1', 'wayne.manor:10.0.0.2')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['ExtraHosts']


def test_docker_run_read_only(client, shipy):
    farg = '--read-only'

    container = run_template(client, shipy, farg=farg)

    assert client.inspect_container(container)['HostConfig']['ReadonlyRootfs']


def test_docker_run_pid(client, shipy):
    farg = '--pid'
    fval = ('host',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['PidMode']


def test_docker_run_ipc(client, shipy):
    farg = '--ipc'
    ipc_cn = cn()
    for fval in (('host',),
                 ('container:{}'.format(ipc_cn),)
                 ):

        if fval[0].split(':')[0] == 'container':
            run_template(client, shipy, cn=ipc_cn)

        container = run_template(client, shipy, farg=farg, fval=fval)

        assert fval[0] == \
            client.inspect_container(container)['HostConfig']['IpcMode']


def test_docker_run_security_opt(client, shipy):
    farg = '--security-opt'
    fval = ('label=type:svirt_apache_t', 'label=level:s0:c100,c200')
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert [fval[0], fval[1]] == \
           client.inspect_container(container)['HostConfig']['SecurityOpt']


def test_docker_run_ulimit(client, shipy):
    farg = '--ulimit'
    fval = ('nproc=3:4', 'nofile=1024')
    container = run_template(client, shipy, farg=farg, fval=fval)

    for v, u in zip(fval,
                client.inspect_container(container)['HostConfig']['Ulimits']):
        name, limit = v.split('=')
        limits = limit.split(':')
        soft = int(limits[0])
        hard = int(limits[1]) if len(limits) == 2 else soft

        assert u['Name'] == name
        assert u['Soft'] == soft
        assert u['Hard'] == hard


def test_docker_run_log_driver(client, shipy):
    farg = '--log-driver'
    fval = ('syslog',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['LogConfig']['Type']


def test_docker_run_log_opt(client, shipy):
    farg = '--log-opt'
    fval = ('tag=batman', 'syslog-format=rfc3164')

    sarg = '--log-driver'
    sval = 'syslog'

    container = run_template(client, shipy, farg=farg, fval=fval,
                             sarg=sarg, sval=sval)

    assert sval == \
           client.inspect_container(container)[
               'HostConfig']['LogConfig']['Type']

    for opt in fval:
        k, v = opt.split('=')
        assert v == \
            client.inspect_container(container)[
                'HostConfig']['LogConfig']['Config'][k]


def test_docker_run_memory(client, shipy):
    farg = '--memory'
    fval = ('100M',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           size(client.inspect_container(container)['HostConfig']['Memory'])


def test_docker_run_memory_swap(client, shipy):
    farg = '--memory-swap'
    fval = ('110M',)

    sarg = '--memory'
    sval = '100M'
    container = run_template(client, shipy, farg=farg, fval=fval,
                             sarg=sarg, sval=sval)

    assert sval == \
           size(client.inspect_container(container)['HostConfig']['Memory'])

    assert fval[0] == \
           size(client.inspect_container(container)['HostConfig']['MemorySwap'])


def test_docker_run_memory_swappiness(client, shipy):
    farg = '--memory-swappiness'
    fval = (42,)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['MemorySwappiness']


def test_docker_run_shm_size(client, shipy):
    farg = '--shm-size'
    fval = ('100M',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           size(client.inspect_container(container)['HostConfig']['ShmSize'])


def test_docker_run_cpu_period(client, shipy):
    farg = '--cpu-period'
    fval = (1000,)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['CpuPeriod']


def test_docker_run_group_add(client, shipy):
    farg = '--group-add'
    fval = ('wheel',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['GroupAdd'][0]


def test_docker_run_device(client, shipy):
    farg = '--device'
    fval = ('/dev/null:/dev/sda2:rwm', '/dev/zero:/dev/sda3:m')
    container = run_template(client, shipy, farg=farg, fval=fval)

    devices = client.inspect_container(container)['HostConfig']['Devices']

    chost_path, ccontainer_path, cperms = [], [], []

    for device in devices:
        chost_path.append(device['PathOnHost'])
        ccontainer_path.append(device['PathInContainer'])
        cperms.append(device['CgroupPermissions'])

    for dev in fval:
        host_path, container_path, perms = dev.split(':')

        assert host_path in chost_path
        assert container_path in ccontainer_path
        assert perms in cperms


def test_docker_run_tmpfs(client, shipy):
    farg = '--tmpfs'
    fval = ('/run/:rw,noexec,nosuid,size=65536k', '/mnt/:size=3G,uid=1000')
    container = run_template(client, shipy, farg=farg, fval=fval)

    tmpfs = client.inspect_container(container)['HostConfig']['Tmpfs']

    for val in fval:
        mount, args = val.split(':')
        assert tmpfs[mount] == args


def test_docker_run_interactive(client, shipy):
    argument = ('-i', '--interactive')

    for farg in argument:
        container = run_template(client, shipy, farg=farg)

        assert client.inspect_container(container)[
            'Config']['AttachStdin']
        assert client.inspect_container(container)[
            'Config']['OpenStdin']
        assert client.inspect_container(container)[
            'Config']['StdinOnce']


def test_docker_run_tty(client, shipy):
    argument = ('-t', '--tty')

    for farg in argument:
        container = run_template(client, shipy, farg=farg)

        assert client.inspect_container(container)['Config']['Tty']


def test_docker_run_volume_driver(client, shipy):
    farg = '--volume-driver'
    fval = ('local',)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['VolumeDriver']


def test_docker_run_oom_kill_disable(client, shipy):
    farg = '--oom-kill-disable'

    container = run_template(client, shipy, farg=farg)

    assert client.inspect_container(container)['HostConfig']['OomKillDisable']


def test_docker_oom_score_adj(client, shipy):
    farg = '--oom-score-adj'
    fval = (42,)
    container = run_template(client, shipy, farg=farg, fval=fval)

    assert fval[0] == \
           client.inspect_container(container)['HostConfig']['OomScoreAdj']


# def test_docker_blkio_weight(client, shipy):
#     farg = '--blkio-weight'
#     fval = (42,)
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     assert fval[0] == \
#            client.inspect_container(container)['HostConfig']['BlkioWeight']
#
#
# def test_docker_blkio_weight_device(client, shipy):
#     farg = '--blkio-weight-device'
#     fval = ('/dev/null:42', '/dev/sdb:84')
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     bk = client.inspect_container(container)['HostConfig']['BlkioWeightDevice']
#
#     cpath, cweight = [], []
#     for blkio in bk:
#         cpath.append(blkio['Path'])
#         cweight.append(blkio['Weight'])
#
#     for val in fval:
#         path, weight = val.split(':')
#
#         assert path in cpath
#         assert weight in cweight
#
#
# def test_docker_device_read_bps(client, shipy):
#     farg = '--device-read-bps'
#     fval = ('/dev/sda:1mb', '/dev/sdb:2mb')
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     bk = client.inspect_container(container)['HostConfig']['BlkioDeviceReadBps']
#
#     cpath, crate = [], []
#     for blkio in bk:
#         cpath.append(blkio['Path'])
#         crate.append(blkio['Rate'])
#
#     for val in fval:
#         path, rate = val.split(':')
#
#         assert path in cpath
#         assert rate in crate
#
#
# def test_docker_device_write_bps(client, shipy):
#     farg = '--device-write-bps'
#     fval = ('/dev/sda:1mb', '/dev/sdb:2mb')
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     bk = client.inspect_container(container)['HostConfig']['BlkioDeviceWriteBps']
#
#     cpath, crate = [], []
#     for blkio in bk:
#         cpath.append(blkio['Path'])
#         crate.append(blkio['Rate'])
#
#     for val in fval:
#         path, rate = val.split(':')
#
#         assert path in cpath
#         assert rate in crate
#
#
# def test_docker_device_read_iops(client, shipy):
#     farg = '--device-read-iops'
#     fval = ('/dev/sda:1000', '/dev/sdb:2000')
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     bk = client.inspect_container(container)['HostConfig'][
#         'BlkioDeviceReadIOps']
#
#     cpath, crate = [], []
#     for blkio in bk:
#         cpath.append(blkio['Path'])
#         crate.append(blkio['Rate'])
#
#     for val in fval:
#         path, rate = val.split(':')
#
#         assert path in cpath
#         assert rate in crate
#
#
# def test_docker_device_write_iops(client, shipy):
#     farg = '--device-write-iops'
#     fval = ('/dev/sda:1000', '/dev/sdb:2000')
#     container = run_template(client, shipy, farg=farg, fval=fval)
#
#     bk = client.inspect_container(container)['HostConfig'][
#         'BlkioDeviceWriteIOps']
#
#     cpath, crate = [], []
#     for blkio in bk:
#         cpath.append(blkio['Path'])
#         crate.append(blkio['Rate'])
#
#     for val in fval:
#         path, rate = val.split(':')
#
#         assert path in cpath
#         assert rate in crate