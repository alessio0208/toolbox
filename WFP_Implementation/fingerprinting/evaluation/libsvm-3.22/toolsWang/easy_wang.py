#!/usr/bin/env python

# easy.py adaption for modified evaluation to compare to Wang's kNN approach
# Splits data k-partitions and uses k-1 partitions for training and k for testing 
# Perform k-fold evaluation
# 	performs grid.py (internal k-fold CV) on each fold's training data to find parameters
# 	trains a model with the best parameters for each fold's training data
# 	use each fold's testing data to predict the results with the corresponding model
# Merge prediction results of all k-folds into a single result
#
# foreground_file has to have a different label for each page: 1..n
# background_file has to have the same label for all pages: 0

# you should have a non-patched (no prediction output) svm-train executable as svm-train-q
# svm-predict has to be patched

import sys
import os
from subprocess import *

import numpy, random, pprint, glob, itertools
try:
	import natsort
except:
	print('You need natsort! (pip install natsort)')
	sys.exit()

# Function to partition randomized lists
def chunks(l, n):
	""" Yield successive n-sized chunks from l.
	"""
	for i in xrange(0, len(l), n):
		yield l[i:i+n]

if not len(sys.argv) in [ 2, 3 ]:
	print('''Usage: 
	a) Wang's 2014 format:
	  {0} path_to_batch_folder
		path_to_batch_folder: e.g. ./batch/
	b) already converted file input:
	  {0} foreground_file background_file
		foreground_file: different labels for each page - 1..n
		background_file: one label for all pages - 0'''.format(sys.argv[0]))
	raise SystemExit

if not 'tools' in os.path.split(os.getcwd())[1]:
	print('Copy to \"tools\"-folder of LibSVM')
	raise SystemExit

# svm, grid, and gnuplot executable files

is_win32 = (sys.platform == 'win32')
if not is_win32:
	svmscale_exe = "../svm-scale"
	svmtrain_exe_q = "../svm-train-q"
	svmpredict_exe = "../svm-predict"
	grid_py = "./grid.py"
	gnuplot_exe = "/usr/bin/gnuplot"
else:
	# example for windows
	svmscale_exe = r"..\windows\svm-scale.exe"
	svmtrain_exe_q = r"..\windows\svm-train-q.exe"
	svmpredict_exe = r"..\windows\svm-predict.exe"
	gnuplot_exe = r"c:\tmp\gnuplot\binary\pgnuplot.exe"
	grid_py = r".\grid.py"

assert os.path.exists(svmscale_exe),"svm-scale executable not found"
assert os.path.exists(svmtrain_exe_q),"svm-train executable not found"
assert os.path.exists(svmpredict_exe),"svm-predict executable not found"
assert os.path.exists(gnuplot_exe),"gnuplot executable not found"
assert os.path.exists(grid_py),"grid.py not found"

###### CONFIG ###### 
# How many folds should be done
folds = 10
# How the "temporary" output and result is named 
scenario = 'LibSVM_Test'
# Should the input be randomized?
shuffle = False
# How much storage is available?
# 'Low' | 'RemoveTemp' | 'High'
storage = 'Low'
# The grid should be adjusted in grid.py
#grid = ...
# Should the separate classifier be used?
# True | False
separateClassifier = False
# How many features does the cumulative part have?
featureCount = 100
####################

