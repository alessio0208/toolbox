#!/bin/bash
# ./fetch-and-calculate.sh [runidentifier] [timeout] [urlfile]

set -x

# Prints help menu
exit_with_help() {
	printf "'FETCH' and 'FETCH_AND_CALCULATE' modes\n\n"
	printf "Usage: `basename $0` [runidentifier] [timeout] [urlfile]\n\n"
	printf "\tProgram for recording webpage traces where:\n"
	printf "\t\t[runidentifier]\t\t\tA name for an identification of a record.\n"
	printf "\t\t[timeout]\t\t\tThe program waits for a given timeout in seconds a webpage to be loaded\n"
	printf "\t\t[urlfile]\t\t\tA text file containing URLs of webpages.\n\n"
	printf "'CALCULATE' mode\n\n"
	printf "Usage: `basename $0`\n\n"
	exit 0
}

# Create the necessary directories for crawling if not existing
create_dirs() {
	if [ ${conf_FUNCTION} != "CHECK_HS_STATE" ]; then
		mkdir ${dir_CRAWLING}dumps/
		mkdir ${dir_CRAWLING}ips/
	fi

	mkdir ${dir_CRAWLING}log/
	mkdir ${dir_CRAWLING}screenshots/
	mkdir ${dir_CRAWLING}timestamps/
	mkdir ${dir_CRAWLING}txtdumps/
	mkdir ${dir_CRAWLING}tmp/

	# Create 'torctldumps' if we check the availablity of a hidden service 
	# (HS). In 'torctldumps' we store torCtl HS events used to check if 
	# the connection between a client and a hidden server is established.
	if [ ${conf_FUNCTION} == "CHECK_HS_STATE" ]; then
		mkdir ${dir_CRAWLING}torctldumps/
	fi
}

