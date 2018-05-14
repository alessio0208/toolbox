#!/usr/bin/python

# Retrieves/stores x subpages for each url in the input file

# python CrawlSite.py

import time, codecs, sys, glob, os, shutil
from selenium import webdriver
from random import randint

firefox_profile = os.getenv('dir_FF_PROFILE')
url_input = os.getenv('file_URLList')
count = int(os.getenv('conf_SUBPAGES'))
MAX_WAIT_TIME_FOR_PAGELOAD = int(os.getenv('conf_PAGELOAD_TIMEOUT'))


def getURL(url):
	profile = webdriver.firefox.firefox_profile.FirefoxProfile(firefox_profile)
	driver = webdriver.Firefox(firefox_profile=profile)
	driver.implicitly_wait(MAX_WAIT_TIME_FOR_PAGELOAD)
	driver.get(url)
	#determine number of clicks
	depth=1
	pagerand=randint(1,10000)
	if 5000 < pagerand and pagerand <= 7500: #25%
		depth=2
	elif 7500 < pagerand and pagerand <= 8750: #12.5%
		depth=3
	elif 8750 < pagerand and pagerand <= 9375: #6.25%
		depth=4
	elif 9375 < pagerand: #6.25%
		depth=5

	print "Depth: %d" %(depth)

	while (depth > 0):
		time.sleep(15)	
		links = driver.find_elements_by_partial_link_text('')
		if ((len(links)-1) <= 0):
			driver.get(url)
			break
		success=0
		while (success == 0):
			linknum=randint(0,len(links)-1)
			print "Link: %d/%d" %(linknum, (len(links)-1))
			l = links[linknum]
			try:
				l.click()
				success = 1
				depth=depth-1
			except:
				print "Fail"
				time.sleep(1)
	

	#print "URL: %s" %(driver.current_url)
	time.sleep(5)
	fetched=driver.current_url
	driver.quit()
	return fetched


if glob.glob('fetches_*.txt'):
	currentTime = time.time()
	os.mkdir("%d" %currentTime)
	for fetch in glob.glob('fetches_*.txt'):
		shutil.move(fetch, "%d" %currentTime)

fdin = open(url_input, 'r')
for url in fdin:
	pages = {}
	i=1
	tries=1
	shorturl = url.replace("\n", "")
	shorturl = shorturl.replace("://www.", "://")
	shorturl = shorturl.replace("http://", "")
	shorturl = shorturl.replace("https://", "")
	pages[shorturl] = 1
	shorturl = shorturl.replace("/", "")
	fdout = codecs.open('fetches_'+shorturl+'.txt', encoding='utf-8', mode='w')
	fdout.write(url)
	while (i <= count):
		deepUrl = getURL(url)
		tries += 1
		#if not shorturl in deepUrl:
		#	print "Wrong Domain: %s" %(deepUrl)
		#	continue
		shortUrl = deepUrl.replace("://www.", "://")
		shortUrl = shortUrl.replace("http://", "")
		shortUrl = shortUrl.replace("https://", "")   
		if not shortUrl in pages: 
			pages[shortUrl] = 1
			i+=1
			fdout.write(deepUrl+"\n")
		else:
			pages[shortUrl] += 1
		if tries >= count*25:
			break
	fdout.close()
fdin.close()





