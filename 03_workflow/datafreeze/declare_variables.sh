#!/bin/bash

# This script allows to set environment variables 
# necessary to run the source code.


# List of variables defined:
# - RUN_FOLDER_PATH: Absolute path to the run directory
# - RUN_FOLDER_BASENAME: Run basename (usually the prefix 'Run_' followed by the name of the run)
# - RUN_NAME: Name of the run (usually the date at format YYYY_MM_DD, eventually followed by the species name)
# - README_FILE_PATH: Absolute path to readme file of the run folder
# - VERBOSITY_LEVEL: Level of verbosity to use (debug by default, debug, info, warning, error, critical available)
# - DB_TYPE: Type of database (MySQL by default, could be changed for SQLite)
#
# - PYTHONPATH: Absolute path to the source code folder
# - TEMPORARY_FOLDER_PATH: Absolute path to the temporary folder (under /tmp by default)
# - PYENSEMBL_CACHE_DIR: Absolute path to the PyEnsembl temporary folder
# - TEMPORARY_DATAFREEZE_FOLDER_PATH: Absolute path to the temporary folder for the ORF datafreeze
#                                     (the same than TEMPORARY_FOLDER_PATH by default)
# - OUTPUT_FOLDER_PATH: Absolute path to the output folder
# - OUTPUT_DATAFREEZE_FOLDER_PATH: Absolute path to the ORF datafreeze output
#
# - CONFIGFILE_NAME: Name of the config file to use to run the program (Optional)
# - CONFIGFILE_PATH: Absolute path to the config file 

# - DS_DB_NAME: Name of the DS database (Optional variable)
# - PRO_DB_NAME: Name of the PRO database (Optional variable)
# - DB_HOST: IP of the host (for MySQL databases only, optional variable)
# - DB_PORT: Port to the host (for MySQL databases only, optional variable)
# - DB_USER: Database's user (for MySQL databases only, optional variable)
# - DB_PASSWORD: Database's user's password (for MySQL databases only, optional variable)


# =========================================================
# Parse the command line arguments
# =========================================================

# Allowed options
# - config: String - Name of the config file (has to be located in the 04_config folder of the run)
# - configpath: String - Absolute path to the config file. This option should be used if the
#                        config file is not located in the 04_config folder of the run
# - dbtype: String - Type of the database (MySQL / SQLite)
# - dsdbname: String - Name of the DS database
# - prodbname: String - Name of the PRO database
# - dbhost: String - IP of the host (for MySQL databases only)
# - dbport: Integer - Port of the host (for MySQL databases only)
# - dbuser: String - Database user (for MySQL databases only)
# - dbpassword: String - Database user's password (for MySQL databases only)
OPTIONS_LIST=(
  "config"
  "configpath"
  "verbosity"
  "dbtype"
  "dsdbname"
  "prodbname"
  "dbhost"
  "dbport"
  "dbuser"
  "dbpassword"
  )

# Parse the options
opts=$(getopt \
  --longoptions "$(printf "%s:," "${OPTIONS_LIST[@]}")" \
  --name "$(basename "$0")" \
  --options "" \
  -- "$@"
  )
eval set --$opts

while [[ $# -gt 0 ]]; do
  case "$1" in 
    --config)
        export CONFIGFILE_NAME=$2
        shift 2
        ;;
        
    --configpath)
        export CONFIGFILE_PATH=$2
        shift 2
        ;;
        
    --verbosity)
        export VERBOSITY_LEVEL=$2
        shift 2
        ;;
        
    --dbtype)
        export DB_TYPE=$2
        shift 2
        ;;
        
    --dsdbname)
        export DS_DB_NAME=$2
        shift 2
        ;;
        
    --prodbname)
        export PRO_DB_NAME=$2
        shift 2
        ;;
        
    --dbhost)
        export DB_HOST=$2
        shift 2
        ;;
        
    --dbport)
        export DB_PORT=$2
        shift 2
        ;;
        
    --dbuser)
        export DB_USER=$2
        shift 2
        ;;
        
    --dbpassword)
        export DB_PASSWORD=$2
        shift 2
        ;;
        
    *)
       break
       ;;
  esac
done



# =========================================================
# Constants
# =========================================================

# Run folder names
export CONFIG_FOLDER_NAME=04_config
export SRC_FOLDER_NAME=06_src
export OUTPUT_FOLDER_NAME=08_output

# Set default values
if [ -z $DB_TYPE ]
then
  export DB_TYPE=MySQL
fi

if [ -z $VERBOSITY_LEVEL ]
then 
  export VERBOSITY_LEVEL=debug
fi



# =========================================================
# Getting the working directory path and name
# =========================================================

# Get the run folder path and basename
export RUN_FOLDER_PATH=$(pwd)
export RUN_FOLDER_BASENAME=$(basename $(pwd))

