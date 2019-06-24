import boto3
import pytz
from datetime import datetime

def write_logs(get_log_events_response, logfile_writer, mode='simple'):
    tz = pytz.timezone('America/Los_Angeles')
    for log_event in get_log_events_response["events"]:
        timestamp = log_event["timestamp"]
        ingestion_timestamp = log_event["ingestionTime"]
        message = log_event["message"]


        if mode == 'simple':
            # [TIMESTAMP_TO_SEC_WITH_TZ] MESSAGE
            # Filter out 'errno'

            if 'errno' in message:
                continue
            ts_str = datetime.fromtimestamp(timestamp / 1000, tz).isoformat(" ", 'seconds')
            log_event_str = f'[{ts_str}] {message}'

        elif mode == 'with_ingestion_ts':
            # [TIMESTAMP_TO_SEC_WITH_TZ | INGESTION_TIMESTAMP_TO_SEC_WITH_TZ] MESSAGE
            # Filter out 'errno'

            if 'errno' in message:
                continue
            ts_str = datetime.fromtimestamp(timestamp / 1000, tz).isoformat(" ", 'seconds')
            ingest_ts_str = datetime.fromtimestamp(ingestion_timestamp / 1000, tz).isoformat(" ", 'seconds')
            log_event_str = f'[{ts_str} | {ingest_ts_str}] {message}'

        elif mode == 'detailed':
            # [TIMESTAMP_TO_MS_WITH_TZ | INGESTION_TIMESTAMP_TO_MS_WITH_TZ] MESSAGE

            ts_str = datetime.fromtimestamp(timestamp / 1000, tz).isoformat(" ", 'milliseconds')
            ingest_ts_str = datetime.fromtimestamp(ingestion_timestamp / 1000, tz).isoformat(" ", 'milliseconds')
            log_event_str = f'[{ts_str} | {ingest_ts_str}] {message}'

        else:
            raise RuntimeError("Unrecognized mode")

        logfile_writer.write(f'{log_event_str}\n')




def download_sm_logs(sm_job_name, download_dir, log_format_mode='simple'):
    if download_dir.endswith("/"):
        download_dir = download_dir[:-1]

    log_client = boto3.session.Session(region_name="us-east-1").client('logs')

    sm_log_group_name = "/aws/sagemaker/TrainingJobs"

    response = log_client.describe_log_streams(
        logGroupName=sm_log_group_name,
        logStreamNamePrefix=sm_job_name,
        orderBy='LogStreamName',
    )

    log_stream_names = [log_stream["logStreamName"] for log_stream in response["logStreams"]]

    for log_stream_name in log_stream_names:
        log_id = log_stream_name.split("/")[1]

        with open(f'{download_dir}/{log_id}.log', 'w+') as logfile:

            response = log_client.get_log_events(
                logGroupName=sm_log_group_name,
                logStreamName=log_stream_name,
                startFromHead=True
            )

            write_logs(response, logfile, mode=log_format_mode)

            last_forward_token = None
            next_forward_token = response["nextForwardToken"]

            while next_forward_token != last_forward_token:
                response = log_client.get_log_events(
                    logGroupName=sm_log_group_name,
                    logStreamName=log_stream_name,
                    nextToken=next_forward_token,
                    startFromHead=True
                )

                write_logs(response, logfile, mode=log_format_mode)

                last_forward_token = next_forward_token
                next_forward_token = response["nextForwardToken"]



if __name__ == "__main__":
    # download_sm_logs("vgg16-2node-benchmark-run1-2018-11-01-23-27-05-896", "./test_logs/", log_format_mode='with_ingestion_ts')
    pass
