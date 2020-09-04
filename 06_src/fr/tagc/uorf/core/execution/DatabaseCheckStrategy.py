# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.execution.dbcheck import *

from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## DatabaseCheckStrategy
#  =====================
#
# This class is a strategy aiming to perform the database check.
# If:
#     - The database does not exists: it creates the database.
#     - The database is empty or does not follow the expected model: it overwrites the database.
#     - The database exists and follows the model: it overwrites the database only if asked.
#
class DatabaseCheckStrategy( object ):
                
    ## Class variables
    #  ---------------
    #
    # List of database models that may be checked
    DATABASE_MODELS = OptionConstants.AVAILABLE_DATABASE_MODELS
    
    
    ## Constructor of DatabaseCheckStrategy
    #  ------------------------------------
    #
    # Intance variables:
    #     - called_strategy: String - The name of the strategy called.
    #
    def __init__( self ):

        self.called_strategy = OptionManager.get_instance().get_strategy()
            


    ## execute
    #  -------
    #
    # Execute the strategy to build the database(s) if it is (they are) not existing or 
    # check (an) existing one(s). The database(s) checked depends on the strategy that 
    # has been initially selected by the user. 
    # See the documentation of the OptionConstants for more information about the 
    # strategies that allows the DatabaseCheck of the different databases.
    #
    def execute( self ):
        
        # For each model of database, if the strategy selected by the user requires to 
        # check / build the database, instantiate the appropriate CheckDatabase class 
        # and execute the CheckDatabase strategy.
        for db_model in self.DATABASE_MODELS:
            
            strategies_checking_db = eval( 'OptionConstants.STRATEGIES_CHECKING_' + db_model + '_DATABASE' )
            
            if ( self.called_strategy in strategies_checking_db ):
                
                Logger.get_instance().info( 'Checking the ' + db_model + ' database...' )
                
                try:
                    check_db = eval( 'Check' + db_model + 'Database()' )
                except Exception as e:
                    raise DenCellORFException( 'DatabaseCheckStrategy: An exception occurred trying to' +
                                               ' instantiate Check' + db_model + 'Database.', e )
                    
                try:
                    check_db.execute()
                except DenCellORFException as e:
                    raise DenCellORFException( 'DatabaseCheckStrategy: An exception occurred trying to' +
                                               ' check the ' + db_model + 'database.', e )
            