#!/bin/bash

# This script allows to run all the strategies necessary to 
# build the DS and PRO databases.

# Expected arguments:
# --config or --configpath
# --dsdbname
# --prodbname
# --dbhost
# --dbport
# --dbuser
# --dbpassword

# =========================================================
# Parse the command line and define environment variables
# =========================================================

# See the documentation of the declare_variables.sh file
# for more information about allowed options
source ./03_workflow/datafreeze/declare_variables.sh $@



# =========================================================
# Start DenCellORF
# =========================================================

## Build the DS database

# DatabaseCheck
echo "DatabaseCheck strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py DatabaseCheck -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py DatabaseCheck -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH

# Insertion
echo "Insertion strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py Insertion -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py Insertion -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH

# LiftOver
echo "LiftOver strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py LiftOver -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py LiftOver -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH


## Build the PRO database

# Merge
echo "Merge strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py Merge -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py Merge -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s

# ComputeMissingInfo
echo "ComputeMissingInfo strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeMissingInfo -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -d" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeMissingInfo -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -d

# ComputeRelCoord
echo "ComputeRelCoord strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeRelCoord -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeRelCoord -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH

# ComputeKozakContext
echo "DatabaseCheck strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeKozakContext -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py ComputeKozakContext -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH

# AnnotateORF
echo "AnnotateORF strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py AnnotateORF -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s -a" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py AnnotateORF -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s -a
