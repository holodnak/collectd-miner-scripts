#!/usr/bin/env python
import telnetlib
import requests
import json
from urlparse import urlparse

import collectd

# for ethminer and claymore
def GetData_JsonRpc(url):

	u1 = urlparse(url)
	url = u1.netloc
	u = url.split(':')
	ip = u[0]
	port = u[1]
	j = ''
	collectd.info("GetData_JsonRpc: connecting to: " + ip + ':' + port)

	json_str = "{\"id\":0,\"jsonrpc\":\"2.0\",\"method\":\"miner_getstat1\"}";
	try:
		tn = telnetlib.Telnet(ip, port, 15)
	except:
		collectd.info("GetData_JsonRpc: Unable to connect to miner: " + ip + ':' + port)
		print "Unable to connect to miner: " + ip + ':' + port
		return j
	#tn.set_debuglevel(100)
	tn.write(json_str + "\n")
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
