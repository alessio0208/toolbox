#!/usr/bin/python
# coding=utf-8
#
##################################################################
#
# ./tor-hsConnStatus-stem.py
#
# Description: Add listening to events:
#	- Circ_event
#	- Circ_minor_event
#	- HS_desc event
# in order to save information for a connection establishment 
# between a client and a hidden service.
#
# Adjust the following variables before executing:
#
#	crawlingPath The name of the path where a file with 
#			HS connection information is saved.
#
#	filename The name of the file where HS connection
#			establishments are saved.
#
###################################################################

import time, sys, os
import stem
import getpass
import stem.connection

from stem.control import Controller, EventType

crawlingPath = os.getenv('dir_CRAWLING')
filename = sys.argv[1]

##################################################
# HS_desc event
##################################################
def print_hs_desc_event(event):
	current_time = int(time.time()  * 1000)
	
	with open(crawlingPath + 'torctldumps/' + filename + '.torctl', 'a') as output:
		output.write('%d HS_DESC %s %s %s %s\n' % (current_time, event.address, event.action, event.authentication, event.reason))

##################################################
# Circ_event
##################################################
def print_circs_event(event):
	current_time = int(time.time()  * 1000)
			
	with open(crawlingPath + 'torctldumps/' + filename + '.torctl', 'a') as output:
		if event.hs_state != None:
			output.write('%d CIRC %s %s %s\n' % (current_time, event.status, event.purpose, event.hs_state))

##################################################
# Circ_minor_event
##################################################
def print_circs_minor_event(event):
	current_time = int(time.time()  * 1000)
	
	with open(crawlingPath + 'torctldumps/' + filename + '.torctl', 'a') as output:
		if event.hs_state != None:
			output.write('%d CIRC_MINOR %s %s %s\n' % (current_time, event.purpose, event.old_purpose, event.hs_state))

##################################################
# Main
##################################################

if __name__ == '__main__':
	
	# Connect to Tor listening on port 9151
	while True:
		try:
			control_socket = stem.socket.ControlPort(port = 9151)
		except stem.SocketError as exc:
			time.sleep(1)
			continue
		break

	with Controller.from_port(port = 9151) as controller:
		controller.authenticate()

		try:
			controller.add_event_listener(print_circs_event, EventType.CIRC)
			controller.add_event_listener(print_hs_desc_event, EventType.HS_DESC)
			controller.add_event_listener(print_circs_minor_event, EventType.CIRC_MINOR)
		except stem.ProtocolError as exc:
			print 'tor-hsConnStatus-stem.py: ProtocolError: %s' % exc
			sys.exit(1)

		try:
			while True:
				time.sleep(5)
		except KeyboardInterrupt: pass
