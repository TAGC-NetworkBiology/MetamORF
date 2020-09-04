# -*- coding: utf-8 -*-

import os
import pandas as pd
import subprocess
import glob
from operator import attrgetter


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## GenerateStatFilesStrategy
#  =========================
#
# This class is a strategy aiming to generate a set of files useful
# to perform a statistical description of the database.
#
class GenerateStatFilesStrategy( object ):
                
    ## Class variables
    #  ---------------
    #
    # Name of files expected to be generated by the strategy
    LOG_LEVEL_COUNTS_FILENAME = 'log_level_counts'
    LOG_CODE_COUNTS_FILENAME = 'log_code_counts'
    
    
    
    ## Constructor of GenerateStatFilesStrategy
    #  ----------------------------------------
    #
    # Instance variables:
    #     - force_overwrite: Boolean - Should any existing stat file be overwritten?
    #     - output_folder: String - The name of the folder where to store the generated files.
    #
    def __init__( self ):
        
        # Check if the forceOverwrite option has been selected
        # (i.e. if existing files need to be replaced by new ones)
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
            self.force_overwrite = True
        else:
            self.force_overwrite = False
        
        # Get the output folder
        self.output_folder = OptionManager.get_instance().get_option( OptionConstants.OPTION_OUTPUT_FOLDER, 
                                                                      not_none = False )
        # By default, save the file in a stat folder
        if ( not self.output_folder ):
            self.output_folder = Constants.STAT_FOLDER
    
        
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the following files:
    #     - A csv file containing the number of time each logging level has been 
    #       used in the log files.
    #     - A csv file containing the number of time each "log code" has been used 
    #       in the log files (cf. LogCode file for more information).
    # 
    def execute( self ):
        
        ## Compute the statistics for each existing 
        #  logging level
        #  --------------------------------------------
        file_exists = os.path.exists( os.path.join( self.output_folder, 
                                                    self.LOG_LEVEL_COUNTS_FILENAME + '.csv' ) )
        if ( self.force_overwrite or not file_exists ):
            
            Logger.get_instance().info( 'Starting to build the logging level stat file.' )
            
            # For each logging level, count the number of time it has been 
            # registered in the log files
            logging_level_counts = {}
            
            for level in Constants.LOG_MODES.keys():
                
                lvl = level.upper()
                cat_logs = subprocess.Popen( [ 'cat' ] + glob.glob( Constants.PATH_LOG + '*' ), 
                                             stdout = subprocess.PIPE, 
                                             stderr = subprocess.PIPE )
                
                grep_level = subprocess.Popen( ['grep', lvl ],
                                              stdin = cat_logs.stdout,
                                              stdout = subprocess.PIPE, 
                                              stderr = subprocess.PIPE )
                
                count_lines = subprocess.Popen( ['wc', '-l' ],
                                                stdin = grep_level.stdout,
                                                stdout = subprocess.PIPE,
                                                stderr = subprocess.PIPE )
                
                ( stdout, stderr ) = count_lines.communicate()
                
                if stderr:
                    Logger.get_instance().error( 'An error occurred trying to get the number of "' + lvl +
                                                 '" lines in the log files: \n' + stderr +
                                                 ' Error code: ' + LogCodes.ERR_SUBPROC_BASH_GREP + '.',
                                                 ex = False )
                elif stdout:
                    logging_level_counts[ lvl ] = int( stdout )
                else:
                    Logger.get_instance().error( 'The command allowing to get the number of "' + lvl +
                                                 '" lines in the log files returned nothing.' +
                                                 ' Error code: ' + LogCodes.ERR_SUBPROC_BASH_EMPTY + '.',
                                                 ex = False )
            
            # Seve the dictionary into a csv file
            FileHandlerUtil.dict_to_csv( output_folder = self.output_folder, 
                                         filename = self.LOG_LEVEL_COUNTS_FILENAME, 
                                         dict = logging_level_counts, 
                                         file_desc = 'Count of occurrence of each level in the log files', 
                                         sort = False,
                                         hdr = [ 'level', 'count' ] )        
        
        ## Compute the statistics for each existing 
        #  warning and error log code
        #  --------------------------------------------
        file_exists = os.path.exists( os.path.join( self.output_folder, 
                                                    self.LOG_CODE_COUNTS_FILENAME + '.csv' ) )
        if ( self.force_overwrite or not file_exists ):
            
            Logger.get_instance().info( 'Starting to build the verbose level stat file.' )
            
            # For each log code that may be registered, count the number 
            # of time it has been registered in the log files
            logcode_counts = {}
                        
            # Get all the log codes that may be registered in log files
            logcodes = [ c for c in dir( LogCodes) if ( not c.startswith( '_' ) ) ]
            
            for code in logcodes:
                
                c = eval( 'LogCodes.' + code )
                
                cat_logs = subprocess.Popen( [ 'cat' ] + glob.glob( Constants.PATH_LOG + '*' ), 
                                             stdout = subprocess.PIPE,
                                             stderr = subprocess.PIPE )
                
                grep_code = subprocess.Popen( ['grep', c ],
                                              stdin = cat_logs.stdout,
                                              stdout = subprocess.PIPE,
                                              stderr = subprocess.PIPE )
                
                if c.startswith( LogCodes.WARN_PREFIX ):
                    grep_code2 = subprocess.Popen( ['grep', 'Warning code:' ],
                                                   stdin = grep_code.stdout,
                                                   stdout = subprocess.PIPE,
                                                   stderr = subprocess.PIPE )
                elif c.startswith( LogCodes.ERR_PREFIX ):
                    grep_code2 = subprocess.Popen( ['grep', 'Error code:' ],
                                                   stdin = cat_logs.stdout,
                                                   stdout = subprocess.PIPE,
                                                   stderr = subprocess.PIPE )
                else:
                    raise DenCellORFException( 'GenerateStatFilesStrategy.execute(): The LogCode "' + c + 
                                               '" does not start with an expected prefix.' +
                                               ' Please contact the developer if you see this message.' )
                
                count_lines = subprocess.Popen( ['wc', '-l' ],
                                                stdin = grep_code2.stdout,
                                                stdout = subprocess.PIPE,
                                                stderr = subprocess.PIPE )
                
                ( stdout, stderr ) = count_lines.communicate()
                
                if stderr:
                    Logger.get_instance().error( 'An error occurred trying to get the number of lines with' +
                                                 ' log code "' + c + '" in the log files: \n' + stderr +
                                                 ' Error code: ' + LogCodes.ERR_SUBPROC_BASH_GREP + '.',
                                                 ex = False )
                elif stdout:
                    logcode_counts[ c ] = int( stdout )
                else:
                    Logger.get_instance().error( 'The command allowing to get the number of lines with' +
                                                 ' log code "' + c + '" in the log files returned nothing.' +
                                                 ' Error code: ' + LogCodes.ERR_SUBPROC_BASH_EMPTY + '.',
                                                 ex = False )
            
            # Save the dictionary into a csv file
            FileHandlerUtil.dict_to_csv( output_folder = self.output_folder, 
                                         filename = self.LOG_CODE_COUNTS_FILENAME, 
                                         dict = logcode_counts,
                                         file_desc = ( 'Count of occurrence of each error /' +
                                                       ' warning code in the log files' ), 
                                         sort = True,
                                         hdr = [ 'code', 'count' ] )
            
        # Generation of statistic files is now implemented in a R package
        Logger.get_instance().info( 'Generation of statistics files from the Python interface' +
                                    ' is deprecated. Please use the "RqueryORF" package of R to' +
                                    ' generate these files.' )
            