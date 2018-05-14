#!/usr/bin/env python

# Script for checking similarities in hidden service contents, runs on storage directory
#
# python check-content-similarity.py [options]

import sys, os, time, difflib, glob
from difflib import Differ
import numpy as np
try:
	from natsort import natsorted
except:
	print('You need natsort! (pip install natsort)')
	sys.exit()
try:
	from sklearn.feature_extraction.text import TfidfVectorizer
	from sklearn.metrics.pairwise import cosine_similarity
except:
	print('You need scikit-learn! (pip install scikit-learn)')
	sys.exit()


def exit_with_help(error=''):
	print("""\
Usage: check-content-similarity.py [options]

options:
   -praw { /Path/ } : Path to the Instances in Folder Raw
   -out { /Path/ } : Path to Outputfile
   -patternspath { /Path/ } : Path to Patterns Files
   -txtdumpspath { /Path/ } : Path to Txtdump Files used for 
				one-vs-all cosine similarity.
				
   -simple-check : If it is set, we compare the text between 
				two txtdumps without applying any specific methods.
   -cos-sim-check : If it is set, we apply cosine similarity
				to compare txtdumps with predefined patterns.
   -one-vs-all : If it is set, we apply cosine similarity
				to a txtdump versus all others without using patterns.
				
   -similarity { 0 <= number <= 100 } : Defines the percentage 
				of similarity that assumes webpages with similar 
				content. By default: 90%.
				
   Note: If you compare two txtdump files with extension '.txt', the 
		best percentage of similarity is 90%. If you compare two 
		different txtdump files with extensions respectively '.txt'
		and '.htm', the best percentage of similarity is 80%.
 """)
	print(error)
	sys.exit(1)
	
def save_in_file(pagenames, outputfile):
	f = open(outputfile, 'a')
	for pagename in pagenames:
		f.write(pagename+'\n')
	f.close()
   

simpleCheck = False
cosineSimilarity = False
oneVsAll = False
simPercentage = 0.9

args = [ ('pathraw', 'dir_STOR_RAW', 'praw'),
         ('pathfetch', 'dir_FETCHES', 'out'),
         ('patternpath', 'dir_FETCH_PATTERNS', 'patternspath') ]

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
		if options[i] == '-praw':
			i = i + 1
			pathraw = options[i]
			if not pathraw.endswith('/'):
				pathraw += '/'
		elif options[i] == '-out':
			i = i + 1
			pathfetch = options[i]
			if not pathfetch.endswith('/'):
				pathfetch += '/'
		elif options[i] == '-patternspath':
			i = i + 1
			patternpath = options[i]
			if not patternpath.endswith('/'):
				patternpath += '/'
		elif options[i] == '-txtdumpspath':
			i = i + 1
			txtdumppath = options[i]
			if not txtdumppath.endswith('/'):
				txtdumppath += '/'
		elif options[i] == '-simple-check':
			simpleCheck = True
		elif options[i] == '-cos-sim-check':
			cosineSimilarity = True
		elif options[i] == '-one-vs-all':
			oneVsAll = True
		elif options[i] == '-similarity':
			i = i + 1
			if options[i].isdigit() and ( int(options[i]) >= 0 and int(options[i]) <= 100):
				simPercentage = int(options[i])/100.
			else: 
				raise ValueError('Use 0 <= number <= 100 as arguments for -similarity.')
		else:
			exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
		i = i + 1

# Check set variables
if not oneVsAll and not os.path.isdir(pathraw):
	exit_with_help('Error: Invalid Raw Fetches Path!')
if not os.path.isdir(pathfetch):
	exit_with_help('Error: Invalid Output Path!')
if (simpleCheck or cosineSimilarity) and not os.path.isdir(patternpath):
	exit_with_help('Error: Invalid Pattern Path!')
if oneVsAll and not os.path.isdir(txtdumppath):
	exit_with_help('Error: Invalid Txtdump Path!')
if (simpleCheck and cosineSimilarity and oneVsAll) or (simpleCheck and cosineSimilarity) or (simpleCheck and oneVsAll) or (cosineSimilarity and oneVsAll) or (not simpleCheck and not cosineSimilarity and not oneVsAll):  
	exit_with_help('Error: Invalid Comparision Method!')
	
