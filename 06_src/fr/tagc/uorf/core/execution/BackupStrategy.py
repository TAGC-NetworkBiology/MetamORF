# -*- coding: utf-8 -*-

import os


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql.SQLManagerFILT import SQLManagerFILT
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## BackupStrategy
#  ==============
#
# This class is a strategy aiming to save all the entries of a database in 
# separate files (one file / table), allowing to restore the database later
# if necessary.
#
class BackupStrategy( object ):
    
    ## Constructor of BackupStrategy
    #  -----------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings (Strings). This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - db_model: String - The name of the database model to use (PRO / DS).
    #     - output_folder: String - The path of the folder where to save the data.
    #     - file_prefix: String - The prefix to add to the file names.
    #
    # @throw DenCellORFException: When the database type provided is not allowed.
    #
    def __init__( self ):
        
        # Get the options necessary to establish the connection to the database
        self.db_settings = {}
        self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE )
        self.db_settings[ Constants.DB_SETTINGS_DB_NAME ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_NAME, 
                                                                                                     not_none = True )
        
        if ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_MYSQL ):
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_USER )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PASSWD )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_HOST_IP )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PORT )
            
        elif ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_SQLITE ):
            self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_FOLDER )
        
        # Get the model of database
        self.db_model = OptionManager.get_instance().get_option( OptionConstants.OPTION_DATABASE_MODEL, 
                                                                 not_none = True )
        if ( self.db_model not in OptionConstants.AVAILABLE_DATABASE_MODELS ):
            raise DenCellORFException( 'The database model provided has to be in the following list: ' + 
                                       ', '.join( OptionConstants.AVAILABLE_DATABASE_MODELS ) + '.' )
        
        # Get the output folder
        self.output_folder = OptionManager.get_instance().get_option( OptionConstants.OPTION_OUTPUT_FOLDER, 
                                                                      not_none = False )
        if ( not self.output_folder ):
            # By default, save the files in a PRO / DS subfolder of the backup default folder
            self.output_folder = os.path.join( Constants.BACKUP_DATA_FOLDER, self.db_model )
        
        # Get the eventual prefix to add to the file names
        self.file_prefix = OptionManager.get_instance().get_option( OptionConstants.OPTION_FILE_PREFIX, 
                                                                    not_none = False )
            
    
    ## execute
    #  -------
    #
    # Execute the strategy to save all the entries of the database.
    # 
    # @throw DenCellORFException: When the database provided does not follow the expected model.
    # @throw DenCellORFException: When the backup of objects into the file failed.
    #
    def execute( self ):
                
        # Set the connection to the database
        self.get_sqlmanager_instance().set_db_settings( self.db_settings )
        
        # Check the integrity of the database
        str_ok = self.get_sqlmanager_instance().check_database_str_integrity()
        if ( not str_ok ):
            raise DenCellORFException( 'The schema of the database provided does not follow' +
                                       ' the expected model. Please make sure the provided model (' + 
                                       self.db_model + ') and the database (' + 
                                       self.db_settings[ Constants.DB_SETTINGS_DB_NAME ] +
                                       ') provided are the right ones.' )
            
        # Get the declarative base corresponding to the database
        base = self.get_sqlmanager_instance().get_declarative_base()
        
        # Build a dictionary of the classes defined in the model
        # where the keys are the classes, and the values their names
        dict_model_classes = {}
        for ( cl_name, cl_object ) in base._decl_class_registry.items():
            if ( not str( cl_name ) == '_sa_module_registry' ):
                dict_model_classes[ cl_object ] = str( cl_name )
        
        # For each table, get the list of all entries and save them in a file
        for table in dict_model_classes.keys():
            
            # Get the name of the tale
            table_name = str( dict_model_classes[ table ] )
            Logger.get_instance().debug( 'Starting to save the entries of the ' + table_name + ' table.' )
            
            # Get all the entries to save
            objects_to_save = self.get_sqlmanager_instance().get_session().query( table ).all()
            
            # Expunge the session to the database to detach the objects in the list from the session
            self.get_sqlmanager_instance().get_session().expunge_all()
            self.get_sqlmanager_instance().close_session()
            
            if self.file_prefix:
                filename = self.file_prefix + table_name
            else:
                filename = table_name
            
            try:
                FileHandlerUtil.save_obj_to_file( objects_to_save = objects_to_save,
                                                  filename = filename,
                                                  output_folder = self.output_folder )
            
            except Exception as e:
                raise DenCellORFException( 'BackupStrategy.execute(): An error occurred trying to' +
                                           ' save data in the file.'
                                           '\n Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
                
            
    
    ## get_sqlmanager_instance
    #  -----------------------
    #
    # Return the appropriate SQLManager instance.
    #
    # @return SQLManager instance corresponding to the database model used.
    # 
    def get_sqlmanager_instance( self ):
        
        sqlmanager_class = eval( 'SQLManager' + self.db_model )
        
        return sqlmanager_class.get_instance()
    