if len(sys.argv) == 2:
	# Wang's 2014 input format
	wang_pathname = sys.argv[1]
	assert os.path.exists(wang_pathname),"wang directory not found"
	
	# list all files we need to process
	wangfiles = natsort.versorted(glob.glob(os.path.join(wang_pathname, '*')))
	file_fg = 'Wang_foreground'
	fg_pathname = os.path.join(os.getcwd(), file_fg)
	file_bg = 'Wang_background'
	bg_pathname = os.path.join(os.getcwd(), file_bg)
	wang_fg = open(fg_pathname, 'w')
	wang_bg = open(bg_pathname, 'w')
	for wangfile in wangfiles:
		file_name = os.path.split(wangfile)[1]
		
		if 'f' in file_name:
			# we have a file from the k-NN classification
			continue
		
		if '-' in file_name:
			# foreground file (label with increasing numbers)
			classnumber = str(int(file_name.split('-')[0])+1)
			instancenumber = str(int(file_name.split('-')[1])+1)
		else:
			# background file (label everything with 0)
			classnumber = '0'
			instancenumber = file_name
		
		# read current instance
		inputfile = open(wangfile, 'r')
		currentinstance = []
		for line in inputfile:
			packet = line.split()[1]
			## Swap sign, change size and append
			if packet == '1':
				currentinstance.append('-586')
			else: 
				currentinstance.append('586')
		inputfile.close()
		
		# generate feature
		features = []
			
		total = []
		cum = []
		pos = []
		neg = []
		inSize = 0
		outSize = 0
		inCount = 0
		outCount = 0
		
		# Process trace
		for item in currentinstance: 
			packetsize = int(item)
			
			# incoming packets
			if packetsize > 0:
				inSize += packetsize
				inCount += 1
				# cumulated packetsizes
				if len(cum) == 0:
					cum.append(packetsize)
					total.append(packetsize)
					pos.append(packetsize)
					neg.append(0)
				else:
					cum.append(cum[-1] + packetsize)
					total.append(total[-1] + abs(packetsize))
					pos.append(pos[-1] + packetsize)
					neg.append(neg[-1] + 0)
		
			# outgoing packets
			if packetsize < 0:
				outSize += abs(packetsize)
				outCount += 1
				if len(cum) == 0:
					cum.append(packetsize)
					total.append(abs(packetsize))
					pos.append(0)
					neg.append(abs(packetsize))
				else:
					cum.append(cum[-1] + packetsize)
					total.append(total[-1] + abs(packetsize))
					pos.append(pos[-1] + 0)
					neg.append(neg[-1] + abs(packetsize))
		
		# add feature
		features.append(classnumber)
		features.append(inCount)
		features.append(outCount)
		features.append(outSize)
		features.append(inSize)
		
		if separateClassifier:
			# cumulative in and out
			posFeatures = numpy.interp(numpy.linspace(total[0], total[-1], featureCount/2), total, pos)
			negFeatures = numpy.interp(numpy.linspace(total[0], total[-1], featureCount/2), total, neg)
			for el in itertools.islice(posFeatures, 1, None):
				features.append(el)
			for el in itertools.islice(negFeatures, 1, None):
				features.append(el)
		else:
			# cumulative in one
			cumFeatures = numpy.interp(numpy.linspace(total[0], total[-1], featureCount+1), total, cum)
			for el in itertools.islice(cumFeatures, 1, None):
				features.append(el)
		
		if '-' in file_name:
			# write to foreground file
			wang_fg.write(str(features[0]) + ' ' + ' '.join(['%d:%s' % (i+1, el) for i,el in enumerate(features[1:])]) + ' # ' + instancenumber + '\n')
		else:
			# write to background file
			wang_bg.write(str(features[0]) + ' ' + ' '.join(['%d:%s' % (i+1, el) for i,el in enumerate(features[1:])]) + ' # ' + instancenumber + '\n')
	
	# close files
	wang_fg.close()
	wang_bg.close()
else:
	# converted input format
	fg_pathname = sys.argv[1]
	assert os.path.exists(fg_pathname),"foreground file not found"
	file_fg = os.path.split(fg_pathname)[1]
	bg_pathname = sys.argv[2]
	assert os.path.exists(bg_pathname),"background file not found"
	file_bg = os.path.split(bg_pathname)[1]



# Scale input data
merged_file = scenario + '.merged.file'
range_file = scenario + '.range'
scaled_file = scenario + '.scale'
scaled_file_fg = file_fg + '.scale'
scaled_file_bg = file_bg + '.scale'