# Extract the base name
case ${RUN_FOLDER_BASENAME:0:4} in
  Run_)
      export RUN_NAME=${RUN_FOLDER_BASENAME:4}
      ;;
  run_)
      export RUN_NAME=${RUN_FOLDER_BASENAME:4}
      ;;
  *)
      case ${RUN_FOLDER_BASENAME:0:3} in
          Run)
              export RUN_NAME=${RUN_FOLDER_BASENAME:3}
              ;;
          run)
              export RUN_NAME=${RUN_FOLDER_BASENAME:3}
              ;;
          *)
              export RUN_NAME=${RUN_FOLDER_BASENAME}
              ;;
      esac
esac

# Readme file
export README_FILE_PATH=${RUN_FOLDER_PATH}/readme.txt


# =========================================================
# Define variables
# =========================================================

echo "----------------"
echo "Run information:"
echo "- Run name: ${RUN_NAME}"
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")"
echo "- Run started by: ${USER}"
echo "- Run on: $(hostname)"
echo "- Path to run folder: ${RUN_FOLDER_PATH}"

## Define environment variables
echo ""
echo "Environment variables:"

# Path to source code
export PYTHONPATH=${RUN_FOLDER_PATH}/${SRC_FOLDER_NAME}
echo "- Python path (PYTHONPATH) set to: ${PYTHONPATH}"

# Path to the temporary folder (defined for the user)
export TEMPORARY_FOLDER_PATH=/tmp/${USER}/ORF_datafreeze/${RUN_NAME}
echo "- Path to the temporary folder: ${TEMPORARY_FOLDER_PATH}"

# Path to the temporary folder for PyEnsembl
export PYENSEMBL_CACHE_DIR=${TEMPORARY_FOLDER_PATH}/pyensembl
  # Create the temporary folder if it does not yet exist
if [ ! -d ${PYENSEMBL_CACHE_DIR} ]
then
    mkdir -p ${PYENSEMBL_CACHE_DIR}
fi
echo "- Path to the temporary folder used by PyEnsembl (PYENSEMBL_CACHE_DIR): ${PYENSEMBL_CACHE_DIR}"


## Define default output and temporary folders
echo ""
echo "Output and temporary directories:"

## Make sure the output folder exist and set the default output
## folder in the source code
export OUTPUT_FOLDER_PATH=${RUN_FOLDER_PATH}/${OUTPUT_FOLDER_NAME}
export OUTPUT_DATAFREEZE_FOLDER_PATH=${OUTPUT_FOLDER_PATH}/datafreeze
if [ ! -d ${OUTPUT_FOLDER_PATH} ]
then
    mkdir -p ${OUTPUT_FOLDER_PATH}
fi
if [ ! -d ${OUTPUT_DATAFREEZE_FOLDER_PATH} ]
then
    mkdir -p ${OUTPUT_DATAFREEZE_FOLDER_PATH}
fi
echo "- Path to the output folder: ${OUTPUT_FOLDER_PATH}"

# Set the output directory defined by default in the source code
sed -i "7s&.*&OUTPUT_FOLDER = '${OUTPUT_DATAFREEZE_FOLDER_PATH}'&" \
	${PYTHONPATH}/fr/tagc/uorf/core/util/DefaultOutputFolder.py


## Set the default temporary folder in the source code
# NB: The following line may be removed. In such case, 
#     the program will create the temporary file in the
#     $OUTPUT_FOLDER folder if necessary
# Change the temporary directory defined by default in the source code
export TEMPORARY_DATAFREEZE_FOLDER_PATH=${TEMPORARY_FOLDER_PATH}

sed -i "8s&.*&TEMPORARY_FOLDER = '${TEMPORARY_DATAFREEZE_FOLDER_PATH}'&" \
	${PYTHONPATH}/fr/tagc/uorf/core/util/DefaultTemporaryFolder.py
	
echo "- Path to the temporary folder: ${TEMPORARY_DATAFREEZE_FOLDER_PATH}"


## Config file

# Get the path of the config file
if [ ! -z ${CONFIGFILE_NAME} ]
then
  ## Path to the config file (if not already defined)
  if [ -z ${CONFIGFILE_PATH} ]
  then
    export CONFIGFILE_PATH=${RUN_FOLDER_PATH}/${CONFIG_FOLDER_NAME}/${CONFIGFILE_NAME}
  fi

  # Replace any eventual "Run_DATE" or "Run_RUN" occurence in 
  # the config file by Run_${RUN}
  sed -i "s/Run_DATE/${RUN_FOLDER_BASENAME}/" ${CONFIGFILE_PATH}
  sed -i "s/Run_RUN/${RUN_FOLDER_BASENAME}/" ${CONFIGFILE_PATH}
fi

echo ""
echo "Path to the config file: ${CONFIGFILE_PATH}"

echo "----------------"
echo ""
