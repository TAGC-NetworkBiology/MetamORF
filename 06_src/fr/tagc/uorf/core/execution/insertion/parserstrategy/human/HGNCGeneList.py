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

## Source: HGNC
#
# NB: This file contains a header
#     This file is expected to be in a tab-delimited format
#
## Description of the columns of the raw data file:
#- [0]: HGNC_ID: HGNC ID (HGNC:[nb]) - String
#- [1]: Approved_symbol: Official symbol - String
#- [2]: Alias_symbol: Gene alias - String
#- [3]: Previous_symbol: Previous HGNC symbol - String
#- [4]: Chromosome: Chromosome name - String
#- [5]: Ensembl_gene_ID: Ensemble gene ID - String
#- [6]: NCBI_gene_ID: NCBI gene ID (Entrez Direct accession number) - Integer


# ===============================================================================
# File parser
# ===============================================================================


## HGNCGeneList
#  ============
#
# This class inherits from ParserStrategy and allows to parse gene lists from HGNC.
# When duplicates of gene symbols are found, alias lists are merged together.
#
class HGNCGeneList( ParserStrategy ):
        
    ## Class variables
    #  ---------------
    #
    # Headers
    HEADER_HGNC_ID = 'HGNC ID'
    HEADER_CHROMOSOME = 'Chromosome'
    HEADER_APPROVED_SYMBOL = 'Approved symbol'
    HEADER_ALIAS_SYMBOL = 'Alias symbol'
    HEADER_PREVIOUS_SYMBOL = 'Previous symbol'
    HEADER_ENSEMBL_GENE_ID = 'Ensembl gene ID'
    HEADER_NCBI_GENE_ID = 'NCBI gene ID'
    
    HEADER_LIST = [ HEADER_HGNC_ID, HEADER_CHROMOSOME, HEADER_APPROVED_SYMBOL, HEADER_ALIAS_SYMBOL, 
                    HEADER_PREVIOUS_SYMBOL, HEADER_ENSEMBL_GENE_ID, HEADER_NCBI_GENE_ID]
    
    # Constants
    CROSS_REF_NAME = 'HGNCGeneList'
    

    ## Constructor of HGNCGeneList
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
        
        # As this list of genes is used as the reference, first make sure there is not any entry in the Gene and GeneAlias tables
        try:
            gene_content_nb = SQLManagerDS.get_instance().get_session().query( Gene ).count()
            gene_alias_content_nb = SQLManagerDS.get_instance().get_session().query( GeneAlias ).count()
            SQLManagerDS.get_instance().close_session()
        except Exception as e:
            raise DenCellORFException( 'HGNCGeneList.execute(): Request on Gene and GeneAlias tables failed.', e)
            
        if ( gene_content_nb != 0 ) or ( gene_alias_content_nb != 0 ):
            Logger.get_instance().critical( 'HGNCGeneList.execute(): Gene and/or GeneAlias table' +
                                            ' already contains data. Make sure to use a new database' +
                                            ' or overwrite existing database before insertion of this gene list.' +
                                            ' Please see the documentation for more information.' )
        
        
        # Get the content of the file
        self.import_file_content( file_sep = '\t' )
        
        # Check the headers of the file
        try:
            self.check_headers()
        except DuplicateHeaderException as e:
            Logger.get_instance().warning( e.get_message() +
                                           ' Warning code: ' + LogCodes.WARN_HEADER_DUPL + '.' )
                
        # Sort the data frame based on the HGNC ID
        # This allows to get the duplicates following each other
        self.file_content = self.file_content.sort_values( by = HGNCGeneList.HEADER_HGNC_ID, axis = 0 )
        
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
    
        # Parse the content of the file and save it in appropriate objects
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
            
            # Get the HGNC gene ID
            current_id = row[ HGNCGeneList.HEADER_HGNC_ID ]
            
            # Log a warning message if the HGNC ID is missing
            if ParserStrategy.is_empty( current_id ):
                Logger.get_instance().warning( 'HGNC Gene List: The line n°' + str( index ) + 
                                               ' does not contain HGNC ID. Hence, this line will be ignored.' +
                                               ' Warning code: ' + LogCodes.WARN_GENELIST_ID_MISS + '.' )
                
            else:
            
                # Create an empty list to store new aliases of the gene
                aliases = []
                
                # Get the chromosome name
                current_chr = row[ HGNCGeneList.HEADER_CHROMOSOME ]

                # Genes located on both chromosomes X and Y are registered as located 
                # on "X and Y" in this file, change this into 'X|Y'.
                current_chr = self.initialize_chromosome_name( current_chr )
                if ( current_chr == 'X and Y' ):
                    current_chr = Constants.CHROMOSOME_NAME_XY
                
                # A new Gene object is created only if the symbol of the current entry does not match
                # with the symbol of the previous one. This allow to identify duplicates.
                if ( current_id != previous_id ):
                    # Create a new Gene entry
                      # Symbol and chromosome names from HGNC are used to create new gene entries
                    gene = Gene( gene_id = current_id,
                                 chromosome = current_chr )
                    objects_to_insert.append( gene )
                    
                    # (Re-)initialize a variable to store all aliases for this gene
                    all_aliases = []
                    
                    # (Re-)initialize a variable to keep record of all approved symbols for this gene
                    approved_symbols = []
                    
                    # Register the HGNC ID as one of the aliases of the gene
                    aliases = [ current_id ]
                    
                    # Add the approved symbol to the aliases of the gene
                    # The approved symbol is add both "bulk" and with a prefix for easier identification
                    app_symbol = row[ HGNCGeneList.HEADER_APPROVED_SYMBOL ]
                    aliases.append( Constants.ALIAS_OFF_PREFIX + app_symbol )
                    aliases.append( app_symbol )
                    all_aliases.append( app_symbol )
                    approved_symbols.append( app_symbol )
                                    
                    # Keep record of this new association gene ID - approved symbol
                    #    NB: This will allow to check later if this approved symbol is not associated with 
                    #        other HGNC IDs. In such case, a GeneRef warning will be logged prior to data 
                    #        insertion for all the approved symbols associated with several gene IDs.
                    existing_app_symbol = all_prev_app_symbols.get( app_symbol )
                    if existing_app_symbol:
                        existing_app_symbol.append( current_id )
                    else:
                        all_prev_app_symbols[ app_symbol ] = [ current_id ]
                
                
                # Else, if the gene ID is the same as the previous one, check the chromosome 
                # and approved symbols are the same.
                else:
                    # Log a critical error if the same HGNC ID is used for genes on different chromosomes
                    if current_chr != previous_chr:
                        Logger.get_instance().critical( 'HGNCGeneList.execute(): Two distinct locations have' +
                                                        ' been found for the gene with ID: "' + str(current_id) + 
                                                        '". Found on chromosomes: ' + str(previous_chr) + 
                                                        ' and ' + str(current_chr) +
                                                        '. Please see the documentation for more information.')
                    
                    app_symbol = row[HGNCGeneList.HEADER_APPROVED_SYMBOL]
                    # Log a GeneRef warning if the same HGNC has several approved gene symbols
                    # and add this new approved gene symbol to the list of aliases
                    if ( app_symbol not in approved_symbols ):
                        if ( len(approved_symbols) == 1 ):
                            # Log a warning for the first approved symbol
                            GeneRefLogger.get_instance().crossref_warning( 'HGNC Gene list: The gene with HGNC ID: ' + 
                                                                           current_id + ' has been found associated with' +
                                                                           ' several approved symbols. New approved symbol:' +
                                                                           approved_symbols[0] + '.' )
                        # Log a warning for the new approved symbol
                        GeneRefLogger.get_instance().crossref_warning( 'HGNC Gene list: A new approved symbol: ' + 
                                                                       app_symbol + ' has been found associated with' +
                                                                       ' the gene with HGNC ID: ' + current_id + '.')
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
                  # Add the alias and the previous official symbol
                if ( ( not ParserStrategy.is_empty( row[ HGNCGeneList.HEADER_ALIAS_SYMBOL ] ) ) 
                     and ( row[ HGNCGeneList.HEADER_ALIAS_SYMBOL ] not in all_aliases ) ):
                    aliases.append( row[ HGNCGeneList.HEADER_ALIAS_SYMBOL ] )
                    all_aliases.append( row[ HGNCGeneList.HEADER_ALIAS_SYMBOL ] )
                
                if ( ( not ParserStrategy.is_empty( row[ HGNCGeneList.HEADER_PREVIOUS_SYMBOL ] ) )  
                     and ( row[ HGNCGeneList.HEADER_PREVIOUS_SYMBOL ] not in all_aliases ) ):
                    aliases.append( row[ HGNCGeneList.HEADER_PREVIOUS_SYMBOL ] )
                    all_aliases.append( row[ HGNCGeneList.HEADER_PREVIOUS_SYMBOL ] )
                
                  # Add the Ensembl gene ID
                if ( ( not ParserStrategy.is_empty(row[ HGNCGeneList.HEADER_ENSEMBL_GENE_ID ] ) ) 
                     and ( row[ HGNCGeneList.HEADER_ENSEMBL_GENE_ID ] not in all_aliases ) ):
                    aliases.append( row[ HGNCGeneList.HEADER_ENSEMBL_GENE_ID ] )
                    all_aliases.append( row[ HGNCGeneList.HEADER_ENSEMBL_GENE_ID ] )
                
                  # Add a prefix to the NCBI ID and add it as an alias of the gene
                if ( not ParserStrategy.is_empty( row[ HGNCGeneList.HEADER_NCBI_GENE_ID ] ) ):
                    row[ HGNCGeneList.HEADER_NCBI_GENE_ID ] =  'NCBI:' + row[ HGNCGeneList.HEADER_NCBI_GENE_ID ]
                    if ( row[ HGNCGeneList.HEADER_NCBI_GENE_ID ] not in all_aliases ):
                        aliases.append( row[ HGNCGeneList.HEADER_NCBI_GENE_ID ] )
                        all_aliases.append( row[ HGNCGeneList.HEADER_NCBI_GENE_ID ] )
                
                # Create the alias objects corresponding to new aliases and add them to the list of objects to insert
                for alias in aliases:
                    if ( alias not in Constants.EMPTY_VALUES ):
                        gene_alias = GeneAlias( gene_id = gene.gene_id,
                                                alias = alias, 
                                                crossref = HGNCGeneList.CROSS_REF_NAME )
                        objects_to_insert.append( gene_alias )
                            
                # Store the ID and chromosome of the current gene for the next iteration
                previous_id = current_id
                previous_chr = current_chr
                
                                
        # Log a CrossRef warning for all approved symbols that has been found associated with
        # several HGNC gene IDs.        
        for app_symbol in all_prev_app_symbols.keys():
            if ( len( all_prev_app_symbols[ app_symbol ] ) != 1 ):
                GeneRefLogger.get_instance().crossref_warning( 'HGNC Gene List: The approved symbol ' + app_symbol +
                                                               ' has been found associated with the following HGNC gene IDs: ' +
                                                               ', '.join( all_prev_app_symbols[ app_symbol ] ) )
    
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'HGNCGeneList.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
        
        return objects_to_insert
