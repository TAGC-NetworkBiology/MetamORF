# -*- coding: utf-8 -*-

import os


## init_log_file
#  -------------
#
# This method allows to erase any existing log file at the 
# provided path and to create a new one.
#
# @param output_folder: String - The path to the folder where to write the file.
# @param filename: String - The name of the file (without its extension). 
# @param ext: String - The extension of the file. ".log" by default.
# 
def init_log_file( output_folder=output_folder, filename=filename, ext='.log' ):

    # Create the output folder if it does not yet exist
    # (and its parent folders if necessary)
    if ( not os.path.isdir( output_folder ) ):
        os.makedirs( output_folder )
    
    file_path = os.path.join( output_folder, filename + ext )
        
    file = open( file_path, mode = 'w' )
    file.close()


## add_to_log_file
#  ---------------
#
# This method allows to add a line to the log file.
#
# @param message: String - The message to add in the log file.
# @param output_folder: String - The path to the folder where to write the file.
# @param filename: String - The name of the file (without its extension). 
# @param ext: String - The extension of the file. ".log" by default.
# 
def add_to_log_file( self, message, output_folder=output_folder, filename=filename, ext='.log' ):
    
    file_path = os.path.join( output_folder, filename + ext )
    
    file = open( file_path, mode = 'a' )
    file.write( message + '\n' )
    file.close()
    