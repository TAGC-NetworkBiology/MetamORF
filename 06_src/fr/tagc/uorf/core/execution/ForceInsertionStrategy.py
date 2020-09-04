# -*- coding: utf-8 -*-

import os


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## ForceInsertionStrategy
#  ======================
#
# This class allows to force the insertion of a list of objects
# using a temporary file that has been generated after the parsing.
#
class ForceInsertionStrategy( object ):

    ## Constructor of ForceInsertionStrategy
    #  -------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - datasource: List of strings - The list of data sources to insert.
    #
    # @throw DenCellORFException: When the name of the data source(s) is (are) not provided, or cannot be 
    #                             converted into a list.
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

        # Get the list of the data sources to insert
        try:
            datasource = OptionManager.get_instance().get_option( OptionConstants.OPTION_SOURCE_NAME, 
                                                                  not_none=True )
        except Exception as e:
            raise DenCellORFException( ' An error occurred trying to get the list of sources to insert' +
                                       ' in the database.', e )
            
        if datasource:
            if isinstance( datasource, basestring ):
                self.datasource = datasource.replace( ' ', '' ).split( ',' )
            
            else:
                raise DenCellORFException( 'ForceInsertionStrategy: The name of the source(s) has to be' +
                                           ' provided as a single string. If there are several' +
                                           ' sources to insert into the database, the sources needs' +
                                           ' to be provided as comma-separated list.' +
                                           ' Please see the documentation for more information.' )
        
        else:
            raise DenCellORFException( 'ForceInsertionStrategy: The name of the source(s) to insert' +
                                       ' has (have) to be provided!' )
    
            

    ## execute
    #  -------
    #
    # Execute the strategy to force the insertion of data in the database.
    # The InsertionStrategy must have been run prior, in order to generate 
    # the appropriate temporary files containing the data to insert.
    # 
    # @throw DenCellORFException: When an error occurred during the insertion of data.
    #
    def execute( self ):
        
        # Create a session to the DS database
        SQLManagerDS.get_instance().set_db_settings( self.db_settings )
        try:
            SQLManagerDS.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'ForceInsertionStrategy.execute(): An error occurred while trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        
        # Get the list of entries in the DataSource table and store them in the DataManager
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DATASOURCES, 
                                                          'query(DataSource).all()' )
        SQLManagerDS.get_instance().close_session()
                    
        # Process to the insertion of data
        Logger.get_instance().info( 'Starting the insertion of data.' )
        
        for data_source in self.datasource:
            try:
                self.insert_datasource( data_source )
            except Exception as e:
                raise DenCellORFException( 'An error occurred trying to insert the data related to ' +
                                             data_source + '.', e )
               
        # Log the end of the insertion
        Logger.get_instance().info( 'The insertion of data has finished.' )   
    
    
    
    ## insert_datasource
    #  -----------------
    #
    # This is a static method that allows to import the data parsed for a particular source
    # from its temporary file and to insert them into the database.
    #
    # @param data_source: String - The name of the data source to insert into the database.
    # 
    # @throw DenCellORFException: When a exception has been raised trying to import the objects 
    #                             from the file created after the parsing of the data source.
    # @throw DenCellORFException: When a exception has been raised trying to insert the objects 
    #                             related to the data source or trying to commit the session.
    #
    @staticmethod
    def insert_datasource( data_source ):
        
        # For an easier manipulation of data stored in the DataManager, 
        # assign a new variable to access the list of data sources
        all_datasources = DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES )
        
        # Make sure the source is not already in the database
        ds = DataSource( name = data_source )
            
        # If the source is in the database, do not proceed to the insertion
        if ds in all_datasources:
            Logger.get_instance().info( 'The source "' + data_source + 
                                        '" has been found in the database.' +
                                        ' Hence, the data from this source will not be inserted again.' +
                                        ' If for some reason you need to perform again the insertion,' +
                                        ' please first use the Deletion strategy.' +
                                        ' Please see the documentation for more information.' )
            
        # Process to the insertion of data
        else:
            Logger.get_instance().debug( 'Starting the insertion of data from ' + data_source + '.' )
            
            # Get the list of objects to insert from the file
            try:
                objects_to_insert = FileHandlerUtil.get_obj_from_file( input_folder = Constants.PARSED_DATA_FOLDER,
                                                                       filename = 'objects_from_' + data_source )
            except Exception as e:
                raise DenCellORFException( 'An error occurred trying to import the data for the source ' +
                                           data_source + ' from its file.' +
                                           '\n Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
                
            else:
                try:
                    SQLManagerDS.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert,
                                                                    process = data_source )
                except DenCellORFException as e:
                    raise DenCellORFException( 'An error occurred trying to insert the data from ' +
                                               data_source + '.' +
                                               '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e )
                    
                Logger.get_instance().info( 'The insertion of data from ' + data_source + ' finished.' )
        