influx_db_private_ip = "172.31.41.46"

from influxdb import InfluxDBClient
import numpy as np
import holoviews as hv
from holoviews import opts
import pandas as pd
from sagemaker_logs import *

hv.extension('bokeh')

heatmap_coords = [(0,0),
          (1,0),
          (2,0),
          (3,0),
          (0,1),
          (1,1),
          (2,1),
          (3,1),
         ]


def get_gpu_util():
    query_str = "SELECT mean(\"utilization_gpu\") FROM \"nvidia_smi\" WHERE \"cluster\" =~ /hackathon-vgg-sagemaker-2node/  AND time > now()-1s GROUP BY time(2s), \"host\", \"index\" fill(null);"

    client = InfluxDBClient(host=influx_db_private_ip, database="telegraf-sm")
    gpu_util_query_response = client.query(query_str)

    results = {}
    for host in ['algo-1', 'algo-2']:
        results[host] = {}
        for gpu_index in range(8):
            datapoint = list(gpu_util_query_response.get_points(measurement='nvidia_smi',
                                                                tags={"host": host,
                                                                      "index": f'{gpu_index}'}))
            if len(datapoint) != 0:
                v = datapoint[-1]['mean']
            else:
                v = 0
            results[host][gpu_index] = v

    return results









def get_gpu_data():
    plottable_data = {}
    for host in ['algo-1', 'algo-2']:
        plottable_data[host] = []
        for gpu_index in range(8):
            v = get_gpu_util()[host][gpu_index]
            x,y = heatmap_coords[gpu_index]

            plottable_data[host].append(f'{x},{y},{v}')

    df = pd.DataFrame(data=plottable_data)
    return df


from tornado.ioloop import PeriodicCallback


def clean(host_data):
    clean_host_data = []
    for r in host_data:
        x = int(r[0])
        y = int(r[1])
        v = r[2]
        if r[2] is None or r[2] == 'None':
            v = 0
        else:
            v = float(v)

        clean_host_data.append((x, y, v))
    return clean_host_data


def gpu_util():
    import datetime as dt

    import psutil
    import pandas as pd
    import holoviews as hv
    from holoviews import dim, opts

    renderer = hv.renderer('bokeh')

    # Define DynamicMap callbacks returning Elements

    def gpu_map(data):
        data_algo1 = [d.split(",") for d in data['algo-1']]
        data_algo2 = [d.split(",") for d in data['algo-2']]

        data_algo1 = clean(data_algo1)
        data_algo2 = clean(data_algo2)

        algo1_map = hv.HeatMap(data_algo1).options(cmap='coolwarm',
                                                   title="GPU Heatmap (algo1)",
                                                   width=400,
                                                   colorbar=True).sort()
        algo2_map = hv.HeatMap(data_algo2).options(cmap='coolwarm',
                                                   title="GPU Heatmap (algo2)",
                                                   width=400,
                                                   colorbar=True).sort()

        full_plot = algo1_map + algo2_map.opts(shared_axes=False)
        return full_plot

    gpu_stream = hv.streams.Buffer(get_gpu_data())

    def cb():
        gpu_stream.send(get_gpu_data())

    # Define DynamicMaps and display plot

    gpu_dmap = hv.DynamicMap(gpu_map, streams=[gpu_stream])

    # Render plot and attach periodic callback
    cb_attacher = PeriodicCallback(cb, 100)
    cb_attacher.start()
    return gpu_dmap, cb_attacher

# gpu_dmap, cb = gpu_util()
# gpu_dmap
# cb.stop()





def bits_to_gbits(bits):
    return bits / 1024 / 1024 / 1024


def query_network_util():
    query_str = "SELECT derivative(bytes_recv, 1s)*8 as \"download_rate\" FROM net WHERE \"user\" =~ /armand/ AND \"host\" =~ /algo-1/ AND \"interface\" = 'eth0' AND time > now()-5s;"

    client = InfluxDBClient(host=influx_db_private_ip, database="telegraf-sm")
    network_util_query_response = client.query(query_str)

    results = []
    for p in network_util_query_response.get_points():
        results.append((p['time'], bits_to_gbits(p['download_rate'])))

    return results


