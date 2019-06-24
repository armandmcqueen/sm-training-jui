import os
import time
import subprocess
import sys


CONST = {
    "gethostname_ld_preload": "/libchangehostname.so",
    "model_output_dir": "/opt/ml/model",
    "mpi_is_running_file": "/mpi_is_running",
    "mpi_is_finished_file": "/mpi_is_finished"

}



def build_host_arg(host_list, gpu_per_host):
    if len(host_list) == 1:
        return f'localhost:{gpu_per_host}'
    arg = ""
    for ind, host in enumerate(host_list):
        if ind != 0:
            arg += ","
        arg += f'{host}:{gpu_per_host}'
    return arg


def signal_mpi_is_finished(host_list):
    for host in host_list:
        signal_mpi_is_finished_cmd = f'ssh {host} touch {CONST["mpi_is_finished_file"]}'
        subprocess.check_call(signal_mpi_is_finished_cmd, shell=True)


def wait_for_mpi_is_finished_signal(verbose=False, sleep_secs=10):
    if verbose: print(f'Waiting for signal that mpi has finished')
    while not os.path.isfile(CONST["mpi_is_finished_file"]):
        if verbose: print(f'mpi has not finished. Sleeping for {sleep_secs} seconds')
        time.sleep(sleep_secs)

    if verbose: print("mpi has finished!")





def wait_for_training_processes_to_appear_and_finish(proccess_id_string):
    print("This solution has problems due to workers finishing while master MPI is doing cleanup, leading to a SageMaker error")

    training_process_started = False
    while True:
        time.sleep(10)
        training_process_ps = subprocess.check_output(f'ps -elf | grep "{proccess_id_string}"', shell=True)
        print(training_process_ps)
        training_process_count = subprocess.check_output(f'ps -elf | grep "{proccess_id_string}" | wc -l', shell=True)
        training_process_count_str = training_process_count.decode("utf-8").replace("\n", "").strip()
        print(training_process_count_str)
        training_process_running = int(training_process_count_str) > 2
        if training_process_started:
            print("training process still running")
            if not training_process_running:
                print("Process done. Exiting after 1min")
                time.sleep(60)
                sys.exit(0)

        if not training_process_started:
            if training_process_running:
                print("training started this iter")
                training_process_started = True