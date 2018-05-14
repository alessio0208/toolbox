#!/usr/bin/python
# coding=utf-8
#
########################################################################
#
# ./check-hs-state.py [options]
#
# Goal: Check if a hidden service address is http(s) or not.
#
# Description: Parse files, created by torCtl, that contain only
#		events regarding hidden services, in order to check
#		if a hidden service address is available.
#
# Output: Possible types of output files:
#		'onions_successful_www': torCtl has shown that the connection
#			between a HS and a client has been established and the 
#			browser has indicated correct page loading.
#		'onions_successful_other': torCtl has shown that the connection
#			beteen a HS and a client has been established but the 
#			browser has not indicated correct page loading.
#		'unreachable_onions': torCtl has shown that the descriptor
#			of a given HS has not been found.
#		'onions_without_state': torCtl has shown that the client could 
#			not connect to a introduction point.
#
########################################################################

import sys, os
try:
	from natsort import natsorted
except:
	print('You need natsort! (pip install natsort)')
	sys.exit()

def exit_with_help(error=''):
	print("""\
Usage: check-hs-state.py [options]

options:
   -crawlingPath { /Path/ } : Path to the Instances in Folder Compiled
   -patternspath { /Path/ } : Path to Pattern Files

 """)
	print(error)
	sys.exit(1)
	
def save_in_file(filename, onion_addr):
	outputfile = open(filename, 'a')
	outputfile.write(onion_addr + "\n")
	outputfile.close()
	
# check for all invalid patterns and output filename, if necessary  
def check_invalid_patterns(patterns, onion_group):
	found = False
	for pattern in patterns:
		if pattern.replace('\n','') in txtcontent.replace('\n',''):
			onion_group.add(onion)
			found = True
			break
	return found
	
	
args = [ ('crawlingPath', 'dir_CRAWLING', 'crawlingPath'),
		 ('patternspath', 'dir_FETCH_PATTERNS', 'patternspath') ]

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
		elif options[i] == '-patternspath':
			i = i + 1
			patternspath = options[i]
			if not patternspath.endswith('/'):
				patternspath += '/'
		else:
			exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
		i = i + 1
		
# Check set variables
if not os.path.isdir(crawlingPath):
	exit_with_help('Error: Invalid Compiled Crawling Path!')
if not os.path.isdir(patternspath):
	exit_with_help('Error: Invalid Raw Pattern Path!')				
				
if not os.path.isdir(crawlingPath + 'output-hs/'):
	os.mkdir(crawlingPath + 'output-hs/')
	
# Additional checks
outputUnreachableonions = crawlingPath + "output-hs/" + "unreachable_onions"
outputOnionsWithoutState = crawlingPath + "output-hs/" + "onions_without_state"
outputWwwonions = crawlingPath + "output-hs/" + "onions_successful_www"
outputOtheronions = crawlingPath + "output-hs/" + "onions_successful_other"

# check if outputfiles already exist
errorfiles = natsorted(os.listdir(crawlingPath + "output-hs/"))
for errorfile in errorfiles:
	if os.path.isdir(crawlingPath + "output-hs/" + errorfile):
		continue
		
	os.remove(crawlingPath + "output-hs/" + errorfile)
	
torctlfiles = os.listdir(crawlingPath + 'torctldumps/')

# save onion addr with state 'HSCR_JOINED' indicating connection established
successful_onions = set()

for torctlfile in torctlfiles:

	runfile, extension = os.path.splitext(torctlfile)
	
	if extension != '.torctl':
		continue
        
	torctlfile = open(crawlingPath + 'torctldumps/' + runfile + '.torctl', 'r')
    
	hs_desc_found = False
	rend_point_connected = False
	int_point_connecting = False
	int_point_connected = False
	client_hs_joined = False

	for torctlline in torctlfile:
		if "HS_DESC" in torctlline and "NOT_FOUND" in torctlline:
			break
			
		if "HS_DESC" in torctlline and "RECEIVED" in torctlline:
			hs_desc_found = True
				
		if "HS_CLIENT_REND" in torctlline and "HSCR_ESTABLISHED_IDLE" in torctlline:
			rend_point_connected = True
				
		if "HS_CLIENT_INTRO" in torctlline and "HSCI_CONNECTING" in torctlline:
			int_point_connecting = True
				
		if "HS_CLIENT_INTRO" in torctlline and "HSCI_DONE" in torctlline:
			int_point_connected = True

		if "HS_CLIENT_REND" in torctlline and "HSCR_JOINED" in torctlline:
			client_hs_joined = True
			
	if hs_desc_found == False:
		save_in_file(outputUnreachableonions, runfile)
		
	else:
		if client_hs_joined == True:
			successful_onions.add(runfile)
			
		else:
			save_in_file(outputOnionsWithoutState, runfile)
				
	torctlfile.close()

txtdumps = os.listdir(crawlingPath + 'txtdumps/')

other_onions = set()
www_onions = set()

patternfiles = natsorted(os.listdir(patternspath))

for onion in successful_onions:

	for txtdump in txtdumps:

		# we don't need checktor
		if 'check.torproject' in txtdump:
                	continue
                	
		if '___-___' in txtdump:
			currenttxtdump = txtdump.split('___')[0]
		else:
			currenttxtdump = txtdump.replace('.htm','')
					
		if onion == currenttxtdump:
			# read content of current txtdump
			f = open(crawlingPath + 'txtdumps/' + txtdump, 'r')
			txtcontent = f.read()
			f.close()

			for patternfile in patternfiles:
				if os.path.isdir(patternspath + patternfile):
					continue
				
				runfile, extension = os.path.splitext(patternfile)
		
				if 'Patterns-error' not in runfile:
					continue
				
				pagenameErrorContent = set()

				#stores output filename
				outputerrorfile = crawlingPath + "output-hs/Txtdump" + runfile.replace('Patterns-error','') + 'Errors.txt'

				f = open(patternspath + runfile + '.txt', 'r')
				patterns = f.readlines()
				f.close()

				# check for all invalid patterns and output filename, if necessary
				if runfile.replace('Patterns-error','') == "UnableToConnect":
					if check_invalid_patterns(patterns, other_onions):
						break

				else:
					if check_invalid_patterns(patterns, pagenameErrorContent):
						for pagename in pagenameErrorContent:
							save_in_file(outputerrorfile, pagename)
						if len(www_onions) == 0:
                					www_onions = [ x for x in successful_onions if x not in pagenameErrorContent ]
        					else:
                					www_onions = [ x for x in www_onions if x not in pagenameErrorContent ]
						break
			break
		
www_onions = [ x for x in www_onions if x not in other_onions ]

if len(www_onions) > 0:
	for www_onion in www_onions:
		save_in_file(outputWwwonions, www_onion)
	
if len(other_onions) > 0:
	for other_onion in other_onions:
		save_in_file(outputOtheronions, other_onion)
