#!/usr/bin/python
# coding=utf-8
import sys, time, os
from stem.control import Controller
from datetime import datetime

crawlingPath = os.getenv('dir_CRAWLING')

try:
	while True:
		inputfile = open(crawlingPath + 'tmp/kill-streams', 'r')
		kill_streams=inputfile.readline()
		inputfile.close()
		
		streams = []
		
		if kill_streams[0]=='1':
			# connect to Tor listening on port 9151
			while True:
				try:
					controller = Controller.from_port(port=9151)
					controller.authenticate()
				except: 
					time.sleep(1)
					continue
				break
			
			
			# kill open streams and print time to file
			streams = controller.get_streams(default='CON_LOST')
			
			with os.fdopen(os.open(crawlingPath + 'tmp/kill-streams', os.O_WRONLY | os.O_CREAT, 0666), 'w') as outputfile:
				outputfile.write('0')
				outputfile.close()
				
			# connection lost, reconnect to Tor
			if streams == 'CON_LOST':
				break;
				
			# iterate through open streams
			for stream in streams:
				try:
					controller.close_stream(stream.id)
				except:
					pass
				
			outputfile = open(crawlingPath + 'tmp/last_closed_streams', 'a')
			outputfile.write(str(datetime.now())+'\n')
			outputfile.close()
		time.sleep(5)
		
except KeyboardInterrupt:
	time.sleep(1)
