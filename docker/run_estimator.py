import boto3
import subprocess
import os
import argparse
import traceback
import sagemaker as sage
from sagemaker.estimator import Estimator

SM_ROLE = "arn:aws:iam::578276202366:role/armand-basic-sm-execution-role"
AWS_ACCOUNT = "578276202366"
REGION = "us-east-1"
IMAGE_REPO = "sm_hvd_training_example"
IMAGE_TAG = "latest"
S3_BUCKET = "aws-tf-sm"
S3_PREFIX = "hackathon/armand-performance-metrics"
JOB = "vgg-base"
NODE_COUNT = 2
INSTANCE_TYPE = "ml.p3.16xlarge"
SUBNET = "subnet-21ac2f2e"
SG_IDS = ["sg-0043f63c9ad9ffc1d", "sg-0d931ecdaccd26af3"]

INFLUX_PRIVATE_IP = "172.31.41.46"


if __name__ == '__main__':

    sess = sage.Session(boto3.session.Session(region_name=REGION))

    image = f'{AWS_ACCOUNT}.dkr.ecr.{REGION}.amazonaws.com/{IMAGE_REPO}:{IMAGE_TAG}'
    output_path = f's3://{S3_BUCKET}/{S3_PREFIX}/{JOB}'




    estimator = Estimator(image,
                          base_job_name=f'armand-vgg-example',
                          role=SM_ROLE,
                          train_volume_size=100,
                          train_instance_count=NODE_COUNT,
                          train_instance_type=INSTANCE_TYPE,
                          sagemaker_session=sess,
                          output_path=output_path,
                          subnets=[SUBNET],
                          security_group_ids=SG_IDS,
                          input_mode='File',
                          hyperparameters={'tig': True,
                                           "influx_private_ip": INFLUX_PRIVATE_IP,
                                           "tig_agent_interval": "10ms",
                                           "tig_flush_interval": "1s"})



    try:
        estimator.fit(logs=True)
    except Exception as ex:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("Error during estimator.fit")
        print(str(ex))
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        raise ex