# Merge input files
fout = open(merged_file, 'w')
for filename in [ fg_pathname, bg_pathname ]:
	fin = open(filename,'r')
	fout.write(fin.read())
	fin.close()

# Obtain range file
print('Scaling data...')
cmd = '{0} -s "{1}" "{2}" > "{3}"'.format(svmscale_exe, range_file, merged_file, scaled_file)
Popen(cmd, shell = True, stdout = PIPE).communicate()

# Scale Foreground data
cmd = '{0} -r "{1}" "{2}" > "{3}"'.format(svmscale_exe, range_file, fg_pathname, scaled_file_fg)
Popen(cmd, shell = True, stdout = PIPE).communicate()
# Scale Background data
cmd = '{0} -r "{1}" "{2}" > "{3}"'.format(svmscale_exe, range_file, bg_pathname, scaled_file_bg)
Popen(cmd, shell = True, stdout = PIPE).communicate()

# Clean merged/temp data
os.remove(merged_file)
os.remove(scaled_file)

# We are only working with scaled data! 

def outputInput(currentClass):
	for currentFold in range(1, folds+1):
		# output training & testing
		ftrainout = open(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.train', 'w')
		ftestout = open(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.test', 'w')
		# iterate through each partition
		count = 1
		for subList in fg_partitioned[currentClass]:
			# where does this instance belong to?
			if count == currentFold:
				for item in subList: 
					# all fg is the same class
					ftestout.write(item+'\n')
			else:
				for item in subList: 
					# all fg is the same class
					ftrainout.write(item+'\n')
			count = count+1
		
		count = 1
		# iterate through each partition 
		for subList in bg_partitioned:
			# where does this instance belong to?
			if count == currentFold:
				for item in subList: 
					ftestout.write(item+'\n')
			else:
				for item in subList: 
					ftrainout.write(item+'\n')
			count = count+1
		ftrainout.close()
		ftestout.close()
	
	return


def evaluation(currentClass):
	# CV for each fold of each
	for currentFold in range(1, folds+1):
		cmd = '{0} -v {1} -svmtrain "{2}" -gnuplot "{3}" "{4}"'.format(grid_py, folds, svmtrain_exe_q, gnuplot_exe, scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.train')
		print('Class: ' + str(currentClass) + ' Fold: ' + str(currentFold) + ' - Cross validation...')
		f = Popen(cmd, shell = True, stdout = PIPE).stdout
		
		line = ''
		while True:
			last_line = line
			line = f.readline()
			if not line: break
		c,g,rate = map(float,last_line.split())
		if className in results:
			results[className].append((c,g,rate))
		else:
			results[className] = [(c,g,rate)]

		print('Class: ' + str(currentClass) + ' Fold: ' + str(currentFold) + ' - Best c={0}, g={1} CV rate={2}'.format(results[className][currentFold-1][0],results[className][currentFold-1][1],results[className][currentFold-1][2]))

	# train model for each fold
	for currentFold in range(1, folds+1):
		cmd = '{0} -c {1} -g {2} "{3}" "{4}"'.format(svmtrain_exe_q,results[className][currentFold-1][0],results[className][currentFold-1][1],scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.train', scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.model')
		print('Class: ' + str(currentClass) + ' Fold: ' + str(currentFold) + ' - Training...')
		Popen(cmd, shell = True, stdout = PIPE).communicate()

	# test model for each fold of each fg class
	for currentFold in range(1, folds+1):
		cmd = '{0} "{1}" "{2}" "{3}"'.format(svmpredict_exe, scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.test', scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.model', scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.predict')
		print('Class: ' + str(currentClass) + ' Fold: ' + str(currentFold) + ' - Testing...')
		Popen(cmd, shell = True).communicate()

	# merge result for each fg class
	fresult = open(scenario + '_' + str(currentClass) + '.result', 'w')
	for currentFold in range(1, folds+1):
		fpredict = open(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.predict', 'r')
		for line in fpredict:
			fresult.write(line)
		fpredict.close()
	fresult.close()
	
	print('Class: ' + str(currentClass) + ' - Output prediction: {0}'.format(scenario + '_' + str(currentClass) + '.result'))
	
	return

def removeTemp(currentClass):
	for currentFold in range(1, folds+1):
		os.remove(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.train')
		os.remove(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.test')
		os.remove(scenario + '_' + str(currentClass) + '_' + str(currentFold) + '.predict')

# Read File into Arrays per class
fg = {}
className = 0
instances_fg = 0
f = open(scaled_file_fg, 'r')
for line in f:
	# which class is the current instance belonging to
	className = int(line.split()[0])
	# append to all gathered instances
	if className in fg:
		fg[className].append(line.rstrip('\n'))
	else:
		fg[className] = [line.rstrip('\n')]
	instances_fg = instances_fg + 1
f.close()

bg = []
instances_bg = 0
f = open(scaled_file_bg, 'r')
for line in f:
	# append to all gathered instances
	bg.append(line.rstrip('\n'))
	instances_bg = instances_bg + 1
f.close()

# Shuffle Arrays
if shuffle:
	for k in fg.keys():
		random.shuffle(fg[k])
	random.shuffle(bg)

# Partition Array
fg_count = len(fg.keys())
fg_partitioned = {}
for k in fg.keys():
	fg_partitioned[k] = list(chunks(fg[k], (instances_fg/fg_count)/folds))
bg_partitioned = []
bg_partitioned = list(chunks(bg, instances_bg/folds))

print('FG-Instances: ' + str(instances_fg) + ', BG-Instances: ' + str(instances_bg) + ', FG-Classes: ' + str(fg_count) + ', Folds: ' + str(folds) + ',\nFG-Partition: ' + ('ok' if (instances_fg/fg_count) % folds == 0 else 'not equal') + ', BG-Partition: ' + ('ok' if (instances_bg) % folds == 0 else 'not equal'))

if ((instances_fg/fg_count) % folds != 0) or ((instances_bg) % folds != 0):
	raise SystemExit

# Save Files 

# unpartitioned
#for k in fg.keys():
#	numpy.savetxt('test_fg_'+str(k)+'.txt', fg[k], fmt="%s")
#numpy.savetxt('test_bg.txt', bg, fmt="%s")

# partitioned (proof of concept)
#fout = open('test_output_fg.txt','w') 
#for k in fg.keys():
	#fout.write('Class ' + str(k) + ': \n')
	#for subList in fg_partitioned[k]:
		#fout.write(', '.join([str(item)[:10] for item in subList]))
		#fout.write('   ' + str(len(subList)) + '\n\n')
	#fout.write('\n\n')
#fout.close()
#fout = open('test_output_bg.txt', 'w')
#for subList in bg_partitioned:
	#fout.write(', '.join([str(item)[:10] for item in subList]))
	#fout.write('   ' + str(len(subList)) + '\n\n')
#fout.close()

results = {}
if storage == 'Low': 
	# Nearly no storage, so we process one class after another
	# for each fg class:
	for currentClass in range(1, fg_count+1):
		# output divided in training and testing per fold
		# for k folds: partition i is used for testing in fold i, the remaining k-1 partitions are used for training
		outputInput(currentClass)
		# perform evaluation
		evaluation(currentClass)
		# remove temporary data
		removeTemp(currentClass)
else:  
	# We have storage, so we create all input files at the beginning
	# for each fg class:
	for currentClass in range(1, fg_count+1):
		# output divided in training and testing per fold
		# for k folds: partition i is used for testing in fold i, the remaining k-1 partitions are used for training
		outputInput(currentClass)
	# for each fg class:
	for currentClass in range(1, fg_count+1):
		# perform evaluation
		evaluation(currentClass)
		# we remove temporary data if specified
		if storage == 'RemoveTemp': 
			# remove temporary data
			removeTemp(currentClass)

