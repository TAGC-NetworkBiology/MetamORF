# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
       

## AddReleaseVersionStrategy
#  =========================
#
# This class is a strategy aiming to add a release version and
# a short description of the database in the Metadata / 
# PROMetadata table.
#
class AddReleaseVersionStrategy( object ):

    ## Constructor of AddReleaseVersionStrategy
    #  ----------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - db_model: String - The name of the database model to use (PRO / DS).
    #     - db_release: String - The version number to use in the metadata table.
    #     - db_desc: String - An (optional) short description of the database.
    #     - force_overwrite: Boolean - Should any existing database version / database description 
    #                                  be replaced by the new one?
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

        # Check if the forceOverwrite option has been selected
        self.force_overwrite = OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, 
                                                                        not_none = False )
            
        # Get the release number
        self.db_release = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_RELEASE_NB,
                                                                   not_none = True )
        
        # Get the description of the release
        self.db_desc = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_RELEASE_DESC,
                                                                not_none = False )
    
        
    
    ## execute
    #  -------
    #
    # Execute the strategy to insert the release-related data 
    # in the metadata table.
    # 
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    #
    def execute( self ):
                
        # Set the connection to the database
        self.get_sqlmanager_instance().set_db_settings( self.db_settings )
        
        try:
            self.get_sqlmanager_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'AddReleaseVersionStrategy.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        self.get_sqlmanager_instance().close_session()
        
        # If there is already an annotation version information registered
        # in the metadata table, get it
        release_metadata_query = self.get_sqlmanager_instance().get_session().query(
                                                                                        self.get_metadata_class() 
                                                                                    ).filter( 
                                                                                                self.get_metadata_class().parameter == Constants.METATABLE_DATABASE_VERSION_NUMBER
                                                                                            )
        
        # If a version has already been registered, update it if necessary 
        # (i.e. if the forceOverwrite option has been selected) or log a 
        # critical message,
        if ( release_metadata_query.count() != 0 ):
        
            # Get the entry
            metadata_release_entry = release_metadata_query.one()
            
            if ( self.force_overwrite ):
                metadata_release_entry.value = self.db_release
                metadata_release_entry.description = self.db_desc
                # Commit the updates
                self.get_sqlmanager_instance().commit()
                
            else:
                if ( ( metadata_release_entry.value != self.db_release )
                     or ( metadata_release_entry.description != self.db_desc ) ):
                    Logger.get_instance().critical( 'A different version has already been registered in the metadata' +
                                                    ' table for this database (' + metadata_release_entry.value +
                                                    ', ' + metadata_release_entry.description + 
                                                    ') and the forceOverwrite option has not been selected.' +
                                                    ' Hence, the version number and/or description will not' +
                                                    ' be updated.' )
             
        # Otherwise, create a new entry in the metadata table   
        else:
            metadata_release = self.get_metadata_class()( parameter = Constants.METATABLE_DATABASE_VERSION_NUMBER,
                                                          value = self.db_release,
                                                          description = self.db_desc )
            self.get_sqlmanager_instance().get_session().add( metadata_release )
            self.get_sqlmanager_instance().commit()
                
        self.get_sqlmanager_instance().close_session()
          
    
    
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
                
            
    
    ## get_metadata_class
    #  ------------------
    #
    # Return the appropriate metadata table class, either Metadata 
    # (DS database) or PROMetadata (PRO database).
    #
    # @return appropriate metadata class corresponding to the database model used.
    # 
    def get_metadata_class( self ):
        
        if ( self.db_model == OptionConstants.DATABASE_DECLARATIVE_PRO ):
            return PROMetadata
        else:
            return Metadata
        