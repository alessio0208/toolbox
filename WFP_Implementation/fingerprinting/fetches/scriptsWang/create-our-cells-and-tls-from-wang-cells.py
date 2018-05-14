#! /usr/bin/env python

# Create our instances of Wang's cell format
# Additionally, reconstruct tls records 
# Works with Wang's 2014 data

import sys, os, shutil


num_of_instances=90
num_of_pages=100
num_of_openWorldBG=9000 #9000 #if unequal zero, only background will be generated


# Clean Up
if os.path.isdir('output-tls-nosendmes/'):
	shutil.rmtree('output-tls-nosendmes/')
os.mkdir('output-tls-nosendmes/')
if os.path.isdir('output-cells-nosendmes/'):
	shutil.rmtree('output-cells-nosendmes/')
os.mkdir('output-cells-nosendmes/')

# Open World or Closed World
if num_of_openWorldBG == 0:
	border = num_of_instances
	outborder = num_of_pages
else:
	border = num_of_openWorldBG
	outborder = 1

# For every Page
for site in range(0,outborder):
	
	# Closed World / Foreground has multiple instances per page
	if num_of_openWorldBG == 0:
		filename = 'alexa_' + str(site).zfill(3) + '.com'
		
		tlsfile = open('output-tls-nosendmes/' + filename, 'w')
		cellfile = open('output-cells-nosendmes/' + filename, 'w')
	
	for instance in range(0, border):
		
		# Closed World / Foreground has multiple instances per page
		if num_of_openWorldBG == 0:
			fname = str(site) + '-' + str(instance)
		else:
			filename = 'bg_alexa_' + str(instance).zfill(6) + '.com'
			
			tlsfile = open('output-tls-nosendmes/' + filename, 'w')
			cellfile = open('output-cells-nosendmes/' + filename, 'w')
			fname = str(instance)
			
		# Write Name and timing information for proper outlier removal
		tlsfile.write('%s %d ' % (filename, instance))
		cellfile.write('%s %d ' % (filename, instance))
		data = []
		
		#Read times, sizes
		f = open('batch/' + fname, 'r')
		data = []
		for x in f:
			x = x.split('\t')
			data.append((float(x[0]), int(x[1])))
		f.close()
		
		# Reconstruct TLS  records from timestamps
		timestamp=1
		prevtime=-1
		count=-1
		direction=0
		for time, packet in data:
			if (prevtime == -1):
					prevtime=time
					direction=packet
					count=0
			
			if (time == prevtime) and (direction == packet):
				count += 1
			else:
				outputsize = count * 512 * direction * -1
				tlsfile.write('%s:%s ' % (str(timestamp),str(outputsize)))
				count=1
				prevtime=time
				direction=packet
				
			cellfile.write('%s:%s ' % (str(timestamp),str(packet*586*-1)))
			timestamp+=1
		
		outputsize = count * 512 * direction * -1
		tlsfile.write('%s:%s\n' % (str(timestamp),str(outputsize)))
		cellfile.write('\n')
		#tlsfile.write('\n')
		
		if num_of_openWorldBG != 0:
			tlsfile.close()
			cellfile.close()

	if num_of_openWorldBG == 0:
		tlsfile.close()
		cellfile.close()
