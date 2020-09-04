# -*- coding: utf-8 -*-

import os
from fr.tagc.uorf.core.util import DefaultOutputFolder


# This file defines the path to the temporary folder to use by default
TEMPORARY_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER, '.tmp' )


# NB: This line can be eventually be changed prior to execute the program 
#     using the following sed command:
# sed -i "8s/.*/TEMPORARY_FOLDER = os.path.join( '\/', 'path', 'to', 'temporary', 'folder' )/" \
#            path/to/src/fr/tagc/uorf/core/util/DefaultTemporaryFolder.py
