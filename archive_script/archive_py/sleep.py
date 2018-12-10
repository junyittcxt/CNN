

import optparse


import datetime
import time
import os

optparser = optparse.OptionParser()
optparser.add_option("-a", "--assetindex", default=0, help="assetindex")
optparser.add_option("-d", "--gpudevice", default=0, help="gpudevice")
optparser.add_option("-t", "--tt", default=0, help="gpudevice")
opts = optparser.parse_args()[0]

tt = int(opts.tt)
print("starting: ", tt)
time.sleep(tt)

print("Done!", t)
