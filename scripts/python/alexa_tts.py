#!/usr/bin/python

import sys
from optparse import OptionParser

from alexa_interface import setup_alexa, get_volume, speak

def main():

    parser = OptionParser()
    parser.add_option('-u', dest='username', help="Amazon username (email address)")
    parser.add_option('-p', dest='password', help="Password")
    parser.add_option('-d', dest='device',   help="target device name")
    parser.add_option('-V', '--volume', dest='volume',   help="Volume (1-100)", type="int", default=30)
    parser.usage = "%prog [options] <text to speak>"

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Missing text to speak")
        
    dev = setup_alexa(options.username, options.password, options.device)

    if dev:
        speak(dev, " ".join(args), options.volume)
    else:
        print("Device '" + options.device + "' not found or login failed")
        sys.exit(3)
        
main()
sys.exit(0)
