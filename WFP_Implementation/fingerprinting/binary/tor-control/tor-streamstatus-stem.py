#!/usr/bin/python
# coding=utf-8
import sys, os, time 
from stem.control import Controller

crawlingPath = os.getenv('dir_CRAWLING')

try:
	while True:

		streams = []
		
		# connect to Tor listening on port 9151
		while True:
			try:
				controller = Controller.from_port(port=9151)
				controller.authenticate()
			except: 
				time.sleep(1)
				continue
			break
		
		# constantly read number of open streams and print to file
		while True:
			streams = controller.get_streams(default='CON_LOST')
			# connection lost, reconnect to Tor
			if streams == 'CON_LOST':
				break;
			# print result
			else: 
				outputfile = open(crawlingPath + 'tmp/number-streams', 'w')
				outputfile.write(str(len(streams)) + '\n')
				outputfile.close()
			time.sleep(5)
		
		time.sleep(1)
		
except KeyboardInterrupt:
	time.sleep(1)
