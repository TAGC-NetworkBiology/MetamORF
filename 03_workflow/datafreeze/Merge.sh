#!/bin/bash

# This script allows to run the Merge strategy.

# Expected arguments:
# --config or --configpath

# =========================================================
# Parse the command line and define environment variables
# =========================================================

# See the documentation of the declare_variables.sh file
# for more information about allowed options
source ./03_workflow/datafreeze/declare_variables.sh $@



# =========================================================
# Start DenCellORF
# =========================================================

# Merge
echo "Merge strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py Merge -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py Merge -v $VERBOSITY_LEVEL -T $DB_TYPE -c $CONFIGFILE_PATH -s
