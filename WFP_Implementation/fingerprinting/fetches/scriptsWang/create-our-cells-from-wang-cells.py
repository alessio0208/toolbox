#! /usr/bin/env python
#
# Build cell instances with and without SendMes from Wang's cell data
# Only creates a single instance, because Wang's 2014 format only allows a single instance per file

import sys, os, glob
try:
    from natsort import natsorted
except:
    print('You need natsort! (pip install natsort)')
    sys.exit()

def process_wang(cellfiles, inFolder, outFolder): 
    
    for cellfile in cellfiles:
        path, inputfilename = os.path.split(cellfile)
        
        # Read name and time from TCP file
        # OLD 1
        #infofile = open('output/' + inputfilename, 'r')
        #line = infofile.readline()
        #urlname = line.split()[0]
        #timestamp = line.split()[1]
        #infofile.close()

        # OLD 2
        #urlname = inputfilename.split('-')[0]
        #timestamp = inputfilename.split('-')[1]

        #outputstr = urlname + ' ' + timestamp


        # NEW, 26.03.2015
        timestamp = inputfilename.split('-')[-1] # Get the timestamp we saved in the filename
        urlname = inputfilename[:-(len(timestamp)+1)] # Remove the timestamp (-xxxxxxxxxx) to get the preceeding URL

        outputstr = urlname + ' ' + timestamp

        print(outputstr+' < timestamp should not have additional file extension!')


        # Process Wang Cells
        inputfile = open(inFolder + inputfilename, 'r')
        i = 1
        for line in inputfile:
            packet = line.split()[1]
            # Swap sign, change size and append
            if packet == '1':
                outputstr += ' ' + str(i) + ':-586'
            else: 
                outputstr += ' ' + str(i) + ':586'
            i += 1
        
        inputfile.close()

        # Write file, Wang Cell files only contain one instance, so we do not append
        outputfile = open(outFolder + inputfilename, 'w')
        outputfile.write(str(outputstr) + '\n')
        outputfile.close()


crawlingPath = os.getenv('dir_CRAWLING')
os.chdir(crawlingPath)

# first process files without SendMes
if not os.path.isdir('output-cells/'):
    os.mkdir('output-cells/')

cellfiles = natsorted(glob.glob('output-cells-wang/*'))
process_wang(cellfiles, 'output-cells-wang/', 'output-cells/')
    
# second process files with SendMes
if not os.path.isdir('output-cells-sendme/'):
    os.mkdir('output-cells-sendme/')

cellfiles = natsorted(glob.glob('output-cells-wang-sendme/*'))
process_wang(cellfiles, 'output-cells-wang-sendme/', 'output-cells-sendme/')
