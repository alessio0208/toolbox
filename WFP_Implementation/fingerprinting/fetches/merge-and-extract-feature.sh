#!/bin/bash
# ./merge-and-extract-feature.sh

if [ ! -d ${dir_STOR_COMPILED} -o ! -d ${dir_STOR_RAW} ]
then
	printf "Is the directory (" + ${dir_STORAGE} + ") empty?"
	exit 1
fi

if [ `find "${dir_STOR_RAW}" -prune -empty -type d` ]
then
	printf "Is the directory (" + ${dir_STOR_RAW} + ") empty?"
	exit 1
fi

if [ `find "${dir_STOR_COMPILED}" -prune -empty -type d` ]
then
	printf "Is the directory (" + ${dir_STOR_COMPILED} + ") empty?"
	exit 1
fi

mkdir -p ${dir_TEMP}
mkdir -p ${dir_TEMP_COMPILED}

URLS=()
for i in `ls ${dir_STOR_COMPILED} | xargs -n 1 basename`; do
	URLNAME="$(echo $i | awk -F '[_]' '{print $5}')"
	if [[ "${URLS[@]}" =~ "${URLNAME}" ]]; then
		continue
	else
		URLS+=(${URLNAME})
	fi
done

for url in "${URLS[@]}"; do
	remove=()
	for d in `ls ${dir_STOR_COMPILED} | xargs -n 1 basename`; do
		URLFILE="$(echo $d | awk -F '[_]' '{print $5}')"
		if [[ ${url} == ${URLFILE} ]]; then
			remove+=("$d")
		fi
	done
	
	for r in "${remove[@]}"; do
		printf "Copy folder ($r) in progress ...\n"
		cp -R ${dir_STOR_COMPILED}${r} ${dir_TEMP_COMPILED}
	done

	echo '-------------------- NEW FEATURE GENERATION --------------------' >> ${dir_FETCHES}generate-feature.log
	echo `date +"%D-%T"`' Starting' >> ${dir_FETCHES}generate-feature.log

	echo 'check-fetches.py:' >> ${dir_FETCHES}generate-feature.log
	echo '----------' >> ${dir_FETCHES}generate-feature.log
	${dir_FETCH_SCRIPTS}check-fetches.py -pcompiled ${dir_TEMP_COMPILED} -praw ${dir_STOR_RAW} | tail -2 >> ${dir_FETCHES}generate-feature.log
	echo '----------' >> ${dir_FETCHES}generate-feature.log

	echo 'clean-fetches.py:' >> ${dir_FETCHES}generate-feature.log
	echo '----------' >> ${dir_FETCHES}generate-feature.log
	CLEAN_FETCHES_OUTPUT="$(${dir_FETCH_SCRIPTS}clean-fetches.py -in ${dir_TEMP_COMPILED})"
	CLEAN_FETCHES=(${CLEAN_FETCHES_OUTPUT// / }) 
	for (( i=0; i<${#CLEAN_FETCHES[@]}; i++ )); do
		if [[ ${CLEAN_FETCHES[$i]} == *"ERROR"* ]]; then
			echo "${CLEAN_FETCHES[$i]} ${CLEAN_FETCHES[$i+1]} ${CLEAN_FETCHES[$i+2]} ${CLEAN_FETCHES[$i+3]} ${CLEAN_FETCHES[$i+4]}" >> ${dir_FETCHES}generate-feature.log
		fi
	done
	echo '----------' >> ${dir_FETCHES}generate-feature.log

	echo 'merge-input.sh:' >> ${dir_FETCHES}generate-feature.log
	echo '----------' >> ${dir_FETCHES}generate-feature.log
	${dir_FETCH_SCRIPTS}merge-input.sh >> ${dir_FETCHES}generate-feature.log
	wait
	echo '----------' >> ${dir_FETCHES}generate-feature.log

	if [ ${conf_SETTING} == "OW_FG" -o ${conf_SETTING} == "CW" ]; then
		echo 'outlier-removal.py:' >> ${dir_FETCHES}generate-feature.log
		echo '----------' >> ${dir_FETCHES}generate-feature.log
		OUTLIER_REMOVAL_OUTPUT="$(${dir_FETCH_SCRIPTS}outlier-removal.py -in ${dir_TEMP_MERGED})"
		OUTLIER_REMOVAL=(${OUTLIER_REMOVAL_OUTPUT// / }) 
		for (( i=0; i<${#OUTLIER_REMOVAL[@]}; i++ )); do
			if [[ ${OUTLIER_REMOVAL[$i]} == *"WARN"* ]]; then
				echo "${OUTLIER_REMOVAL[$i]} ${OUTLIER_REMOVAL[$i+1]} ${OUTLIER_REMOVAL[$i+2]} ${OUTLIER_REMOVAL[$i+3]}" >> ${dir_FETCHES}generate-feature.log
			fi
		done
		echo '----------' >> ${dir_FETCHES}generate-feature.log
	fi

	echo 'generate-feature.py:' >> ${dir_FETCHES}generate-feature.log
	echo '----------' >> ${dir_FETCHES}generate-feature.log

	if [ ! -d ${dir_TEMP_MERGED} -a ${conf_SETTING} == "OW_BG" ]; then
		printf "No available data for generating BG features!"
		exit 1
	fi

	if [ ! -d ${dir_TEMP_OUTLIERFREE} -a ${conf_SETTING} != "OW_BG" ]; then
		printf "No available data for generating FG and/or CW features!"
		exit 1
	fi
	
	if [ ${conf_SETTING} == "OW_BG" ]; then
		mkdir -p ${dir_FETCHES}features-BG/
		GENERATE_FEATURE_OUTPUT="$(${dir_FETCH_SCRIPTS}generate-feature.py -in ${dir_TEMP_MERGED} -out ${dir_FETCHES}features-BG/ -instances "1" -setting "OW_BG" -force "YES")"
	fi

	if [ ${conf_SETTING} == "OW_FG" -o ${conf_SETTING} == "CW" ]; then
		GENERATE_FEATURE_OUTPUT="$(${dir_FETCH_SCRIPTS}generate-feature.py -in ${dir_TEMP_OUTLIERFREE} -force "NO")"
	fi

	GENERATE_FEATURE=(${GENERATE_FEATURE_OUTPUT// / }) 
	for (( i=0; i<${#GENERATE_FEATURE[@]}; i++ )); do
		if [[ ${GENERATE_FEATURE[$i]} == *"WARN"* ]]; then
			echo "${GENERATE_FEATURE[$i]} ${GENERATE_FEATURE[$i+1]} ${GENERATE_FEATURE[$i+2]} ${GENERATE_FEATURE[$i+3]}" >> ${dir_FETCHES}generate-feature.log
		fi
	done
	echo '----------' >> ${dir_FETCHES}generate-feature.log

	if [ ${conf_DO_BACKUP} == "Yes" ]; then
		rm -rf ${dir_TEMP_COMPILED}
		mkdir -p ${dir_TEMP}${url}/
		mv ${dir_TEMP}merged ${dir_TEMP}${url}/
		if [ ${conf_SETTING} == "OW_FG" -o ${conf_SETTING} == "CW" ]; then
			mv ${dir_TEMP}outlierfree ${dir_TEMP}${url}/
		fi
		cp ${dir_FETCHES}generate-feature.log ${dir_TEMP}${url}
		mv ${dir_FETCHES}TxtdumpErrors.txt ${dir_TEMP}${url}
	else
		rm -rf ${dir_TEMP}
	fi

	if [ ${conf_SETTING} == "OW_BG" ]; then
		mv ${dir_FETCHES}features-BG ${dir_STORAGE}
		# TODO: The same here as well!!!
	else
		if [ -d ${dir_STORAGE}features/ ]; then
			for d in `ls ${dir_FETCH_FEATURES} | xargs -n 1 basename`; do
				if [ -d ${dir_STORAGE}features/${d} ]; then
					mv ${dir_FETCH_FEATURES}${d}/* ${dir_STORAGE}features/${d}
				else
					mv ${dir_FETCH_FEATURES}${d} ${dir_STORAGE}features/
				fi
			done
		else
			mv ${dir_FETCH_FEATURES} ${dir_STORAGE}
		fi
	fi
	
	mv ${dir_FETCHES}generate-feature.log ${dir_STORAGE}
done
