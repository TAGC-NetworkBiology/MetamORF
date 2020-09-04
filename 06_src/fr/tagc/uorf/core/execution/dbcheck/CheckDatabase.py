# -*- coding: utf-8 -*-

import ConfigParser
import os

from abc import abstractmethod


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## CheckDatabase
#  =============
#
# This class is an abstract class and metaclass of classes that aim to perform the 
# checking of particular databases.
# If:
#     - The database does not exists, then it creates the database.
#     - The database is empty or does not follow the expected model, then it overwrites the database.
#     - The database exists and follows the model, then it overwrites the database only if asked.
#
class CheckDatabase( object ):
    
    ## Class variables
    #  ---------------
    #
    # General constants
    STRATEGIES_ALLOWING_FORCE_OVERWRITE = OptionConstants.STRATEGIES_ALLOWING_FORCE_OVERWRITE
    
    
    ## Constructor of CheckDatabase
    #  ----------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A number of settings to connect to the database.
    #     - configfile: String - Path to the config file.
    #     - force_overwrite: Boolean - Should overwrite any existing database at this path?
    #     - species: String - The name of the species.
    #     - db_settings: Dictionary - A number of settings to connect to the database.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the 
    #                             provided path.
    #
    def __init__( self ):
        
        self.classname = str( self.__class__.__name__ )
        
        self.db_settings = {}
        
        # Get and parse the config file
        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, \
                                                              not_none = True )
        
        if configfile:
            self.configfile = configfile
            if not os.path.exists( configfile ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            self.parse_config()
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' See the documentation for more information.' )
        
        self.force_overwrite = False
    
    
    ## parse_config
    #  ------------
    #
    # Parse the config file to retrieve required information.
    # Raise an exception if expected information is missing.
    #
    # Instantiate the instance variables:
    #     - self.species: String - The name of the species.
    #     - self.db_settings: Dictionary - A number of settings to connect to the database.
    #
    # @throw DenCellORFException: When expected sections / options are not provided in the config file.
    #
    @abstractmethod
    def parse_config( self ):
        
        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
        
        # Check the database section is provided in the config file
        if not config.has_section( Constants.CONFIG_SECTION_DATABASE ):
            raise DenCellORFException( 'The ' + Constants.CONFIG_SECTION_DATABASE +
                                       ' section has to be provided in the config file.' )
        
        
        # First, get the information that are common to all the databases 
        # (if several databases have to be build / used)
        # Get the species
        if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_SPECIES ):
            self.species = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                       Constants.CONFIG_SECTION_DATABASE_ITEM_SPECIES )
            
            # Check if the species provided is in the list of expected species
            if ( self.species not in Constants.SPECIES_LIST ):
                raise DenCellORFException( 'The species provided in the config file (' + 
                                           Constants.CONFIG_SECTION_DATABASE_ITEM_SPECIES + ': ' +
                                           self.species + ') must be one of the following species: ' + 
                                           ', '.join( Constants.SPECIES_LIST ) + '.' )
        
        else:
            raise DenCellORFException( 'The species (' + 
                                       Constants.CONFIG_SECTION_DATABASE_ITEM_SPECIES +
                                       ' item) has to be provided in the config file.' )
        
        
        # Get the type of the database
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE ):
            self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE )
            
            # Check the provided type
            if ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] not in SQLConstants.AUTORIZED_DB_TYPES ):
                raise DenCellORFException( 'The database type (' + 
                                           self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] +
                                           ') must be one of the following types: ' + 
                                           ', '.join( SQLConstants.AUTORIZED_DB_TYPES ) + '.' )
            
            
            # If non-default information are provided for the MySQL server, get them
            if self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_MYSQL:
                
                if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_USER_NAME ):
                    self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                                                                       Constants.CONFIG_SECTION_DATABASE_ITEM_USER_NAME )
                
                if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_USER_PASSWD ):
                    self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD ] = config.get( Constants.CONFIG_SECTION_DATABASE,
                                                                                         Constants.CONFIG_SECTION_DATABASE_ITEM_USER_PASSWD )
                
                if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_HOST_IP ):
                    self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                                                                       Constants.CONFIG_SECTION_DATABASE_ITEM_HOST_IP )
                
                if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_PORT ):
                    self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                                                                       Constants.CONFIG_SECTION_DATABASE_ITEM_PORT )
                
            
            # If non-default path is provided for the SQLite database, get it
            elif self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_SQLITE:
                if config.has_option( Constants.CONFIG_SECTION_DATABASE, Constants.CONFIG_SECTION_DATABASE_ITEM_DB_FOLDER ):
                    self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] = config.get( Constants.CONFIG_SECTION_DATABASE, 
                                                                                      Constants.CONFIG_SECTION_DATABASE_ITEM_DB_FOLDER )
        
            
        # Get the name of the database
        self.parse_config_DB_name( config )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to build the database if it is not existing or to check an existing database.
    # If the forceOverwrite option has been selected, any previously existing database of this name at 
    # this path / on the MySQL server will be removed first.
    #
    # @throw DenCellORFException: When an error occurs trying to add the species to the database.
    #
    @abstractmethod
    def execute( self ):
        
        # Check if the forceOverwrite option has been selected
        # NB: The value of this option is only get when the strategy selected by the user authorize to use it
        called_strategy = OptionManager.get_instance().get_strategy()
        if ( called_strategy in self.STRATEGIES_ALLOWING_FORCE_OVERWRITE ):
            if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
                self.force_overwrite = True
        
        # Build the database
        self.get_SQLManager_instance().build_database( db_settings = self.db_settings,  
                                                       species = self.species,
                                                       force_overwrite = self.force_overwrite )
        
        # Check if there are already information about species in the database.
        # If the species is provided, get it.
        species_query = self.get_SQLManager_instance().get_session().query( self.get_speciescatalog_class() )
        species_count = species_query.count()
        
        if ( species_count == 1 ):
            species = species_query.one()
            if ( species.name == self.species ):
                Logger.get_instance().info( 'This database contains information for ' + species.name + '.' )
            else:
                Logger.get_instance().critical( 'This database contains information for ' + species.name + 
                                                ' while the config file provides information for ' + 
                                                self.species + '.' )
        
        # If there is no species information contained in the database, use the information 
        # provided in the config file to add it to the database.
        elif ( species_count == 0 ):
            # Create the new SpeciesCatalog entry
            sp = self.get_speciescatalog_class()( name = self.species )
            try:
                self.get_SQLManager_instance().get_session().add( sp )
                self.get_SQLManager_instance().commit()
            except Exception as e:
                raise DenCellORFException( self.classname + '.execute(): Error occurred trying to add the species ' + 
                                           self.species + ' to the ' + self.get_speciescatalog_class().__tablename__ + 
                                           ' table of the database.', e )
            else:
                Logger.get_instance().info( 'The species ' + self.species + ' has been added to the ' +
                                            self.get_speciescatalog_class().__tablename__ + 
                                            ' table of the database.' )
        
        # If several species have been found in the database, 
        # log a critical message with the names of the species
        else:
            species = species_query.all()
            sp_names = [ str( sp.name ) for sp in species ]
            Logger.get_instance().critical( 'This database seems to contain information about several species!' +
                                            ' Following species have been found in the ' +
                                            self.get_speciescatalog_class().__tablename__ + ' table: ' + 
                                            ', '.join( sp_names ) + 
                                            '. Please kindly note that this program has not been built to be' +
                                            ' able to manage databases containing information for several species!' +
                                            ' Please see the documentation for more information.' )
        
        # If there is one single species, get its name and store it into the DataManager for further use
        if ( Constants.SPECIES_SHORT not in DataManager.get_instance().get_data_manager_keys() ):
            # Store the short name of the species (like 'Hsapiens')
            sp_short_name = species_query.one().name
            DataManager.get_instance().store_data( Constants.SPECIES_SHORT, sp_short_name )
        
            # Get the full name of the species from the short name and store the
            # value in the DataManager (like 'homo_sapiens', as it is used by some tools)
            DataManager.get_instance().store_data( Constants.SPECIES_FULL, 
                                                   Constants.SPECIES_CATALOG_FULL_NAMES[ sp_short_name ] )
        
        # Close the session to the database
        self.get_SQLManager_instance().close_session()
    
    
    
    ## parse_config_DB_name
    #  --------------------
    #
    # This method is expected to be defined in the children classes.
    # It should allow to get the name of the database from the config file.
    #
    # @throw DenCellORFException: Always.
    #
    @abstractmethod
    def parse_config_DB_name( self ):
        
        raise DenCellORFException( 'This is a place holder that should never been logged.' +
                                   ' A method "parsed_config_DB_name()" is expected to be defined' +
                                   ' in the class: ' + self.classname + '.' )



    ## get_SQLManager_instance
    #  -----------------------
    #
    # This method is expected to be defined in the children classes.
    # It should allow to get the SQLManager instance corresponding to the model of the database.
    #
    # @throw DenCellORFException: Always.
    #
    @abstractmethod
    def get_SQLManager_instance( self ):
        
        raise DenCellORFException( 'This is a place holder that should never been logged.' +
                                   ' A method "get_SQLManager_instance()" is expected to be defined' +
                                   ' in the class: ' + self.classname + '.' )



    ## get_sp_class_for_model
    #  ----------------------
    #
    # This method is expected to be defined in the children classes.
    # It should allow to get the class corresponding to the SpeciesCatalog table of the database 
    # (in order to allow SQLAlchemy to query this table).
    #
    # @throw DenCellORFException: Always.
    #
    @abstractmethod
    def get_sp_class_for_model( self ):
        
        raise DenCellORFException( 'This is a place holder that should never been logged.' +
                                   ' A method "get_sp_class_for_model()" is expected to be defined' +
                                   ' in the class: ' + self.classname + '.' )
    