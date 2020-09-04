#!/bin/bash

# This script allows to run the AssessDatabaseContent strategy.

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

# AssessDatabaseContent
echo "AssessDatabaseContent strategy" >> ${README_FILE_PATH}
echo "- Started on $(date "+%d/%m/%y, at %H:%M:%S")" >> ${README_FILE_PATH}
echo "  python $PYTHONPATH/fr/tagc/uorf/uorf.py AssessDatabaseContent -v $VERBOSITY_LEVEL -T $DB_TYPE -H $DB_HOST -P $DB_PORT -u $DB_USER -p $DB_PASSWORD -N $DS_DB_NAME -M DS" >> ${README_FILE_PATH}
echo "" >> ${README_FILE_PATH}
python $PYTHONPATH/fr/tagc/uorf/uorf.py AssessDatabaseContent -v $VERBOSITY_LEVEL -T $DB_TYPE \
  -H $DB_HOST -P $DB_PORT -u $DB_USER -p $DB_PASSWORD -N $DS_DB_NAME -M DS
