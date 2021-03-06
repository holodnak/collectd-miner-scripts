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
    'software': 'claymore',
    'algo':     'ethash',
    'units':    'hash',
    'interval': '10',
    'factor':   '1000',
    'urlstr':   '{IP}:3333',
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

def readvals_claymore(url, rigname):

    # fetch miner data from its api
    try:
        j = miner.GetData_JsonRpc(url)
    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return

    # process the json returned
    try:
        if j == '':
            return

        software = "Claymore " + j['result'][0]
        uptime = str(int(j['result'][1]) * 60)
        pools = j['result'][7]

        # detect claymore type
        alg = software[-3:]

        # equihash
        if alg == 'ZEC':
            cfg['units'] = "sol"
            cfg['algo'] = "equihash"
            cfg['factor'] = 1

        # ethash
        elif alg == 'ETH':
            cfg['units'] = "hash"
            cfg['algo'] = "ethash"
            cfg['factor'] = 1000

        # unknown
        else:
            collectd.info('unknown claymore type: {0}'.format(software))
            return

        # send hashrates to collectd
        workers = {}

        ratestr = j['result'][3]
        rates = ratestr.split(';')
        num = 0
        for n in rates:
            w = { 
              'rate': str(n),
              'temp': 0,
              'watt': 0,
              'fan' : 0,
              'num' : num
            }
            workers[num] = w
            num = num + 1

        # send temperatures and fan speeds to collectd
        tempfans = j['result'][6].split(';')
        i = 0
        num = 0
        for n in tempfans:
            if i == 0:
                workers[num]['temp'] = str(n)
                i = 1
            else:
                workers[num]['fan'] = str(n)
                i = 0
                num = num + 1

        for n in workers:
            w = workers[n]
            miner.dispatch_worker(w['num'], rigname, cfg['algo'], [w['rate'], w['temp'], w['watt'], w['fan']])
        miner.dispatch_miner(miner.get_master(), 'rigpass', rigname, software, cfg['algo'], uptime, pools, 1000, 'hash')

    except NameError, e:
        collectd.info('error parsing json for {0}:  {1}'.format(cfg['software'], e))
        return

    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_claymore(rig['url'], rig['rigname'])

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
