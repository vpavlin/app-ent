import argparse


def define_parsers():
    shipy_parser = argparse.ArgumentParser(prog='shipy')
    shipy_parser.add_argument(
        '-V',
        '--verbose',
        default=False,
        dest='isverbose',
        action='store_true',
        help='shows more verbose output'
    )
    shipy_subparsers = shipy_parser.add_subparsers(dest='mode')
    run_parser(shipy_subparsers)
    ps_parser(shipy_subparsers)
    kill_parser(shipy_subparsers)
    stop_parser(shipy_subparsers)
    rm_parser(shipy_subparsers)
    pull_parser(shipy_subparsers)
    restart_parser(shipy_subparsers)
    version_parser(shipy_subparsers)

    return shipy_parser


def run_parser(subparsers):
    run_subparser = subparsers.add_parser('run')
    run_subparser.add_argument(
        'run',
        action='store_true'
    )
    run_subparser.add_argument(
        'image',
        help='the image to run'
    )
    run_subparser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
        help='the command to be run in the container'
    )
    run_subparser.add_argument(
        '--name',
        type=str,
        help='a name for the container'
    )
    run_subparser.add_argument(
        '--entrypoint',
        type=str,
        help='an entrypoint'
    )
    run_subparser.add_argument(
        '-d',
        '--detach',
        action='store_true',
        dest='detach',
        help='detached mode, run container in the background'
    )
    run_subparser.add_argument(
        '--hostname',
        dest='hostname',
        help='optional hostname for the container'
    )
    run_subparser.add_argument(
        '-u',
        '--user',
        dest='user',
        help='sets the username or UID used and optionally the '
             'groupname or GID for the  specified command'
    )
    run_subparser.add_argument(
        '-i',
        '--interactive',
        dest='stdin_open',
        action='store_true',
        help='keep STDIN open even if not attached'
    )
    run_subparser.add_argument(
        '-t',
        '--tty',
        dest='tty',
        action='store_true',
        help='allocate a pseudo-TTY'
    )
    run_subparser.add_argument(
        '-e',
        '--env',
        action='append',
        dest='environment',
        help='set environment variables'
    )
    run_subparser.add_argument(
        '--cpu-shares',
        dest='cpu_shares',
        type=int,
        help='CPU shares (relative weight)'
    )
    run_subparser.add_argument(
        '-w',
        '--workdir',
        dest='working_dir',
        help='working directory inside the container'
    )
    run_subparser.add_argument(
        '--mac-address',
        dest='mac_address',
        type=str,
        help='container MAC address (e.g. 92:d0:c6:0a:29:33)'
    )
    run_subparser.add_argument(
        '-l',
        '--label',
        action='append',
        dest='labels',
        help='set metadata on the container '
             '(e.g., --label com.example.key=value)'
    )
    run_subparser.add_argument(
        '--volume-driver',
        dest='volume_driver',
        type=str,
        help='container\'s volume driver. This driver creates volumes '
             'specified either from a Dockerfile\'s VOLUME instruction '
             'or from the docker run -v flag'
    )
    run_subparser.add_argument(
        '--stop-signal',
        dest='stop_signal',
        type=str,
        help='signal to stop a container. Default is SIGTERM'
    )
    # HostConfig object parameters hereafter
    run_subparser.add_argument(
        '-v',
        '--volume',
        action='append',
        dest='binds',
        help='bind mount a volume'
    )
    run_subparser.add_argument(
        '-p',
        '--publish',
        action='append',
        dest='port_bindings',
        help='port bindings'
    )
    run_subparser.add_argument(
        '--oom-kill-disable',
        action='store_true',
        dest='oom_kill_disable',
        help='whether to disable OOM Killer for the container or not'
    )
    run_subparser.add_argument(
        '--oom-score-adj',
        dest='oom_score_adj',
        type=int,
        help='tune the host\'s OOM preferences for containers '
             '(accepts -1000 to 1000)'
    )
    run_subparser.add_argument(
        '-P',
        '--publish-all',
        action='store_true',
        dest='publish_all_ports',
        help='publish all exposed ports to random ports on the host interfaces'
    )
    run_subparser.add_argument(
        '--link',
        dest='links',
        action='append',
        help='add link to another container in the form of <name or id>:alias '
             'or just <name or id> in which case the alias will match the name'
    )
    run_subparser.add_argument(
        '--privileged',
        action='store_true',
        dest='privileged',
        help='give extended privileges to this container'
    )
    run_subparser.add_argument(
        '--dns',
        action='append',
        dest='dns',
        help='set custom DNS servers'
    )
    run_subparser.add_argument(
        '--dns-search',
        action='append',
        dest='dns_search',
        help='set custom DNS search domains'
    )
    run_subparser.add_argument(
        '--volumes-from',
        action='append',
        dest='volumes_from',
        help='mount volumes from the specified container(s)'
    )
    run_subparser.add_argument(
        '--net',
        dest='network_mode',
        help='set the Network mode for the container'
    )
    run_subparser.add_argument(
        '--restart',
        dest='restart_policy',
        help='Restart policy to apply when a container exits '
             '(no, on-failure[:max-retry], always, unless-stopped)'
    )
    run_subparser.add_argument(
        '--cap-add',
        action='append',
        dest='cap_add',
        help='add Linux capabilities'
    )
    run_subparser.add_argument(
        '--cap-drop',
        action='append',
        dest='cap_drop',
        help='drop linux capabilities'
    )
    run_subparser.add_argument(
        '--add-host',
        action='append',
        dest='extra_hosts',
        help='Add a line to /etc/hosts (host:IP)'
    )
    run_subparser.add_argument(
        '--read-only',
        action='store_true',
        dest='read_only',
        help='mount the container\'s root filesystem as read only'
    )
    run_subparser.add_argument(
        '--pid',
        dest='pid_mode',
        choices=['host'],
        help='set the PID mode for the container\n'
             'host: use the host\'s PID namespace inside the container'
    )
    run_subparser.add_argument(
        '--ipc',
        dest='ipc_mode',
        help='set the IPC mode for the container'
    )
    run_subparser.add_argument(
        '--security-opt',
        action='append',
        dest='security_opt',
        help='security options'
    )
    run_subparser.add_argument(
        '--ulimit',
        action='append',
        dest='ulimits',
        help='ulimit options, --ulimit is specified with a soft and hard limit'
             '\nas such: <type>=<soft limit>[:<hard limit>]'
    )
    run_subparser.add_argument(
        '--log-driver',
        dest='log_driver',
        help='logging configuration of the container'
    )
    run_subparser.add_argument(
        '--log-opt',
        action='append',
        dest='log_opt',
        help='logging configuration of the container'
    )
    run_subparser.add_argument(
        '-m',
        '--memory',
        dest='mem_limit',
        help='memory limit (format: [number][optional unit], where '
             'unit = b, k, m, or g)'
    )
    run_subparser.add_argument(
        '--memory-swap',
        dest='memswap_limit',
        help='a limit value equal to memory plus swap. Must be used with '
             'the  -m (--memory) flag. '
             'The swap LIMIT should always be larger '
             'than -m (--memory) value.'
    )
    run_subparser.add_argument(
        '--memory-swappiness',
        dest='mem_swappiness',
        type=int,
        help='tune a container\'s memory swappiness behavior. '
             'Accepts an integer between 0 and 100.'
    )
    run_subparser.add_argument(
        '--shm-size',
        dest='shm_size',
        help='size of /dev/shm'
    )
    run_subparser.add_argument(
        '--cpu-period',
        dest='cpu_period',
        type=int,
        help='limit the CPU CFS (Completely Fair Scheduler) period'
    )
    run_subparser.add_argument(
        '--group-add',
        action='append',
        dest='group_add',
        help='add additional groups to run as'
    )
    run_subparser.add_argument(
        '--device',
        action='append',
        dest='devices',
        help='add a host device to the container '
             '(e.g. --device=/dev/sdc:/dev/xvdc:rwm)'
    )
    run_subparser.add_argument(
        '--tmpfs',
        action='append',
        dest='tmpfs',
        help='create a tmpfs mount'
    )
    # run_subparser.add_argument(
    #     '--blkio-weight',
    #     dest='blkio_weight',
    #     help='block IO weight (relative weight)'
    # )
    # run_subparser.add_argument(
    #     '--device-read-bps',
    #     dest='device_read_bps',
    #     action='append',
    #     help='Limit read rate (bytes per second) from a device '
    #          '(e.g., --device-read-bps=/dev/sda:1mb)'
    # )
    # run_subparser.add_argument(
    #     '--device-write-bps',
    #     action='append',
    #     dest='device_write_bps',
    #     help='Limit write rate (bytes per second) from a device'
    # )
    # run_subparser.add_argument(
    #     '--device-read-iops',
    #     action='append',
    #     dest='device_read_iops',
    #     help='limit read rate (IO per second) from a device'
    # )
    # run_subparser.add_argument(
    #     '--device-write-iops',
    #     action='append',
    #     dest='device_write_iops',
    #     help='limit write rate (IO per second) from a device'
    # )
    # run_subparser.add_argument(
    #     '--blkio-weight-device',
    #     action='append',
    #     dest='blkio_weight_device',
    #     help='Block IO weight (relative device weight, format:'
    #          ' `DEVICE_NAME:WEIGHT`)'
    # )


