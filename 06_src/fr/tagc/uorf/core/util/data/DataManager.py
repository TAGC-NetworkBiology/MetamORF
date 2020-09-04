# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# =============================================================================
# Information
# =============================================================================

# When the attributes of an existing entry of the database are updated, 
# it is necessary to refresh the object, flush or commit the session 
# prior to perform any new query on the database. As this process and 
# as well as highly repetitive queries could quickly become highly time
# consuming, this DataManager has been designed in order to store query 
# results, as well as any object (that needs to be access anywhere in the 
# program) in a dictionary. This DataManager allows an easier manipulation 
# of data.
# The DataManager instance contains a dictionary (data attribute) where
# the various data are stored.
# By default the results of queries are stored in a dictionary where each
# key and its associated value both equal one of the object in the list 
# returned by the query. Obviously, this dictionary is used to manage
# new instances prior to their insertion in the database.


## DataManager
#  ===========
#
# This class is a singleton allowing to store and access any data anywhere 
# in the program. This singleton handle the data through a dictionary.
# It contains also methods allowing to query easily the databases and 
# store the results in an efficient way.
#
class DataManager( object ):

    __instance = None
    

    ## Constructor of DataManager
    #  --------------------------
    #
    # Instance variable:
    #    - data: Dictionary - A dictionary of objects 
    #                         (usually - but not necessarily - dictionaries).
    #
    def __init__( self ):
        
        self.data = {}
                        

    ## get_instance
    #  ------------
    #
    # First time create an instance of DataManager, then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        if ( DataManager.__instance == None ):
            DataManager.__instance = DataManager()

        return DataManager.__instance
            

    ## store_DS_query_result
    #  ---------------------
    #
    # Query the DS database and store the result in the data dictionary 
    # as a dictionary (with each object of the result as key and value).
    #
    # @param keyword: String - The name of the dictionary in which results of the query 
    #                          have to be stored.
    # @param query_string: String - Query as a string.
    #
    # @throw DenCellORFException: When an exception has been raised querying the DS database.
    #
    def store_DS_query_result( self, keyword, query_string ):
        
        # Perform the query
        Logger.get_instance().debug( 'DataManager.store_DS_query_result():' +
                                     ' Querying the DS database: ".' + query_string + '".' )
        try:
            query_result = eval( 'SQLManagerDS.get_instance().get_session().' + query_string )
        except Exception as e:
            raise DenCellORFException( 'DataManager.store_DS_query_result(): The query ".' + 
                                       query_string + '" failed.', e )
        
        # Convert the result of the query into a dictionary where the keys equal 
        # the values and each of them are one of the result in the list
        query_result = GeneralUtil.list_to_dict( query_result )
        
        # Store the dictionary in the data dictionary
        self.data[ keyword ] = query_result
            

    ## store_PRO_query_result
    #  ----------------------
    #
    # This method allows to query the PRO database and store the result 
    # in the data dictionary as a dictionary (with each object of the 
    # result as key and value).
    #
    # @param keyword: String - The name of the dictionary in which results of the query 
    #                          have to be stored.
    # @param query_string: String - Query as a string.
    #
    # @throw DenCellORFException: When an exception has been raised querying the PRO database.
    #
    def store_PRO_query_result( self, keyword, query_string ):
        
        # Perform the query
        Logger.get_instance().debug( 'DataManager.store_PRO_query_result():' +
                                     ' Querying the PRO database: ".' + query_string + '".' )
        try:
            query_result = eval( 'SQLManagerPRO.get_instance().get_session().' + query_string )
        except Exception as e:
            raise DenCellORFException( 'DataManager.store_PRO_query_result(): The query ".' + 
                                       query_string + '" failed.', e )
        
        # Convert the result of the query into a dictionary where the keys equal 
        # the values and each of them are one of the result in the list
        query_result = GeneralUtil.list_to_dict( query_result )
        
        # Store the dictionary in the data dictionary
        self.data[ keyword ] = query_result
            

    ## store_data
    #  ----------
    #
    # This method allows to store any object in the data dictionary.
    #
    # @param keyword: String - The key to use to store the object in the data dictionary.
    # @param data_to_store: String - The object to store.
    #
    def store_data( self, keyword, data_to_store ):
        
        self.data[ keyword ] = data_to_store
            

    ## get_data
    #  --------
    #
    # This method allows to get an object stored in the data dictionary.
    #
    # @param keyword: String - The key to use to access the object in the data dictionary.
    #
    # @return Object - The object corresponding to this keyword in the data dictionary.
    #
    # @throw DenCellORFException: When the provided keyword is not a key of the data dictionary.
    #
    def get_data( self, keyword ):
    
        if ( keyword not in self.data.keys() ):
            raise DenCellORFException( 'DataManager.get_data(): The provided keyword ('  + keyword + 
                                       ') is not a key of the DataManager main dictionary.' )
        
        return self.data.get( keyword )    
            

    ## delete_data
    #  -----------
    #
    # This method allows to delete an entry in the data dictionary.
    #
    # @param keyword: String - Key to used to store the object in the data dictionary.
    #
    # @throw DenCellORFException: When the provided keyword is not a key of the data dictionary.
    #
    def delete_data( self, keyword ):
        
        if ( keyword in self.data.keys() ):
            del self.data[ keyword ]
        else:
            raise DenCellORFException( 'DataManger.delete_data(): The provided keyword ('  + keyword + 
                                       ') is not a key of the DataManager main dictionary.')
            

    ## get_data_manager_keys
    #  ---------------------
    #
    # Return the keys of the data dictionary.
    #
    # @return self.data.keys(): List - The list of keys of the data dictionary.
    #
    def get_data_manager_keys( self ):
        
        return self.data.keys()
    