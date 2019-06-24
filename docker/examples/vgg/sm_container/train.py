import json
import os
import subprocess
import sys

from sagemaker_hvd_setup import setup
from sagemaker_hvd_utils import wait_for_training_processes_to_appear_and_finish
from sagemaker_hvd_utils import build_host_arg
from sagemaker_hvd_utils import CONST


GPUS_PER_HOST=8




if __name__ == "__main__":

    outdir = CONST["model_output_dir"]
    gethostname_ld_preload = CONST["gethostname_ld_preload"]
    print("pre-setup check")
    setup()

    rc_path = "/opt/ml/input/config/resourceconfig.json"
    with open(rc_path, 'r') as f:
        resources = json.load(f)

    print("--- resourceconfig.json ---")
    print(json.dumps(resources, indent=4))
    print("--- END resourceconfig.json ---")

    hyperparams_path = "/opt/ml/input/config/hyperparameters.json"
    with open(hyperparams_path, 'r') as f:
        hyperparams = json.load(f)

    print("--- hyperparameters.json ---")
    print(json.dumps(hyperparams, indent=4))
    print("--- END hyperparameters.json ---")

    current_host = resources["current_host"]
    all_hosts = resources["hosts"]
    num_hosts = len(all_hosts)

    is_master = current_host == sorted(all_hosts)[0]

    # Launch telegraf

    if hyperparams["enable_tig"] == True:
        influx_public_ip = "34.237.52.143"
        influx_private_ip = "172.31.79.15"
        create_telegraf_config_cmd = f'''\
        python /hutils/tig/telegraf_config.py \\
        --agent_interval {hyperparams["tig_agent_interval"]} \\
        --agent_flush_interval {hyperparams["tig_flush_interval"]} \\
        --influx_url http://{influx_private_ip}:8086 \\
        --influx_db telegraf-sm \\
        --tags user=armand,cluster=vgg-sagemaker-{num_hosts}node \\
        --input_filters cpu:mem:diskio:disk:net \\
        --hostname {current_host}'''

        subprocess.check_call(create_telegraf_config_cmd, shell=True)
        subprocess.check_call("telegraf --config telegraf.conf &", shell=True)



    if not is_master:
        process_search_term = "python3.6 /official-benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py"
        wait_for_training_processes_to_appear_and_finish(process_search_term)
        print(f'Worker {current_host} has completed')

    else:
        num_processes = num_hosts * GPUS_PER_HOST

        mpirun_cmd = f'''HOROVOD_TIMELINE={outdir}/htimeline.json \\
        mpirun -np {num_processes} \\
        --host {build_host_arg(all_hosts, GPUS_PER_HOST)} \\
        --allow-run-as-root \\
        --display-map \\
        --tag-output \\
        -mca btl_tcp_if_include eth0 \\
        -mca oob_tcp_if_include eth0 \\
        -x NCCL_SOCKET_IFNAME=eth0 \\
        --mca plm_rsh_no_tree_spawn 1 \\
        -bind-to none -map-by slot \\
        -mca pml ob1 -mca btl ^openib \\
        -mca orte_abort_on_non_zero_status 1 \\
        -x NCCL_MIN_NRINGS=8 -x NCCL_DEBUG=INFO \\
        -x LD_LIBRARY_PATH -x PATH \\
        -x LD_PRELOAD={gethostname_ld_preload} \\
        -x HOROVOD_TIMELINE \\
        --output-filename {outdir}/hlog \\
        sh -c "touch /mpi_is_running && \\
        python3.6 /official-benchmarks/scripts/tf_cnn_benchmarks/tf_cnn_benchmarks.py \\
            --num_batches={str(int(2000/num_hosts))} \\
            --model vgg16 \\
            --batch_size 64 \\
            --variable_update horovod \\
            --horovod_device gpu \\
            --use_fp16 \\
            && EXIT_CODE=$?"'''

        print(mpirun_cmd)
        print("###########")
        outfile = os.path.join(outdir, 'log.log')
        with open(outfile, 'w') as o:
            o.write(mpirun_cmd)

            try:
                out = subprocess.check_output(mpirun_cmd, shell=True)
                o.write("\n")
                o.write(out.decode("utf-8"))
                # for l in out.decode("utf-8").split("\n"):
                #     print(l)
                # print('---')
                # print(out.decode("utf-8"))
                exitcode = 0
                e = "----NO ERROR----"
                print(str(e))
                o.write("\n")
                o.write(str(e))
            except Exception as e:
                print("exception occured")
                exitcode = 1
                print(str(e))
                o.write("\n")
                o.write(str(e))
        # print(os.listdir(outdir))

        sys.exit(exitcode)




