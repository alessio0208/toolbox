#!/usr/bin/env python

# Script for removing faulty instances from input folder
#
# python clean-fetches.py

import sys, os, errno

def exit_with_help(error=''):
    print("""\
Usage: clean-fetches.py [options]

options:
   -pcompiled { /Path/ } : Path to the Instances in Folder Compiled
   -in { /Path/ } : Path to Inputfile with faulty Instances
   -cleanTxtdumps { /Path/ }: If it is set, faulty Instances from '/Path/'
                folder are also removed. (By default, we do not use it!)
 """)
    print(error)
    sys.exit(1)
    
def remove_faulty_instance(formatfilename):
    removed = False
    try:
        #print formatfilename
        os.remove(formatfilename)
        removed = True;
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
    return removed
	
args = [ ('pathcompiled', 'dir_TEMP_COMPILED', 'pcompiled'),
         ('pathfetch', 'dir_FETCH_SCRIPTS', 'in'),  
         ('pathtxtdumps', 'dir_STOR_RAW', 'cleanTxtdumps') ]    
         
# Identifies if faulty txtdump Instances should be removed as well
removeTxtdumps = False

# Checking if all variables are/will be set
for var, env, arg in args:
    if not '-'+arg in sys.argv:
        vars()[var] = os.getenv(env)
        if vars()[var] == None and var != 'pathtxtdumps': # This var is otional!
            exit_with_help('Error: Environmental Variables or Argument'+
                        ' insufficiently set! ($'+env+' / "-'+arg+'")')

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
        elif options[i] == '-in':
            i = i + 1
            pathfetch = options[i]
            if not pathfetch.endswith('/'):
                pathfetch += '/'
        elif options[i] == '-cleanTxtdumps':
            i = i + 1
            removeTxtdumps = True
            pathtxtdumps = options[i]
            if not pathtxtdumps.endswith('/'):
                pathtxtdumps += '/'
        else:
            exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
        i = i + 1

# Check set variables
if not os.path.isdir(pathcompiled):
    exit_with_help('Error: Invalid Compiled Fetches Path!')
if not os.path.isdir(pathfetch):
    exit_with_help('Error: Invalid Input Path for faulty Instances!')
if removeTxtdumps:
    if not os.path.isdir(pathtxtdumps):
        exit_with_help('Error: Invalid Input Path for faulty txtdump Instances!')

# Additional checks
inputfile = pathfetch + '../TxtdumpErrors.txt' #stored filenames
if not os.path.isfile(inputfile):
    print('Error: No input file exists!\nRun check-fetches.py to create ' + inputfile)
    sys.exit(1)

# input invalid patterns
f = open(inputfile, 'r')
faultyfiles = f.readlines()
f.close()

removed=0
removedTxtdump = 0
for faulty in faultyfiles:    
    if faulty == "" or faulty == '\n':
        continue
        
    top, pagename = faulty.split('/')
    pagename = pagename.rstrip()

    subpath=pathcompiled+top+'/'
    try:
        formats=os.listdir(subpath)
    except OSError as e:
        print('Is the input directory ('+ pathcompiled + ') empty?')
        break
   
    done = False
    for form in formats:
        
        if os.path.isfile(subpath + form):
            continue

        # added due to compatability problems
        if '___-___' in pagename:
            # Skip non-existing files
            if not os.path.isfile(subpath + form + '/' + pagename):
                continue
            done = remove_faulty_instance(subpath+form+'/'+pagename)
        else:
            formatpages = os.listdir(subpath + form + '/')
            for formatpage in formatpages:
                if formatpage.split('___-___')[0] == pagename:
                    done = remove_faulty_instance(subpath + form + '/' + formatpage)

    if done:
        removed=removed+1
        print('INFO: (' + str(removed) + '/' + str(len(faultyfiles)) + ') have been removed')
    else:
        print('ERROR: Did not find '+top+'/.../'+pagename)
       
    if removeTxtdumps:
        subtxtdumpspath = pathtxtdumps + top + '/txtdumps/'
        subpngspath = pathtxtdumps + top + '/screenshots/'
        
        try:
            txtdumps = os.listdir(subtxtdumpspath)
        except OSError as e:
            print('Is the txtdumps directory ('+ pathtxtdumps + ') empty?')
            break
            
        try:
            screenshots = os.listdir(subpngspath)
        except OSError as e:
            print('Is the txtdumps directory ('+ subpngspath + ') empty?')
            break
            
        txtdone = False
        
        # Skip non-existing files
        if os.path.isfile(subtxtdumpspath + pagename + '.txt'):
            try:
                os.remove(subtxtdumpspath + pagename + '.txt')
                os.remove(subpngspath + pagename + '.png')
                txtdone = True;
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

        if txtdone:
            removedTxtdump = removedTxtdump + 1
            print('INFO: (' + str(removedTxtdump) + '/' + str(len(faultyfiles)) + ') txtdump have been removed')
        else:
            print('ERROR: Did not find '+ subtxtdumpspath + pagename + '.txt')

print('\nOverall '+str(removed)+'/'+str(len(faultyfiles))+' faulty instance(s) removed from input directory!')

if removeTxtdumps:
    print('\nOverall '+str(removedTxtdump)+'/'+str(len(faultyfiles))+' faulty txtdump instance(s) removed from txtdumps directory!')
    if removedTxtdump != len(faultyfiles):
        print('Error(s) occured during removing faulty txtdump instance(s).')
    
#if removed == len(faultyfiles):
    #os.remove(inputfile)
    #print('Input file ('+inputfile+') has been deleted.')
#else: 
    #print('Error(s) occured. Input file ('+inputfile+') has not been deleted.')
if removed != len(faultyfiles):
    print('Error(s) occured while removing faulty instance(s).')
