#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, shutil
import subprocess

def strip_ip(packet):
	rpacket = ""
	if packet != "": #last packet done. strip off header
		ip_offset = int(packet[1], 16) #in words (8 hexadecimals)
		tcp_offset = int(packet[ip_offset * 8 + 24], 16)
		offset = ip_offset + tcp_offset
		rpacket = packet[offset * 8:]
	return rpacket

def dump2ip(srcip, desip, l):

	ip = []
	want_packet = 0
	packet = ""
	for line in l:
		if line[0] == "1": #is header
			want_packet = 0
			header = line.split(" ")
			if len(header) > 4:
				if srcip in header[2] and desip in header[4]:
					if header[7] == "seq" and ":" in header[8]:
						if packet != "":
							ip.append([startseq, endseq, time, packet])
##                            if (endseq-startseq != len(packet)/2 - 52):
##                                print header
##                                print startseq, endseq, len(packet)
						time = float(header[0])
						seq = header[8].split(":")
						startseq = int(seq[0])
						endseq = int(seq[1][:-1])
						want_packet = 1
						packet = ""
		if line[0] == "\t": #is data
			if (want_packet == 1):
				data = line[10:]
				data = data[:data.index("  ")]
				data = data.split(" ")
				data = "".join(data)
				packet += data

	ip = sorted(ip, key = lambda ip:ip[0])
	retip = []
	lastseq = -1
	for x in ip:
		if (lastseq == -1 or x[0] == lastseq):
			retip.append(x)
			lastseq = x[1]
	return retip
    

def ip2stream(ip):
	#turns ip packets into stream
	#strips off both ip and tcp header

	stream = ""
	streamtimes = []
	for x in ip:
		stream += strip_ip(x[3])
		streamtimes.append([x[2], len(stream)])
	return stream, streamtimes

def stream2cell(stream, streamtimes, direction):
	cells = []
	i = 0 #points at the stream
	timelen = 0 #follows i, but is used for stream time. 
	streamtime_ptr = 0
	while i < len(stream):
		if stream[i:i+5] != "17030": #ssl data, major version 3, minor version unknown (1 or 2 usually)
			print "Version not correct at", i, "data", stream[i:i+5]
			if "17030" in stream[i:]:
				i += stream[i:].index("17030")
			else:
				return cells
		else:
			length = int(stream[i+6:i+10], 16)
			i = i + 10 + length * 2
    #        print "i", i, length
			for c in range(0, length/512):
				while (streamtimes[streamtime_ptr][1] < timelen):
					streamtime_ptr += 1
				time = streamtimes[streamtime_ptr][0]
				cells.append([time, direction])
				timelen += 1024
		totallen = i
	return cells
                
def findip(l):
	#returns two most popular ips
	ips = []
	ipfreqs = []
	for line in l:
		if line[0] == "1": #is header
##            print line
			header = line.split(" ")
			if len(header) > 4:
				if header[1] == "IP":
					srcip = header[2]
					desip = header[4][:-1]

                    #remove port
					srcip = ".".join(srcip.split(".")[:-2])
					desip = ".".join(desip.split(".")[:-2])
					if srcip in ips:
						ipfreqs[ips.index(srcip)] += 1
					else:
						ips.append(srcip)
						ipfreqs.append(1)
					if desip in ips:
						ipfreqs[ips.index(desip)] += 1
					else:
						ips.append(desip)
						ipfreqs.append(1)
	ips = zip(ips, ipfreqs)
	ips = sorted(ips, key=lambda ip: -ip[1])
	ipslist = []
	for x in ips:
		ipslist.append(x[0])
	return ipslist

#INPUT: Files of the format X-Y.txt in the same folder
#       These files are the text format of tcpdump files
#       X is the site number, Y is the instance number, if two
#       files share X they came from the same web page
#OUTPUT: X-X.cell, which is the cell format used for our experiments

###################################################################################################################
# Main code
###################################################################################################################

if __name__ == '__main__':
	
	# Arguments to be read from WFP_conf
	args = [ ('crawlingPath', 'dir_CRAWLING', 'crawlingPath') ]

	# Checking if all variables are/will be set
	for var, env, arg in args:
		if not '-'+arg in sys.argv:
			vars()[var] = os.getenv(env)
			if vars()[var] == None:
				exit_with_help('Error: Environmental Variables or Argument'+
							' insufficiently set! ($'+env+' / "-'+arg+'")')

	# Read parameters from command line call
	if len(sys.argv) != 0:
		i = 0
		options = sys.argv[1:]
		# iterate through parameter
		while i < len(options):
			if options[i] == '-crawlingPath':
				i = i + 1
				crawlingPath = options[i]
				if not crawlingPath.endswith('/'):
					crawlingPath += '/'
			else:
				exit_with_help('Error: Unknown Argument! ('+ options[i] + ')')
			i = i + 1
	
	outputDir = 'output-Wang-cell/'
	
	# Clean Output
	if os.path.isdir(crawlingPath + outputDir):
		shutil.rmtree(crawlingPath + outputDir)
	os.mkdir(crawlingPath + outputDir)
	
	print "Start..."
	badips = ["255.255.255"]    #also include your ip here
								#it is used to filter out all packets that
								#on the connection with the Tor entry node
	ownips = []
								
	ipfiles = os.listdir(crawlingPath + 'ips/')
	for ipfile in ipfiles:
		runfile, extension = os.path.splitext(ipfile)
		ownipsfile = open(crawlingPath + 'ips/{0}.ownips'.format(runfile), 'r')
		for ipaddr in ownipsfile:
			if ipaddr.replace('\n','') not in ownips:
				ownips.append(ipaddr.replace('\n',''))
			if ipaddr.replace('\n','') not in badips:
				badips.append(ipaddr.replace('\n',''))
		ownipsfile.close()
	
	# Looping over all files containing istances
	tcpWangfiles = os.listdir(crawlingPath  + 'output-tcp-Wang/')
	for tcpWangfile in tcpWangfiles:

		f = open(crawlingPath  + 'output-tcp-Wang/' + tcpWangfile, "r")
		l = f.readlines()
		f.close()

		ips = findip(l)
		good = 1
		for ip_i in range(0, min(len(ips), 8)):
			ip = ips[ip_i]
			out_cells = []
			inc_cells = []
			if (not(ip in badips)):
				print ip,
				try:
					if len(ownips) == 1:
						srcip = ownips[0] #write your ip here
								#a substring of it is ok, e.g. "1.2.3" works for "1.2.3.4"
					desip = ip
					ip = dump2ip(srcip, desip, l)

					stream, streamtimes = ip2stream(ip)
					out_cells = stream2cell(stream, streamtimes, 1)
                    
					temp = desip
					desip = srcip
					srcip = temp
					ip = dump2ip(srcip, desip, l)
					stream, streamtimes = ip2stream(ip)
					inc_cells = stream2cell(stream, streamtimes, -1)
					if (len(out_cells) > 5 and len(inc_cells) > 5):
						break
				except:
					pass
		for x in inc_cells:
			out_cells.append(x)
		out_cells = sorted(out_cells)

		fout = open(crawlingPath + outputDir + tcpWangfile + ".cell", "w")
		for x in out_cells:
			fout.write(repr(x[0]) + "\t" + str(x[1]) + "\n")
		fout.close()

		print len(out_cells), len(inc_cells)

