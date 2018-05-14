#! /usr/bin/env python

# Synchronized Outlier Removal
#
# python outlier-removal.py [multiple Options]

import sys, re, os, glob, math, random, shutil, errno, copy
try:
    from natsort import natsorted
except:
    print('You need natsort! (pip install natsort)')
    sys.exit()

def exit_with_help(error=''):
    print("""\
Usage: outlier-removal.py [options]

options:
   -in { /Path/ } : Path to Merged Instances (with Formats as Sub-Dirs)
   -out { /Path/ } : Path to Outlier-free Instances (creates Sub-Dirs)

   -ignoreOutlier { YES | NO } : Ignore Outlier Removal if necessary
   -instances { #Number } : Number (!) of Instances per Webpage
   -outlierRemoval { None | Simple | Strict | Wang } : "Strictness" 
                                                  of Outlier Removal
   -setting { CW | OW_BG | OW_FG } : Evaluated Scenario 
                                     (OW_BG has outlierRemoval None )
   -randomInstances { YES | NO } : Take Random Instances if Possible
   -referenceFormat { tcp | tls | tls-legacy | tls-nosendme | 
                      cell | cell-nosendme } : Reference 
                               Format for synchronized Outlier Removal

Default Configuration is extracted from Environmental Variables
        Check, Adjust & Reload WFP_config if necessary

Notes:
 - Instances that break the Classifier are ALWAYS removed!
 - Script always processes ALL available formats!
 - Background-Setting processes a single instance per webpage 
 - Background-Setting only checks the format (No outlier removal)
 """)
    print(error)
    sys.exit(1)

# Define formats
formats = [ 'tcp', 'tls', 'tls-legacy', 'tls-nosendme', 
            'tls-nosendme-legacy', 'cell', 'cell-nosendme', 
            'cell-legacy', 'cell-nosendme-legacy' ]

# Arguments to be read from WFP_conf
args = [ ('mergedPath', 'dir_TEMP_MERGED', 'in'),
         ('outlierfreePath', 'dir_TEMP_OUTLIERFREE', 'out'),
         ('setting', 'conf_SETTING', 'setting'),
         ('referenceFormat', 'conf_OUTLIER_REFERENCE', 'referenceFormat'),
         ('outlierRemoval', 'conf_OUTLIER_REMOVAL', 'outlierRemoval'),
         ('tmp1', 'conf_IGNORE_OUTLIER', 'ignoreOutlier'),
         ('tmp2', 'conf_RANDOM_INSTANCES', 'randomInstances'),
         ('tmp3', 'conf_INSTANCES', 'instances') ]

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
        if options[i] == '-in':
                i = i + 1
                mergedPath = options[i]
        elif options[i] == '-out':
                i = i + 1
                outlierfreePath = options[i]
        elif options[i] == '-referenceFormat':
                i = i + 1
                referenceFormat=options[i]
        elif options[i] == '-outlierRemoval':
                i = i + 1
                outlierRemoval=options[i]
        elif options[i] == '-setting':
                i = i + 1
                setting = options[i]
        elif options[i] == '-ignoreOutlier':
                i = i + 1
                tmp1 = options[i]
        elif options[i] == '-randomInstances':
                i = i + 1
                tmp2 = options[i]
        elif options[i] == '-instances':
                i = i + 1
                tmp3 = options[i]
        else:
            exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
        i = i + 1

# Check set variables
if not os.path.isdir(mergedPath):
    exit_with_help('Error: Invalid Input Path!')
if referenceFormat not in formats:
    exit_with_help('Error: Unknown Reference Format!')
if not os.path.isdir(mergedPath + 'output-' + referenceFormat):
    exit_with_help('Error: Reference Format does not exist!')
if outlierRemoval not in [ 'None', 'Simple', 'Strict', 'Wang' ]:
    exit_with_help('Error: Unknown Outlier Removal!')
if setting not in [ 'CW', 'OW_BG', 'OW_FG' ]:
    exit_with_help('Error: Unknown Setting!')
if tmp1 in [ 'YES', 'NO' ]:
    if tmp1 == 'YES':
        ignoreOutlier = True
    else:
        ignoreOutlier = False
else:
    exit_with_help('Error: Unknown Ignore Outlier Option!')
