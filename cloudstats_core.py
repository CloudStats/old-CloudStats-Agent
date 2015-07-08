import urllib2, urllib, socket, os, statvfs, commands, sys, re
from locale import *
# Linux / Darwin / SunOS
op_sys = os.popen('uname').readline().strip()
try:
   setlocale(LC_NUMERIC, getdefaultlocale())
except NameError:
   print "Default locale updated. Collecting Data. Please wait..."
except ValueError:
   setlocale(LC_NUMERIC, '')

try:
    any
except NameError:
    def any(s):
        for v in s:
            if v:
                return True
        return False

def iostat():
  iostat_list = os.popen("iostat -d 2 5 -x | awk '{print $4}'")
  blk_reads = 0.0
  blk_writes = 0.0
  for i in iostat_list:
    if i[0].strip() != '(' and i.strip() != 'r/s':
      try:
        blk_reads += atof(i)
      except ValueError:
        continue
  iostat_list = os.popen("iostat -d 2 5 -x | awk '{print $5}'")
  for i in iostat_list:
    if i[0].strip() != '(' and i.strip() != 'w/s':
      try:
        blk_writes += atof(i)
      except ValueError:
        continue


  return [blk_reads, blk_writes]

def uptime():
  return os.popen("uptime").readline()

def disk():
  global op_sys
  disk_volume_index = 1
  if op_sys == "Darwin":
    disk_list = os.popen("df -h | grep -v sshfs | awk {'print $1 \" | \" $NF'}")
    disk_volume_index = 0
  else:
    disk_list = os.popen("df -h -x nfs -x sshfs -x tmpfs |awk {'print $1 \" | \" $NF'}")

  disk_free = 0
  disk_size = 0
  disk_used = 0

  for d in disk_list:
    dd = d.split('\n')[0]
    if dd.split('|')[1] != " on":
      try:
        disk = os.statvfs(dd.split('|')[disk_volume_index].strip())
        #print dd.split('|')[1].strip()
        # bytes
        disk_free += (disk.f_bavail * disk.f_frsize)
        disk_size += (disk.f_blocks * disk.f_frsize)
        disk_used += (disk.f_blocks * disk.f_frsize) - (disk.f_bavail * disk.f_frsize)
      except OSError:
        print "\tSkipping disk: " + dd.split('|')[disk_volume_index].strip()
  return [disk_free, disk_size, disk_used]

def release_info():
  release_info = ""
  release_info = os.popen("cat /etc/*release 2> /dev/null").readline()
  if len(release_info) == 0:
    release_info += os.popen("cat /etc/debian_version 2> /dev/null").readline()
  return release_info

def kernel():
  return os.popen("uname -a").readline()

def running_procs():
  return  os.popen("ps ax | wc -l").readline()

def operating_system():
  return os.popen("uname").readline()

def connection_count():
  return int(commands.getoutput("netstat -an | grep -c ':'"))

def memory_usage():
  global op_sys
  # memory usage - EXPECTS BYTES TO BE SENT SO MAKE SURE YOU MULTIPLY BY PROP VALUE
  free_memory = 0
  used_memory = 0
  if op_sys == "Darwin":
    free = commands.getoutput("top -l 1 | head -n 7 | tail -n 1 | awk '{print $2 \" \" $4 \" \" $6 \" \" $10}'  | sed 's/M//g'").split(' ')
    used_memory = atof(free[0]+free[1]+free[2]) * 1024 * 1024
    free_memory = atof(free[3]) * 1024 * 1024
  else:
    meminfo = open('/proc/meminfo').read()
    matched_mem_total = re.search(r'^MemTotal:\s+(\d+)', meminfo)
    if matched_mem_total:
        mem_total = int(matched_mem_total.groups()[0]) * 1024

    matched_mem_aval = re.search(r'MemAvailable:\s+(\d+)', meminfo)
    if matched_mem_aval:
        free_memory = int(matched_mem_aval.groups()[0]) * 1024
    else:
        free = commands.getoutput("free | grep Mem | tr -s ' ' | cut -d ' ' -f3,4").split(' ')
        free_memory = atof(free[1]) * 1024

    used_memory = mem_total - free_memory

  return [used_memory,free_memory]

def number_of_cpus():
  global op_sys
  if op_sys == "Darwin":
    return int(os.popen("system_profiler | grep 'Number Of Processors: ' | grep -o '[0-9]'").readline())
  else:
    return int(os.popen("cat /proc/cpuinfo | grep -c 'processor'").readline())

def cpu_usage():
  return 100.0 - atof(os.popen("sar -u 1 20 | awk '{ print $NF }' | tail -n 1").readline())

def network_usage():
  # Interfaces to be excluded
  # by default loop interface it's excluded from the network usage
  #
  EXCLUDE = ['lo']
  #
  # Add another interface using the syntax:
  # EXCLUDE += ['<interface name>']
  # example
  # EXCLUDE += ['br']
  #
  #Uncomment the above line to exclude virtual interfaces
  # EXCLUDE += ['venet', 'br', 'tap', 'vifvm', 'vboxnet']


  # lets get network usage now via sar, we need to figure out which columns are what and sum them
  net = commands.getoutput("sar -n DEV 15 1").split('\n')
  # look through first line
  find_iface = net[2]
  #print find_iface
  in_bytes = 0
  out_bytes = 0
  i = 0
  in_bytes_col = 0
  out_bytes_col = 0
  kilo = 1
  for h in find_iface.split(' '): #find the position column of the if headers
      if len(h) > 0:
          if h == "Ibytes/s" or h == "rxbyt/s" or h == "rxkB/s":
             in_bytes_col = i
          if h == "rxkB/s":
	     kilo = 1024
          if h == "Obytes/s" or h == "txbyt/s" or h == "txkB/s":
              out_bytes_col = i
          i+=1
  for c in net[3:-1]:
      if not any(x in c for x in EXCLUDE):
          this_c = c.split(' ')
          x = 0
          for col in this_c:
              if len(col) > 0 and this_c[0] != "Average:":
                              try:
                                      if x == in_bytes_col:
                                              in_bytes+=atof(col) * kilo
                                      if x == out_bytes_col:
                                              out_bytes+=atof(col) * kilo
                              except ValueError:
                                      pass
                              x+=1

  return [in_bytes,out_bytes]

def process_list():
  global op_sys
  if op_sys == "Darwin":
    ps_output = os.popen('ps -eo user,pid,ppid,rss,vsize,pcpu,pmem,command -O vsize')
  else:
    ps_output = os.popen('ps -eo user,pid,ppid,rss,vsize,pcpu,pmem,command --sort vsize')

  ps = ""
  for x in ps_output:
	ps += x
  return ps

def update_count():
  global op_sys
  if op_sys == "Darwin":
    try:
      x = int(os.popen("softwareupdate -l | grep -v Missing | grep -c '*'"))
    except TypeError:
      x = 0
    return x
  else:
    if os.popen("which aptitude").readline().strip() == "/usr/bin/aptitude":
      x = os.popen("aptitude safe-upgrade -s | grep upgraded | grep -v following").readline().split(',')[0]
      try:
        x = int(x.strip('packages upgraded').strip())
      except ValueError:
        x = 0

      return x
    else:
      if os.popen("which yum").readline().strip() == '/usr/bin/yum':
        EXCLUDE = '.i386\|.x86_64\|.noarch\|.src\|.nosrc\|.alpha\|.sparc\|.mips\|.ppc\|.m68k\|.SGI'
        return int(os.popen("yum check-update | grep '" + EXCLUDE + "' | wc -l").readline())
      else:
        return 0
