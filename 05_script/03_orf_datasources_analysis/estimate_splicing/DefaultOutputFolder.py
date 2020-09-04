# -*- coding: utf-8 -*-

import os


# This file defines the path to the output folder to use by default
OUTPUT_FOLDER = os.path.join( '/', 'data', '08_output', '03_orf_datasources_analysis' )


# NB: This line can be eventually be changed prior to execute the program 
#     using the following sed command:
# sed -i "7s/.*/OUTPUT_FOLDER = os.path.join( '\/', 'path', 'to', 'output', 'folder' )/" \
#            path/to/05_script/03_orf_datasources_analysis/estimate_splicing/DefaultOutputFolder.py
