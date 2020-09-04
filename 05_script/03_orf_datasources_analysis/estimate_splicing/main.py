# -*- coding: utf-8 -*-

import os
from fractions import Fraction


import constants
import DefaultInputFolder
import DefaultOutputFolder
import LogFileHandler
from spl_Fields2015 import Fields2015
from spl_Johnstone2016 import Johnstone2016
from spl_Laumont2016 import Laumont2016
from spl_Mackowiak2015 import Mackowiak2015
from spl_McGillivray2018 import McGillivray2018
from spl_Samandi2017 import Samandi2017
from spl_smPROT import smPROT
from spl_TISdb import TISdb

# Define path to input and output folders
INPUT_FOLDER = DefaultInputFolder.INPUT_FOLDER
OUTPUT_FOLDER = DefaultOutputFolder.OUTPUT_FOLDER


for sp in [ 'HUMAN', 'MOUSE' ]:
    
    log_filename = 'estimate_splicing_' + sp.lower()
    
    # Create a new log file for the species
    LogFileHandler.init_log_file( output_folder = OUTPUT_FOLDER,
                                  filename = log_filename ) 
    
    # Add the headers to the file
    headers = ( 'Total count of ORFs processed\t' + 
                'Computed length (nt) = Provided length (nt)\t' + 
                'Absolute difference below ' + str( constants.DIFF_MAX ) + ' nt\t' +
                'Computed length below ' + str( constants.MAX_LEN ) + ' nt' )
    LogFileHandler.add_to_log_file( message = headers,
                                    output_folder = OUTPUT_FOLDER,
                                    filename = log_filename ) 
    
    # Add a new line with information about the dataset processed
    LogFileHandler.add_to_log_file( message = ( '---\n' + 'Estimation of splicing for the ORF' +
                                                ' datasets related to ' + sp + '.' ),
                                    output_folder = OUTPUT_FOLDER,
                                    filename = log_filename )
    
    
    for ( dataset, datapath ) in eval( 'constants.FILEPATHS_' + sp + '.items()' ):
        
        # Get the path to the data source
        absolute_path = os.path.join( INPUT_FOLDER, datapath )
        
        # Execute the function
        (total_count, equal_len_count, equal_approx, below_max_nt) = eval( dataset + '( data_path ="' + absolute_path + '" )' )
        
        # Log the counts and proportions of ORFs
        if ( equal_len_count != 'NA' ):
            
            equal_len_count_fraction = round( float( Fraction( equal_len_count, total_count ) ) , 3 ) * 100
            equal_approx_fraction = round( float( Fraction( equal_approx, total_count ) ) , 3 ) * 100 
            below_max_nt_fraction = round( float( Fraction( below_max_nt, total_count ) ) , 3 ) * 100
            
            message = ( str( total_count ) + '\t' + 
                        str( equal_len_count_fraction ) + '(' + str( equal_len_count ) + ')\t' + 
                        str( equal_approx_fraction ) + '(' + str( equal_approx ) + ')\t' +
                        str( below_max_nt_fraction ) + '(' + str( below_max_nt ) + ')' )
            
            LogFileHandler.add_to_log_file( message = message,
                                            output_folder = OUTPUT_FOLDER,
                                            filename = log_filename )
            
        else:
            below_max_nt_fraction = round( float( Fraction( below_max_nt, total_count ) ) , 3 ) * 100
            
            message = ( str( total_count ) + '\t' + 
                        'ORF length not provided\t' + 
                        'ORF length not provided\t' + 
                        str( below_max_nt_fraction ) + '(' + str( below_max_nt ) + ')' )
            
            LogFileHandler.add_to_log_file( message = message,
                                            output_folder = OUTPUT_FOLDER,
                                            filename = log_filename )
    