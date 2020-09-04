# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.dbcheck.CheckDatabase import CheckDatabase

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## CheckDSDatabase
#  ===============
#
# This class is an class inheriting from CheckDatabase aiming to perform the database check
# of databases using the DS model.
# If:
#     - The database does not exists, then it creates the database.
#     - The database is empty or does not follow the expected model, then it overwrites the database.
#     - The database exists and follows the model, then it overwrites the database only if asked.
#
class CheckDSDatabase( CheckDatabase ):
        
    ## Class variables
    #  ---------------
    #
    # General constants
    STRATEGIES_ALLOWING_FORCE_OVERWRITE = OptionConstants.STRATEGIES_ALLOWING_FORCE_OVERWRITE_ON_DS_DB
    
    
    ## Constructor of CheckDSDatabase
    #  ------------------------------
    #
    # See the documentation of the constructor of CheckDatabase for more information.
    #
    def __init__( self ):
        
        CheckDatabase.__init__( self )
    
    
    
    ## parse_config_DB_name
    #  --------------------
    #
    # This method allows to get the name of the DS database from the config file and 
    # to store it in the db_settings dictionary of the object.
    #
    # @throw DenCellORFException: When database name cannot be found in the config file.
    #
    def parse_config_DB_name( self, config ):
                
        # Get the name of the DS database
        if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_DS_DB_NAME ):
            self.db_settings[ Constants.DB_SETTINGS_DB_NAME ] = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                                                            Constants.CONFIG_SECTION_DATABASE_ITEM_DS_DB_NAME )
        else:
            raise DenCellORFException( 'The DS database name (' + 
                                       Constants.CONFIG_SECTION_DATABASE_ITEM_DS_NAME +
                                       ' item) has to be provided in the config file.' )
    
    
    
    ## get_SQLManager_instance
    #  -----------------------
    #
    # This method allows to get the SQLManager instance corresponding to the model of the database.
    #
    # @return SQLManagerDS.get_instance(): The instance of the SQLManagerDS 
    #                                      (allowing to manage DS databases).
    #
    def get_SQLManager_instance( self ):
        
        return SQLManagerDS.get_instance()
    
    
    
    ## get_sp_class_for_model
    #  ----------------------
    #
    # This method allows to get the class corresponding to the SpeciesCatalog table of the database 
    # (in order to allow SQLAlchemy to query this table).
    #
    # @return SpeciesCatalog: The SpeciesCatalog class (of the DS database model).
    #
    def get_speciescatalog_class( self ):
        
        return SpeciesCatalog
    