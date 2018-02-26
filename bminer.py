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
    'urlstr':   'http://{IP}:1880/api/status',
    'rigs':     []
}

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
            cfg['rigs'].append(rig)

        # global config variables
        for k in ['interval']:
            if node.key == k:
                cfg[k] = node.values[0]

def readvals_bminer(url, rigname):
    try:
        j = miner.GetData_RestApi(url)
    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return

    try:
        start_time = j['start_time']
    except:
        collectd.info('error getting restapi for {0}'.format(rigname))
        return

    end_time = time.time()

    software = "bminer " + j['version']
    uptime = end_time - start_time
    pool = ''
    num = 0
    num_miners = len(j['miners'])
    miners = j['miners']
    for x in miners:
        m = miners[x]
        device = m['device']
        solver = m['solver']
        miner.dispatch_worker(num, rigname, cfg['algo'], [solver['solution_rate'], device['temperature'], device['power'], 0])
        num = num + 1
    miner.dispatch_miner(miner.get_master(), 'rigpass', rigname, software, cfg['algo'], uptime, pool, 1, 'sol')
    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_bminer(rig['url'], rig['rigname'])

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
