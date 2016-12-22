#!/usr/bin/python

import keystoneclient.v2_0.client as ksclient
import urllib2
import json
import os
import argparse

from datetime import datetime, timedelta

parser = argparse.ArgumentParser()
parser.add_argument('--user', default='admin', help='keystone user')
parser.add_argument('--password', default='admin', help='keystone password')
parser.add_argument('--keystone_host', default='localhost', help='keystone server ip')
parser.add_argument('--ceilometer_host', default='localhost', help='ceilometer server ip')

args = parser.parse_args()
args = vars(args)
user = args['user']
passwd = args['password']
keystone_host = args['keystone_host']
ceilometer_host = args['ceilometer_host']

keystone = ksclient.Client(auth_url="http://{0}:5000/v2.0".format(keystone_host),
        username=user,
        password=passwd,
        tenant_name="admin")

token = keystone.auth_ref['token']['id']

headers = {'X-Auth-Token': token}
subtract = datetime.now() + timedelta(days=-1)

cur_date = str(datetime.now())[:10]
old_date = str(subtract)[:10]

# Send the GET request
url = "http://{0}:8777/v2/events?q.field=start_time&q.field=end_time&q.op=eq&q.op=eq&q.type=&q.type=&q.value={1}T00:00:00&q.value={2}T00:00:00".format(ceilometer_host,old_date,cur_date)
#Use code below for a specific date and time
#url = "http://{0}:8777/v2/events?q.field=start_time&q.field=end_time&q.op=eq&q.op=eq&q.type=&q.type=&q.value=2015-03-19T14:50:14&q.value=2015-03-25T00:00:00".format(ceilometer_host)
req = urllib2.Request(url, None, headers)

# Read the response
resp = urllib2.urlopen(req).read()
decode = json.loads(resp)

# Path to be created
path = "/var/www/nailgun/reports/"

if not os.path.exists(path):
    os.makedirs(path)

g = open(os.path.join(path, old_date + '.yaml'),'w')
g.write("---\n")
g.close()
for a in decode:
   f = open(os.path.join(path, old_date + '.yaml'),'a')
   if a["event_type"] in ['compute.instance.create.end', 'compute.instance.delete.end']:
       f.write("-\n  type: \"instance\"\n  action: \"{0}\"\n  timestamp: \"{1}\"\n  name: \"{2}\"\n  id: \"{3}\"\n  vcpus: \"{4}\"\n  ram: \"{5}\"\n  tenant: \"{6}\"\n  user_id: \"{7}\"\n".format(
                               a["event_type"][17:23],
                               a["generated"],
                               a["traits"][10]["value"],
                               a["traits"][11]["value"],
                               a["traits"][9]["value"],
                               a["traits"][-1]["value"],
                               a["traits"][6]["value"],
                               a["traits"][2]["value"]))
   elif a["event_type"] in ['image.create', 'image.delete'] and a["traits"][6]["value"] == 'snapshot':
       f.write("-\n  type: \"instance snapshot\"\n  action: \"{0}\"\n  timestamp: \"{1}\"\n  name: \"{2}\"\n  id: \"{3}\"\n  instance_id: \"{4}\"\n  vcpus: \"{5}\"\n  ram: \"{6}\"\n  tenant: \"{7}\"\n  user_id: \"{8}\"\n".format(
                               a["event_type"][6:12],
                               a["generated"],
                               a["traits"][3]["value"],
                               a["traits"][5]["value"],
                               a["traits"][-4]["value"],
                               a["traits"][-3]["value"],
                               a["traits"][1]["value"],
                               a["traits"][-2]["value"],
                               a["traits"][2]["value"]))
   elif a["event_type"] in ['volume.create.end', 'volume.delete.end']:
       f.write("-\n  type: \"volume\"\n  action: \"{0}\"\n  timestamp: \"{1}\"\n  name: \"{2}\"\n  id: \"{3}\"\n  size: \"{4}\"\n  tenant: \"{5}\"\n  user_id: \"{6}\"\n".format(
                               a["event_type"][7:13],
                               a["generated"],
                               a["traits"][1]["value"],
                               a["traits"][6]["value"],
                               a["traits"][-1]["value"],
                               a["traits"][4]["value"],
                               a["traits"][-3]["value"]))
   elif a["event_type"] in ['snapshot.create.end', 'snapshot.delete.end']:
       f.write("-\n  type: \"volume snapshot\"\n  action: \"{0}\"\n  timestamp: \"{1}\"\n  name: \"{2}\"\n  id: \"{3}\"\n  volume_id: \"{4}\"\n  size: \"{5}\"\n  tenant: \"{6}\"\n  user_id: \"{7}\"\n".format(
                               a["event_type"][9:-4],
                               a["generated"],
                               a["traits"][1]["value"],
                               a["traits"][6]["value"],
                               a["traits"][-1]["value"],
                               a["traits"][-5]["value"],
                               a["traits"][4]["value"],
                               a["traits"][-3]["value"]))
   elif a["event_type"] in ['network.create.end', 'network.delete.end']:
       f.write("-\n  type: \"network\"\n  action: \"{0}\"\n  timestamp: \"{1}\"\n  id: \"{2}\"\n".format(a["event_type"][8:-4],a["generated"],a["traits"][2]["value"]))
   f.close()
