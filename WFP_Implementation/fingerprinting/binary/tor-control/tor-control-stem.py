#!/usr/bin/python
# coding=utf-8
import sys, time

from stem.util.connection import get_connections, get_system_resolvers
from stem.util.system import get_pid_by_name

resolvers = get_system_resolvers()

if not resolvers:
  print 'Stem doesn\'t support any connection resolvers on our platform.'
  sys.exit(1)

picked_resolver = resolvers[0]  # lets just opt for the first
#print 'Our platform supports connection resolution via: %s (picked %s)' % (', '.join(resolvers), picked_resolver)

seenips = set()

try:
	while True:
		#try to get tor pid
		tor_pids = []
		while len(tor_pids) != 1:
			tor_pids = get_pid_by_name('tor', multiple = True)
			time.sleep(5)
		tor = tor_pids[0]

		# constantly read tor ips and output them
		while tor in get_pid_by_name('tor', multiple = True):
			try:
				for conn in get_connections(picked_resolver, process_pid = tor_pids[0], process_name = 'tor'):
					#print '  %s:%s => %s:%s' % (conn.local_address, conn.local_port, conn.remote_address, conn.remote_port)
					if conn.remote_address == '127.0.0.1':
						continue
					elif conn.remote_address not in seenips:
						print conn.remote_address
						seenips.add(conn.remote_address)
						sys.stdout.flush()
					# should be included in *.ownips
					# if conn.local_address not in seenips:
					#	print conn.local_address
					#	seenips.add(conn.local_address)
					#	sys.stdout.flush()	
				time.sleep(1)
			except:
				break
		time.sleep(1)
	
except KeyboardInterrupt:
	time.sleep(1)
