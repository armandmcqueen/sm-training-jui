FROM tensorflow/tensorflow:1.12.0-gpu-py3

RUN apt-get update -y && \
    apt-get install -y git wget influxdb

RUN wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.6_amd64.deb && dpkg -i influxdb_1.7.6_amd64.deb

RUN git clone https://github.com/tensorflow/benchmarks -b cnn_tf_v1.12_compatible /tf_benchmarks


#WORKDIR /tf_benchmarks/scripts/tf_cnn_benchmarks
WORKDIR /
COPY entrypoint /train
COPY influx_runner.py /influx_runner.py

RUN chmod +x /train




