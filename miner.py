#!/usr/bin/env python
import telnetlib
import requests
import json
from urlparse import urlparse

import collectd

# for ethminer and claymore
def GetData_JsonRpc(url):

        u = url.split(':')
        ip = u[0]
        port = u[1]
	j = ''

	strout = "{\"id\":0,\"jsonrpc\":\"2.0\",\"method\":\"miner_getstat1\"}";
	try:
		tn = telnetlib.Telnet(ip, port, 15)
	except:
		collectd.info("GetData_JsonRpc: Unable to connect to miner: " + ip + ':' + port)
		print "Unable to connect to miner: " + ip + ':' + port
		return j
	#tn.set_debuglevel(100)
	tn.write(strout + "\n")
	ret = tn.read_until("\n", 5)
	tn.close()
	try:
		j = json.loads(ret)
	except:
		collectd.info("GetData_JsonRpc: error parsing json")
		print "error parsing json"
	return j

# for bminer
def GetData_RestApi(url):
    try:
        ret = requests.get(url)
        if ret.status_code != 200:
            collectd.info("GetData_RestApi error: status = " + str(ret.status_code))
            print "error: status = " + str(ret.status_code)
        j = json.loads(ret.text)
    except:
        j = ''
        print "error loading/parsing json"
    return j

def parse_raw(strn):
  ns = strn.split("|")
  ret = []
  for n in ns:
    dat = {}
    if ';' not in n:
      break
    d = n.split(";")
    for v in d:
      kv = v.split("=")
      dat[kv[0]] = kv[1]
    ret.append(dat)
  return ret

# for other
def GetData_Raw(url,strout):

        u = url.split(':')
        ip = u[0]
        port = u[1]
	j = ''

	try:
		tn = telnetlib.Telnet(ip, port, 15)
	except:
		collectd.info("GetData_JsonRpc: Unable to connect to miner: " + ip + ':' + port)
		print "Unable to connect to miner: " + ip + ':' + port
		return j
	#tn.set_debuglevel(100)
	tn.write(strout + "\n")
	ret = tn.read_until("\n", 5)
	tn.close()
	return ret


def dispatch_worker(ti, rigname, plugname, v):
    c = collectd.Values()
    c.host = rigname
    c.plugin = plugname
    c.type_instance = str(ti)
    c.dispatch(type = 'worker', values = v)

def dispatch_miner(remote_url, password, rigname, software, algo, uptime = 0, pool = '', factor = 1, unit = 'sol'):
    try:
        r = requests.post(remote_url, json={"password": password, "rigname": rigname, "uptime": uptime, "software": software, "algo": algo, "pool": pool, "factor": factor, "unit": unit}, timeout=10)
    except:
        collectd.info('error POST-ing miner data to remote host: {0}'.format(remote_url))

def dispatch_miner_stats(remote_url, password, rigname, temp, watt, fan):
    try:
        r = requests.post(remote_url, json={"password": password, "rigname": rigname, "temp": temp, "watt": watt, "fan": fan}, timeout=10)
    except:
        collectd.info('error POST-ing miner stats data to remote host: {0}'.format(remote_url))

# this function returns the master that the stats are POST'ed to
def get_master():
    return 'http://mstat/submit/james'
