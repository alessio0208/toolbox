#
# Script for merging the input data into single files per url (output folders)
#
# bash merge-input.sh [options]

exit_with_help() {

   echo "Usage: merge-input.sh [options]

options:
   -in { /Path/ } : Path to Compiled Fetches (with Fetches as Sub-Dirs)
   -out { /Path/ } : Path to Merged Instances (with Formats as Sub-Dirs)
   -setting { CW | OW_BG | OW_FG } : Evaluated Scenario 
                                     (Incluences Merging Behavior)

${1}"
   exit
}


# Read configuration from "WFP_config"
INPUT=${dir_TEMP_COMPILED}
OUTPUT=${dir_TEMP_MERGED}

SETTING=${conf_SETTING}

while [[ $# > 0 ]]
do
key="$1"

case $key in
    -in)
    INPUT="$2"
    shift # past argument
    ;;
    -out)
    OUTPUT="$2"
    shift # past argument
    ;;
    -setting)
    SETTING="$2"
    shift # past argument
    ;;
    *)
    exit_with_help "Error: Unknown Argument! (${1})" # unknown option
    ;;
esac
shift # past argument or value
done

# Check set variables
if [ ! -d "$INPUT" ]; then
    exit_with_help "Error: Invalid Input Path!"
fi
settings=( "CW" "OW_FG" "OW_BG")
if [[ ! " ${settings[*]} " == *" ${SETTING} "* ]]; then
    exit_with_help "Error: Unknown Setting!"
fi

# Additional checks
# Check if there are traces
if ([ ! "$(ls -A ${INPUT})" ] || [ ! -d "${INPUT}" ]); then
    echo "Error: ${INPUT} is empty?!"
    exit
fi

# Define all available formats
formats=( "tcp" "tls" "tls-legacy" "tls-nosendme" 
"cell" "cell-nosendme" "cell-legacy" "cell-nosendme-legacy" )

# Clean up output
if [ -d "$OUTPUT" ]; then
    rm -rf ${OUTPUT}
fi
mkdir -p ${OUTPUT}

# Create Sub-Directories for each Format
for format in ${formats[@]}; do
    mkdir -p ${OUTPUT}output-${format}
done


count=1
# Only iterate through folders for the outer loops
max=$(ls -d ${INPUT}*/ | wc -l)
for d in `ls -d ${INPUT}*/ | xargs -n 1 basename`; do
    echo "(${count}/${max}) ${d}"
    for format in ${formats[@]}; do
        if [ ! -d "${INPUT}${d}/output-${format}" ]; then
            continue
        fi
        for f in `ls ${INPUT}${d}/output-${format}`; do
            if [ "${f}" == "check.torproject.org" ]; then
                continue
            fi
            
            if [[ ${SETTING} == "OW_BG" ]]; then
                cat ${INPUT}${d}/output-${format}/${f} >> ${OUTPUT}output-${format}/${f}
            else
                # This is really dangerous!!! Different pages can become a single one...
                # Now, we store the whole URL (and not the first 100 symbols as we did)
                # and hopefully the concern above will not happen.
                fn=${f%___-___*}
                cat ${INPUT}${d}/output-${format}/${f} >> ${OUTPUT}output-${format}/${fn}
            fi
        done
    done
    count=$[$count+1]
done

# Clean up output directories (remove non-existing formats)
# Check if every format exists
for format in ${formats[@]}; do
    if [ ! "$(ls -A ${OUTPUT}output-${format})" ]; then
        rmdir ${OUTPUT}output-${format}
    fi
done
