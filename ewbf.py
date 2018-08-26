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
import time

cfg = {
    'software': 'ewbf',
    'algo':     'equi2109',
    'units':    'sol',
    'interval': '10',
    'factor':   '1',
    'urlstr':   '{IP}:2222',
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
      software = "ewbf 0.5"
      uptime = time.time() - j['start_time']
      pool = j['current_server']
      num = 0
      num_miners = len(j['result'])
      miners = j['result']
      for x in miners:
        miner.dispatch_worker(num, rigname, cfg['algo'], [x['speed_sps'], x['temperature'], x['gpu_power_usage'], 0])
        num = num + 1
      collectd.info('dispatching...')
      miner.dispatch_miner(miner.get_master(), 'rigpass', rigname, software, cfg['algo'], uptime, pool, 1, 'sol')
    except:
      collectd.info('error processing for ' + url)
    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_bminer(rig['url'], rig['rigname'])

if __name__ == "__main__":
    print "main"
    readvals_bminer('http://192.168.50.156:2222/getstat', 'miner')
    sys.exit() 

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