# input patterns
if cosineSimilarity or simpleCheck:
	subdirpatterns = natsorted(os.listdir(patternpath))

	for subdirpattern in subdirpatterns:
		if os.path.isfile(patternpath + subdirpattern):
			continue
			
		#stores output filename
		outputhscontentfile = pathfetch + subdirpattern + '.txt'
	
		# check if output already existis
		if os.path.isfile(outputhscontentfile):
			# we don't care, just remove :-)
			print('Output file already exists, will remove in 3 seconds\n3')
			time.sleep(1); print('2'); time.sleep(1); print('1'); time.sleep(1)
			os.remove(outputhscontentfile) 
			
		pagenameHscontent = set()
			
		patternfiles = natsorted(os.listdir(patternpath + subdirpattern + '/txtdumps/'))
		
		for patternfile in patternfiles:
		
			f = open(patternpath + subdirpattern + '/txtdumps/' + patternfile, 'r')
			patternsHscontent = f.read()
			f.close()
	
			txtdumps = natsorted(os.listdir(pathraw + 'txtdumps/'))
	
			print ('Check hscontent ' + subdirpattern + ':')

			for txtdump in txtdumps:
				if os.path.isdir(txtdump):
					continue
        
				# we don't need checktor
				if 'check.torproject' in txtdump:
					continue
        
				# read content of current txtdump
				f = open(pathraw + 'txtdumps/' + txtdump, 'r')
				txtcontent = f.read()
				f.close()
					
				if cosineSimilarity:
					tfidf_vectorizer = TfidfVectorizer()
					tfidf_pattern_content = tfidf_vectorizer.fit_transform((unicode(patternsHscontent, errors='ignore'), unicode(txtcontent, errors='ignore')))

					cos_similarity = np.asfarray(cosine_similarity(tfidf_pattern_content[0:1], tfidf_pattern_content), dtype='float')
			
					# 90% similarity assumes webpages with similar content
					if cos_similarity[0][1] > simPercentage:
						pagenameHscontent.add(txtdump.replace('.txt','').replace('.htm',''))
					else:	
						if cos_similarity[0][1] >= 0.5:
							print txtdump.replace('.txt','').replace('.htm','') + " : hscontent" + subdirpattern + " = " + str(cos_similarity[0][1])
						
				if simpleCheck:
					diff = list(difflib.unified_diff(patternsHscontent[4:-2].split("\n"), txtcontent[4:-3].split("\n")))
					equal = True
					for line in diff:
						if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
							equal = False
							break
				
					if equal:
						pagenameHscontent.add(txtdump.replace('.txt','').replace('.htm',''))

		if len(pagenameHscontent) > 0:
			save_in_file(pagenameHscontent, outputhscontentfile)

if oneVsAll:
	
	# check if output already existis and remove it
	outputfiles = natsorted(os.listdir(pathfetch))
	for outputfile in outputfiles:
		if os.path.isdir(pathfetch + outputfile):
			continue
			
		runfile, extension = os.path.splitext(outputfile)
	
		if 'hscontent' not in runfile:
			continue
			
		if os.path.isfile(pathfetch + outputfile):
			# we don't care, just remove :-)
			os.remove(pathfetch + outputfile) 
	
	
	txtdumpfiles = natsorted(os.listdir(txtdumppath))
	
	current = 1
	for txtdumpfile in txtdumpfiles:
		if os.path.isdir(txtdumppath + txtdumpfile):
			continue
			
		print('INFO: (' + str(current) + '/' + str(len(txtdumpfiles)) + ') ' + txtdumpfile)
		
		f = open(txtdumppath + txtdumpfile, 'r')
		patterntxtdump = f.read()
		f.close()
		
		hswebpages = set() # saves current group of addresses with similar content
		
		hscontentaddr = set() # saves already assigned addresses
		
		currentoutputfiles = natsorted(glob.glob(pathfetch + 'hscontent00*.txt'))
		for currentoutputfile in currentoutputfiles:
			onions = open(currentoutputfile, 'r')
			for onion in onions:
				hscontentaddr.add(onion.replace('\n',''))
			onions.close()
			
		for txtdump in txtdumpfiles:
			if txtdumpfile == txtdump:
				continue
				
			if txtdump.replace('.txt', '') in hscontentaddr:
				continue
				
			# read content of current txtdump
			f = open(txtdumppath + txtdump, 'r')
			txtcontent = f.read()
			f.close()
			
			tfidf_vectorizer = TfidfVectorizer()
			tfidf_pattern_content = tfidf_vectorizer.fit_transform((unicode(patterntxtdump, errors='ignore'), (unicode(txtcontent, errors='ignore'))))

			cos_similarity = np.asfarray(cosine_similarity(tfidf_pattern_content[0:1], tfidf_pattern_content), dtype='float')
			
			# 90% similarity assumes webpages with similar content
			if cos_similarity[0][1] > simPercentage:
				hswebpages.add(txtdump.replace('.txt',''))
			else:	
				if cos_similarity[0][1] >= 0.5:
					print txtdump.replace('.txt','') + " : " + txtdumpfile.replace('.txt','') + " = " + str(cos_similarity[0][1])
		
		if len(hswebpages) > 0:
			hswebpages.add(txtdumpfile.replace('.txt',''))
			currentoutputfiles = natsorted(glob.glob(pathfetch + 'hscontent00*.txt'))
			
			if len(currentoutputfiles) == 0:
				outputhspagefile = pathfetch + 'hscontent0013.txt'
			else:
				currentpagenumber = int(currentoutputfiles[-1].split('/')[-1].replace('hscontent00', '').replace('.txt','')) + 1
				outputhspagefile = pathfetch + 'hscontent00' + str(currentpagenumber) + '.txt'
			
			save_in_file(hswebpages, outputhspagefile)
							
		current += 1
