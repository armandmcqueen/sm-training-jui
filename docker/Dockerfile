FROM armandmcqueen/tensorflow-training:1.13-horovod-gpu-py36-cu100-ubuntu16.04

RUN apt-get update -y && \
    apt-get install -y git \
                       wget

# Install OpenSSH for MPI to communicate between containers
RUN apt-get install -y --no-install-recommends openssh-client openssh-server
RUN mkdir -p /var/run/sshd && \
  mkdir -p /root/.ssh/ && \
  ssh-keygen -q -t rsa -N '' -f /root/.ssh/id_rsa && \
  cp /root/.ssh/id_rsa.pub /root/.ssh/authorized_keys && \
  printf "Host *\n  StrictHostKeyChecking no\n" >> /root/.ssh/config

##########################################################################################
# Good MPI defaults
##########################################################################################


#ENV LD_PRELOAD=/libchangehostname.so

# In the Deep Learning container, the mpirun executable is a wrapper script around the original mpirun executable
# (mpirun.real) that adds some default arguments. We do the same with additional default arguments.
COPY resources/mpirun_with_defaults /usr/local/bin/mpirun
RUN chmod +x /usr/local/bin/mpirun

COPY resources/openmpi-mca-params.conf /usr/local/etc/openmpi-mca-params.conf
COPY resources/nccl.conf /etc/nccl.conf

##########################################################################################
# SageMaker requirements
##########################################################################################

#RUN pip install sagemaker-containers
COPY resources/changehostname.c /changehostname.c
COPY resources/change-hostname.sh /usr/local/bin/change-hostname.sh

RUN chmod +x /usr/local/bin/change-hostname.sh

# SSH login fix. https://docs.docker.com/engine/examples/running_ssh_service/
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ARG CACHEBUST=1

COPY resources/sagemaker_hvd_setup.py /sagemaker_hvd_setup.py
COPY resources/sagemaker_hvd_utils.py /sagemaker_hvd_utils.py



##########################################################################################
# Training-job specific requirements
##########################################################################################

RUN git clone https://github.com/tensorflow/benchmarks -b cnn_tf_v1.13_compatible /tf_benchmarks
RUN pip install matplotlib



ARG CACHEBUST=1

#WORKDIR /tf_benchmarks/scripts/tf_cnn_benchmarks
WORKDIR /
COPY resources/train_entrypoint.py /train_entrypoint.py
COPY resources/train.sh /usr/local/bin/train
RUN chmod +x /usr/local/bin/train

# Copies the training code inside the container



# Defines train.py as script entry point
#ENV SAGEMAKER_PROGRAM train.py

##########################################################################################
# Installs for monitoring
##########################################################################################

RUN git clone https://github.com/armandmcqueen/horovod-utils hutils

RUN wget https://dl.influxdata.com/telegraf/releases/telegraf_1.11.0-1_amd64.deb && \
    sudo dpkg -i telegraf_1.11.0-1_amd64.deb

#COPY influx_runner.py /influx_runner.py
#
#RUN apt-get install sudo
#RUN wget https://dl.influxdata.com/telegraf/releases/telegraf_1.9.1-1_amd64.deb
##RUN wget https://dl.influxdata.com/influxdb/releases/influxdb_1.7.6_amd64.deb && dpkg -i influxdb_1.7.6_amd64.deb
#RUN sudo dpkg -i telegraf_1.9.1-1_amd64.deb