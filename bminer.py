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

cfg = {
    'software': 'bminer',
    'algo':     'equihash',
    'units':    'sol',
    'interval': '10',
    'factor':   '1',
    'urlstr':   'http://{IP}:1880/api/status'
}

cons = True

def dispatch_value(rigname, ti, t, v):
    c = collectd.Values()
    c.host = rigname
    c.plugin = cfg['algo']
    c.type_instance = ti
    c.dispatch(type = t, values = v)

# store all bminer instances
rigs = []

def readconf(config):
    for node in config.children:
        collectd.info('node: {0} = {1}'.format(node.key, node.values[0]))

        # new miner instance definition
        if node.key == 'Instance':

            # create new dict object
            rig = {}

            # iterate the children and fill in the rig data dict
            for inst in node.children:
                collectd.info('instance {0} : {1} = {2}'.format(node.values[0], inst.key, inst.values[0]))
                rig[inst.key] = inst.values[0]

            # add miner to rig list
            rigs.append(rig)

        # global config variables
        for k in ['interval']:
            if node.key == k:
                cfg[k] = node.values[0]


def readvals_bminer(url, rigname):
    try:
        j = miner.GetData_RestApi(url)
    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return str(e)

    start_time = j['start_time']
    end_time = time.time()

    software = "bminer " + j['version']
    uptime = end_time - start_time
    
    num = 0
    rates = []
    temps = []
    watts = []
    num_miners = len(j['miners'])
    miners = j['miners']
    for x in miners:
        m = miners[x]
        device = m['device']
        solver = m['solver']
        ti = 'worker' + str(num)
        dispatch_value(rigname, ti, 'rate', [solver['solution_rate']])
        dispatch_value(rigname, ti, 'temp', [device['temperature']])
        dispatch_value(rigname, ti, 'watt', [device['power']])
        num = num + 1
    return ''

def readvals():
    try:
        for rig in rigs:
            collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
            error = readvals_bminer(rig['url'], rig['rigname'])
            print(error)
    except KeyError, e:
        print(e)

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
