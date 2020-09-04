# -*- coding: utf-8 -*-

import os


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.execution.insertion.parserstrategy import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log import *


## ParserWrapper
#  =============
#
# This class is a Wrapper which allows to execute the appropriate ParserStrategy to parse
# the data from a source and instantiate the appropriate objects to fill in the tables of 
# the database.
#
class ParserWrapper( object ):

    ## Constructor of ParserWrapper
    #  ----------------------------
    #
    # Instance variables:
    #     - data_source: String - The source of the data (should be the name of a parserstrategy).
    #     - data_path: String - The path to the data file.
    #
    # @param data_source: String - The source of the data (should be the name of a parserstrategy).
    # @param data_path: String - The path to the data file.
    #
    # @throw DenCellORFException: When the data source file cannot be found at the provided path.
    # @throw DenCellORFException: When an exception was raised during the instantiation 
    #                             of the ParserStrategy.
    #
    def __init__( self, data_source, data_path ):
        
        if os.path.exists(data_path):
            self.data_source = data_source
            self.data_path = data_path
        else:
            raise DenCellORFException( 'ParserWrapper: No file may be found at the path provided' +
                                       ' in the configfile (' + data_path + ').' )
        
        try:
            self.parser_strategy = eval( data_source + "('" + self.data_path + "')" )
        except Exception as e:
            raise DenCellORFException( 'ParserWrapper: No parsing strategy associated with data source ' + 
                                       data_source + '. Please make sure the name of the parser selected' +
                                       ' in the config file is the right one.', e )
        


    ## execute
    #  -------
    #
    # Execute the strategy related to the source, which parses the file and creates 
    # the entries to insert in the database.
    # Raise an exception if the strategy cannot be executed.
    #
    # @return objects_to_insert: List - A list of objects to insert in the database.
    #
    # @throw InsertException: When a data source of this name has already been inserted into the database
    #                         / when there are entries related to this data source in the database.
    # @throw DenCellORFException: When the parser has not been instantiated (see documentation of the
    #                             constructor).
    # @throw DenCellORFException: When an exception is raised during the parsing.
    #
    def execute( self ):
 
        # Parse the data source using the appropriate ParserStrategy
        if ( self.parser_strategy ):
            objects_to_insert = None
            
            # If a data source with the same name has already been inserted in the database,
            # skip the insertion of data and raise an InsertException
            ds = DataSource( name = self.data_source )
            if ( ds in DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES ).keys() ):
                raise InsertException( 'The data source ' + self.data_source + 
                                       ' already exists in the DataSource table.' +
                                       ' Hence, data from this source will not be parsed and inserted.' )
                
            # Make sure there is not any DSORF, DSTranscript or DSORFTranscriptAsso
            # related to this source in the database
            else:
                DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DSORFS_FOR_SOURCE, 'query(DSORF).filter(DSORF.data_source == "' + self.data_source + '").all()' )
                DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DSTRANSCRIPTS_FOR_SOURCE, 'query(DSTranscript).filter(DSTranscript.data_source == "' + self.data_source + '").all()' )
                DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DSORFTRANSCRIPTASSO_FOR_SOURCE, 'query(DSORFTranscriptAsso).filter(DSORFTranscriptAsso.data_source == "' + self.data_source + '").all()' )
                SQLManagerDS.get_instance().close_session()
        
                # If these dictionaries are not empty raise an InsertException
                if ( ( DataManager.get_instance().get_data( Constants.DM_ALL_DSORFS_FOR_SOURCE ) != {} )
                     or ( DataManager.get_instance().get_data( Constants.DM_ALL_DSTRANSCRIPTS_FOR_SOURCE ) != {} )
                     or ( DataManager.get_instance().get_data( Constants.DM_ALL_DSORFTRANSCRIPTASSO_FOR_SOURCE ) != {} ) ):
                    raise InsertException( 'ParserWrapper.execute(): Some data related to ' + 
                                           self.data_source + ' has been found in the database' +
                                           ' whilst this source has not been found in the DataSource table!' +
                                           ' Please not that the relational integrity of the database' +
                                           ' seems not to be respected!' )
            
                # Else, parse the data source
                else:
                    try:
                        objects_to_insert = self.parser_strategy.execute()
                    except Exception as e:
                        raise DenCellORFException( 'ParserWrapper.execute():' +
                                                   ' An exception has been raised during the parsing of ' + 
                                                   self.data_source, e )
                        
        # Raise an exception if the parser cannot be found
        else:
            raise DenCellORFException( 'ParserWrapper.execute(): The parser has not been instantiated for ' + 
                                       self.data_source + '. Please contact the developer for more information.' )
        
        # Log in debug mode the number of objects created during the parsing and expected to be inserted
        if objects_to_insert:
            Logger.get_instance().debug( 'ParserWrapper.execute(): ' + str(len(objects_to_insert)) +
                                         ' objects created during the parsing of ' + self.data_source + 
                                         ' are expected to be added to the database.' )
    
        return objects_to_insert
