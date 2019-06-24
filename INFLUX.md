# How to set up InfluxDB instance

- hackathon_sm_board KeyPair

 - Create AL2 instance
 - m5d.12xlarge
 - 500gb disk
 - Telegraf-sender and grafana-web-ui ports
 
 
 - Influx/Grafana public ip = 18.232.49.245
 
 - `ssh -L 127.0.0.1:3000:127.0.0.1:3000 ec2-user@34.226.215.169`

## Installing

Install influxdb 
```
wget https://dl.influxdata.com/influxdb/releases/influxdb-1.7.6.x86_64.rpm
sudo yum localinstall influxdb-1.7.6.x86_64.rpm

sudo service influxdb start

# start influx cli
create database "telegraf-sm"
```
 

```
SHOW DATABASES
CREATE DATABASE "telegraf-sm"
USE "telegraf-sm"

# Confirm no data exists
SELECT * FROM "cpu" LIMIT 100
show series
```

## Seeing if data is coming in

```
sudo yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
sudo yum update

yum install nload -y
nload
```