case "${conf_FUNCTION}" in
"FETCH" | "FETCH_AND_CALCULATE" | "CHECK_HS_STATE")
    if [ $# -ne 3 ]; then
		exit_with_help
    fi
    ;;
"CALCULATE")
    if [ $# -ne 0 ]; then
		printf "Invalid input!\n"
		exit_with_help
    fi
    ;;
esac

ECHO_DATE=true
DATE=$(date +%Y%m%d_%H%M%S)

COMPUTERNAME=${HOSTNAME}
USERNAME=${conf_USER}
RAWBACKUPFOLDER=${dir_STOR_RAW}
COMPILEDFOLDER=${dir_STOR_COMPILED}

# Parameter 1: Crawling-Directory
# Parameter 2: Log-Directory
parseFormats () {
	CRAWL=$1
	LOG=$2
	
	if [ ! -d $CRAWL -o ! -e $LOG ]
	then
		# invalid directories
		exit
	fi
	
	formats=("${conf_FORMATS[@]}") 
	if [[ " ${formats[@]} " =~ " tcp " ]]; then
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' raw-to-tcp.py'; fi
		echo 'raw-to-tcp.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}raw-to-tcp.py -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' parse-tcp.py'; fi
		echo 'parse-tcp.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}parse-tcp.py -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		df -h >> ${LOG}calculatelog-"${FILENAME}".log
		rm ${CRAWL}dumps/*.tcpdump
		delete=("tcp")
		formats=(${formats[@]/$delete})
	fi
	if [[ " ${formats[@]} " =~ " Wang-cell " ]]; then
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' raw-to-tcp.py'; fi
		echo 'raw-to-tcp.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}raw-to-tcp.py -crawlingPath ${CRAWL} -tcp-Wang-format "YES" >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' parse-tcp.py'; fi
		echo 'parse-tcp.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}parse-tcp.py -crawlingPath ${CRAWL} -tcp-Wang-format "YES" >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' ip2cell_wang_sanitized.py'; fi
		echo 'ip2cell_wang_sanitized.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}ip2cell_wang_sanitized.py -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		df -h >> ${LOG}calculatelog-"${FILENAME}".log
		rm ${CRAWL}dumps/*.txt
		delete=("Wang-cell")
		formats=(${formats[@]/$delete})
	fi
	
	if [[ ! ${#formats[@]} -eq 0 ]]; then
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' raw-to-tls.py'; fi
		echo 'raw-to-tls.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}raw-to-tls.py -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
	fi
	
	if [[ " ${formats[@]} " =~ "legacy" ]]; then
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' parse-tls.py -legacy'; fi
		echo 'parse-tls.py -legacy:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}parse-tls.py -legacy -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		delete=("tls-legacy")
		formats=(${formats[@]/$delete})
		
		temp=()
		for format in "tls-nosendme-legacy" "cell-legacy" "cell-nosendme-legacy"
		do
			if [[ " ${formats[@]} " =~ " ${format} " ]]; then
				temp+=("${format}")
			fi
		done
		if [ ! ${#temp[@]} -eq 0 ]; then
			advFormats=$(IFS=,; echo "${temp[*]}")
			echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
			if $ECHO_DATE; then echo `date +"%D-%T"`' parse-cells.py -legacy -formats '${advFormats}; fi
			echo 'parse-cells.py -legacy -formats '${advFormats}':' >> ${LOG}calculatelog-"${FILENAME}".log
			${dir_CRAWL_SCRIPTS}parse-cells.py -legacy -formats ${advFormats} -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
			wait
			for del in ${temp[@]}
			do
			   formats=(${formats[@]/$del})
			done
		fi
	fi
	
	if [[ ! ${#formats[@]} -eq 0 ]]; then
		# we have to have a non-legacy, non-tcp format
		echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' parse-tls.py'; fi
		echo 'parse-tls.py:' >> ${LOG}calculatelog-"${FILENAME}".log
		${dir_CRAWL_SCRIPTS}parse-tls.py -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
		wait
		delete=("tls")
		formats=(${formats[@]/$delete})
		
		temp=()
		for format in "tls-nosendme" "cell" "cell-nosendme"
		do
			if [[ " ${formats[@]} " =~ " ${format} " ]]; then
				temp+=("${format}")
			fi
		done
		if [ ! ${#temp[@]} -eq 0 ]; then
			advFormats=$(IFS=,; echo "${temp[*]}")
			echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
			if $ECHO_DATE; then echo `date +"%D-%T"`' parse-cells.py -formats '${advFormats}; fi
			echo 'parse-cells.py -formats '${advFormats}':' >> ${LOG}calculatelog-"${FILENAME}".log
			${dir_CRAWL_SCRIPTS}parse-cells.py -formats ${advFormats} -crawlingPath ${CRAWL} >> ${LOG}calculatelog-"${FILENAME}".log
			wait
			for del in ${temp[@]}
			do
			   formats=(${formats[@]/$del})
			done
		fi
	fi
	
	if [[ ! ${#formats[@]} -eq 0 ]]; then
		echo 'Something went wrong, not every format has been extracted?!'
	fi
	
	# Check if TLS was computed
	TLSRaw=(${CRAWL}dumps/*.tls)
	if [ -e ${TLSRaw[0]} ]
	then
		rm ${CRAWL}dumps/*.tls
	fi
	echo '----------' >> ${LOG}calculatelog-"${FILENAME}".log
	df -h >> ${LOG}calculatelog-"${FILENAME}".log
}


case "${conf_FUNCTION}" in
"FETCH" | "FETCH_AND_CALCULATE" | "CHECK_HS_STATE")

	RUNIDENTIFIER=$1
	TIMEOUT=$2
	URLFILE=$3

	FILENAME="${RUNIDENTIFIER}"-"${HOSTNAME}"-"${URLFILE}"

	# Clean directories used for crawling
	# Create the necessary directories for crawling if not existing
	${dir_CRAWLING}clear-all.sh
	create_dirs

	# Kill all processes, just to be sure
	echo Script: Killing all processes
	sudo ${dir_CRAWLING}kill-all.sh

	echo '-------------------- NEW RUN --------------------' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	if $ECHO_DATE; then echo `date +"%D-%T"`' Starting'; fi
	echo 'Starting' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	date >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	
	if [ ${conf_FUNCTION} == "FETCH_AND_CALCULATE" ]
	then
		echo '-------------------- NEW CALCULATION --------------------' >> ${dir_CRAWL_LOG}calculatelog-"${FILENAME}".log
		echo 'Starting' >> ${dir_CRAWL_LOG}calculatelog-"${FILENAME}".log
		date >> ${dir_CRAWL_LOG}calculatelog-"${FILENAME}".log
	fi

	time ${dir_CRAWLING}run-client-torbrowser.sh $RUNIDENTIFIER $TIMEOUT $URLFILE >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	echo "-------------------Fetched $(wc -l < ${URLFILE}-random) URLs once">> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	wait
	echo 'Finished' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	date >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	;;
"CALCULATE")
	for d in `ls ${dir_STOR_RAW} | xargs -n 1 basename`; do
		if [ ! -d "${dir_STOR_RAW}${d}" ]; then
			continue
		fi
		
		FILENAME="$(echo -e ${d} | awk -F '[_]' '{print $3}')-$(echo -e ${d} | awk -F '[_]' '{print $6}')-$(echo -e ${d} | awk -F '[_]' '{print $5}')"
	
		echo '-------------------- NEW CALCULATION --------------------' >> ${dir_STOR_RAW}${d}/log/calculatelog-"${FILENAME}".log
		if $ECHO_DATE; then echo `date +"%D-%T"`' Starting'; fi
		echo 'Starting' >> ${dir_STOR_RAW}${d}/log/calculatelog-"${FILENAME}".log
		date >> ${dir_STOR_RAW}${d}/log/calculatelog-"${FILENAME}".log
		
		# Extract Formats
		# NOTE: This would result in additional formats in the "raw" folder
		#       i.e. tls is required for tls-nosendme
		#       or cell is created together with cell-nosendme
		#       Therefore, we clean up later!
		parseFormats ${dir_STOR_RAW}${d}/ ${dir_STOR_RAW}${d}/log/
		
		COMP_FOLDER=$COMPILEDFOLDER"$(echo -e ${d} | awk -F '[_]' '{print $1}')_$(echo -e ${d} | awk -F '[_]' '{print $2}')_$(echo -e ${d} | awk -F '[_]' '{print $3}')_$(echo -e ${d} | awk -F '[_]' '{print $4}')_$(echo -e ${d} | awk -F '[_]' '{print $5}')_$(echo -e ${d} | awk -F '[_]' '{print $6}')"
		mkdir -p "${COMP_FOLDER}"
		
		cp ${dir_STOR_RAW}${d}/log/calculatelog-"${FILENAME}".log ${COMP_FOLDER}/
		
		for format in ${conf_FORMATS}
		do
			cp -R ${dir_STOR_RAW}${d}/output-${format} ${COMP_FOLDER}/
		done
		rm -rf ${dir_STOR_RAW}${d}/tmp
		
		# Cleanup "raw" folder
		for dir in `ls ${dir_STOR_RAW}${d}/ | grep "output-*" | xargs -n 1 basename`; 
		do 
			if [ ! -d ${dir_STOR_COMPILED}${d}/$dir ]
			then
				# Remove additional formats
				rm -r ${dir_STOR_RAW}${d}/$dir
			fi
		done
	done
	;;
esac

if [ ${conf_FUNCTION} == "FETCH_AND_CALCULATE" ]; then
	# Extract formats
	parseFormats ${dir_CRAWLING} ${dir_CRAWL_LOG}
fi

if [ ${conf_FUNCTION} == "CHECK_HS_STATE" ]; then
	echo '----------' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	if $ECHO_DATE; then echo `date +"%D-%T"`' check-hs-state.py'; fi
	echo 'check-hs-state.py:' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	${dir_CRAWL_SCRIPTS}check-hs-state.py >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	wait
	echo '----------' >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
	df -h >> ${dir_CRAWL_LOG}fetchlog-"${FILENAME}".log
fi

if [ ${conf_FUNCTION} == "FETCH" -o ${conf_FUNCTION} == "FETCH_AND_CALCULATE" -o ${conf_FUNCTION} == "CHECK_HS_STATE" ]
then
	# Kill all processes
	sudo ${dir_CRAWLING}kill-all.sh

	mkdir -p $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	
	if [ ${conf_FUNCTION} == "FETCH_AND_CALCULATE" ]
	then
		mkdir -p $COMPILEDFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
		
		for format in ${conf_FORMATS}
		do
			cp -R ${dir_CRAWLING}output-${format} $COMPILEDFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME/
			mv ${dir_CRAWLING}output-${format} $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
		done

		cp ${dir_CRAWLING}log/fetchlog-"${FILENAME}".log $COMPILEDFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME/
		cp ${dir_CRAWLING}log/calculatelog-"${FILENAME}".log $COMPILEDFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME/
		
		if [ -f ${dir_CRAWLING}ERRORS.txt ]
		then
			cp ${dir_CRAWLING}ERRORS.txt $COMPILEDFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME/
		fi
		
		cd $COMPILEDFOLDER
		chown -R $USERNAME *
	fi
		
	if [ -f ${dir_CRAWLING}ERRORS.txt ]
	then
		mv ${dir_CRAWLING}ERRORS.txt $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME/
	fi
	
	if [ ${conf_FUNCTION} != "CHECK_HS_STATE" ]; then
		mv ${dir_CRAWLING}dumps $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
		mv ${dir_CRAWLING}ips $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	fi
	
	mv ${dir_CRAWLING}log $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	mv ${dir_CRAWLING}screenshots $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	mv ${dir_CRAWLING}timestamps $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	mv ${dir_CRAWLING}txtdumps $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	
	if [ ${conf_FUNCTION} == "CHECK_HS_STATE" ]; then
		mv ${dir_CRAWLING}torctldumps $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
		mv ${dir_CRAWLING}output-hs $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	fi
	
	rm -rf ${dir_CRAWLING}tmp
	rm -rf ${dir_CRAWLING}*-random

	cd ${dir_CRAWLING}
	chown -R $USERNAME *

	cd $RAWBACKUPFOLDER
	#uncomment if archive wanted
	#tar -zcvf $DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME".tar.gz" $RAWBACKUPFOLDER$DATE"_"$RUNIDENTIFIER"_"$TIMEOUT"_"$URLFILE"_"$COMPUTERNAME
	chown -R $USERNAME *

	echo ""
	echo "Watch out for the ERROR.txt file. If it exists there occured errors during crawling."
	
	# Clean up
	${dir_CRAWLING}clear-all.sh
	df -h
fi

if $ECHO_DATE; then echo `date +"%D-%T"`; fi
set +x
