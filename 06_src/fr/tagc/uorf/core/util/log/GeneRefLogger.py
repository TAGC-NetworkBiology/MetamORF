# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger


## GeneRefLogger
#  =============
#
# This class is a singleton which allows to log warnings relative to the gene 
# cross references (gene IDs / symbol / aliases...) anywhere in the program.
#
# /!\ There is one single logging level for this logger: WARNING.
# NB: Logs created with this logger are not displayed on the console.
#
class GeneRefLogger( object ):

    __instance = None


    ## Constructor of GeneRefLogger
    #  ----------------------------
    #
    # Instance variable:
    #     - logg: GeneRefLogger - A logging object allowing to log.
    #
    # @param log_path: String - The path to the log file.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #                               Constants.GENEREF_LOG_DEFAULT by default.
    #
    def __init__( self, log_path=Constants.PATH_GENEREF_LOG, writing_mode=Constants.GENEREF_LOG_DEFAULT ):
        
        self.logg = GeneRefLogger.set_logger( log_path, writing_mode )
        
        # Log the instantiation of this logger in the main logger
        Logger.get_instance().warning( 'A warning related to gene references has been raised' +
                                       ' during the execution of the program. All warnings related' +
                                       ' to the gene references will be logged in the file "' + 
                                       str( log_path ) + '". Please see the documentation for' +
                                       ' more information.' )


    ## set_logger
    #  ---------
    #
    # This is a static method that allows to set the options of the logger.
    #
    # @param log_path: String - The path to the log file.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #
    # @return logger - The logger instance.
    #
    @staticmethod
    def set_logger( log_path, writing_mode ):
                
        # Reinitialize log file
        ERROR_FILE = open( log_path, writing_mode )
        ERROR_FILE.write( '-----------------------------------\n' )
        ERROR_FILE.close()
        
        # Logger object which is used to write in log
        logger = logging.getLogger( 'generef_logger' )
        
        # Set level to mode        
        logger.setLevel( logging.INFO )
        
        # Create formatter which will add time and log level for each message
        # when a message will be written
        formatter = logging.Formatter( '%(asctime)s :: %(message)s' )
        
        # Create the handler which will redirect the message to the
        # log file, with append mode and maximum size (Default = 1 Mo)
        generef_file_handler = RotatingFileHandler( log_path, 
                                                    'a', 
                                                    Constants.GENEREF_LOG_SIZE_MAX, 
                                                    Constants.GENEREF_LOG_MAX_FILES_NB )
        # Set the level of the handler
        generef_file_handler.setLevel( logging.INFO )
        generef_file_handler.setFormatter( formatter )
        # Add this handler to the logger
        logger.addHandler( generef_file_handler )
        
        return logger


    ## get_instance
    #  ------------
    #
    # First time create an instance of GeneRefLogger, 
    # then return this instance.
    #
    # @param log_path: String - The path to the log file.
    #                           Constants.PATH_GENEREF_LOG by default.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #                               Constants.GENEREF_LOG_DEFAULT by default.
    #
    # @return the logger instance.
    #
    @staticmethod
    def get_instance( log_path=Constants.PATH_GENEREF_LOG, writing_mode=Constants.GENEREF_LOG_DEFAULT ):
        if ( GeneRefLogger.__instance == None ):
            GeneRefLogger.__instance = GeneRefLogger( log_path, writing_mode )
            
        return GeneRefLogger.__instance


    ## crossref_warning
    #  ----------------
    #
    # Log cross reference errors.
    # It adds the 'CROSSREF WARNING' prefix.
    #
    # @param message: String - The message to log.
    #
    def crossref_warning( self, message ):
        
        self.logg.warning( 'CROSSREF WARNING :: ' + message )


    ## gene_search
    #  -----------
    #
    # Log warnings raised during gene search.
    # It adds the 'GENE SEARCH' prefix.
    #
    # @param message: String - The message to log.
    #
    def gene_search_warning( self, message ):
        
        self.logg.warning( 'GENE SEARCH :: ' + message )


    ## gene_update
    #  -----------
    #
    # Log warnings raised during gene search.
    # It adds the 'GENE UPDATE' prefix.
    #
    # @param message: String - The message to log.
    #
    def gene_update_warning( self, message ):
        
        self.logg.warning( 'GENE UPDATE :: ' + message )


    ## missing_ref
    #  -----------
    #
    # Log missing reference errors.
    # It adds the 'MISSING REFERENCE' prefix.
    #
    # @param message: String - The message to log.
    #
    def missing_ref_warning( self, message ):
        self.logg.warning( 'MISSING REFERENCE :: ' + message )


    ## new_entry
    #  ---------
    #
    # Log Gene and GeneAlias newly created during execution of the program 
    # (in particular during data parsing and insertion).
    # It adds the 'NEW ENTRY' prefix.
    #
    # NB: All entries created during the insertion of the main cross references 
    #     (gene lists) are not logged here. 
    #
    # @param message: String - The message to log.
    #
    def new_entry_warning( self, message ):
        
        self.logg.warning( 'NEW ENTRY :: ' + message )


    ## conflict_info
    #  -------------
    #
    # Log warnings raised when conflicting information have been found.
    # It adds the 'CONFLICTING INFO' prefix.
    #
    # @param message: String - The message to log.
    #
    def conflict_info_warning( self, message ):
        
        self.logg.warning( 'CONFLICTING INFO :: ' + message )


    ## close
    #  -----
    #
    # Close all logging handlers.
    #
    def close( self ):
        
        handlers = self.logg.handlers[:]
        for handler in handlers:
            handler.close()
            self.logg.removeHandler( handler )
    