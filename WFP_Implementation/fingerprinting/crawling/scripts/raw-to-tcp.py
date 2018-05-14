#!/usr/bin/python
# coding=utf-8
#
# Extract TCP information from dump

import sys, os, glob

def exit_with_help(error=''):
    print("""\
Usage: raw-to-tcp.py [options]

options:
    -crawlingPath { /Path/ } : Path to the Crawling Directory
    
    -tcp-Wang-format { YES/NO } : If it is set, it converts 
			the '.raw' tcpdump files into the text version 
			of tcpdump. By default: NO.
    
 """)
    print(error)
    sys.exit(1)
    
tmp1 = 'NO' # Option "-tcp-Wang-format" is disabled by default

# Arguments to be read from WFP_conf
args = [ ('crawlingPath', 'dir_CRAWLING', 'crawlingPath') ]

# Checking if all variables are/will be set
for var, env, arg in args:
    if not '-'+arg in sys.argv:
        vars()[var] = os.getenv(env)
        if vars()[var] == None:
            exit_with_help('Error: Environmental Variables or Argument'+
                            ' insufficiently set! ($'+env+' / "-'+arg+'")')

# Read parameters from command line call
if len(sys.argv) != 0:
    i = 0
    options = sys.argv[1:]
    # iterate through parameter
    while i < len(options):
        if options[i] == '-crawlingPath':
            i = i + 1
            crawlingPath = options[i]
            if not crawlingPath.endswith('/'):
                crawlingPath += '/'
        elif options[i] == '-tcp-Wang-format':
			i = i + 1
			tmp1 = options[i]
        else:
            exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
        i = i + 1
        

if tmp1 in [ 'YES', 'NO' ]:
    if tmp1 == 'YES':
        tcpWangFormat = True
    else:
        tcpWangFormat = False
else:
    exit_with_help('Error: Unknown TCP-Wang-format Option!')

rawfiles = glob.glob(crawlingPath + 'dumps/*.raw')

# Process every dump
for rawfile in rawfiles:
	fullpath, extension = os.path.splitext(rawfile)

	if not tcpWangFormat:
		os.system("""sudo tcpdump -r {0} -n -l -tt -q -v | sed -e 's/^[ 	]*//' | awk '/length ([0-9][0-9]*)/{{printf "%s ",$0;next}}{{print}}' > {1}""".format(rawfile, fullpath + '.tcpdump'))

	else:
		# Convert every raw file into the text version of the tcpdump (needed for Wang's format!)
		os.system("""sudo tcpdump -nnttXSr {0} > {1}""".format(rawfile, fullpath + '.txt'))
