# -*- coding: utf-8 -*-

import os


# This file defines the path to the input folder to use by default
INPUT_FOLDER = os.path.join( '/', 'data', '07_input', 'ORF_datasource' )


# NB: This line can be eventually be changed prior to execute the program 
#     using the following sed command:
# sed -i "7s/.*/INPUT_FOLDER = os.path.join( '\/', 'path', 'to', 'input', 'folder' )/" \
#            path/to/05_script/03_orf_datasources_analysis/estimate_splicing/DefaultInputFolder.py
