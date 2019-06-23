# sm-training-jui
Jupyter UI for SageMaker Training focused on watching logs, infrastructure metrics, and science metrics in real-time

https://www.influxdata.com/blog/tips-for-running-the-tick-stack-using-docker/

## Converting from Notebook to Markdown

https://github.com/jupyter/nbconvert

```
pip install jupyter

# jupyter nbconvert --to <output format> <input notebook>
jupyter nbconvert --to markdown realtime_jui_investigation.ipynb

```

# Download influx binary

https://portal.influxdata.com/downloads

```
docker pull influxdb:1.7.6
# docker run -it influxdb:1.7.6 /bin/bash

docker run -p 8086:8086 \
      -v influxdb:/var/lib/influxdb \
      influxdb:1.7.6
      
sudo docker exec -i -t ${CONTAINER_ID} /bin/bash
```

Run `influx`

```
CREATE DATABASE mydb
USE mydb
```

# Telegraf

https://docs.influxdata.com/telegraf/v1.11/introduction/installation/

```
LATEST=1.11.0
docker pull telegraf:${LATEST}

docker run --rm telegraf:${LATEST} telegraf config > telegraf.conf
```

