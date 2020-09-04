# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException


## Logger
#  ======
#
# This class is a singleton which allows to log messages anywhere in the program.
#
# There are different logging's levels:
#    - DEBUG: show all possible log. This includes information useful to the developer.
#    - INFO: show info to user but no developer info.
#    - WARNING: show messages about something which can alter the processing.
#    - ERROR: an error happened during the execution of the program but did not stop the program.
#    - CRITICAL: an error occurred and stopped the program.
# Please see the documentation for extensive information about the log levels.
# ERROR and CRITICAL level log also the stacktrace.
# By default, the logging mode is set to INFO.
#
class Logger( object ):

    __instance = None


    ## Constructor of Logger
    #  ---------------------
    #
    # Instance variable:
    #     - logg: Logger - A logging object allowing to log.
    #     - mode: String - The logging's level.
    #
    # @param log_path: String - The path to the log file.
    # @param mode: String - The logging's level.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #                               Constants.LOG_DEFAULT by default.
    #
    def __init__( self, log_path=Constants.PATH_LOG, mode=Constants.MODE_INFO, writing_mode=Constants.LOG_DEFAULT ):
        
        self.logg = Logger.set_logger( log_path, mode, writing_mode )
        self.mode = mode


    ## set_logger
    #  ---------
    #
    # This is a static method that allows to set the options of the logger.
    #
    # @param log_path: String - The path to the log file.
    # @param mode: String - The logging's level.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #
    # @return logger - The logger instance.
    #
    @staticmethod
    def set_logger( log_path, mode, writing_mode ):

        # Reinitialize log file
        ERROR_FILE = open( log_path, writing_mode )
        ERROR_FILE.write( '-----------------------------------\n' )
        ERROR_FILE.close()

        # Logger object which is used to write in log
        logger = logging.getLogger( 'main_logger' )
        
        # Set level to mode
        logger.setLevel( mode )

        # Create formatter which will add time and log level for each message
        # when a message will be written
        formatter = logging.Formatter \
        ('%(asctime)s :: %(levelname)s :: %(message)s')

        # Create the handler which will redirect the message to the
        # log file, with append mode and maximum size (Default = 1 Mo)
        file_handler = RotatingFileHandler( log_path, 
                                            'a', 
                                            Constants.LOG_SIZE_MAX, 
                                            Constants.LOG_MAX_FILES_NB )
        # Set the level of the handler
        file_handler.setLevel( mode )
        file_handler.setFormatter( formatter )
        # Add this handler to the logger
        logger.addHandler( file_handler )

        # Set a second handler to print the messages logged on the console
        steam_handler = logging.StreamHandler()
        steam_handler.setLevel( mode )
        # Add this handler to the logger
        logger.addHandler( steam_handler )

        return logger


    ## get_instance
    #  ------------
    #
    # First time create an instance of Logger, 
    # then return this instance.
    #
    # @param log_path: String - The path to the log file.
    # @param logging_mode: Logging - The logging's level.
    # @param writing_mode: String - The writing mode (overwrite file or append).
    #                               Constants.LOG_DEFAULT by default.
    #
    # @return the logger instance.
    #
    @staticmethod
    def get_instance( log_path=Constants.PATH_LOG, logging_mode=Constants.MODE_INFO, writing_mode=Constants.LOG_DEFAULT ):
        
        if ( Logger.__instance == None ):
            Logger.__instance = Logger( log_path, logging_mode, writing_mode )

        return Logger.__instance


    ## set_mode
    #  --------
    #
    # Set the level of verbosity of the Logger.
    #
    # @param logging_mode: The logging mode.
    #                      Constants.MODE_INFO by default.
    #
    # @throw DenCellORFException: When the provided level of verbosity is not allowed.
    #
    def set_mode( self, logging_mode=Constants.MODE_INFO ):
        
        # If the verbosity level is incorrect, raise a DenCellORFException.
        if ( logging_mode not in Constants.LOG_MODES.values() ):
            raise DenCellORFException( 'The provided level of verbosity is incorrect. It must be one of: ' +
                                        ', '.join( Constants.LOG_MODES.keys() ) +
                                       '. Please see the documentation for more information.' )
        
        else:
            self.mode = logging_mode
            # Reset the level of logger and handlers
            self.logg.setLevel( logging_mode )
            for hdl in self.logg.handlers:
                hdl.setLevel( logging_mode )

        return None


    ## debug
    #  -----
    #
    # Log at debug level.
    #
    # @param message: String - The message to log.
    #
    def debug( self, message ):
        
        if ( self.mode == Constants.MODE_DEBUG ):
            self.logg.debug( message )


    ## info
    #  ----
    #
    # Log at info level.
    #
    # @param message: String - The message to log.
    #
    def info( self, message ):
        
        if ( ( self.mode == Constants.MODE_DEBUG )
             or ( self.mode == Constants.MODE_INFO ) ):
                self.logg.info( message )


    ## warning
    #  -------
    #
    # Log at warning level.
    #
    # @param message: String - The message to log.
    #
    def warning( self, message ):
        
        if ( ( self.mode == Constants.MODE_DEBUG )
             or ( self.mode == Constants.MODE_INFO )
             or ( self.mode == Constants.MODE_WARNING ) ):
                self.logg.warning( message )


    ## error
    #  -----
    #
    # Log at error level.
    #
    # @param message: String - The message to log.
    # @param ex: Boolean - Does exception information have to be added to the log?
    #                      True by default.
    #
    def error( self, message, ex=True ):

        if ex:
            if ( ( self.mode == Constants.MODE_DEBUG )
                 or ( self.mode == Constants.MODE_INFO )
                 or ( self.mode == Constants.MODE_WARNING )
                 or ( self.mode == Constants.MODE_ERROR ) ):
                    self.logg.error( message, exc_info=True )
        else:
            if ( ( self.mode == Constants.MODE_DEBUG )
                 or ( self.mode == Constants.MODE_INFO )
                 or ( self.mode == Constants.MODE_WARNING )
                 or ( self.mode == Constants.MODE_ERROR ) ):
                    self.logg.error( message )


    ## critical
    #  --------
    #
    # Log at critical level and exit the program.
    #
    # @param message: String - The message to log.
    # @param ex: Boolean - Does exception information have to be added to the log?
    #                      False by default.
    #
    def critical( self, message, ex=False ):
        
        self.logg.critical( message + '\n Program prematurely halted.', exc_info=False )
        exit()
        

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
