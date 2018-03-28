#!/usr/bin/env python

import requests
import collectd
import re
import json
import sys
import time
import socket
import urlparse
import telnetlib
import miner

import subprocess
import pprint
import pynvml as N

cfg = {}
cfg['interval'] = 30

def readconf(config):
    for node in config.children:
        collectd.info('node: {0} = {1}'.format(node.key, node.values[0]))

        # global config variables
        for k in ['interval']:
            if node.key == k:
                cfg[k] = node.values[0]

def get_gpu_stat(handle):
	ret = {}

	# get temperature
	try:
		ret['temp'] = N.nvmlDeviceGetTemperature(handle, N.NVML_TEMPERATURE_GPU)
	except:
		ret['temp'] = None

	# get power usage
	try:
		ret['watt'] = N.nvmlDeviceGetPowerUsage(handle) / 1000
	except:
		ret['watt'] = None

	ret['fan'] = 0

	# return information gathered
	print("temp: {0}, watt: {1}".format(ret['temp'], ret['watt']))
	return ret

def send_health_info(ti, rigname, v):
	c = collectd.Values()
	c.host = rigname
	c.plugin = 'health'
	c.type_instance = str(ti)
	c.dispatch(type = 'worker', values = v)

def readvals():
	hostname = socket.gethostname()

	N.nvmlInit()
	gpu_list = []
	device_count = N.nvmlDeviceGetCount()

	for index in range(device_count):
		handle = N.nvmlDeviceGetHandleByIndex(index)
		gpu_stat = get_gpu_stat(handle)
		send_health_info(index, hostname, [ 0, gpu_stat['temp'], gpu_stat['watt'], gpu_stat['fan'] ] )
		gpu_list.append(gpu_stat)
	N.nvmlShutdown()
	pprint.pprint(gpu_list)


if __name__ == '__main__':
	readvals()

else:
	collectd.register_config(readconf)
	collectd.register_read(readvals, int(cfg['interval']))

