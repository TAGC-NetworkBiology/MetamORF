# -*- coding: utf-8 -*-

import pandas as pd
import datetime


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.execution.insertion.ParserStrategy import ParserStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log import *


# ===============================================================================
# Description of the file parsed using this class
# ===============================================================================

## Source: NCBI
#
# NB: This file contains a header
#     This file is expected to be in a tab-delimited format
#
## Description of the columns of the raw data file:
#- [0]: \#tax_id: Taxon ID - Integer
#- [1]: GeneID: NCBI gene ID (Entrez Direct accession number) - Integer
#- [2]: Symbol: Gene symnol (NCBI) - String
#- [3]: LocusTag: Unique gene identifier (NBCI) - String
#- [4]: Synonyms: Aliases of the gene (separated with "|") - String
#- [5]: dbXrefs: Cross references (separated with "|") - String
#        Available cross references: 
#            - Ensembl ("Ensembl:REFERENCE") 
#            - HGNC ("HGNC:REFERENCE")
#            - MGI ("MGI:REFERENCE")
#            - MMI ("MMI:REFERENCE")
#- [6]: chromosome: Chromosome name - String
#- [7]: map_location: Location - String
#- [8]: description: Description - String
#- [9]: type_of_gene: Type of gene - String
#- [10]: Symbol_from_nomenclature_authority: Symbol from nomenclature authority - String
#- [11]: Full_name_from_nomenclature_authority: Description from nomenclature authority - String
#- [12]: Nomenclature_status: Nomenclature status - String
#- [13]: Other_designations: Other descriptions (separated with "|") - String
#- [14]: Modification_date: Modification date (as "YYYYMMDD") - String
#- [15]: Feature_type: Feature type - String


# ===============================================================================
# File parser
# ===============================================================================


