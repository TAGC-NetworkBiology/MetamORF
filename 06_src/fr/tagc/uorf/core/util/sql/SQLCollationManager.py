# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.util.sql import SQLConstants


## SQLCollationManager
#  ===================
#
# This class is a singleton aiming to manage the collation of the database.
# The value of the collation is useful to define the column which aim to
# receive strings (such as VARCHAR or TEXT types).
#
class SQLCollationManager( object ):
    
    __instance = None
    

    ## Constructor of SQLCollationManager
    #  ----------------------------------
    #
    # Instance variable:
    #     - db_collation: String - The collation used in the database.
    #    
    def __init__( self ):
        
        self.db_collation = None
            
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of SQLCollationManager, 
    # then return this instance.
    #
    # @return the singleton instance
    #   
    @staticmethod
    def get_instance():
        
        if ( SQLCollationManager.__instance == None ):
            SQLCollationManager.__instance = SQLCollationManager()

        return SQLCollationManager.__instance
            
            

    ## set_db_collation
    #  ----------------
    #
    # This method allows to set the appropriate collation according 
    # to the database type.
    # If the database type is not provided, it will set the collation 
    # to the value of the default type. See the documentation of the 
    # SQLConstants file for more information.
    #
    # @param db_type: String - The type of database (MySQL / SQLite).
    #
    # @throw Exception: When there is no collation defined for the 
    #                   database type selected.
    #
    def set_db_collation( self, db_type ):
        
        if ( db_type == None ):
            self.db_collation = SQLConstants.DEFAULT_COLLATION[ SQLConstants.DEFAULT_DB_TYPE ]
            
        elif ( db_type in SQLConstants.DEFAULT_COLLATION.keys() ):
            self.db_collation = SQLConstants.DEFAULT_COLLATION[ db_type ]
            
        else:
            raise Exception( 'SQLCollationManager.set_db_collation(): There is no collation' +
                             ' defined for the database type provided (' + db_type + 
                            '). Please check the database type provided.' +
                            ' If the error persists, please contact the developer.' )
        
            

    ## get_db_collation
    #  ----------------
    #
    # Get the collation to use.
    #
    # @return self.db_collation: String - The collation.
    #
    def get_db_collation( self ):
        
        return self.db_collation
            