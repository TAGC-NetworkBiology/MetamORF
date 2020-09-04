# -*- coding: utf-8 -*-

import os


# This file defines the path to the output folder to use by default
OUTPUT_FOLDER = os.path.join( '/', 'output' )


# NB: This line can be eventually be changed prior to execute the program 
#     using the following sed command:
# sed -i "7s/.*/OUTPUT_FOLDER = os.path.join( '\/', 'path', 'to', 'output', 'folder' )/" \
#            path/to/src/fr/tagc/uorf/core/util/DefaultOutputFolder.py
