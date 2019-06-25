import ipywidgets as widgets
import boto3
import time
from collections import deque
from IPython.display import clear_output

SM_CW_LOG_GROUP = "/aws/sagemaker/TrainingJobs"

class WidgetLogger:
    def __init__(self, out_widget):
        self.max_lines = 15
        self.tail_buffer = deque([], maxlen=self.max_lines)
        self.out_widget = out_widget

    def logline_handler(self, line):
        if 'errno' in line or 'inputs.nvidia_smi' in line:
            return
        line = line.replace('#011','\t')
        self.tail_buffer.append(line)
        with self.out_widget:
            clear_output(wait=True)
            print('\n'.join(self.tail_buffer))

def get_wlogger():
    out = widgets.Output(layout={'border': '1px solid black'})
    wlogger = WidgetLogger(out)
    return out, wlogger

def tail_sm_logs(sm_job_name, hostname, logline_handler, region="us-east-1"):
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

def tail_log_task(sm_job_name="armand-vgg-example-2019-06-25-19-53-40-033", hostname="algo-1", region='us-east-1'):
    from IPython.display import display
    out, wlogger = get_wlogger()
    display(out)
    import threading
    thread = threading.Thread(target=tail_sm_logs, args=(sm_job_name, hostname, wlogger.logline_handler, region))
    thread.start()