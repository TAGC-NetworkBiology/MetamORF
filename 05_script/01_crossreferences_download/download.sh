#!/bin/bash

# This script allows to download the cross-references (Gene lists)

# Define the output directory
source ./DefaultOutputFolder.txt

# Define the log
LOG_FILE=${OUTPUT_DIR}/crossreferences_download.log

echo '-----------------------------------' > $LOG_FILE

# If it does not yet exists, create a folder to store the cross-references
echo 'Cross-references and data will be stored in: ${OUTPUT_DIR}.' >> $LOG_FILE
if [ ! -d $OUTPUT_DIR ]
then
    mkdir -p $OUTPUT_DIR
fi


# NCBI Gene lists
# ---------------

echo 'Starting to download cross-references from NCBI.' >> $LOG_FILE

NCBI_DIR=$OUTPUT_DIR/NCBI
if [ ! -d $NCBI_DIR ]
then
    mkdir -p $NCBI_DIR
fi

# H. sapiens
curl -o $NCBI_DIR/hsapiens.gene_info.gz \
  -O ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz

# M. musculus
curl -o $NCBI_DIR/mmusculus.gene_info.gz \
  -O ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Mus_musculus.gene_info.gz

# Unzip all NCBI gene lists
gunzip $NCBI_DIR/*.gene_info.gz



# Ensembl Gene Lists
# ------------------

echo 'Starting to download cross-references from Ensembl.' >> $LOG_FILE

ENSEMBLE_DIR=$OUTPUT_DIR/Ensembl
if [ ! -d $ENSEMBLE_DIR ]
then
    mkdir -p $ENSEMBLE_DIR
fi

Rscript ./ensembl_gene_lists.R >> $LOG_FILE



# MGI Gene list
# -------------

echo 'Starting to download cross-references from MGI.' >> $LOG_FILE

MGI_DIR=$OUTPUT_DIR/MGI
if [ ! -d $MGI_DIR ]
then
    mkdir -p $MGI_DIR
fi

curl -o $MGI_DIR/mmusculus_MGI.rpt \
  -O http://www.informatics.jax.org/downloads/reports/MGI_Gene_Model_Coord.rpt
