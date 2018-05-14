#!/usr/bin/env python

# Script for checking txtdumps for errors, runs on storage directory
#
# python check-fetches.py [options]

import sys, os, time
try:
    from natsort import natsorted
except:
    print('You need natsort! (pip install natsort)')
    sys.exit()

def exit_with_help(error=''):
    print("""\
Usage: check-fetches.py [options]

options:
   -pcompiled { /Path/ } : Path to the Instances in Folder Compiled
   -praw { /Path/ } : Path to the Instances in Folder Raw
   -out { /Path/ } : Path to Outputfile
   -patternspath { /Path/ } : Path to Pattern Files
   -patterns { Filename } : Name of Pattern File
   
   -hs-check : If it is set, a fixed set of pattern files will be used
            to differentiate several error codes. Note, if a pattern 
            file is given by '-patterns', it will be ignored.

   -removeError { YES | NO } : Configures Checking for OW_BG Scenario
   -setting { CW | OW_BG | OW_FG } : Evaluated Scenario 
                                     (Might influence Checking)
 """)
    print(error)
    sys.exit(1)

# check for all invalid patterns and output filename, if necessary  
def check_invalid_patterns(patterns, outputfile):
    found = False
    for pattern in patterns:
        if pattern.replace('\n','') in txtcontent.replace('\n',''):
            f = open(outputfile, 'a')
            if '.txt' in txtdump:
                f.write(folder+'/'+txtdump.replace('.txt','')+'\n')
            if '.htm' in txtdump:
                f.write(folder+'/'+txtdump.replace('.htm','')+'\n')
            f.flush()
            f.close()
            found = True
            break
    return found

args = [ ('pathcompiled', 'dir_TEMP_COMPILED', 'pcompiled'),
         ('pathraw', 'dir_STOR_RAW', 'praw'),
         ('pathfetch', 'dir_FETCH_SCRIPTS', 'out'),
         ('patternpath', 'dir_FETCH_PATTERNS', 'patternspath'),
         ('patternsfile', 'conf_PATTERNS', 'patterns'),
         ('setting', 'conf_SETTING', 'setting'),
         ('tmp1', 'conf_DEL_TRANSMISSION_ERR', 'removeError') ]

# Checking if all variables are/will be set
for var, env, arg in args:
    if not '-'+arg in sys.argv:
        vars()[var] = os.getenv(env)
        if vars()[var] == None:
            exit_with_help('Error: Environmental Variables or Argument'+
                        ' insufficiently set! ($'+env+' / "-'+arg+'")')

forceHsCheck = False
# Read parameters from command line call
if len(sys.argv) != 0:
    i = 0
    options = sys.argv[1:]
    # iterate through parameter
    while i < len(options):
        if options[i] == '-pcompiled':
            i = i + 1
            pathcompiled = options[i]
            if not pathcompiled.endswith('/'):
                pathcompiled += '/'
        elif options[i] == '-praw':
            i = i + 1
            pathraw = options[i]
            if not pathraw.endswith('/'):
                pathraw += '/'
        elif options[i] == '-out':
            i = i + 1
            pathfetch = options[i]
        elif options[i] == '-patternspath':
            i = i + 1
            patternpath = options[i]
            if not patternpath.endswith('/'):
                patternpath += '/'
        elif options[i] == '-patterns':
            i = i + 1
            patternsfile = options[i]
        elif options[i] == '-hs-check':
            i = i + 1
            forceHsCheck = True
        elif options[i] == '-setting':
            i = i + 1
            setting = options[i]
        elif options[i] == '-removeError':
            i = i + 1
            tmp1 = options[i]
        else:
            exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
        i = i + 1

# Check set variables
if not os.path.isdir(pathcompiled):
    exit_with_help('Error: Invalid Compiled Fetches Path!')
if not os.path.isdir(pathraw):
    exit_with_help('Error: Invalid Raw Fetches Path!')
if not os.path.isdir(pathfetch):
    exit_with_help('Error: Invalid Output Path!')
if not os.path.isdir(patternpath):
    exit_with_help('Error: Invalid Pattern Path!')
if not os.path.isfile(patternpath + patternsfile):
    exit_with_help('Error: Invalid Pattern-File!')
if setting not in [ 'CW', 'OW_BG', 'OW_FG' ]:
    exit_with_help('Error: Unknown Setting!')
if tmp1 in [ 'YES', 'NO' ]:
    if tmp1 == 'YES':
        removeError = True
    else:
        removeError = False
else:
    exit_with_help('Error: Unknown Remove Error Option!')

# Additional checks
outputfile = pathfetch + '../TxtdumpErrors.txt' #stores filename

# check if output already exists
errorfiles = natsorted(os.listdir(pathfetch + '../'))
for errorfile in errorfiles:
    if os.path.isdir(errorfile):
        continue
        
    if 'Txtdump' not in errorfile:
        continue
    
    # we don't care, just remove :-)
    print('Output file already exists, will remove in 3 seconds\n3')
    time.sleep(1); print('2'); time.sleep(1); print('1'); time.sleep(1)
    os.remove(pathfetch + '../' + errorfile)
    
# Do we really want that?!
if not removeError and setting == 'OW_BG':
    print('No Fetch cleaning configured!')
    print('Exiting now!')
    sys.exit(1)

# input patterns
if not forceHsCheck:
    f = open(patternpath + patternsfile, 'r')
    patterns = f.readlines()
    f.close()

faulty=0
current=0
dirs=natsorted(os.listdir(pathcompiled))

for folder in dirs:
    current=current+1
    
    if os.path.isfile(folder):
        continue

    print('INFO: (' + str(current) + '/' + str(len(dirs)) + ') ' + folder)
    
    subpath=pathraw+folder+'/txtdumps/'
    if not os.path.isdir(subpath):
        print('INFO: Appear to be an old fetch - no txtdumps available! - Skipping')
        print('      ('+folder+')')
        continue
    
    subdirs=os.listdir(subpath)
    
    for txtdump in subdirs:
        if os.path.isdir(txtdump):
            continue
        
        # we don't need checktor
        if 'check.torproject' in txtdump:
            continue
        
        # read content of current txtdump
        f = open(subpath+txtdump, 'r')
        txtcontent = f.read()
        f.close()
        
        # check for all invalid patterns and output filename, if necessary
        if not forceHsCheck:
            if check_invalid_patterns(patterns, outputfile):
                faulty=faulty+1
        else:
            patternfiles = natsorted(os.listdir(patternpath))

            for patternfile in patternfiles:
                if os.path.isdir(patternfile):
                    continue
    
                runfile, extension = os.path.splitext(patternfile)
        
                if 'Patterns-error' not in runfile:
                    continue
            
                #stores output filename
                outputerrorfile = pathfetch + '../Txtdump' + runfile.replace('Patterns-error','') + 'Errors.txt'

                f = open(patternpath + runfile + '.txt', 'r')
                errorpatterns = f.readlines()
                f.close()
                
                if check_invalid_patterns(errorpatterns, outputerrorfile):
                    faulty=faulty+1
                    break

if not forceHsCheck:
    print('\nOverall '+str(faulty)+' faulty instance(s) detected!\nCheck ' + outputfile + ' for found web pages')
else:
    print('\nOverall '+str(faulty)+' faulty instance(s) detected!\nCheck ' + pathfetch + '../Txtdump*Errors.txt' + ' files for found web pages')
