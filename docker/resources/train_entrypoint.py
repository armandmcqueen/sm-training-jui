from sagemaker_hvd_setup import setup, is_master
from sagemaker_hvd_utils import wait_for_mpi_is_finished_signal, signal_mpi_is_finished, num_total_processes, \
    num_hosts, exit_successfully, exit_due_to_failure, write_hostfile, hyperparams, current_host
import subprocess


def pretraining_hook_allnodes():
    print(subprocess.check_output("env", shell=True))

    hps = hyperparams()

    if hps["tig"] == True:
        create_telegraf_config_cmd = f'''\
        python /hutils/tig/telegraf_config.py \\
        --agent_interval {hps["tig_agent_interval"]} \\
        --agent_flush_interval {hps["tig_flush_interval"]} \\
        --influx_url http://{hps["influx_private_ip"]}:8086 \\
        --influx_db telegraf-sm \\
        --tags user=armand,cluster=vgg-sagemaker-{num_hosts()}node \\
        --input_filters cpu:mem:diskio:disk:net \\
        --hostname {current_host()}'''

        subprocess.check_call(create_telegraf_config_cmd, shell=True)
        subprocess.check_call("telegraf --config telegraf.conf &", shell=True)



def master_training_code():
    write_hostfile()
    print(subprocess.check_output("cat /hostfile", shell=True))


    num_batches = int(2000/num_hosts())
    mpirun_cmd = f'''\\
    mpirun -np {num_total_processes()} \\
        --output-filename /hlog \\
        python3.6 /tf_benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py \\
            --num_batches={num_batches} \\
            --model vgg16 \\
            --batch_size 64 \\
            --variable_update horovod \\
            --horovod_device gpu \\
            --use_fp16'''



    print(subprocess.check_output("cat /usr/local/bin/mpirun", shell=True))
    print(mpirun_cmd)
    subprocess.check_call(mpirun_cmd, shell=True)



if __name__ == '__main__':
    setup()

    pretraining_hook_allnodes()

    try:
        if is_master():
            master_training_code()
            signal_mpi_is_finished()
        else:
            wait_for_mpi_is_finished_signal()

        exit_successfully()
    except Exception as e:
        exit_due_to_failure(str(e))


