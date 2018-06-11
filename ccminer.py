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
    'software': 'ccminer',
    'algo':     'multi',
    'units':    'hash',
    'interval': '10',
    'factor':   '1',
    'urlstr':   '{IP}:4068',
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

def process_ret(j):
    v = j.split(";")
    dat = {}
    for vv in v:
        kv = vv.split("=")
        dat[kv[0]] = kv[1]
    return dat

def readvals_claymore(url, rigname):

    # fetch miner data from its api
    try:
        j = miner.GetData_Raw(url, "summary")
        j2 = miner.GetData_Raw(url, "pool")
        j3 = miner.GetData_Raw(url, "threads")

    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return

    dat = process_ret(j)
    dat2 = process_ret(j2)
    dat3 = miner.parse_raw(j3)
    # process the json returned
    try:
        software = dat["NAME"] + " v" + dat["VER"]
        uptime = str(dat["UPTIME"])
        pools = dat2["POOL"]

        cfg['units'] = "KHS"
        cfg['algo'] = dat["ALGO"]
        cfg['factor'] = 1

        # send hashrates to collectd
        workers = {}
        num = 0
        for n in dat3:
            w = {
              'rate': n["KHS"],
              'temp': 0,
              'watt': 0,
              'fan' : 0,
              'num' : n["GPU"] 
            }
            workers[num] = w
            num = num + 1

        for n in workers:
            w = workers[n]
            miner.dispatch_worker(w['num'], rigname, cfg['algo'], [w['rate'], w['temp'], w['watt'], w['fan']])
        miner.dispatch_miner(miner.get_master(), 'rigpass', rigname, software, cfg['algo'], uptime, pools, cfg['factor'], cfg['units'])

    except NameError, e:
        collectd.info('error parsing json for {0}:  {1}'.format(cfg['software'], e))
        return

    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_claymore(rig['url'], rig['rigname'])

if __name__ == '__main__':
    readvals_claymore('localhost:4068', 'miner3')

else:
    collectd.register_config(readconf)
    collectd.register_read(readvals, int(cfg['interval']))

