import subprocess
import os
out = subprocess.Popen("lsusb", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
lines = out.stdout.readlines()
for l in lines:
    if "Intel" in l.decode('utf-8'):
        entries = l.decode('utf-8').split()
        idx = entries.index('ID')
        addr = entries[idx+1]
        break

cmd = "usbreset %s" % addr
print(cmd)
os.system(cmd)