## NCBIGeneList
#  ============
#
# This class inherits from ParserStrategy and allows to parse gene lists from NCBI.
# When duplicates of gene symbols are found, alias lists are merged together.
#
class NCBIGeneList( ParserStrategy ):
                
    ## Class variables
    #  ---------------
    #
    # Headers
    HEADER_NCBI_ID = 'GeneID'
    HEADER_CHROMOSOME = 'chromosome'
    HEADER_APPROVED_SYMBOL = 'Symbol'
    HEADER_SYNONYMS = 'Synonyms'
    HEADER_CROSS_REFERENCES = 'dbXrefs'
    
    HEADER_LIST = [ HEADER_NCBI_ID, HEADER_CHROMOSOME, HEADER_APPROVED_SYMBOL, HEADER_SYNONYMS,
                    HEADER_CROSS_REFERENCES ]
    
    # Constants
    CROSS_REF_NAME = 'NCBIGeneList'
    

    ## Constructor of NCBIGeneList
    #  ---------------------------
    #
    def __init__( self, data_path ):
        
        ParserStrategy.__init__( self, data_path )
                     

    ## execute
    #  -------
    #
    # Execute the parsing strategy.
    # See the execute() method documentation of the ParserStrategy metaclass for 
    # more information about the main steps of the algorithm run in this method.
    #
    # @return objects_to_insert: List - List of objects to insert in the database.
    #
    # @throw DenCellORFException: When this parser cannot be used for the species of the database.
    # @throw DenCellORFException: When an exception has been raised checking the headers of the file.
    #
    def execute( self ):
        
        # =============================================================================
        # /!\ This list and the cross references associated with are expected to be 
        #     inserted prior to any other list!
        # =============================================================================
        
        # As this list of genes is used as the reference, first make sure there is not any entry 
        # in the Gene and GeneAlias tables
        try:
            gene_content_nb = SQLManagerDS.get_instance().get_session().query( Gene ).count()
            gene_alias_content_nb = SQLManagerDS.get_instance().get_session().query( GeneAlias ).count()
            SQLManagerDS.get_instance().close_session()
        except Exception as e:
            raise DenCellORFException( 'NCBIGeneList.execute(): Request on Gene and GeneAlias tables failed.', e)
        
        if ( gene_content_nb != 0 ) or ( gene_alias_content_nb != 0 ):
            Logger.get_instance().critical( 'NCBIGeneList.execute(): Gene and/or GeneAlias table already' +
                                            ' contains data. Make sure to use a new database or overwrite' +
                                            ' an existing database before insertion of this gene list.' +
                                            ' Please see the documentation for more information.' )
        
        
        # Get the content of the file
        self.import_file_content( file_sep = '\t' )
        
        # Check the headers of the file
        try:
            self.check_headers()
        except DuplicateHeaderException as e:
            Logger.get_instance().warning( e.get_message() +
                                           ' Warning code: ' + LogCodes.WARN_HEADER_DUPL + '.' )
                
        # Sort the data frame based on the NCBI Gene ID
        # This allows to get the duplicates following each other
        self.file_content = self.file_content.sort_values( by = NCBIGeneList.HEADER_NCBI_ID, axis = 0 )
        
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
        # Initialize the list of objects to insert
        objects_to_insert = []
        
        # Declare some useful variables
        previous_id = None
        previous_chr = None
        all_prev_app_symbols = {}
        
        # Parse the content of the file and save it in appropriate objects
        start_time = datetime.datetime.now()
        for ( index, row ) in self.file_content.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Get the NCBI gene ID
            current_id = row[ NCBIGeneList.HEADER_NCBI_ID ]
            
            # Log a warning message if the NCBI gene ID is missing
            if ParserStrategy.is_empty( current_id ):
                Logger.get_instance().warning( 'NCBI Gene List: The line n°' + str( index ) +
                                               ' does not contain NCBI gene ID. Hence, this line will be ignored.' +
                                               ' Warning code: ' + LogCodes.WARN_GENELIST_ID_MISS + '.' )
            
            
            else:
                
                # Add the NCBI prefix to the ID
                current_id = 'NCBI:' + str( current_id )
                
                # Create an empty list to store new aliases of the gene
                aliases = []
                
                # Get the chromosome name
                current_chr = row[ NCBIGeneList.HEADER_CHROMOSOME ]
                  # Replace missing values of chromosome name by None
                  # NB: Genes located on both chromosomes X and Y are registered 
                  #     as located on "X|Y" in this file
                current_chr = self.initialize_chromosome_name( current_chr )
                
                # A new Gene object is created only if the symbol of the current entry does not match
                # with the symbol of the previous one. This allow to identify duplicates.
                if ( current_id != previous_id ):
                    # Create a new Gene entry
                    # ID and chromosome name from NCBI are used to create new Gene entries
                    gene = Gene( gene_id = current_id,
                                 chromosome = current_chr )
                    objects_to_insert.append( gene )
                    
                    # (Re-)initialize a variable to store all aliases for this gene
                    all_aliases = []
                    
                    # (Re-)initialize a variable to keep record of all approved symbols for this gene
                    approved_symbols = []
                    
                    # Register the NCBI ID as one of the aliases of the gene (with "NCBI:" prefix)
                    aliases = [ current_id ]
                    
                    # Add the approved symbol to the aliases of the gene
                    # The approved symbol is add both "bulk" and with a prefix for easier identification
                    app_symbol = row[ NCBIGeneList.HEADER_APPROVED_SYMBOL ]
                    aliases.append( Constants.ALIAS_OFF_PREFIX + app_symbol )
                    aliases.append( app_symbol )
                    all_aliases.append( app_symbol )
                    approved_symbols.append( app_symbol )
                                    
                    # Keep record of this new association gene ID - approved symbol
                    #    NB: This will allow to check later if this approved symbol is not associated with 
                    #        other NCBI IDs. In such case, a GeneRef warning will be logged prior to data 
                    #        insertion for all the approved symbols associated with several gene IDs.
                    existing_app_symbol = all_prev_app_symbols.get( app_symbol )
                    if existing_app_symbol:
                        existing_app_symbol.append( current_id )
                    else:
                        all_prev_app_symbols[ app_symbol ] = [ current_id ]
    
    
                # Else, if the gene ID is the same as the previous one, check the chromosome and approved
                # symbols are the same.
                else:
                    # Log a critical message if the same NCBI ID is used for genes on different chromosomes
                    if current_chr != previous_chr:
                        Logger.get_instance().critical( 'NCBIGeneList.execute(): Two distinct locations' +
                                                        ' have been found for the gene with NCBI ID "' +
                                                        str( current_id ) + '". Found on chromosomes: ' + 
                                                        str(previous_chr) + ' and ' + str(current_chr) + 
                                                        '. Please see the documentation for more information.')
                    
                    app_symbol = row[ NCBIGeneList.HEADER_APPROVED_SYMBOL ]
                    # Log a GeneRef warning if the same NCBI ID has several approved gene symbols
                    # and add this new approved gene symbol to the list of aliases
                    if ( app_symbol not in approved_symbols ):
                        if ( len( approved_symbols ) == 1 ):
                            # Log a warning for the first approved symbol which 
                            # has been associated with this gene ID
                            GeneRefLogger.get_instance().crossref_warning( 'NCBI Gene list: The gene with NCBI ID ' + 
                                                                           current_id + ' has been found associated' +
                                                                           ' with several approved symbols.' +
                                                                           ' New approved symbol: ' +
                                                                           approved_symbols[ 0 ] + '.')
                        # Log a warning for the new approved symbol
                        GeneRefLogger.get_instance().crossref_warning( 'NCBI Gene list: A new approved symbol: ' + 
                                                                       app_symbol + ' has been found associated with' +
                                                                       ' the gene with NCBI ID: ' + current_id + '.')
                        # Keep record of this new approved symbol
                        approved_symbols.append( app_symbol )
                        # Add this new approved symbol to the list of aliases
                        aliases.append( Constants.ALIAS_OFF_PREFIX + app_symbol )
                        aliases.append( app_symbol )
                        all_aliases.append( app_symbol )
                                    
                        # Keep record of this new association gene ID - approved symbol
                        existing_app_symbol = all_prev_app_symbols.get( app_symbol )
                        if existing_app_symbol:
                            existing_app_symbol.append( current_id )
                        else:
                            all_prev_app_symbols[ app_symbol ] = [ current_id ]                     
                        
                        
                # Get the new aliases of the gene
                  # Get the list of aliases (parse them as a list)
                if ( not ParserStrategy.is_empty( row[ NCBIGeneList.HEADER_SYNONYMS ] ) ):
                    synonyms = row[ NCBIGeneList.HEADER_SYNONYMS ].split( '|' )
                else:
                    synonyms = []
                
                  # Get the list of external references (parse external references as a list)
                if ( not ParserStrategy.is_empty( row[ NCBIGeneList.HEADER_CROSS_REFERENCES ] ) ):
                    external_refs = row[ NCBIGeneList.HEADER_CROSS_REFERENCES ].split( '|' )
                    
                    ext_ref = []
                    for r in external_refs:
                        ref = r.split(':', 1)
                        if ( len( ref ) == 2 ):
                            ext_ref.append( ref[ 1 ] )
                        else:
                            Logger.get_instance().error( 'NCBIGeneList.execute(): Error during parsing of' +
                                                         ' external references for the gene NCBI ID ' +
                                                         current_id + '. The external reference: ' + r + 
                                                         ' is in an unexpected format (expected as "database:ID").' +
                                                         ' Hence, this reference will not be recorded as' +
                                                         ' an alias of the gene in the database.' +
                                                         ' Error code: ' + LogCodes.ERR_GENELIST_FORM + '.' )
                else:
                    ext_ref = []
                    
                  # Concatenate these two lists of aliases
                synonyms += ext_ref
                
                  # Add each new alias to the list
                for syn in synonyms:
                    if ( syn not in all_aliases ):
                        aliases.append( syn )
                        all_aliases.append( syn )
                        
                # Create the alias objects corresponding to new aliases and add them to the list of objects to insert
                for alias in aliases:
                    if ( alias not in Constants.EMPTY_VALUES ):
                        gene_alias = GeneAlias( gene_id = gene.gene_id, 
                                                alias = alias,
                                                crossref = NCBIGeneList.CROSS_REF_NAME )
                        objects_to_insert.append( gene_alias )
                            
                # Store the ID and chromosome of the current gene for the next iteration
                previous_id = current_id
                previous_chr = current_chr
                
                
        # Log a CrossRef warning for all approved symbols that has been found associated with
        # several NCBI gene IDs.
        for app_symbol in all_prev_app_symbols.keys():
            if ( len( all_prev_app_symbols[ app_symbol ] ) != 1 ):
                GeneRefLogger.get_instance().crossref_warning( 'NCBI Gene List: The approved symbol ' + app_symbol +
                                                               ' has been found associated with the following NCBI gene IDs: ' +
                                                               ', '.join( all_prev_app_symbols[ app_symbol ] ) )
    
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'NCBIGeneList.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
        
        return objects_to_insert
    