def ps_parser(subparsers):
    ps_subparser = subparsers.add_parser('ps')
    ps_subparser.add_argument(
        'ps',
        action='store_true'
    )
    ps_subparser.add_argument(
        '-a',
        '--all',
        dest='all',
        action='store_true',
        help='show all containers'
    )


def kill_parser(subparsers):
    kill_subparser = subparsers.add_parser('kill')
    kill_subparser.add_argument(
        'kill',
        action='store_true',
        help='kill a container'
    )
    kill_subparser.add_argument(
        'container',
        help='the container to kill'
    )


def stop_parser(subparsers):
    stop_parser = subparsers.add_parser('stop')
    stop_parser.add_argument(
        'stop',
        action='store_true',
        help='stop a running container'
    )
    stop_parser.add_argument(
        'container',
        help='the container to stop'
    )


def rm_parser(subparsers):
    rm_parser = subparsers.add_parser('rm')
    rm_parser.add_argument(
        'rm',
        action='store_true',
        help='remove a container'
    )
    rm_parser.add_argument(
        'container',
        help='the container to remove'
    )
    rm_parser.add_argument(
        '-f',
        '--force',
        dest='force',
        action='store_true',
        help='force the removal of a running container'
    )
    rm_parser.add_argument(
        '-v',
        '--volume',
        dest='volumes',
        action='store_true',
        help='remove the volumes associated with the container'
    )
    rm_parser.add_argument(
        '-l',
        '--link',
        dest='link',
        action='store_true',
        help='remove the specified link and not the underlying container'
    )


def pull_parser(subparsers):
    pull_parser = subparsers.add_parser('pull')
    pull_parser.add_argument(
        'pull',
        action='store_true',
        help='pull a container image'
    )
    pull_parser.add_argument(
        'image',
        help='the container image to pull'
    )


def restart_parser(subparsers):
    restart_parser = subparsers.add_parser('restart')
    restart_parser.add_argument(
        'restart',
        action='store_true',
        help='restart a container'
    )
    restart_parser.add_argument(
        'container',
        help='the container image to pull'
    )


def version_parser(subparsers):
    version_parser = subparsers.add_parser('version')
    version_parser.add_argument(
        'version',
        action='store_true',
        help='show the docker version information'
    )
