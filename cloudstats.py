#!/usr/bin/env python

#v 1.2.1

import urllib2, urllib, socket, os, statvfs, commands, sys
from cloudstats_services import *
from cloudstats_core import *

cloudstatsapp = "https://DOMAIN.cloudstats.me/status/updateKEY"

# SET THIS TO YOUR SERVER ID INSIDE CloudStats IF YOU HAVE
# MULTIPLE SERVERS BEHIND A NAT/FIREWALL AND THEY REPORT WITH
# THE SAME IP ADDRESS
server_id = 0

#if os.path.isfile("/tmp/cloudstats.lock"):
#  print "Exiting: running already... or delete /tmp/cloudstats.lock "
#  sys.exit()

#cloudstats_lock = open('/tmp/cloudstats.lock', 'w')
#cloudstats_lock.close()


###############################
## CloudStats CORE                 ##
###############################
disk = disk()
load = os.getloadavg()
disk_free,disk_size,disk_used = disk[0],disk[1], disk[2]
kernel = kernel()
release_info = release_info();
procs = running_procs()
opsys = operating_system()
conns = connection_count()
memory = memory_usage()
free_memory,used_memory = memory[1],memory[0]
ncpus = number_of_cpus()
cpu_usage = cpu_usage()
net = network_usage()
in_bytes,out_bytes = net[0],net[1]
ps = process_list()
iostat = iostat()
uptime = uptime()

#package updates
update_cnt = update_count()

###############################
##   CloudStats SERVICES MONITOR   ##
###############################
services = {
    'http': http(),
    'db': database(),
    'ftp': ftp(),
    'ssh': ssh(),
    'nfs': nfs(),
    'dns': dns(),
    'mail': mail(),
    'memcached': memcached(),
    'puma': puma()
    }

for i in range(1,len(sys.argv)):
  services[sys.argv[i]] = globals()[sys.argv[i]]()


login = {
        'server_id': server_id,
        'srvly[cpu_usage]': cpu_usage,
        'srvly[disk_used]': disk_used,
        'srvly[disk_size]': disk_size,
        'srvly[mem_used]': used_memory,
        'srvly[mem_free]': free_memory,
        'srvly[running_procs]': procs,
        'srvly[load_one]': "%.2f" % load[0],
        'srvly[load_five]': "%.2f" % load[1],
        'srvly[load_fifteen]': "%.2f" % load[2],
        'srvly[net_in]': in_bytes,
        'srvly[net_out]': out_bytes,
        'srvly[number_of_cpus]': ncpus,
        'srvly[os]': opsys,
        'srvly[ps]': ps,
        'srvly[blk_reads]': iostat[0],
        'srvly[blk_writes]': iostat[1],
        'srvly[uptime]': uptime,
        'srvly[connections]': conns,
    	'srvly[kernel]': kernel,
        'srvly[release]': release_info,
        'services': services,
        'srvly[pending_updates]': update_cnt,
        'srvly[hostname]': socket.gethostname()
    }

try:
  e = urllib2.urlopen(cloudstatsapp, urllib.urlencode(login))
  print "Status posted to " + cloudstatsapp
  print e.read()
  #print login

except Exception, e:
  print "There was an error posting to cloudstats. Please contact support."
  raise e

#os.unlink('/tmp/cloudstats.lock')
