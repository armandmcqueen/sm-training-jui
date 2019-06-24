import json
import os
import time
import subprocess
import sys





CONST = {
    "gethostname_ld_preload": "/libchangehostname.so",
    "model_output_dir": "/opt/ml/model",
    "mpi_is_running_file": "/mpi_is_running",
    "mpi_is_finished_file": "/mpi_is_finished",
    # "hostfile_location": "/Users/armanmcq/PycharmProjects/sm-training-jui"
    "hostfile_path": "/hostfile",

}

def hyperparams():
    with open("/opt/ml/input/config/hyperparameters.json", 'r') as hps:
        return json.load(hps)



def slots_per_instance():
    slots = 8
    return slots


def num_hosts():
    return len(hosts())


def num_total_processes():
    return slots_per_instance() * num_hosts()

def current_host():
    rc_path = "/opt/ml/input/config/resourceconfig.json"
    with open(rc_path, 'r') as f:
        resources = json.load(f)
    return resources["current_host"]


def hosts():
    rc_path = "/opt/ml/input/config/resourceconfig.json"
    with open(rc_path, 'r') as f:
        resources = json.load(f)
    return sorted(resources["hosts"])

def exit_successfully():
    sys.exit(0)

def exit_due_to_failure(error_message):
    # TODO: Write the error message to the correct SM location
    sys.exit(1)


def write_hostfile():
    hostfile_lines = [f'{host} slots={slots_per_instance()}' for host in hosts()]
    with open(CONST['hostfile_path'], 'w') as hf:
        for line in hostfile_lines:
            hf.write(line)
            hf.write("\n")







def build_host_arg(host_list, gpu_per_host):
    if len(host_list) == 1:
        return f'localhost:{gpu_per_host}'
    arg = ""
    for ind, host in enumerate(host_list):
        if ind != 0:
            arg += ","
        arg += f'{host}:{gpu_per_host}'
    return arg


def signal_mpi_is_finished():
    for host in hosts():
        signal_mpi_is_finished_cmd = f'ssh {host} touch {CONST["mpi_is_finished_file"]}'
        subprocess.check_call(signal_mpi_is_finished_cmd, shell=True)


def wait_for_mpi_is_finished_signal(verbose=False, sleep_secs=10):
    if verbose: print(f'Waiting for signal that mpi has finished')
    while not os.path.isfile(CONST["mpi_is_finished_file"]):
        if verbose: print(f'mpi has not finished. Sleeping for {sleep_secs} seconds')
        time.sleep(sleep_secs)

    if verbose: print("mpi has finished!")


