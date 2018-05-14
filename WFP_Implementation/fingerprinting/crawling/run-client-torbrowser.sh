#!/bin/bash
# ./run-client-torbrowser.sh [runidentifier] [timeout] [urlfile]

set -x 

if [ $# -ne 3 ]; then
	echo "Usage: `basename $0` [runidentifier] [timeout] [urlfile]"
	exit -1
fi

USERNAME=${conf_USER}
ETHDEVICE=${conf_ETHDEVICE}

TCPDUMPBIN="tcpdump"
TORCONTROLBIN="${dir_BIN_TOR}tor-control-stem.py"
TORSTATUSBIN="${dir_BIN_TOR}tor-streamstatus-stem.py"
TORKILLSTREAMBIN="${dir_BIN_TOR}tor-kill-streams-stem.py"
TORHSCONNECTION="${dir_BIN_TOR}tor-hsConnStatus-stem.py"
FIREFOXLAUNCHER="${dir_CRAWLING}scripts/launch-browser.py"
FIREFOXPROFILE="${dir_BIN_TBB}Browser/TorBrowser/Data/Browser/profile.default"

BASEPATH="${dir_CRAWLING}"
RUNIDENTIFIER=$1
TIMEOUT=$2
URLFILE=$3

# !!! Please, do not change the value of ${LISTSIZE} without a reason !!! 
# !!! Other scripts use the same value !!!
# If the value is different in the different scripts, then you have a problem!
if [[ ${RUNIDENTIFIER} == *"wsc"* ]]; then
	LISTSIZE="1"
else
	LISTSIZE="5"
fi

HARDTIMEOUTFACTOR="2" #defined by other scripts

FILENAME="${RUNIDENTIFIER}"-"${HOSTNAME}"-"${URLFILE}"

if [ ${conf_FUNCTION} != "CHECK_HS_STATE" ]; then
	LOCALEIP=$(/sbin/ip addr show ${ETHDEVICE} | grep "inet " | sed 's/\// /' | awk '{print $2}')
fi

# save data about tor browser
echo Script: saving information about used TBB
unzip -c ${dir_BIN_TBB}/Browser/browser/omni.ja defaults/preferences/000-tor-browser.js | grep "torbrowser.version"
cat ${FIREFOXPROFILE}/prefs.js | grep "gecko.mstone"
cat ${FIREFOXPROFILE}/prefs.js | grep "gecko.buildID"
cat ${FIREFOXPROFILE}/prefs.js | grep "extensions.enabledAddons"

# emptying status file
echo Script: emptying status file
echo "" > ${BASEPATH}tmp/.lock-${HOSTNAME}

# initializing number of streams status file
echo Script: initializing number of streams and kill streams status file
echo "0" > ${BASEPATH}tmp/number-streams
echo "0" > ${BASEPATH}tmp/kill-streams

if [ ${conf_FUNCTION} != "CHECK_HS_STATE" ]; then
	# saving own ip
	echo Script: saving own ip
	echo ${LOCALEIP} > ${BASEPATH}ips/"${FILENAME}".ownips

	# continuously saving ips of tor entry nodes
	echo Script: continuosly saving ips of tor entry nodes
	sudo ${TORCONTROLBIN} > ${BASEPATH}ips/"${FILENAME}".torips &
fi

# monitoring tor stream status
${TORSTATUSBIN} & ${TORKILLSTREAMBIN} &

# check if we have duplicate entries in url file
echo Script: checking for duplicate urls
duplicates=$(sort ${URLFILE} | uniq -d | wc -l)
if [ ${duplicates} -ne 0 ]; then
	echo Script: "${duplicates}" duplicate urls found - duplicates will be removed
	sort ${URLFILE} | uniq -d > ${BASEPATH}log/duplicates-"${FILENAME}".log
fi

# randomize url file
echo Script: randomize url file and remove duplicates
for i in `cat ${URLFILE} | sort -u`; do echo "$RANDOM $i"; done | sort | sed -r 's/^[0-9]+ //' > ${BASEPATH}`basename ${URLFILE}`-random

# creating files containing subset of pages
${FIREFOXLAUNCHER} -setting "PREPARE_URLS" -runidentifier "${RUNIDENTIFIER}" -urlfile "${URLFILE}"-random

if [ ${conf_FUNCTION} != "CHECK_HS_STATE" ]; then
	# starting tcpdump
	echo Script: starting tcpdump
	sudo ${TCPDUMPBIN} -Z ${USERNAME} -n -i ${ETHDEVICE} -w ${BASEPATH}dumps/"${FILENAME}".raw -s 0 -U "tcp and (src host ${LOCALEIP} or dst host ${LOCALEIP}) and not ( (src host ${LOCALEIP} and (src port 22 or src port 5900)) or (dst host ${LOCALEIP} and (dst port 22 or dst port 5900)) )" &
	sleep 5
else
	lineCounter=0
fi

# starting Firefox
echo Script: starting Firefox
for f in `ls ${dir_CRAWLING}run-*.txt | xargs -n 1 basename`; do
	echo "Processing file $f"; 
	FINISHEDREGULARLY=0
	# when firefox crashed it will timeout and be restartet with the last 10 pages that were loaded.
	
	if [ ${conf_FUNCTION} == "CHECK_HS_STATE" ]; then
		let lineCounter=lineCounter+1
		# log hs connection establishment
		${TORHSCONNECTION} "$(cat ${URLFILE}-random | head -$lineCounter | tail -1)" &
	fi

	STARTTIME=$(date +%s)
	CURRENTTIME=$(date +%s)
	${FIREFOXLAUNCHER} -setting "LAUNCH_BROWSER" -urlfile "$f" -timeout "${TIMEOUT}" -runidentifier "${RUNIDENTIFIER}" -hostname "${HOSTNAME}" >> ${BASEPATH}log/tbb-"${FILENAME}".log &
	while [ $(grep -c 1 ${BASEPATH}tmp/.lock-${HOSTNAME}) -ne 1 -a $((STARTTIME+LISTSIZE*TIMEOUT*HARDTIMEOUTFACTOR)) -gt $CURRENTTIME ]; do
		sleep 5;
		CURRENTTIME=$(date +%s)
	done
	if [ $((STARTTIME+LISTSIZE*TIMEOUT*HARDTIMEOUTFACTOR)) -gt $CURRENTTIME ]; then
		FINISHEDREGULARLY=1
		echo "everything went ok"
	else
		echo "Firefox seems to be crashed. Storing list of of potentially unfinished URLs."
		cat ${dir_CRAWLING}$f
		echo "Last finished URL before crash:"
		tail -1 ${dir_CRAWLING}timestamps/"${FILENAME}".log
		echo "Last finished URL before crash:" >> ERRORS.txt
		tail -1 ${dir_CRAWLING}timestamps/"${FILENAME}".log >> ERRORS.txt
		echo "-----------------------------------" >> ERRORS.txt
		echo "Storing list of potentially unfinished URLs:" >> ERRORS.txt
		cat ${dir_CRAWLING}$f >> ERRORS.txt
		echo "-----------------------------------" >> ERRORS.txt
	
	fi
	echo "" > ${BASEPATH}tmp/.lock-${HOSTNAME}
	sudo killall -9 firefox
	sudo killall -9 firefox-bin
	sudo killall -9 ${TORHSCONNECTION}
	sleep 5;

	rm -rf ${dir_CRAWLING}$f
done

rm  ${BASEPATH}tmp/.lock-${HOSTNAME}

echo Script: killing programs
sudo ${BASEPATH}kill-all.sh

sudo chown -R ${USERNAME} *
set +x
