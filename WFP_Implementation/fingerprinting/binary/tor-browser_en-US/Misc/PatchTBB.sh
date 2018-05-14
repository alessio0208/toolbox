#!/bin/bash

# Check if WFP_config is set
if [ -z "${dir_BIN_TBB}" ]; then
	echo "Properly load your WFP_config!"
	echo "Or set \"dir_BIN_TBB\" manually."
	exit
fi

TBB_DIR="${dir_BIN_TBB}"
TBB_START="${TBB_DIR}Browser/start-tor-browser"

PROFILE_DIR="${TBB_DIR}Browser/TorBrowser/Data/Browser/profile.default/"
PROFILE="${PROFILE_DIR}prefs.js"

# correlated to patches
names=( 
# "network.http.use-cache" # This option does not exist anymore.
"browser.cache.disk.smart_size.enabled"
"browser.cache.memory.enable"
"dom.caches.enabled"
"app.update.enabled" 
"browser.search.update" 
# "extensions.torbutton.no_updates" # This option does not exist anymore.
"extensions.torbutton.launch_warning" 
# "extensions.torbutton.saved.app_update" # This option does not exist anymore.
# "extensions.torbutton.saved.auto_update" # This option does not exist anymore.
# "extensions.torbutton.saved.extension_update" # This option does not exist anymore.
# "extensions.torbutton.saved.search_update" # This option does not exist anymore.
"extensions.torbutton.versioncheck_enabled" 
"extensions.update.autoUpdateDefault" 
"extensions.update.enabled" 
"lightweightThemes.update.enabled" 
"extensions.blocklist.enabled"
"extensions.torbutton.lastUpdateCheck" )

# correlated to names
patches=(
# "user_pref(\"network.http.use-cache\", false);"
"user_pref(\"browser.cache.disk.smart_size.enabled\", false);"
"user_pref(\"browser.cache.memory.enable\", false);"
"user_pref(\"dom.caches.enabled\", false);"
"user_pref(\"app.update.enabled\", false);" 
"user_pref(\"browser.search.update\", false);" 
# "user_pref(\"extensions.torbutton.no_updates\", true);" 
"user_pref(\"extensions.torbutton.launch_warning\", false);" 
# "user_pref(\"extensions.torbutton.saved.app_update\", false);" 
# "user_pref(\"extensions.torbutton.saved.auto_update\", false);" 
# "user_pref(\"extensions.torbutton.saved.extension_update\", false);" 
# "user_pref(\"extensions.torbutton.saved.search_update\", false);" 
"user_pref(\"extensions.torbutton.versioncheck_enabled\", false);" 
"user_pref(\"extensions.update.autoUpdateDefault\", false);" 
"user_pref(\"extensions.update.enabled\", false);" 
"user_pref(\"lightweightThemes.update.enabled\", false);" 
"user_pref(\"extensions.blocklist.enabled\", false);"
"user_pref(\"extensions.torbutton.lastUpdateCheck\", \"0\");" )

remove=( "dom.max_chrome_script_run_time" )

# Check & Update user config
# TODO: User configs can be updated via tor browser selenium! (I think update via tor browser selenium would be the better solution!) 
i=0
for line in ${names[@]}; do
	new="${patches[$i]}"
	if grep -q "$line" "${PROFILE}"
		then
			sed -i '/'"$line"'/c\'"${new}"'' "${PROFILE}"
		else
			echo "${new}" >> "${PROFILE}"
	fi
	i=`expr $i + 1`
done

# Remove unwanted items from user config
for line in ${remove[@]}; do
	sed -i '/'"$line"'/d' "${PROFILE}"
done

### We do not need that any more
# Patch start script if we are running on 64 bit
#if [ 64 -eq $(getconf LONG_BIT) ]; then
#	sed -i 's/^SYSARCHITECTURE=.*/SYSARCHITECTURE=32/g' "${TBB_START}"
#fi

# Patch file download (unknownContentType.xul in omni.ja)
zip -u "${TBB_DIR}Browser/omni.ja" ./chrome/toolkit/content/mozapps/downloads/unknownContentType.xul 
