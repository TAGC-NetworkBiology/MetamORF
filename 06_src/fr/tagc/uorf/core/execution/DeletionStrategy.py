# -*- coding: utf-8 -*-

import os
from sqlalchemy import or_, and_


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## DeletionStrategy
#  ================
#
# This class allows to remove from the database all the entries related
# to a particular data source.
#
class DeletionStrategy( object ):

    ## Constructor of DeletionStrategy
    #  -------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - datasource: List of strings - The list of data sources to delete.
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

        # Get the list of data sources to delete
        try:
            datasource = OptionManager.get_instance().get_option( OptionConstants.OPTION_SOURCE_NAME, 
                                                                  not_none = True )
        except Exception as e:
            raise DenCellORFException( 'An error occurred trying to get the list of sources to remove' +
                                       ' from the database.', e )
        
        # Convert the string containing the data sources to delete into a list
        if datasource:
            if isinstance( datasource, basestring ):
                self.datasource = datasource.split( ',' )
            
            else:
                raise DenCellORFException( 'DeletionStrategy: The name of the source(s) has to be' +
                                           ' provided as a single string. If there are several' +
                                           ' sources to remove from the database, the sources needs' +
                                           ' to be provided as comma-separated list.' +
                                           ' Please see the documentation for more information.' )
        else:
            raise DenCellORFException( 'DeletionStrategy: The name of the source(s) to remove' +
                                       ' has (have) to be provided!' )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to remove from the database any data related to the data source provided.
    # 
    # @throw DenCellORFException: When a connection to the DS database cannot be created.
    #
    def execute( self ):
        
        # Create a session to the DS database
        SQLManagerDS.get_instance().set_db_settings( self.db_settings )
        try:
            SQLManagerDS.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'DeletionStrategy.execute(): An error occurred while trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
            
        # Get the list of entries in the DataSource table and store them in the DataManager
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DATASOURCES, 
                                                          'query( DataSource ).all()' )
        SQLManagerDS.get_instance().close_session()
                
        # Process to the deletion of data
        Logger.get_instance().info( 'Starting the deletion of data.' )
        
        for data_source in self.datasource:
            try:
                self.delete_datasource( data_source )
            except Exception as e:
                Logger.get_instance().error( 'An error occurred trying to delete the data related to ' +
                                             data_source + '\n' + str( e ) + '.' +
                                             ' Error code: ' + LogCodes.ERR_DELETE_DS + '.',
                                             ex = False )
                        
        # Log the end of the deletion
        Logger.get_instance().info( 'Deletion of data has finished.' )
    
    
    
    ## delete_datasource
    #  -----------------
    #
    # This is a static method that allows to delete from the database 
    # the entries related to a particular data source.
    # NB: Please note that this method removes the ORF, Transcript and ORFTranscriptAsso 
    #     entries related to the provided data source, but DO NOT remove the Gene and 
    #     GeneAlias entries that have been created during the parsing and insertion of
    #     data of the source and that are no more used.
    #
    # @param data_source: String - The name of the data source to delete from the database.
    # 
    # @throw DenCellORFException: When a exception has been raised trying to delete the 
    #                             objects from the session or trying to commit the session.
    #
    @staticmethod
    def delete_datasource( data_source ):
        
        # For an easier manipulation of data stored in the DataManager, 
        # assign a new variable to access the list of data sources
        all_datasources = DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES )
        
        # Check that the source is in the database
        ds = DataSource( name = data_source )
        
        existing_ds = all_datasources.get( ds )
        if ( not existing_ds ):
            Logger.get_instance().info( 'The source "' + data_source + '" cannot be found in the database.' +
                                        ' Hence, no data will be deleted from this source.' )
        else:
            # Queries to perform to get the entries related to the data source
            datasource_to_delete = SQLManagerDS.get_instance().get_session().query( DataSource ).filter( DataSource.name == data_source )
            dsorfs_to_delete_qr = SQLManagerDS.get_instance().get_session().query( DSORF ).filter( DSORF.data_source == data_source )
            dstranscripts_to_delete_qr = SQLManagerDS.get_instance().get_session().query( DSTranscript ).filter( DSTranscript.data_source == data_source )
            dsorftranscriptasso_to_delete_qr = SQLManagerDS.get_instance().get_session().query( DSORFTranscriptAsso ).filter( DSORFTranscriptAsso.data_source == data_source )
            utdstranscriptgeneconflict_to_delete_qr = SQLManagerDS.get_instance().get_session().query( UTDSTranscriptGeneConflict ).filter( UTDSTranscriptGeneConflict.data_source == data_source )
            
            # Ask the user to confirm the deletion of the data source
            total_to_delete = ( datasource_to_delete.count() + 
                                dsorfs_to_delete_qr.count() + 
                                dstranscripts_to_delete_qr.count() + 
                                dsorftranscriptasso_to_delete_qr.count() )
            
            Logger.get_instance().info( str( dsorfs_to_delete_qr.count() ) + ' DSORF, ' +
                                        str( dstranscripts_to_delete_qr.count() ) + ' DSTranscript, and ' +
                                        str( dsorftranscriptasso_to_delete_qr.count() ) + 
                                        ' DSORFTranscriptAsso entries (total of ' + 
                                        str( total_to_delete ) + ' entries)'
                                        ' have been found related to the data source ' + data_source +
                                        ' and are about to be deleted from the database.' )
            
            confirm_deletion = None
            while ( confirm_deletion not in [ 'Y', 'N' ] ):
                print( 'Do you want to proceed to the deletion? (Y/N)' )
                confirm_deletion = raw_input().upper()
            
            # Delete the objects from the database if the deletion has been confirmed
            if ( confirm_deletion == 'Y' ):
                try:
                    datasource_to_delete.delete()
                    utdstranscriptgeneconflict_to_delete_qr.delete()
                except DenCellORFException as e:
                    raise DenCellORFException( 'DeletionStrategy.execute(): An error occurred trying' +
                                               ' to delete all the entries related to ' + data_source + 
                                               ' from the session.', e )
                    
                # Commit the changes
                try:
                    SQLManagerDS.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'DeletionStrategy.execute(): An error occurred trying to' +
                                               ' commit the changes after deletion of the entries related to ' +
                                               data_source + ' from the session.', e )
                else:
                    # Log in debug mode the number of objects successfully deleted
                    Logger.get_instance().debug( 'InsertionStrategy.execute(): the objects related to ' +
                                                 data_source + ' have been successfully deleted from' +
                                                 ' the database.' )
                SQLManagerDS.get_instance().close_session()
                
            else:
                Logger.get_instance().info( 'Deletion of data related to ' + data_source + 
                                            ' aborted by the user.' )
            