if tmp2 in [ 'YES', 'NO' ]:
    if tmp2 == 'YES':
        randomInstances = True
    else:
        randomInstances = False
else:
    exit_with_help('Error: Unknown Random Instances Option!')
if tmp3.isdigit():
    if int(tmp3) > 0:
        numOfInstances = int(tmp3)
    else:
        exit_with_help('Error: Number of Instances is not a Number!')
else:
    exit_with_help('Error: Number of Instances is not a Number!')

# Additional checks
if setting == 'OW_BG' and '-outlierRemoval' not in sys.argv:
    outlierRemoval = 'None'
if setting == 'OW_BG':
    numOfInstances = 1

# For reading instances
class Instance:
    def __init__(self):
        pass
    
    def __init__(self, url='', timestamp=0, entries=0, packets=[]):
        self.url = url
        self.timestamp = int(timestamp)
        self.entries = int(entries)
        self.packets = packets
    
    def __str__( self ):
        return self.url + ' ' + str(self.timestamp) + ' ' + str(self.entries) + ' ' + ' '.join(self.packets) + '\n'

# Clean up output folder
if os.path.isdir(outlierfreePath):
    shutil.rmtree(outlierfreePath)
try:
    os.mkdir(outlierfreePath)
except:
    pass

remove = []
for form in formats:
	if not os.path.isdir(mergedPath + 'output-' + form):
		remove.append(form)
		print('INFO: ' + form + ' does not exist as input directory - removed!')
formats = [x for x in formats if x not in remove]

reffiles = natsorted(glob.glob(mergedPath + 'output-' + referenceFormat + '/*'))

