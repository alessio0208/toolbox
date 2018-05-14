#!/usr/bin/python
# coding=utf-8
#
# Extract main stream from instances
#
# The packets over the main entry are considered! A main entry is that entry over which the 
# most packets are transmitted with respect to the absolute packet size.
#
# The ouputfile is in the form:
# [url] [start timestamp] [number of entries] [timestamp]:[IP of entry node]:[size] [timestamp]:[IP of entry node]:[size] ...

import sys, os, shutil, glob

def exit_with_help(error=''):
	print("""\
Usage: extract-main.py [options]

options:
	-crawlingPath { /Path/ } : Path to the Crawling Directory
	-tcp : Uses TCP as input format (default: TLS)
	-legacy : Uses TLS-Legacy as input format (default: TLS)
 """)
	print(error)
	sys.exit(1)

mainFormat = 'tls'
inputFormat = ''
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
		elif options[i] == '-tcp':
			mainFormat = 'tcp'
		else:
			exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
		i = i + 1

if inputFormat == '-legacy' and mainFormat == 'tcp':
	print('Legacy Format is only applicable with TLS!')
	sys.exit(0)

class Substream:
	def __init__(self, entry=''):
		self.entry = entry
		self.packets = []
		self.abspacketsize = 0

def process_file(inputFile, outputFile):
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
		outputFile.write(urlname + ' ' + timestamp + ' ' + str(entrynodes))
		if entrynodes == 1:
			outputFile.write(' ' + ' '.join(['{0}'.format(el) for el in entries[3:]]))
		else:
			for entry in entries[3:]:
				foundsubstream = False
				if len(currentstream) > 0:
					for substream in currentstream:
						if substream.entry == entry.split(':')[1]:
							foundsubstream = True
							substream.packets.append(entry)
							substream.abspacketsize += abs(int(entry.split(':')[2]))
			
				if not foundsubstream:
					firstsubstream = Substream(entry.split(':')[1])
					firstsubstream.packets.append(entry)
					firstsubstream.abspacketsize += abs(int(entry.split(':')[2]))
					currentstream.append(firstsubstream)
			
			currentstream = sorted(currentstream, key = lambda v: v.abspacketsize, reverse=True)
			outputFile.write(' ' + ' '.join(['{0}'.format(el) for el in currentstream[0].packets]))	
		outputFile.write('\n')


# Check if TLS has been extracted
inputDir = 'output-{0}{1}/'.format(mainFormat, inputFormat)
if not os.path.isdir(crawlingPath + inputDir):
	print('Execute raw-to-'+mainFormat+'.py and parse-'+mainFormat+inputFormat+'.py first!')
	sys.exit(0)

# Clean Output
outputDir = 'output-{0}{1}-main/'.format(mainFormat, inputFormat)
if os.path.isdir(crawlingPath + outputDir):
	shutil.rmtree(crawlingPath + outputDir)
os.mkdir(crawlingPath + outputDir)

inputfiles = glob.glob(crawlingPath + inputDir + '*')

# parse TLS data
for inputfile in inputfiles:
	path, inputfilename = os.path.split(inputfile)

	# Inputfile
	inputFile = open(crawlingPath + inputDir + inputfilename, 'r')
	# Outputfile
	outputFile = open(crawlingPath + outputDir + inputfilename, 'w')
	
	process_file(inputFile, outputFile)
	
	# Close files
	inputFile.close()
	outputFile.close()
