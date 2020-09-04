# -*- coding: utf-8 -*-

from datetime import datetime


# NB: The following modules are not imported at the beginning of the file 
#     but during the execution of the main function:
#         - execution module: from fr.tagc.uorf.core.execution import *
#     Please see the main function for more information.

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## DenCellORF
#  ==========
#
# This is the main class of the uORF project. 
# It contains the methods necessary to execute the program.
#
class DenCellORF( object ):

    ## execute
    #  -------
    #
    # Execute the strategy provided in the user command line.
    # Raise an exception if the strategy cannot be executed.
    #
    # @throw DenCellORFException: When an exception has been raised instantiating the strategy.
    # @throw DenCellORFException: When an exception has been raised executing the strategy.
    #
    def execute(self):

        strategy_command = OptionManager.get_instance().get_strategy()
        
        if ( strategy_command != None ):
            try:
                strategy = eval( strategy_command + 'Strategy()' )
            except Exception as e:
                raise DenCellORFException( 'DenCellORF.execute(): An error occurred during the' +
                                           ' instantiation of the strategy: ' + str( e ) )
        else:
            Logger.get_instance().critical( 'DenCellORF.execute(): A strategy must be provided!' +
                                            ' The following strategies are available: ' +
                                            ', '.join( OptionConstants.STRATEGIES_LIST ) +
                                            '. See the documentation for more information.' )
        
        try:
            strategy.execute()
        except Exception as e:
            raise DenCellORFException( 'DenCellORF.execute(): An error occurred during the execution'+
                                       ' of the program.', e )



# ===============================================================================
# The main function
# ===============================================================================

if __name__ == '__main__':
    
    # Create the Logger instance
    Logger.get_instance().info( 'DenCellORF Starting...' )
    start_time = datetime.now()
    
    # Store the options
    try:
        OptionManager.get_instance().initialize()
    except DenCellORFException as e:
        Logger.get_instance().critical( 'An error occurred during the initialization of the' +
                                        ' OptionManager: ' + e.get_message() )
    except Exception as e:
        Logger.get_instance().critical( 'An error occurred during the initialization of the' +
                                        ' OptionManager: ' + str( e ) )

    try:
        # Set the level of verbosity of the main Logger
        verbosity_level = OptionManager.get_instance().get_option( OptionConstants.OPTION_VERBOSITY )
        if ( verbosity_level not in Constants.LOG_MODES.keys() ):
            Logger.get_instance().critical( 'The level of verbosity selected is incorrect.' +
                                            ' It must be one of: ' + ', '.join( Constants.LOG_MODES.keys() ) + 
                                            '. Please see the documentation for more information.' )
        Logger.get_instance().set_mode( Constants.LOG_MODES[ verbosity_level ] )
        
        # Get the type of database, in order to set the appropriate collation for strings
        SQLCollationManager.get_instance().set_db_collation( OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE ) )
        # NB: The execution module is only imported after this step in order to allow a 
        #     "dynamic" creation of the model (classes inheriting from SQLAlchemy Base). 
        #     Indeed, once the model has been loaded, this is not possible to update the
        #     collation of the columns.
        from fr.tagc.uorf.core.execution import *
        
        # Instantiate DenCellORF
        DenCellORF = DenCellORF()
        
        # Execute the strategy
        DenCellORF.execute()
    
    except Exception as e:
        Logger.get_instance().critical( 'A critical error occurred during the execution of the program: ' +
                                        str( e ) )
        
    else:
        # Compute the time necessary to run the process
        end_time = datetime.now()
        Logger.get_instance().debug( 'Duration of the process: {}'.format( end_time - start_time ) )
        
        # Log the end of the process
        Logger.get_instance().info( 'End of DenCellORF process.' )

