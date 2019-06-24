from __future__ import absolute_import

from contextlib import contextmanager
import signal

import os
import socket
import subprocess
import time
import json


def setup():

    # Read info that SageMaker provides
    rc_path = "/opt/ml/input/config/resourceconfig.json"
    with open(rc_path, 'r') as f:
        resources = json.load(f)
    current_host = resources["current_host"]
    all_hosts = resources["hosts"]

    hosts = list(all_hosts)

    # Apply gethostname() patch for OpenMPI
    _change_hostname(current_host)

    # Allow processes launched by mpirun to assume SageMaker IAM role
    _expose_aws_credential_chain_to_mpi_processes()

    # Enable SSH connections between containers
    _start_ssh_daemon()

    if current_host == _get_master_host_name(hosts):
        _wait_for_worker_nodes_to_start_sshd(hosts)


def is_master():
    # Read info that SageMaker provides
    rc_path = "/opt/ml/input/config/resourceconfig.json"
    with open(rc_path, 'r') as f:
        resources = json.load(f)
    current_host = resources["current_host"]
    all_hosts = sorted(list(resources["hosts"]))
    return current_host == all_hosts[0]



class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds=0, minutes=0, hours=0):
    """
    Add a signal-based timeout to any block of code.
    If multiple time units are specified, they will be added together to determine time limit.
    Usage:
    with timeout(seconds=5):
        my_slow_function(...)
    Args:
        - seconds: The time limit, in seconds.
        - minutes: The time limit, in minutes.
        - hours: The time limit, in hours.
    """

    limit = seconds + 60 * minutes + 3600 * hours

    def handler(signum, frame):  # pylint: disable=W0613
        raise TimeoutError('timed out after {} seconds'.format(limit))

    try:
        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, limit)
        yield
    finally:
        signal.alarm(0)


def _change_hostname(current_host):
    """Compiles a shared library to correct the behavior of the gethostname system call,
        which OpenMPI depends on.

    Args:
        current_host (str): name of the current host, such as algo-1, algo-2, etc.
    """
    os.system("change-hostname.sh {}".format(current_host))



def _expose_aws_credential_chain_to_mpi_processes():
    """
    At runtime, SageMaker sets an envvar (unique per node) in each container that adds the IAM role to the AWS
    credential chain. When mpirun launches processes on a remote host, those processes do not see that envvar
    and AWS SDK calls fail due to lack of credentials. So we add the envvar to the beginning of .bashrc to expose it to
    the mpirun processes
    """
    with open('/root/.bashrc.new', 'w+') as new_bashrc:
        new_bashrc.write(f'export AWS_CONTAINER_CREDENTIALS_RELATIVE_URI={os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")}\n')
    subprocess.check_output("cat /root/.bashrc >> /root/.bashrc.new", shell=True)
    subprocess.check_output("mv /root/.bashrc.new /root/.bashrc", shell=True)

def _get_master_host_name(hosts):
    return sorted(hosts)[0]

def _start_ssh_daemon():
    subprocess.Popen(["/usr/sbin/sshd", "-D"])

def _wait_for_worker_nodes_to_start_sshd(hosts, interval=1, timeout_in_seconds=180):
    with timeout(seconds=timeout_in_seconds):
        while hosts:
            print("hosts that aren't SSHable yet: %s", str(hosts))
            for host in hosts:
                ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if _can_connect(host, 22, ssh_socket):
                    hosts.remove(host)
            time.sleep(interval)


def _can_connect(host, port, s):
    try:
        print("testing connection to host %s", host)
        s.connect((host, port))
        s.close()
        print("can connect to host %s", host)
        return True
    except socket.error:
        print("can't connect to host %s", host)
        return False




