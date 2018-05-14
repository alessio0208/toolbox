#!/usr/bin/python
# coding=utf-8
#
# Convert TLS instances to Cell, CellNoSendMe and TLSNoSendMe format
#
# The ouputfile is in the form:
# [url] [start timestamp] [number of entries] [timestamp]:[IP of entry node]:[size] [timestamp]:[IP of entry node]:[size] ...

import sys, os, shutil, glob

def exit_with_help(error=''):
	print("""\
Usage: parse-cells.py [options]

options:
	-crawlingPath { /Path/ } : Path to the Crawling Directory
	-legacy : Uses TLS-Legacy as input format (default: TLS)
	-main : Only uses main stream as input format (default: 'all')
	-formats { format1,...,formatN } : Output the following formats (default: cell, cell-nosendme, tls-nosendme)
 """)
	print(error)
	sys.exit(1)

stream = ''
inputFormat = ''
outputFormats = [ 'cell', 'cell-nosendme', 'tls-nosendme' ]
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
		elif options[i] == '-legacy':
			inputFormat = '-legacy'
		elif options[i] == '-main':
			stream = '-main'
		elif options[i] == '-formats':
			i = i + 1
			outputFormats = options[i].split(',')
		else:
			exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
		i = i + 1


def process_file(inputFile, outputFiles):
	
	for line in inputFile:
		entries = []

		entries.extend(line.rstrip().split(' '))
		if len(entries) < 3:
			print('WARN: No valid instance found!')
			return

		urlname = entries[0]
		timestamp = entries[1]
		entrynodes = int(entries[2])

		currentstream = []

		if entrynodes < 1:
			print('WARN: No entry nodes found!')
			return
			
		# Write instance information
		for i in range(len(outputFiles)):
			outputFiles[i].write(urlname + ' ' + timestamp + ' ' + str(entrynodes))
		
		cell = outputFormats.index('cell') if 'cell' in outputFormats else -1
		cellNoSendMe = outputFormats.index('cell-nosendme') if 'cell-nosendme' in outputFormats else -1
		TLSNoSendMe = outputFormats.index('tls-nosendme') if 'tls-nosendme' in outputFormats else -1
		
		Streams = {}
		# Process all packets
		
		for entry in entries[3:]:
			time, torip, size = entry.split(':')
			
			# Initialize SendMe Removal
			p1 = 45
			p2 = 50
			if not torip in Streams:
				Streams[torip] = (0, 0, 0) # (ccell, csendme, cremout)
			else:
				Streams[torip] = Streams[torip][:-1] + (0,) # cremout = 0
			incoming = (int(size) > 0)
			cells = abs(int(size))/512
			
			if cells > 0:
				for i in range(cells):
					if incoming:
						if cell != -1: outputFiles[cell].write(' {0}:{1}:512'.format(time,torip))
						if cellNoSendMe != -1: outputFiles[cellNoSendMe].write(' {0}:{1}:512'.format(time,torip))
						Streams[torip] = (Streams[torip][0]+1, Streams[torip][1], Streams[torip][2]) # ccell += 1
					else:
						if cell != -1: outputFiles[cell].write(' {0}:{1}:-512'.format(time,torip))
						if Streams[torip][0] < p1:
							if cellNoSendMe != -1: outputFiles[cellNoSendMe].write(' {0}:{1}:-512'.format(time,torip))
						else:
							# next outgoing is sendme
							Streams[torip] = (Streams[torip][0]-p2, Streams[torip][1]+1, Streams[torip][2]+1) # ccell -= p2; csendme+=1; cremout+=1
				if incoming:
					if TLSNoSendMe != -1: outputFiles[TLSNoSendMe].write(' {0}:{1}:{2}'.format(time,torip,size))
				else:
					if cells > Streams[torip][2]: # cremout*512bytes are removed from TLS-record if it contains more cells
						if TLSNoSendMe != -1: outputFiles[TLSNoSendMe].write(' {0}:{1}:{2}'.format(time,torip,int(size)-512*Streams[torip][2]))
		
		for i in range(len(outputFiles)):
			outputFiles[i].write('\n')


# Check if TLS has been extracted
inputDir = 'output-tls{0}{1}/'.format(inputFormat, stream)
if not os.path.isdir(crawlingPath + inputDir):
	print('Execute raw-to-tls.py and parse-'+inputFormat+'.py first!')
	exit()

# Clean Output
for form in outputFormats:
	outputDir = 'output-{0}{1}{2}/'.format(form, inputFormat, stream)
	if os.path.isdir(crawlingPath + outputDir):
		shutil.rmtree(crawlingPath + outputDir)
	os.mkdir(crawlingPath + outputDir)

tlsfiles = glob.glob(crawlingPath + inputDir + '*')

# parse TLS data
for tlsfile in tlsfiles:
	path, inputfilename = os.path.split(tlsfile)

	# Inputfile
	inputFile = open(crawlingPath + inputDir + inputfilename, 'r')
	# Outputfiles
	outputFiles = []
	for form in outputFormats:
		outputDir = 'output-{0}{1}{2}/'.format(form, inputFormat, stream)
		outputFiles.append(open(crawlingPath + outputDir + inputfilename, 'w'))
	
	process_file(inputFile, outputFiles)
	
	# Close files
	inputFile.close()
	for i in range(len(outputFiles)):
		outputFiles[i].close()
