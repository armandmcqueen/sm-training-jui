import boto3
import time
from collections import deque
from IPython.display import clear_output, display

SM_CW_LOG_GROUP = "/aws/sagemaker/TrainingJobs"

region = "us-east-1"
sm_job = "armand-vgg-example-2019-06-24-22-12-16-025"
hostname = "algo-1"


def horovod_logline_handler(line):
    if 'errno' in line:
        pass
    else:
        # line = line.replace("#011", '\t')
        print(line)



def tail_sm_logs(sm_job_name, hostname, region="us-east-1", logline_handler=horovod_logline_handler):

    log_client = boto3.session.Session(region_name=region).client('logs')
    response = log_client.describe_log_streams(
        logGroupName=SM_CW_LOG_GROUP,
        logStreamNamePrefix=sm_job_name,
        orderBy='LogStreamName',
    )

    log_stream_prefix = f'{sm_job_name}/{hostname}-'
    log_stream_name = [s['logStreamName']
                       for s
                       in response['logStreams']
                       if s['logStreamName'].startswith(log_stream_prefix)]

    assert len(log_stream_name) == 1, "There should only be one matching logstream"
    log_stream_name = log_stream_name[0]

    response = log_client.get_log_events(
        logGroupName=SM_CW_LOG_GROUP,
        logStreamName=log_stream_name,
        startFromHead=False
    )
    next_forward_token = response["nextForwardToken"]

    for log_event in response["events"]:
        logline_handler(log_event["message"])

    while True:
        response = log_client.get_log_events(
            logGroupName=SM_CW_LOG_GROUP,
            logStreamName=log_stream_name,
            nextToken=next_forward_token,
            startFromHead=False
        )

        for log_event in response["events"]:
            logline_handler(log_event["message"])

        # last_forward_token = next_forward_token
        next_forward_token = response["nextForwardToken"]
        time.sleep(0.5)


class JupyterFixedMemoryLogger:
    def __init__(self):
        self.max_lines = 300
        self.pagination_overlap_lines = 50
        self.tail_buffer = deque([], maxlen=self.pagination_overlap_lines)
        self.output_length = 0

    def logline_handler(self, line):
        if 'errno' in line:
            return

        self.tail_buffer.append(line)
        self.output_length += 1
        print(line)

        if self.output_length == self.max_lines:
            clear_output()
            for l in self.tail_buffer:
                print(l)

            self.tail_buffer.clear()
            self.output_length = self.pagination_overlap_lines