def get_network_data_dict_of_lists():
    network_timeseries = query_network_util()
    timestamps = [pd.Timestamp(d[0]) for d in network_timeseries]
    rates = [d[1] for d in network_timeseries]

    df = pd.DataFrame(data={'timestamps': timestamps, 'download_rate': rates})
    return df



def get_network_data():
    return get_network_data_dict_of_lists()


from tornado.ioloop import PeriodicCallback


def network_util_graph():


    renderer = hv.renderer('bokeh')

    # Define DynamicMap callbacks returning Elements

    def network_map(data):
        plot = hv.Curve(data).options(title="Network utilization (algo1)", width=800, padding=0.1)
        return plot

    network_stream = hv.streams.Buffer(get_network_data(), length=500, index=False)

    def cb():
        network_stream.send(get_network_data())

    # Define DynamicMaps and display plot

    network_dmap = hv.DynamicMap(network_map, streams=[network_stream])

    # Render plot and attach periodic callback
    cb_attacher = PeriodicCallback(cb, 100)
    cb_attacher.start()
    return network_dmap, cb_attacher

# network_graph, cb = network_util_graph()
# network_graph

# cb.stop()







def get_cpu_boxplot_data():
    client = InfluxDBClient(host=influx_db_private_ip, database="telegraf-sm")
    mean_cpu_in_use = client.query(
        "SELECT 100 - mean(\"usage_idle\") as \"in_use\" FROM \"cpu\" WHERE \"user\" =~ /armand/ AND time > now()-{} GROUP BY time({}), \"cpu\", \"host\" fill(null);".format(
            '5s', '1s'))
    data = {}
    for host in ['algo-1', 'algo-2']:
        data[host] = []
        for i in range(64):
            data[host].append(list(mean_cpu_in_use.get_points(measurement='cpu',
                                                              tags={"host": host, "cpu": f'cpu{i}'})))
    algo1, algo2 = [], []
    # print(data)
    for i in range(len(data['algo-1'][0])):
        tmp1, tmp2 = [], []
        for j in range(64):
            tmp1.append(data['algo-1'][j][i]['in_use'])
            tmp2.append(data['algo-2'][j][i]['in_use'])
        algo1.append(tmp1)
        algo2.append(tmp2)

    algo = pd.DataFrame({'algo-1': algo1[0], "algo-2": algo2[0]})
    # algo2 = pd.DataFrame({'cpu usage algo2': algo2})
    return algo


def cpu_boxplot():
    renderer = hv.renderer('bokeh')

    def datafunc_down(data):
        algo1_data = data['algo-1']
        algo2_data = data['algo-2']

        return hv.BoxWhisker(algo1_data, vdims='algo-1') + hv.BoxWhisker(algo2_data, vdims='algo-2')

    # def datafunc_up(data):
    #    return hv.BoxWhisker(data, vdims='cpu usage algo2')
    def cb():
        down_stream.send(get_cpu_boxplot_data())

    down_stream = hv.streams.Buffer(get_cpu_boxplot_data(), length=100, index=False)
    mem_dmap = hv.DynamicMap(datafunc_down, streams=[down_stream])

    # Render plot and attach periodic callback

    cb_attacher = PeriodicCallback(cb, 100)
    cb_attacher.start()
    return mem_dmap, cb_attacher


## Pretty wrappers

class UXWrapper:
    def __init__(self, graph, stopper):
        self.graph = graph
        self.stopper = stopper

    def display(self):
        return self.graph

    def stop(self):
        self.stopper.stop()

def init(*args):
    return

def graph(graph_type):
    assert graph_type in ['network-line', 'gpu-heatmap', 'cpu-box']

    if graph_type == 'network-line':
        network_graph, cb = network_util_graph()
        return UXWrapper(network_graph, cb)

    if graph_type == 'gpu-heatmap':
        gpu_graph, callback = gpu_util()
        return UXWrapper(gpu_graph, callback)

    if graph_type == 'cpu-box':
        cpu_graph, callback = cpu_boxplot()
        return UXWrapper(cpu_graph, callback)







