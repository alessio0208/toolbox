#!/bin/bash

# Deletes all collected and computed data
# ./clear-all.sh

rm -rf ${dir_CRAWLING}dumps/
rm -rf ${dir_CRAWLING}ips/
rm -rf ${dir_CRAWLING}log/
rm -Rf ${dir_CRAWLING}output*
rm -rf ${dir_CRAWLING}screenshots/
rm -rf ${dir_CRAWLING}timestamps/
rm -rf ${dir_CRAWLING}txtdumps/
rm -Rf ${dir_CRAWLING}tmp/
rm -rf ${dir_CRAWLING}run-*.txt
rm -rf ${dir_CRAWLING}*-random
rm -rf ${dir_CRAWLING}ERRORS.txt

if [ ${conf_FUNCTION} == "CHECK_HS_STATE" ]
then
	rm -Rf ${dir_CRAWLING}torctldumps/
fi
