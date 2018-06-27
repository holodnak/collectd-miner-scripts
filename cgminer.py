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
    'software': 'cgminer',
    'algo':     'multi',
    'units':    'hash',
    'interval': '10',
    'factor':   '1',
    'urlstr':   '{IP}:4028',
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
        for k in ['interval', 'algo']:
            if node.key == k:
                cfg[k] = node.values[0]

def process_ret(j):
    v = j.split(";")
    dat = {}
    for vv in v:
        kv = vv.split("=")
        dat[kv[0]] = kv[1]
    return dat





def linesplit(socket):
    buffer = socket.recv(4096)
    done = False
    while not done:
        more = socket.recv(4096)
        if not more:
            done = True
        else:
            buffer = buffer+more
    if buffer:
        return buffer

def get_cgminer(api_command, api_ip, api_port):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((api_ip,int(api_port)))
    if len(api_command) == 2:
        s.send(json.dumps({"command":api_command[0],"parameter":api_command[1]}))
    else:
        s.send(json.dumps({"command":api_command[0]}))
    response = linesplit(s)
    response = response.replace('\x00','')
    response = json.loads(response)
#   print response
    s.close()
    return response





def readvals_cmore(url, rigname, rig):

    # fetch miner data from its api
    try:
        u = url.split(':')
        ip = u[0]
        port = u[1]
        res = get_cgminer(["summary"], ip, port);
        res2 = get_cgminer(["pools"], ip, port);

    except ValueError, e:
        collectd.info('error getting restapi for {0}:  {1}'.format(cfg['software'], e))
        return
    # process the json returned
    try:
        sta = res['STATUS'][0]
        res = res['SUMMARY'][0]
        res2 = res2['POOLS'][0]
        software = sta['Description']
        uptime = str(res["Elapsed"])
        pools = res2['Stratum URL']

        cfg['units'] = rig["units"]
        cfg['algo'] = rig["algo"]
        cfg['factor'] = 1000

        # send hashrates to collectd
        workers = {}
        if 'GHS 5s' in res:
            rate = res['GHS 5s'];
        if 'MHS 5s' in res:
            rate = res['MHS 5s'];
        if 'KHS 5s' in res:
            rate = res['KHS 5s'];
        num = 0
        w = {
            'rate': int(float(rate) * cfg['factor']),
            'temp': 0,
            'watt': 0,
            'fan' : 0,
            'num' : 0
        }
        workers[num] = w
        num = 1

        for n in workers:
            w = workers[n]
            miner.dispatch_worker(w['num'], rigname, cfg['algo'], [w['rate'], w['temp'], w['watt'], w['fan']])
        miner.dispatch_miner(miner.get_master(), 'rigpass', rigname, software, cfg['algo'], uptime, pools, cfg['factor'], cfg['units'])

    except NameError, e:
#        collectd.info('error parsing json for {0}:  {1}'.format(cfg['software'], e))
        print ("err {0}".format(e))
        return

    return

def readvals():
    for rig in cfg['rigs']:
        collectd.info('reading: {0} @ {1}'.format(rig['rigname'], rig['url']))
        readvals_cmore(rig['url'], rig['rigname'], rig)

if __name__ == '__main__':
    readvals_cmore('192.168.50.74:4028', 'test', cfg)

else:
    collectd.register_config(readconf)
    collectd.register_read(readvals, int(cfg['interval']))

