#! /usr/bin/env python
#
# Build instances in Wang's 2014 format from outlierfree TLS data

import sys, os, glob, shutil
try:
    from natsort import natsorted
except:
    print('You need natsort! (pip install natsort)')
    sys.exit()

outlierfreePath = os.getenv('dir_TEMP_OUTLIERFREE')
wangPath = outlierfreePath + '../wang/'
setting=os.getenv('conf_SETTING')

# Clean up output folder
if os.path.isdir(wangPath):
    shutil.rmtree(wangPath)
try:
    os.mkdir(wangPath)
except:
    pass

if os.path.isdir(wangPath + 'output-cell-wang/'):
    shutil.rmtree(wangPath + 'output-cell-wang/')
os.mkdir(wangPath + 'output-cell-wang/')

if os.path.isdir(wangPath + 'output-cell-nosendme-wang/'):
    shutil.rmtree(wangPath + 'output-cell-nosendme-wang/')
os.mkdir(wangPath + 'output-cell-nosendme-wang/')


tlsfiles = natsorted(glob.glob(outlierfreePath + 'output-tls-outlierfree/*'))

# Create Matching file
matchingFile = open(wangPath + 'Matching.txt', 'w')

page=0
for tlsfile in tlsfiles:
    path, inputfilename = os.path.split(tlsfile)
    
    matchingFile.write('%d\t%s\n' % (page, inputfilename))
    
    entries = []
    count=0
    # Read file
    for line in open(outlierfreePath + 'output-tls-outlierfree/' + inputfilename, 'r'):
        entries = []

        entries.extend(line.split(' '))
        data = []
        
        # Parse records
        for entry in entries[2:]:
            tsinfo, tls = entry.split(':')
            tstart, tend = tsinfo.split('-')
            data.append((int(tstart), int(tls)))
        data = sorted(data, key=lambda(k,v): k)
        #print 'File contains %d TLS records' % len(data)
        
        # data is a set of tuples (TIMESTAMP, TLS_RECORD_SIZE)
        p1 = 45 # Parameters for SENDME removal
        p2 = 40 # Parameters for SENDME removal
        ccell = 0
        csendme=0
        cout=0
        ts0 = data[0][0] # Timestamp of first TLS record
        
        # Outputfile
        if setting == 'OW_BG':
            cellfileWangSend = open(wangPath + 'output-cell-wang/' + str(page), 'w')
            cellfileWangNoSend = open(wangPath + 'output-cell-nosendme-wang/' + str(page), 'w')
        else:
            cellfileWangSend = open(wangPath + 'output-cell-wang/' + str(page) + '-' + str(count), 'w')
            cellfileWangNoSend = open(wangPath + 'output-cell-nosendme-wang/' + str(page) + '-' + str(count), 'w')
        
        for tsfull, tls in data:
            ts = (tsfull-ts0)*1e-6
            incoming = (tls > 0) # In our format incoming=+1, in Wang's format incoming=-1
            cells = abs(tls)/512
            if cells > 0:
                for i in range(cells):
                    if incoming:
                        cellfileWangSend.write('%.9f\t-1\n' % ts)
                        cellfileWangNoSend.write('%.9f\t-1\n' % ts)
                        ccell += 1
                    else:
                        cout+=1
                        cellfileWangSend.write('%.9f\t1\n' % ts)
                        if ccell < p1:
                            cellfileWangNoSend.write('%.9f\t1\n' % ts)
                        else:
                            # next outgoing is sendme
                            ccell -= p2
                            csendme+=1
                            
        cellfileWangSend.close()
        cellfileWangNoSend.close()
        if setting == 'OW_BG':
            page=page+1
        
    if setting != 'OW_BG':
        page=page+1

matchingFile.close()
