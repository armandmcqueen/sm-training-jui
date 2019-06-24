import boto3
import subprocess
import os
import argparse
import traceback
import sagemaker as sage
from sagemaker.estimator import Estimator
from utils.cwlogs.sm_cw_logs import download_sm_logs


def benchmarks(args):

    ############################################################
    ## ENVVARS
    ############################################################
    aws_region = os.environ["AWS_REGION"]
    aws_account = os.environ["AWS_ACCOUNT"]
    sm_role = os.environ["SM_EXECUTION_ROLE"]
    sm_instance_type = os.environ["SM_INSTANCE_TYPE"]

    sm_subnet = os.environ["SM_SUBNET"]
    sm_sgs = os.environ["SM_SECURITY_GROUPS"].split(",")
    sm_disk_gbs = int(os.environ["SM_VOLUME_GBS"])

    benchmark = os.environ["BENCHMARK"]
    s3_bucket = os.environ["S3_BUCKET"]
    s3_prefix = os.environ["S3_PREFIX"]

    image_name = os.environ["IMAGE_NAME"]
    image_tag = os.environ["IMAGE_TAG"]
    ############################################################

    print(f'Starting {args.node_count} node benchmark runs starting at {args.start_at} and ending after {args.end_after}')

    sess = sage.Session(boto3.session.Session(region_name=aws_region))

    base_save_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), args.save_folder)


    image = f'{aws_account}.dkr.ecr.{aws_region}.amazonaws.com/{image_name}:{image_tag}'
    output_path = f's3://{s3_bucket}/{s3_prefix}/{benchmark}/{args.node_count}node'


    for i in range(args.start_at, args.end_after+1):


        estimator = Estimator(image, base_job_name=f'{benchmark}-{args.node_count}node-benchmark-run-{i}',
                              role=sm_role,
                              train_volume_size=sm_disk_gbs,
                              train_instance_count=args.node_count,
                              train_instance_type=sm_instance_type,
                              sagemaker_session=sess,
                              output_path=output_path,
                              subnets=[sm_subnet],
                              security_group_ids=sm_sgs,
                              input_mode='File',
                              hyperparameters={"enable_tig": args.enable_tig,
                                               "tig_agent_interval": args.tig_agent_interval,
                                               "tig_flush_interval": args.tig_flush_interval})

        result_dir = f'{base_save_folder}/{args.node_count}node/{i}'
        cw_log_dir = f'{result_dir}/cw'

        subprocess.check_call(f'rm -rf {cw_log_dir}', shell=True)

        try:
            estimator.fit(logs=False)
        except Exception as ex:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Error during estimator.fit")
            print(str(ex))
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            if not args.continue_on_error:
                subprocess.check_call(f'mkdir -p {cw_log_dir}', shell=True)
                download_sm_logs(sm_job_name=estimator._current_job_name, download_dir=cw_log_dir)
                raise ex

        # print(f'model.tar.gz is available at {estimator.model_data}')
        # print(f'Job Name: {estimator._current_job_name}')

        subprocess.check_call(f'mkdir -p {cw_log_dir}', shell=True)
        subprocess.check_call(f'aws s3 cp {estimator.model_data} {result_dir}/run{i}.tar.gz', shell=True)
        subprocess.check_call(f'cd {result_dir} && tar -xzf run{i}.tar.gz', shell=True)
        subprocess.check_call(f'rm {result_dir}/run{i}.tar.gz', shell=True)

        download_sm_logs(sm_job_name=estimator._current_job_name, download_dir=cw_log_dir)

        print(f'Finished {args.node_count} Node Benchmark Run {i}')
    print("FINISHED ALL!")





if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="SageMakerBenchmarkLooper")
    parser.add_argument('--node_count', help='Number of nodes to run benchmarks on', type=int, required=True)
    parser.add_argument('--start_at',
                        help='The run to resume from. If the first log_file you want to create is run_1.log, start_at 1',
                        type=int, default=1)
    parser.add_argument('--end_after',
                        help='The run to quit after. Allows each cluster to do a part of the work. If end_at 20, run_20.log will be the final log created',
                        type=int, required=True)
    parser.add_argument('--save_folder',
                        help="Name of folder to save results to. Settable so that you can run multiple experiments in parallel. Default=results/tmp",
                        default="results/tmp")
    parser.add_argument('--continue_on_error', help='Set this flag to not exit in the case of exception', action="store_true")
    parser.add_argument('--enable_tig', help='Set this flag to enable TIG observability stack', action="store_true")
    parser.add_argument('--tig_agent_interval', help="How often should telegraf extract stats", default="10ms")
    parser.add_argument('--tig_flush_interval', help="How often should telegraf send stats to influx", default="1s")




    args = parser.parse_args()
    print(args)

    # assert args.node_count in [1, 2, 4], "Only 1/2/4 node benchmarks are set up"

    try:
        benchmarks(args)
    except Exception as ex:
        print("EXCEPTION")
        print(str(ex))
        traceback.print_exc()

