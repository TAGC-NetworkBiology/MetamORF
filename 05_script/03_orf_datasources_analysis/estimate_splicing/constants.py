# -*- coding: utf-8 -*-

import os


# Number of rows to treat
DEFAULT_NB_ROWS = 2000000
NB_ROWS = DEFAULT_NB_ROWS

# Threshold for the maximal difference between computed length and reported length
DEFAULT_DIFF_MAX = 6
DIFF_MAX = DEFAULT_DIFF_MAX

# Threshold for the maximal ORF length
DEFAULT_MAX_LEN = 300
MAX_LEN = MAX_LEN

# Path to files
ORF_FOLDER = os.path.join( '/', 'input_data', 'ORF_data' )

FILEPATHS_HUMAN = {
                'Mackowiak2015' : 'hsapiens_Mackowiak2015.txt',
                'McGillivray2018' : 'hsapiens_McGillivray2018.preprocessed.tsv',
                'Laumont2016' : 'hsapiens_Laumont2016.csv',
                'Johnstone2016' : 'hsapiens_Johnstone2016.txt',
                'Samandi2017' : 'hsapiens_altprot_Samandi2017.tsv',
                'smPROT' : 'hsapiens_smPROT.csv',
                'TISdb' : 'hsapiens_TISdb.csv'
            }

FILEPATHS_MOUSE = {
                'Mackowiak2015' : 'mmusculus_Mackowiak2015.txt',
                'Fields2015' : 'mmusculus_Fields2015.csv',
                'Johnstone2016' : 'mmusculus_Johnstone2016.txt',
                'Samandi2017' : 'mmusculus_altprot_Samandi2017.tsv',
                'smPROT' : 'mmusculus_smPROT.csv',
                'TISdb' : 'mmusculus_TISdb.csv'
            }
