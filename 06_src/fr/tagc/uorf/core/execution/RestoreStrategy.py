# -*- coding: utf-8 -*-

import os


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql.SQLManagerFILT import SQLManagerFILT
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## RestoreStrategy
#  ===============
#
# This class is a strategy aiming to restore a database using 
# the files created with the Backup strategy.
#
class RestoreStrategy( object ):
        
    ## Class variables
    #  ---------------
    #
    # Orders of insertion of tables in the databases
    DS_ORDER_OF_INSERTION = [ 'SpeciesCatalog', 'Metadata', 
                              'Gene', 'GeneAlias', 'UTGeneFromAlias',
                              'DataSource', 'DSORF', 'DSTranscript', 'DSORFTranscriptAsso' ]
    
    PRO_ORDER_OF_INSERTION = [ 'PROSpeciesCatalog', 'PROMetadata', 
                               'PROGene', 'PROGeneAlias',
                               'UTRNABiotypeCatalog',
                               'ORF', 'ORFDSAsso', 'Transcript', 'TranscriptDSAsso',
                               'ORFTranscriptAsso', 'ORFTranscriptAssoDSAsso',
                               'CellContextCatalog', 'CellContext', 
                               'ProvidedCategoryCatalog', 'ProvidedCategory',
                               'FLOSSClassCatalog', 'FLOSSClass',
                               'ORFCategoryCatalog', 'ORFCategory' ]
    
    
    ## Constructor of RestoreStrategy
    #  ------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - db_model: String - The name of the database model to use (PRO / DS).
    #     - input_folder: String - The path of the folder where to find the data previously saved.
    #     - file_prefix: String - The eventual prefix added to the file names. 
    #
    # @throw DenCellORFException: When the provided database model is not one of those known.
    #
    def __init__( self ):
        
        # Get the options necessary to establish the connection to the database
        self.db_settings = {}
        self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE )
        self.db_settings[ Constants.DB_SETTINGS_DB_NAME ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_NAME, 
                                                                                                     not_none = True )
        
        if self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_MYSQL:
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_USER )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PASSWD )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_HOST_IP )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PORT )
            
        elif self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_SQLITE:
            self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_FOLDER )
        
        # Get the force overwrite option
        self.force_overwrite = OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, 
                                                                        not_none = False )
                
        # Get the model of database
        self.db_model = OptionManager.get_instance().get_option( OptionConstants.OPTION_DATABASE_MODEL, 
                                                                 not_none = True )
        if ( self.db_model not in OptionConstants.AVAILABLE_DATABASE_MODELS ):
            raise DenCellORFException( 'The database model provided has to be in the following list: ' + 
                                       ', '.join( OptionConstants.AVAILABLE_DATABASE_MODELS ) + '.' )
        
        # Get the input folder
        self.input_folder = OptionManager.get_instance().get_option( OptionConstants.OPTION_INPUT_FOLDER, not_none = False )
        if ( not self.input_folder ):
            # By default, the files are saved in a PRO / DS subfolder of the backup default folder
            self.input_folder = os.path.join( Constants.BACKUP_DATA_FOLDER, self.db_model )
        
        # Get the eventual prefix added to the file names
        self.file_prefix = OptionManager.get_instance().get_option( OptionConstants.OPTION_FILE_PREFIX, 
                                                                    not_none = False )
            
    
    ## execute
    #  -------
    #
    # Execute the strategy to restore the database.
    # 
    # @throw DenCellORFException: When a session to the database cannot be created.
    # @throw DenCellORFException: When an exception has been raised trying to load the
    #                             content of a file (generated by the Backup strategy).
    # @throw DenCellORFException: When an exception has been raised trying to insert
    #                             an entry into a table of the database.
    # @throw DenCellORFException: When an exception has been raised trying to commit
    #                             session.
    # 
    def execute( self ):
        
        # Set the connection to the database
        self.get_sqlmanager_instance().set_db_settings( self.db_settings )
        try:
            self.get_sqlmanager_instance().get_instance().get_session()
            self.get_sqlmanager_instance().get_instance().close_session()
        except DenCellORFException as e:
            raise DenCellORFException( 'RestoreStrategy.execute(): An error occurred while trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
            
        # Check if the database already exists. 
        # If it exists, then ask the user to confirm the deletion of the database.
        if ( ( not self.force_overwrite ) and ( self.get_sqlmanager_instance().db_exists() ) ):

            confirm_deletion = None
            Logger.get_instance().info( 'A database already exists at the provided connection settings.' +
                                        ' Hence, any existing data nooeds to be removed prior the insertion' +
                                        ' of the data to restore.' )
            while ( confirm_deletion not in [ 'Y', 'N' ] ):
                print( 'Do you want to confirm the deletion of the database? (Y/N)' )
                confirm_deletion = raw_input().upper()
                
            if ( confirm_deletion == 'N' ):
                Logger.get_instance().critical( 'As a database already exists at the provided connection' +
                                                ' settings and as the deletion of existing data has been' +
                                                ' canceled by the user, the program will be stopped.' +
                                                ' Please see the documentation for more information.' )
            
        # (Re-)create the empty database
        self.get_sqlmanager_instance().build_database( db_settings = self.db_settings,
                                                       species = None, 
                                                       sp_mandatory = False,
                                                       force_overwrite = True )
        
        # Get the appropriate order in which the tables needs to be filled in
        order_of_insertion = eval( 'self.' + self.db_model + '_ORDER_OF_INSERTION' )
        
        # For each table of the list, get the corresponding file, 
        # upload the content and insert the data in the database
        for tablename in order_of_insertion:
            
            Logger.get_instance().debug( 'Starting to load and insert the data saved from the table ' + 
                                         tablename + '.' )
            
            # Get the name of the file (without its extension)
            if self.file_prefix:
                filename = self.file_prefix + tablename
            else:
                filename = tablename
            
            # Get the content of the file
            try:
                objects_to_insert = FileHandlerUtil.get_obj_from_file( input_folder = self.input_folder, 
                                                                       filename = filename )
            except Exception as e:
                raise DenCellORFException( 'A error occurred trying to import the objects to insert in the ' +
                                           tablename + 'table.' )
            
            Logger.get_instance().debug( str( len( objects_to_insert ) ) + ' entries are expected' +
                                         ' to be inserted into the ' + tablename + ' table.' )
               
            # Insert the data 
            # NB: Using the add_all() method of the session does not work (probably because
            #     the objects saved in the file were mapped to the session). Hence, it is 
            #     necessary to add the objects one at a time using the merge method.
            
            # Get the number total number of elements expected to be treated and
            # reset the ProgressionBar instance to follow the progression
            ProgressionBar.get_instance().reset_instance( total = len( objects_to_insert ) )
            
            for entry in objects_to_insert:
            
                # Update and display the progression bar on the console
                ProgressionBar.get_instance().increase_and_display()

                try:
                    self.get_sqlmanager_instance().get_session().merge( entry )
                except Exception as e:
                    raise DenCellORFException( 'An error occurred trying to insert the data into the ' +
                                               tablename + ' table. Please make sure the backup occurred' +
                                               ' successfully', e )
            
            # Commit the session
            try:
                self.get_sqlmanager_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'An error occurred trying to commit changes after insertion' +
                                           ' of data in the ' + tablename + ' table.' +
                                           '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.' )
                
            entry_count = self.get_sqlmanager_instance().get_session().query( eval( tablename ) ).count()
            Logger.get_instance().debug( str( entry_count ) + ' entries have been successfully added' +
                                         ' to the ' + tablename + ' table.' )
            self.get_sqlmanager_instance().close_session()
        
        # Log the end of the restoration
        Logger.get_instance().info( 'Restoration of the database has finished.' )
            
    
    
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
        