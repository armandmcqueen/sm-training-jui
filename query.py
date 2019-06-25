from influxdb import InfluxDBClient

#interval: how much time from now to query the data
interval = "1s"
#group: only works when there is an aggregation function, indicating how much time to aggregate data
group = "1s"
client = InfluxDBClient(host='127.0.0.1', database="telegraf-sm")
# From disk
mean_free_disk = client.query("SELECT mean(\"free\") FROM \"disk\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND \"device\" =~ /xvda1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
free_disk = client.query("SELECT \"free\" FROM \"disk\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND \"device\" =~ /xvda1/ AND time > now()-{};".format(interval))
# From mem
mean_free_mem = client.query("SELECT mean(\"free\") FROM \"mem\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
free_mem = client.query("SELECT \"free\" FROM \"mem\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{};".format(interval))
# From diskio
mean_read_bytes = client.query("SELECT mean(\"read_bytes\") FROM \"diskio\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
read_bytes = client.query("SELECT \"read_bytes\" FROM \"diskio\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{};".format(interval))
mean_write_bytes = client.query("SELECT mean(\"write_bytes\") FROM \"diskio\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
write_bytes = client.query("SELECT \"write_bytes\" FROM \"diskio\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{};".format(interval))
# From cpu
mean_cpu_in_use = client.query("SELECT 100 - mean(\"usage_idle\") as \"in_use\" FROM \"cpu\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
cpu_in_use = client.query("SELECT 100 - \"usage_idle\" as \"in_use\" FROM \"cpu\" WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{};".format(interval))
# From net
mean_download_rate = client.query("SELECT derivative(mean(bytes_recv), 1s)*8 as \"download rate\" FROM net WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
download_rate = client.query("SELECT derivative(bytes_recv, 1s)*8 as \"download rate\" \
                         FROM net WHERE \"user\" =~ /armand/ AND \"host\" =~ /algo-1/ AND time > now()-{};".format(interval))
mean_upload_rate = client.query("SELECT derivative(mean(bytes_sent), 1s)*8 as \"upload rate\" FROM net WHERE \"user\" =~ /armand/ AND \"host\" \
                         =~ /algo-1/ AND time > now()-{} GROUP BY time({}) fill(null);".format(interval, group))
upload_rate = client.query("SELECT derivative(bytes_sent, 1s)*8 as \"upload rate\" \
                         FROM net WHERE \"user\" =~ /armand/ AND \"host\" =~ /algo-1/ AND time > now()-{};".format(interval))
