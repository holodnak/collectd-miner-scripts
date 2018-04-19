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
    'software': 'xmrstak',
    'algo':     'cryptonote',
    'units':    'hash',
    'interval': '10',
    'factor':   '1',
    'urlstr':   'http://{IP}:40000/api.json',
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

def readvals_xmrstak(url, rigname):
    try:
        j = miner.GetData_RestApi(url)
    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return

    try:
        software = j['version']
        uptime = j['connection']['uptime']
        pool = j['connection']['pool']
        num = 0
        hashrate = j['hashrate']
        for n in hashrate['threads']:
            rate = n[0]
            if rate == None:
               rate = n[1]
            collectd.info('dispatching: {0} @ {1}'.format('worker' + str(num), str(rate)))
            miner.dispatch_worker(num, rigname, cfg['algo'], [str(rate), 0, 0, 0])
            num = num + 1
        r = requests.post(miner.get_master(), json={"password": "rigpass", "rigname": rigname, "uptime": uptime, "software": software, "algo": cfg['algo'], "pool": pool, "factor": 1, "unit": 'sol'})
    except NameError, e:
        collectd.info('error parsing json for {0}:  {1}'.format(cfg['software'], e))
        return

    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_xmrstak(rig['url'], rig['rigname'])

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