current=1
countList = 0
for reffile in reffiles:
	
	reffilepath, reffilename = os.path.split(reffile)
	
	if 'check.torproject.org' in reffilename:
		current+=1
		continue
	
	# List with all instances that exist in all formats
	instancesAllFormats = []
	
	nextFile = False
	for form in formats:
		instances = []

		# read all available instances
		try:
			inputfile = open(mergedPath + 'output-' + form + '/' + reffilename, 'r')
		except:
			nextFile = True
			break
		for instanceline in inputfile:
			entries = []
			
			entries.extend(instanceline.rstrip().split(' '))
			incomingsize = 0
			
			url = entries[0]
			timestamp = entries[1]
			# for compatibility 
			if len(timestamp) > 13:
				border = len(timestamp) - 13
				timestamp = timestamp[:-border]
			if ':' in entries[2]:
				entrynodes = '0'
				data = entries[2:]
			else:
				entrynodes = entries[2]
				data = entries[3:]
			instance = Instance(url, timestamp, entrynodes, data)
			
			for entry in data:
				size = int(entry.split(':')[-1])
				if size > 0:
					incomingsize += size
			
			instances.append((incomingsize, instance))
			
		inputfile.close()
		instances = sorted(instances, key=lambda(k,v): k)
		instancesAllFormats.append(instances)
	
	# We were not able to read in all formats -> skipping this file
	if nextFile:
		continue
	
	instanceCount = [None] * len(instancesAllFormats)
	for i in range(0, len(instancesAllFormats)):
		instanceCount[i] = [len(instancesAllFormats[i])]

	timestamps = []
	for i in range(0, len(instancesAllFormats)):
		timestamps.append(set(x[1].timestamp for x in instancesAllFormats[i]))
	
	# Take intersection
	outlierTimestamps = set.intersection(*timestamps)
	outlierCount = len(outlierTimestamps)

	# Perform outlier removal on each format
	for i in range(0, len(instancesAllFormats)):
		instances = instancesAllFormats[i]
		# Remove instances with less than 2 incoming packets
		remove = []
		for outlierFeature, instance in instancesAllFormats[i]:
			if outlierFeature < 2*512 or len(instance.packets) <= 2:
				remove.append((outlierFeature, instance))
		instancesAllFormats[i] = [x for x in instancesAllFormats[i] if x not in remove]
	
		instanceCount[i].append(len(instances))
		
		if ignoreOutlier:
			instancesBackup = copy.deepcopy(instances)

		# outlier removal
		if outlierRemoval in ['Wang', 'Strict']:
			# remove based on median
			
			# calculate median
			if not (len(instances) % 2):
				med = (instances[len(instances)/2][0] + instances[len(instances)/2 -1][0]) /2.0
			else:
				med = instances[len(instances)/2][0]

			remove = []
			# remove outlier based on median metric
			if ['Strict']:
				for outlierFeature, instance in instances:
					if (outlierFeature < (0.2*med)) or (outlierFeature > (1.8*med)):
						remove.append((outlierFeature, instance))
			if ['Wang']:
				for outlierFeature, instance in instances:
					if (outlierFeature < (0.2*med)):
						remove.append((outlierFeature, instance))
						
			# NOW remove the instances
			instances = [x for x in instances if x not in remove]
			
			instanceCount[i].append(len(instances))
			if ignoreOutlier and len(instances) >= numOfInstances:
				instancesBackup = copy.deepcopy(instances)
			
		if outlierRemoval in ['Simple', 'Strict']:
			# remove based on quantiles
			
			# calculate quantiles
			q2l = ((len(instances)+1)/2)
			q1l = int(math.ceil((q2l/2)))
			q3l = int(math.ceil((3*(q2l/2))))-1
			if q1l < 0:
				q1l = 0
			if q3l < 0:
				q3l = 0
			if q3l >= len(instances):
				q3l = len(instances) -1
			
			q1 = instances[q1l][0]
			q3 = instances[q3l][0]

			remove = []
			# remove outlier based on quantile metric
			for outlierFeature, instance in instances:
				if (outlierFeature < (q1-1.5 * (q3-q1))) or (outlierFeature > (q3+1.5 * (q3-q1))):
					remove.append((outlierFeature, instance))
					
			# NOW remove the instances
			instances = [x for x in instances if x not in remove]
			
			instanceCount[i].append(len(instances))
			if ignoreOutlier and len(instances) >= numOfInstances:
				instancesBackup = copy.deepcopy(instances)
			
			# Restore instances, in case we do not have enough
			if ignoreOutlier:
				instances = instancesBackup
			
	
	# We synchronize all instances: we consider only instances existing in all formats
	timestamps = []
	for i in range(0, len(instancesAllFormats)):
		timestamps.append(set(x[1].timestamp for x in instancesAllFormats[i]))
	
	# Take intersection
	outlierfreeTimestamps = set.intersection(*timestamps)
	outlierfreeCount = len(outlierfreeTimestamps)
	
	# skip if number of instances is not sufficient
	if outlierfreeCount < numOfInstances:
		print('WARN: ' + reffilename + ' only ' + str(outlierfreeCount) + '/' + str(outlierCount) + ' of ' + str(numOfInstances)) # TODO: Add detailed statistics
		current+=1
		continue
	else:
		print('INFO: (' + str(current) + '/' + str(len(reffiles)) + ') ' +  reffilename + ' ' + str(outlierfreeCount) +'/' + str(outlierCount)) # TODO Add detailed statistics

	outlierfreeTimestamps = sorted(outlierfreeTimestamps)
	if randomInstances:
		samples = random.sample(outlierfreeTimestamps, numOfInstances)
	else:
		samples = outlierfreeTimestamps[:numOfInstances-1]

	# output all remaining available instances
	failed = False
	for i in range(0, len(instancesAllFormats)):
		
		if not os.path.isdir(outlierfreePath + 'output-' + formats[i] + '-outlierfree/'):
			os.mkdir(outlierfreePath + 'output-' + formats[i] + '-outlierfree/')
		outputfile = open(outlierfreePath + 'output-' + formats[i] + '-outlierfree/' + reffilename, 'w')
		
		instancesAllFormats[i] = [x[1] for x in instancesAllFormats[i] if x[1].timestamp in samples]
		if len(instancesAllFormats[i]) != numOfInstances:
			outputfile.close()
			for form in formats:
				try:
					os.remove(outlierfreePath + 'output-' + form + '-outlierfree/' + reffilename)
				except OSError as e:
					if e.errno != errno.ENOENT:
						raise
			print('WARN: ' + reffilename + ' has not enough instances?!')
			failed = True
			break
		else:
			for instance in instancesAllFormats[i]:
				outputfile.write(str(instance))
			outputfile.close()
	if not failed: countList+=1
	current+=1

print('INFO: (' + str(countList) + '/' + str(len(reffiles)) + ') outputted')
