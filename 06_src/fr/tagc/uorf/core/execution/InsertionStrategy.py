# -*- coding: utf-8 -*-

import ConfigParser
import os
from sqlalchemy import func


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.execution import *
from fr.tagc.uorf.core.execution.insertion import *
from fr.tagc.uorf.core.execution.insertion.ParserWrapper import ParserWrapper

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## InsertionStrategy
#  =================
#
# This class allows to get the names and paths of all the gene lists and data sources 
# that need to be parsed and inserted in the database (searching for them in the config 
# file) and to perform the insertion of new entries in the database.
#
class InsertionStrategy( object ):

    ## Constructor of InsertionStrategy
    #  --------------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - genelists_dict: Dictionary - A dictionary that associate to each gene list
    #                                    the path to its file.
    #     - genelist_order: List - The list containing the order in which the gene lists
    #                              have to be inserted.
    #     - source_dict: Dictionary - A dictionary that associate to each data source 
    #                                 the path to its file.
    #     - source_order: List - The list containing the order in which the data sources
    #                            have to be inserted.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    #
    def __init__( self ):

        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none=True )

        if configfile:
            self.configfile = configfile
            if ( not os.path.exists( configfile ) ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            self.parse_config()
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' Please see the documentation for more information.' )



    ## parse_config
    #  ------------
    #
    # Parse the config file to retrieve required information.
    # 
    # @throw DenCellORFException: When the order of insertion of the gene list or of the data 
    #                             source contains files for which there is no path provided.
    #
    def parse_config( self ):

        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
        
        # Set a dictionary of reference gene lists
        self.genelists_dict = {}
        self.genelist_order = []
        
        if config.has_section( Constants.CONFIG_SECTION_GENE_LIST ):
            
            for genelist in config.items( Constants.CONFIG_SECTION_GENE_LIST ):
                self.genelists_dict[ genelist[ 0 ] ] = genelist[ 1 ]
        
            # If the gene list is expected to be inserted in a precise order, get it
            if ( config.has_section( Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION )
                 and config.has_option( Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION, Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION_ITEM_ORDER )
                 and config.get( Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION, Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION_ITEM_ORDER ) not in [ '', [], 'NA' ]):
                
                self.genelist_order = config.get( Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION, 
                                                  Constants.CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION_ITEM_ORDER )
                # Convert the string into a list
                self.genelist_order = self.genelist_order.replace( ' ','' ).split( ',' )
                
                # Make sure all the gene lists provided in this list are well provided 
                # in the data source section. Raise an exception otherwise.
                if ( not all( elt in self.genelists_dict.keys() for elt in self.genelist_order ) ):
                    raise DenCellORFException( 'InsertionStrategy.parse_config(): The order of insertion' +
                                               ' of the gene lists provided in the configfile (' + 
                                               str( self.genelist_order ) + ') contains gene lists' +
                                               ' for which there is no path provided.' )
    
            elif self.genelists_dict:
                Logger.get_instance().info( 'The gene lists will not be parsed and inserted in a' +
                                            ' particular order as no order of insertion has been provided' +
                                            ' in the config file.' )
                
            # Get the order in which the gene lists have to be parsed and inserted
            self.genelist_order += [ gl for gl in self.genelists_dict.keys() if ( gl not in self.genelist_order ) ]
        
        
        # Set a dictionary of data sources
        self.source_dict = {}
        self.source_order = []
        
        if config.has_section( Constants.CONFIG_SECTION_DATASOURCE ):
            
            for datasource in config.items( Constants.CONFIG_SECTION_DATASOURCE ):
                self.source_dict[ datasource[ 0 ] ] = datasource[ 1 ]
        
            # If the data is expected to be inserted in the precise order, get it
            if ( config.has_section( Constants.CONFIG_SECTION_DATA_ORDER_OF_INSERTION)
                 and config.has_option( Constants.CONFIG_SECTION_DATA_ORDER_OF_INSERTION, Constants.CONFIG_SECTION_ORDER_OF_INSERTION_ITEM_ORDER )
                 and config.get( Constants.CONFIG_SECTION_DATA_ORDER_OF_INSERTION, Constants.CONFIG_SECTION_ORDER_OF_INSERTION_ITEM_ORDER ) not in [ '', [], 'NA' ]):
                
                self.source_order = config.get( Constants.CONFIG_SECTION_DATA_ORDER_OF_INSERTION, 
                                                Constants.CONFIG_SECTION_ORDER_OF_INSERTION_ITEM_ORDER )
                # Convert the string into a list
                self.source_order = self.source_order.replace( ' ','' ).split( ',' )
                
                # Make sure all the sources provided in this list are well provided 
                # in the data source section. Raise an exception otherwise.
                if not all( elt in self.source_dict.keys() for elt in self.source_order ):
                    raise DenCellORFException( 'InsertionStrategy.parse_config(): The order of insertion' +
                                               ' of data provided in the configfile (' + 
                                               str( self.source_order ) + ') contains data sources' +
                                               ' for which there is no path provided.' )
                
            elif self.source_dict:
                Logger.get_instance().info( 'Data sources will not be parsed and inserted in a' +
                                            ' particular order as no order of insertion has been provided' +
                                            ' in the config file.' )
                
            # Get the order in which the data sources have to be parsed and inserted
            self.source_order += [ ds for ds in self.source_dict.keys() if ( ds not in self.source_order ) ]
            
            

    ## execute
    #  -------
    #
    # Execute the strategy to parse and insert data from gene list and 
    # data sources into the database.
    # 
    # @throw DenCellORFException: When an exception has been raised during the
    #                             DatabaseCheck.
    # @throw DenCellORFException: When an exception has been raised during the parsing 
    #                             of a gene list.
    # @throw DenCellORFException: When the Gene table is empty and there is no gene list 
    #                             provided in the config file.
    # @throw DenCellORFException: When the DataSource table contains entries whilst the
    #                             Gene table do not.
    #
    def execute( self ):
        
        # Run DatabaseCheck in order to check the DS database is reachable prior to insertion of data
        Logger.get_instance().info( 'Checking the database prior to data insertion...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( 'An error occurred whilst checking the database prior to' +
                                       ' data insertion.' +
                                         '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        # Process to the insertion of the gene lists. 
        # NB: The gene lists are only added if there is not any entry in the Gene table.
        
        # Prior to any insertion of data, get all the entries of the DataSource table and 
        # store them into the DataManager for a faster and easier access during data parsing
        # NB: Please see the documentation of the DataManager for more information.
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DATASOURCES, 
                                                          'query( DataSource ).all()' )
                
        # If there is not any Gene entry in the database and not any entry in the 
        # DataSource table, insert the gene lists provided
        gene_table_count = SQLManagerDS.get_instance().get_session().query( Gene ).count()
        SQLManagerDS.get_instance().close_session()
        
        if ( ( gene_table_count == 0 ) 
             and ( DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES ) == {} ) ):

            # Parse and insert the gene lists in the appropriate order
            if self.genelist_order:
                
                Logger.get_instance().info( 'Starting the insertion of the gene lists.' )
                
                if ( len( self.genelist_order ) > 1 ): 
                    Logger.get_instance().debug( 'InsertionStrategy.execute(): The gene lists' +
                                                 ' will be parsed and inserted in the following order: ' + 
                                                 ', '.join( self.genelist_order ) + '.' )
                
                for gene_list in self.genelist_order:
                    
                    # Get the corresponding data path
                    data_path = self.genelists_dict[ gene_list ]
                    
                    # Instantiate the ParserWrapper
                    try:
                        parser_wrapper = ParserWrapper( data_source = gene_list, 
                                                        data_path = data_path )
                    except Exception as e:
                        raise DenCellORFException( 'InsertionStrategy.execute(): An error occurred' +
                                                   ' trying to instantiate the ParserWrapper for' + 
                                                   ' the gene list "' + gene_list + '".', e )
                    
                    # Execute the parsing and insertion of genes
                    Logger.get_instance().info( 'Starting the parsing and the insertion of the gene list "' + 
                                                gene_list + '".' )
                    
                    # Parse the gene list
                    Logger.get_instance().debug( 'Starting the parsing of the gene list "' + 
                                                 gene_list + '".' )
                    try:
                        objects_to_insert = parser_wrapper.execute()
                    except Exception as e:
                        raise DenCellORFException( 'InsertionStrategy.execute(): An error occured parsing' +
                                                   ' the gene list "' + gene_list +
                                                     '".\n Error code: ' + LogCodes.ERR_PARS_PARSING + '.', e )
                    
                    # Insert the data parsed
                    self.batch_insert_to_db( objects_to_insert = objects_to_insert, 
                                             source = gene_list )
                
            
            # If there is no gene list provided, raise an exception
            else:
                raise DenCellORFException( 'The database does not contain any entry in the Gene table' +
                                           ' and there is not any gene lists or cross-reference provided' +
                                           ' in the config file.' )
                               
        elif ( gene_table_count != 0 ):
            Logger.get_instance().info( 'The Gene table already contains entries.' +
                                        ' Hence the gene lists provided in the config file will not' +
                                        ' be inserted. If you changed the gene lists provided in the config' +
                                        ' file, make sure to overwrite the existing database prior data' +
                                        ' insertion using the "-f" option. Please see the documentation' +
                                        ' for more information.' )
        
        else:
            raise DenCellORFException( 'The DataSource table already contains data whilst the Gene table' +
                                       ' does not contain any data! Please contact the developer if you' +
                                       ' see this message.' )
        
                
        # Once the Gene and GeneAlias table are filled in, complete the UTGeneFromAlias table.
        # NB: This table associates to each alias (i.e. entry of the GeneAlias table) its gene ID(s).
        #     To do this, for a given alias, a first search is performed for the symbol in the list
        #     of approved symbols. 
        #         - If no results are found in the list of approved symbols, a search is then performed
        #           in the whole list of aliases. 
        #         - If a unique gene is found, its ID is saved in the "gene_ids" attribute.
        #         - If several genes are found matching this alias, these IDs are all concatenated and 
        #           saved as a string in the "gene_ids" attribute (comma-separated values).
        utgenefromalias_query = SQLManagerDS.get_instance().get_session().query(UTGeneFromAlias)
        utgenefromalias_count = utgenefromalias_query.count()
        SQLManagerDS.get_instance().close_session()
        
        # If the UTGeneFromAlias table is empty, fill it in processing data from Gene and GeneAlias tables
        if ( utgenefromalias_count == 0 ):
                        
            Logger.get_instance().info( 'Starting to match to each unique alias of the GeneAlias table' +
                                        ' the list of its associated gene IDs. The information will be' +
                                        ' recorded in the UTGeneFromAlias table.' )
            
            # Get the dictionary that associate to each unique "official" 
            # alias of the GeneAlias table its corresponding gene ID(s)
            # (as a comma-separated list if several gene IDs are associated
            # to the alias)
            off_aliases_dict = SQLManagerDS.get_instance().get_session().query( 
                                                                                GeneAlias.alias, 
                                                                                func.group_concat( GeneAlias.gene_id ) 
                                                                               ).filter( 
                                                                                            GeneAlias.alias.like( Constants.ALIAS_OFF_PREFIX  + '%' ) 
                                                                                        ).group_by( 
                                                                                                    GeneAlias.alias 
                                                                                                    ).all()
            off_aliases_dict = GeneralUtil.list_of_2tuples_to_dict( off_aliases_dict )
            
            # Get the dictionary that associate to each unique "non official" 
            # alias of the GeneAlias table its corresponding gene ID(s)
            # (as a comma-separated list if several gene IDs are associated
            # to the alias)
            non_off_aliases_dict = SQLManagerDS.get_instance().get_session().query( 
                                                                                    GeneAlias.alias, 
                                                                                    func.group_concat( GeneAlias.gene_id ) 
                                                                                    ).filter( 
                                                                                                GeneAlias.alias.notlike( Constants.ALIAS_OFF_PREFIX  + '%' ) 
                                                                                            ).group_by( 
                                                                                                        GeneAlias.alias 
                                                                                                        ).all()
            non_off_aliases_dict = GeneralUtil.list_of_2tuples_to_dict( non_off_aliases_dict )    
            
            # Get the list of all the aliases used in the GeneAlias table
            all_uniq_aliases = SQLManagerDS.get_instance().get_session().query( GeneAlias.alias ).distinct().all()                
            all_uniq_aliases = GeneralUtil.query_result_to_list( all_uniq_aliases )
                        
            # Get the number total number of objects expected to be treated and 
            # reset the ProgressionBar instance to follow the progression
            ProgressionBar.get_instance().reset_instance( total = len( all_uniq_aliases ) )
            SQLManagerDS.get_instance().close_session()
            
            # For each unique gene alias, get the list of corresponding gene IDs
            # and store it in the UTGeneFromAlias table.
            objects_to_insert = []
            for alias in all_uniq_aliases:
                        
                # Update and display the progression bar on the console
                ProgressionBar.get_instance().increase_and_display()
                
                # If the alias has not the prefix of an official symbol,
                # then get the alias with the prefix
                if ( alias.startswith( Constants.ALIAS_OFF_PREFIX ) ):
                    alias_with_off = alias
                else:
                    alias_with_off = Constants.ALIAS_OFF_PREFIX + alias
                    
                # If the alias exists as an approved / official alias in the 
                # GeneAlias table, then get the list of gene IDs associated to
                # it and create a new entry in the UTGeneFromAlias table
                alias_in_off_dict = off_aliases_dict.get( alias_with_off )
                if ( alias_in_off_dict ):
                    utgenefromalias = UTGeneFromAlias( alias = alias, 
                                                       gene_ids = alias_in_off_dict )
                    objects_to_insert.append( utgenefromalias )
                
                # Otherwise, try to get the list of gene IDs that are associated to it.
                # If the alias is not register in the dictionary, log a critical error 
                # as it means the database integrity has been compromised.
                else:
                    alias_in_non_off_dict = non_off_aliases_dict.get( alias )
                    
                    if ( alias_in_non_off_dict ):
                        utgenefromalias = UTGeneFromAlias( alias = alias, 
                                                           gene_ids = alias_in_non_off_dict )
                        objects_to_insert.append( utgenefromalias )
                        
                    else: 
                        Logger.get_instance().critical( 'InsertionStrategy.get_gene_ids_from_symbol():' +
                                                ' Unexpected query result: the search for the symbol ' + 
                                                symbol + ' in the list of all symbols from the GeneAlias' +
                                                ' table returned an empty result. Please contact the' +
                                                ' developer if you see this message.' )
            
            Logger.get_instance().info( 'The association of each unique aliases of the GeneAlias table' +
                                        ' to its list of corresponding gene IDs has finished.' )
            
            # Insert these new objects into the database
            self.batch_insert_to_db( objects_to_insert = objects_to_insert, 
                                     source = 'UTGeneFromAlias' )
            
        else:
            Logger.get_instance().info( 'The UTGeneFromAlias table already contains data.' +
                                        ' Hence, the computation of its content will not be performed again.' )
            
        
        # Prior to the insertion of data, get all the entries of the Gene, GeneAlias, 
        # UTGeneFromAlias and UTDSTranscriptGeneConflict tables and store them into 
        # the DataManager for a faster and easier access during the parsing
        # NB: See the DataManager documentation for more information.        
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_GENES, 
                                                          'query( Gene ).all()' )
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_GENEALIASES, 
                                                          'query( GeneAlias ).all()' )
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_GENESFROMALIASES, 
                                                          'query( UTGeneFromAlias ).all()' )
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_UTDSTRANSCRIPTGENECONFLICT, 
                                                          'query( UTDSTranscriptGeneConflict ).all()' )
        
        # Create a dictionary that associates to each gene ID
        # its Gene object and store it into the DataManager
        all_gene_id_asso = {}
        for g in DataManager.get_instance().get_data( Constants.DM_ALL_GENES ).keys():
            all_gene_id_asso[ g.gene_id ] = [ g ]
        DataManager.get_instance().store_data( Constants.DM_ALL_GENE_ID_ASSO, all_gene_id_asso )
        
        
        # Create an empty dictionary that will allow to associate to each (symbol, chromosome) 
        # pair, a unique Gene object or an Exception containing a message to log. This dictionary
        # will be filled as data insertion is going on. This allows to faster the insertion of
        # data as the Gene / Exception object is only search once for each (symbol, chromosome) 
        # pair that is recorded.
        DataManager.get_instance().store_data( Constants.DM_ALL_GENE_SYMBOL_ASSO, {} )
        
        # As the data source can eventually be inserted in several times, it is necessary to 
        # get also the "conflict" symbols that have already been created during the insertion
        # of the previous data source, and to consider them in this dictionary.
        all_gene_symbol_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_SYMBOL_ASSO )
        # Query the database to get all the entry of the Gene table that have the 
        # "CONFLICT_GENE" prefix in their symbol and record them in the dictionary.
        all_gene_conflict = SQLManagerDS.get_instance().get_session().query( Gene ).filter( Gene.gene_id.like( Constants.PREFIX_CONFLICT_GENE_TRANSCRIPT + '%' ) ).all()
        for gene_conflict in all_gene_conflict:
            all_gene_symbol_asso[ ( gene_conflict.gene_id, gene_conflict.chromosome ) ] = gene_conflict
        SQLManagerDS.get_instance().close_session()
        
        
        # Get the highest values of ID for the DSORF, DSTranscript and DSORFTranscriptAsso 
        # tables and initialize the first autoincrement value at the maximum value + 1 
        # (or to 1 if no data have yet been inserted and all three tables are empty). 
        # This value is stored in the DataManager main dictionary in order to be used 
        # by the parsers.
        # NB: One single autoincrement value is set, meaning that the same variable will 
        #     be incremented of 1 each time a new variable is created either in the DSORF, 
        #     DSTranscript or DSORFTranscriptAsso table.
        max_dsorf_id = SQLManagerDS.get_instance().get_session().query( func.max( DSORF.id ) ).one()[ 0 ]
        max_dstranscript_id = SQLManagerDS.get_instance().get_session().query( func.max( DSTranscript.id ) ).one()[ 0 ]
        max_dsota_id = SQLManagerDS.get_instance().get_session().query( func.max( DSORFTranscriptAsso.id ) ).one()[ 0 ]
        SQLManagerDS.get_instance().close_session()
        
        if ( max_dsorf_id, max_dstranscript_id, max_dsota_id ) != ( None, None, None ):
            autoincrement = max( max_dsorf_id, max_dstranscript_id, max_dsota_id ) + 1
        else:
            autoincrement = 1
        
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
          
        # Parse and insert the data
        if self.source_order:
            
            Logger.get_instance().info( 'Starting the insertion of data.' )
            
            if ( len( self.source_order ) > 1 ):
                Logger.get_instance().debug( 'InsertionStrategy().execute(): The data sources' +
                                             ' will be parsed and inserted in the following order: ' + 
                                             ', '.join( self.source_order ) + '.' )
        
        
        for data_source in self.source_order:
                    
            # Get the corresponding data path
            data_path = self.source_dict.get( data_source )
                    
            # Instantiate the ParserWrapper
            try:
                parser_wrapper = ParserWrapper( data_source = data_source, 
                                                data_path = data_path )
            except Exception as e:
                Logger.get_instance().error( 'InsertionStrategy().execute(): An error occurred trying' +
                                             ' to instantiate the ParserWrapper for ' + data_source + '\n' + 
                                             str( e ) + '\n Hence data from this source will not be' +
                                             ' inserted in the database.' +
                                             ' Error code: ' + LogCodes.ERR_PARS_PARSER + '.',
                                             ex = False )
            
            else:
                # Execute the parsing and insertion of data
                Logger.get_instance().info( 'Starting the parsing and insertion of the data from ' + 
                                            data_source + '.' )
                
                # Parse the data source
                Logger.get_instance().debug( 'Starting the parsing of the data from ' + data_source + '.' )
                try:
                    objects_to_insert = parser_wrapper.execute()
                except InsertException as e:
                    Logger.get_instance().info( e.get_message() )
                except Exception as e:
                    Logger.get_instance().error( 'InsertionStrategy.execute(): An error occurred trying to' +
                                                 ' parse the data from ' + data_source + ': ' + str( e ) + 
                                                 '\n Hence the data from this source will not be inserted' +
                                                 ' in the database.' +
                                                 '\n Error code: ' + LogCodes.ERR_PARS_PARSING + '.',
                                                 ex = False )
                else:                    
                    # Insert the data
                    
                    try:
                        self.batch_insert_to_db( objects_to_insert = objects_to_insert, 
                                                 source = data_source )
                    except Exception as e:
                        Logger.get_instance().error( 'InsertionStrategy.execute(): An error occurred trying to' +
                                                     ' insert the data from ' + data_source + ': ' + 
                                                     str( e ) + '\n Hence the data from this source will' +
                                                     ' not be inserted in the database.' +
                                                     '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.',
                                                     ex = False )
        
        # Remove from the Gene table all the "conflict" genes without children in the 
        # DSTranscript table (such Gene entries may have been created during the insertion 
        # but no longer used because other genes have been added to the list after the 
        # 'CONFLICT_' prefix)
        all_gene_conflict_wo_child_query = SQLManagerDS.get_instance().get_session().query( Gene ).filter( 
                                                                                                            Gene.gene_id.like( Constants.PREFIX_CONFLICT_GENE_TRANSCRIPT + '%' ),
                                                                                                            Gene.DSTranscript_list == None 
                                                                                                          )
        all_gene_conflict_wo_child_count = all_gene_conflict_wo_child_query.count()
        
        if ( all_gene_conflict_wo_child_count != 0 ):
            Logger.get_instance().debug( 'Removing from the Gene table all the "conflict" entries that' +
                                         ' have been created during the insertion but have no longer any' +
                                         ' children in the DSTranscript table (' + 
                                         str( all_gene_conflict_wo_child_count ) + ' entries will be deleted).' +
                                         ' Please see the documentation for more information.' )
            
            entries_to_delete_str = ', '.join( [ g.gene_id for g in all_gene_conflict_wo_child_query.all() ] )
            try:
                all_gene_conflict_wo_child_query.delete( synchronize_session = 'fetch' )
                SQLManagerDS.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'InsertionStrategy.execute(): An error occurred trying to' +
                                           ' remove the following Gene entries from the session' +
                                           ' and to commit changes: ' + entries_to_delete_str + '.', e )
        
        # Log the end of the insertion
        if self.source_order:
            Logger.get_instance().info( 'The insertion of data has finished.' )  
            
            

    ## batch_insert_to_db
    #  ------------------
    #
    # This method allows to insert a list of objects in the database.
    # See the documentation of the SQLManager.batch_insert_to_db() function 
    # for more information.
    #
    # @param objects_to_insert: List - The list of objects to insert in the database.
    # @param source: String - The name of the source from which these objects have been created.
    # 
    def batch_insert_to_db( self, objects_to_insert, source ):
        
        Logger.get_instance().debug( 'Starting the insertion of data from ' + source + '.' ) 
        
        # Save into a temporary file the data that should be inserted.
        # This allows to recover the data later if an exception is raised during
        # the insertion, saving thus the parsing time.
        try:
            FileHandlerUtil.save_obj_to_file( objects_to_save = objects_to_insert,
                                              filename = 'objects_from_' + source, 
                                              output_folder = Constants.PARSED_DATA_FOLDER )
        except Exception as e:
            Logger.get_instance().error( 'InsertionStrategy.batch_insert_to_db():' +
                                         ' An error occurred trying to save data from ' + 
                                         source + ': \n' + str( e ) +
                                         ' Error code: ' + LogCodes.ERR_FILEHAND + '.',
                                         ex = False )
        
        # Insert the objects into the database
        SQLManagerDS.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert, 
                                                        process = source )
        
        Logger.get_instance().debug( 'The insertion of data from ' + source + ' has finished.' )
    