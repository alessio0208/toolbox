#!/usr/bin/python
# coding=utf-8

import sys, os
from tbselenium.tbdriver import TorBrowserDriver

def prepare_url_files(url_listsize, file_urls):
	"""Return files containing subsets of urls."""
	filenumber = 0
	count_pages = 0
	temp_url_list = []
	
	fin = open(file_urls, 'r')
	for page in fin:
		temp_url_list.append(page.replace('\n',''))
		count_pages += 1
		if count_pages == url_listsize:
			fout = open("run-" + file_urls.split('/')[-1] + "-" + str(filenumber).zfill(8) + ".txt", 'w')
			for url in temp_url_list:
				fout.write(url + '\n')
			fout.close()
			temp_url_list = []
			count_pages = 0
			filenumber += 1
	
	if len(temp_url_list) > 0:
		fout = open("run-" + file_urls.split('/')[-1] + "-" + str(filenumber).zfill(8) + ".txt", 'w')
		for url in temp_url_list:
			fout.write(url + '\n')
		fout.close()
	fin.close()
	
def parse_url_list(file_urls):
	"""Return list of urls from a file."""
	url_list = []
	
	with open(file_urls) as f:
		file_contents = f.read()
		url_list = file_contents.splitlines()

	return url_list
    
def exit_with_help(error=''):
	print("""\
Usage: launch-browser.py [options]

options:
	-setting { PREPARE_URLS | LAUNCH_BROWSER } : Select scenatio.
	-urlfile { /Path/to/Filename } : List of URLs for crawling
	-timeout { Number } : We wait for a given timeout in seconds a webpage to be loaded.
		(By default, it is 180 seconds.)
	-runidentifier { Name } : A name for an identification of a record.
	-hostname { Name } : Name of the crawling machine.
			
 """)
	print(error)
	sys.exit(1)

###################################################################################################################
# Main code
###################################################################################################################

if __name__ == '__main__':
	
	# Default parameters
	tmp1 = '180' # timeout for page load (in seconds)
	runidentifier = None
	hostname = None
	setting = None
	
	# Arguments to be read from WFP_conf
	args = [ ('tbb_dir', 'dir_BIN_TBB') ]

	# Checking if all variables are/will be set
	for var, env in args:
		vars()[var] = os.getenv(env)
		if vars()[var] == None:
			exit_with_help('Error: Environmental Variables or Argument ' + '$' + str(env) + ' insufficiently set!')

	# Read parameters from command line call
	if len(sys.argv) != 1:
		i = 0
		options = sys.argv[1:]
		# iterate through parameter
		while i < len(options):
			if options[i] == '-setting':
				i = i + 1
				setting = options[i]
			elif options[i] == '-urlfile':
				i = i + 1
				urlfile = options[i]
			elif options[i] == '-timeout':
				i = i + 1
				tmp1 = options[i]
			elif options[i] == '-runidentifier':
				i = i + 1
				runidentifier = options[i]
			elif options[i] == '-hostname':
				i = i + 1
				hostname = options[i]
			else:
				exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
			i = i + 1
	else:
		exit_with_help('Error: Arguments are missing!')

	# Check set variables
	if setting not in [ 'PREPARE_URLS', 'LAUNCH_BROWSER' ]:
		exit_with_help('Error: Unknown Setting!')
	
	if not os.path.isfile(urlfile):
		exit_with_help('Error: List of URLs dies not exist!')
		
	if runidentifier == None:
		exit_with_help('Error: Runidentifier is is not defined!')
		
	if setting == "PREPARE_URLS":
		# Determine how many pages are loaded before restarting the browser
		if runidentifier.startswith('wsc'):
			listsize_urls = 1
		else:
			listsize_urls = 5
			
		# Prepare files with subsets of URLs
		prepare_url_files(listsize_urls, urlfile)
	
	else:	
		if tmp1.isdigit():
			if int(tmp1) > 0:
				timeout = int(tmp1)
			else:
				exit_with_help('Error: Timeout is a Negative Number!')
		else:
			exit_with_help('Error: Timeout is is not a Number!')
		
		if hostname == None:
			exit_with_help('Error: Hostname is is not defined!')
			
		# Read URLs
		urls = parse_url_list(urlfile)
	
		urlfilename = urlfile.split('/')[-1]
	
		with TorBrowserDriver(tbb_dir) as driver:
			driver.load_url_improved(urls, runidentifier, hostname, urlfile, timeout)
