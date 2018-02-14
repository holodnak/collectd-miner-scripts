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
    'urlstr':   '{IP}:3333'
}

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

        # new miner instance definition
        if node.key == 'Instance':

            # create new dict object
            rig = {}

            # iterate the children and fill in the rig data dict
            for inst in node.children:
                rig[inst.key] = inst.values[0]

            # add miner to rig list
            rigs.append(rig)

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
        ratestr = j['result'][3]
        rates = ratestr.split(';')
        num = 0
        for n in rates:
            collectd.info('dispatching: {0} @ {1}'.format('worker' + str(num) + "/rate", str(n)))
            dispatch_value(rigname, 'worker' + str(num), 'rate', [str(n)])
            num = num + 1

        # send temperatures and fan speeds to collectd
        tempfans = j['result'][6].split(';')
        i = 0
        num = 0
        for n in tempfans:
            if i == 0:
                collectd.info('dispatching: {0} @ {1}'.format('worker' + str(num) + "/temp", str(n)))
                dispatch_value(rigname, 'worker' + str(num), 'temp', [str(n)])
                i = 1
            else:
                collectd.info('dispatching: {0} @ {1}'.format('worker' + str(num) + "/fan", str(n)))
                dispatch_value(rigname, 'worker' + str(num), 'fan', [str(n)])
                i = 0
                num = num + 1

    except NameError, e:
        collectd.info('error parsing json for {0}:  {1}'.format(cfg['software'], e))
        return

    return

def readvals():
    try:
        for rig in rigs:
            collectd.info('clay_reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
            readvals_claymore(rig['url'], rig['rigname'])
    except KeyError, e:
        collectd.info(e)

collectd.register_config(readconf)
collectd.register_read(readvals, int(cfg['interval']))
