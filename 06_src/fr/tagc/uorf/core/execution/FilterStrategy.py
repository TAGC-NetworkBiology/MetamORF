# -*- coding: utf-8 -*-

import ConfigParser
import os

import pandas as pd


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql.SQLManagerFILT import SQLManagerFILT
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## FilterStrategy
#  ==============
#
# This class is a strategy that aims to create a FILT database by copying all the 
# information of the PRO database related to a provided set of genes or related to
# a particular cell context.
#
class FilterStrategy( object ):

    ## Constructor of FilterStrategy
    #  -----------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - gene_list: String - The path to the gene list file.
    #     - cell_context: List - The list of cellular contexts on which perform the filtering.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    # 
    def __init__( self ):

        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none = True )
            
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
    # @throw DenCellORFException: When expected filter section may not be found in the config file.
    # @throw DenCellORFException: When there is no strategy of filtering provided.
    # @throw DenCellORFException: When there are several strategies of filtering provided.
    # @throw DenCellORFException: When the type of filtering provided is not allowed 
    #                             (i.e. neither 'intersection' nor 'union').
    # @throw DenCellORFException: When a list of genes has been provided to perform the filtering 
    #                             and the type has been set to 'intersection'..
    #
    def parse_config( self ):
        
        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
        
        # Check the filter section is well provided in the config file
        if config.has_section( Constants.CONFIG_SECTION_FILTER ):
            
            self.selected_strat_count = 0
            
            # Get the type of filtering to use (either union or intersection)
            # By default, the type union is selected, as the queries writen for this 
            # type could be performed is there is one single element in the list.
            if config.has_option( Constants.CONFIG_SECTION_FILTER, Constants.CONFIG_SECTION_FILTER_ITEM_TYPE ):
                self.filt_type = config.get( Constants.CONFIG_SECTION_FILTER, 
                                             Constants.CONFIG_SECTION_FILTER_ITEM_TYPE )
                if( self.filt_type not in [ Constants.FILTER_INTERSECTION, Constants.FILTER_UNION ] ):
                    raise DenCellORFException( 'The filtering type provided (' + str( self.filt_type ) +
                                               ') is not allowed. You need to select either ' + 
                                               Constants.FILTER_INTERSECTION + ' or ' + Constants.FILTER_UNION + 
                                               '. Please see the documentation for more information.' )
            else:
                self.filt_type = Constants.FILTER_UNION
                Logger.get_instance().debug( 'As there was no filtering type provided in the config file,' +
                                             ' the filtering strategy will be run using the ' + 
                                             Constants.FILTER_UNION + ' parameter.' )
            
            # Get the path to the file containing the gene list
            if config.has_option( Constants.CONFIG_SECTION_FILTER, Constants.CONFIG_SECTION_FILTER_ITEM_GENE_LIST ):
                self.selected_strat_count += 1
                self.gene_list = config.get( Constants.CONFIG_SECTION_FILTER, 
                                             Constants.CONFIG_SECTION_FILTER_ITEM_GENE_LIST )
            else:
                self.gene_list = None
                
                
            # Get the list of cell contexts to use to filter the PRO database
            if config.has_option( Constants.CONFIG_SECTION_FILTER, Constants.CONFIG_SECTION_FILTER_ITEM_CELL_CONTEXT ):
                self.selected_strat_count += 1
                self.cell_context = config.get( Constants.CONFIG_SECTION_FILTER, 
                                                Constants.CONFIG_SECTION_FILTER_ITEM_CELL_CONTEXT )
                # Replace the eventual spaces nears to the comma and convert the string as a list
                self.cell_context = self.cell_context.replace( ', ', ',' ).replace( ' ,', ',' ).split( ',' )
                
            else:
                self.cell_context = None
                
                
            # Get the list of ORF categories to use to filter the PRO database
            if config.has_option( Constants.CONFIG_SECTION_FILTER, Constants.CONFIG_SECTION_FILTER_ITEM_ORF_CAT ):
                self.selected_strat_count += 1
                self.orf_categories = config.get( Constants.CONFIG_SECTION_FILTER, 
                                                  Constants.CONFIG_SECTION_FILTER_ITEM_ORF_CAT )
                # Replace the eventual spaces nears to the comma and convert the string as a list
                self.orf_categories = self.orf_categories.replace( ', ', ',' ).replace( ' ,', ',' ).split( ',' )
                
            else:
                self.orf_categories = None
                
                
            # Get the list of ORF annotations to use to filter the PRO database
            if config.has_option( Constants.CONFIG_SECTION_FILTER, Constants.CONFIG_SECTION_FILTER_ITEM_ORF_ANNOT ):
                self.selected_strat_count += 1
                self.orf_annotations = config.get( Constants.CONFIG_SECTION_FILTER, 
                                                   Constants.CONFIG_SECTION_FILTER_ITEM_ORF_ANNOT )
                # Replace the eventual spaces nears to the comma and convert the string as a list
                self.orf_annotations = self.orf_annotations.replace( ', ', ',' ).replace( ' ,', ',' ).split( ',' )
                
            else:
                self.orf_annotations = None
            
            
            # If there is no gene list and no cell context provided, raise an exception
            if ( self.selected_strat_count == 0 ):
                raise DenCellORFException( 'FilterStrategy: A strategy of filtering has to be provided,' +
                                           ' i.e. the path to a file containing a gene list (item ' + 
                                           Constants.CONFIG_SECTION_FILTER_ITEM_GENE_LIST + '),' +
                                           ' or a comma-separated list of cellular context (item ' + 
                                           Constants.CONFIG_SECTION_FILTER_ITEM_CELL_CONTEXT + '),' + 
                                           ' or a comma-separated list of ORF categories (item ' +
                                           Constants.CONFIG_SECTION_FILTER_ITEM_ORF_CAT + 
                                           ') has to be provided.'  )
            
            # If several strategies of filtering have been selected, raise an exception
            if ( self.selected_strat_count > 1 ):
                # NB: This strategy has been built with the idea that only one strategy of filtering will 
                #     be applied at a time. If necessary it may be easily updated to use both strategies 
                #     of filtering. To do so, the easiest way would be to use an intermediate database 
                #     containing the filtered data from the first list query, and to make the second list 
                #     of queries on this intermediate database to build the final one. This would probably
                #     improve the time of computation compared with making the two list of queries at the
                #     same time.
                raise DenCellORFException( 'FilterStrategy: Several strategies of filtering cannot be' +
                                           ' provided at the same time. Please provide only one of the' +
                                           ' following items in the config file: ' + 
                                           Constants.CONFIG_SECTION_FILTER_ITEM_GENE_LIST + 
                                           ', ' + Constants.CONFIG_SECTION_FILTER_ITEM_CELL_CONTEXT + 
                                           ', ' + Constants.CONFIG_SECTION_FILTER_ITEM_ORF_CAT +
                                           ', ' + Constants.CONFIG_SECTION_FILTER_ITEM_ORF_ANNOT +
                                           '. Please see the documentation for more information.' )
                
            # If a list of gene has been provided, the filtering type should 
            # necessarily be set to 'union'. If this is not the case, then 
            # raise an exception.
            if ( self.gene_list 
                 and ( self.filt_type == Constants.FILTER_INTERSECTION ) ):
                raise DenCellORFException( 'A list of genes has been provided for the filtering whilst' +
                                           ' the type of filtering has been set to ' +  
                                           Constants.FILTER_INTERSECTION + 
                                           '. This is not allowed as, according to the database' +
                                           ' relationships a transcript can only belong to one unique gene' +
                                           ' (even if it could obviously be related to several aliases' +
                                           ' which are themselves related to the same single gene).' +
                                           ' Please see the documentation for more information.' )
                
        else:
            raise DenCellORFException( 'FilterStrategy: The ' + Constants.CONFIG_SECTION_FILTER + 
                                       ' section has to be provided in the config file.' )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete the FILT database filtering information in the PRO database.
    #
    # @throw DenCellORFException: When the insertion of UTRNABiotypeCatalog objects fails.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check both PRO and FILT databases are reachable and use
        # the appropriate models prior to the merging of data.
        Logger.get_instance().info( 'Checking the PRO and FILT databases prior' +
                                    ' to filter the PRO database...' )
        try:
            DatabaseCheckStrategy().execute()
        except DenCellORFException as e:
            raise DenCellORFException( 'An error occurred whilst checking the database prior to' +
                                       ' compute missing information.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        Logger.get_instance().info( 'Starting to perform the queries to copy the appropriate' +
                                    ' information in the FILT database...' )
        
        # Copy the content of the PROMetadata table in the FILT table
        query_metadata = SQLManagerPRO.get_instance().get_session().query( PROMetadata )
        self.PRO_to_FILT( query_metadata )
        
        # Filter using the gene list
        if self.gene_list:
            self.gene_list_filter()
        
        # Filter using the list of cell contexts
        elif self.cell_context:
            self.cell_context_filter()
        
        # Filter using the list of ORF categories
        elif self.orf_categories:
            self.orf_categories_filter()
            
        # Filter using the list of ORF annotations
        elif self.orf_annotations:
            self.orf_annotations_filter()
        
            
        # Fill in the UTRNABiotypeCatalog with unique biotypes from the Transcript entries
        all_uniq_rna_biotype = SQLManagerFILT.get_instance().get_session().query( Transcript.rna_biotype ).filter( Transcript.rna_biotype != None ).distinct().all()
        uniq_rna_biotype_list = GeneralUtil.query_result_to_list( all_uniq_rna_biotype )
        
        objects_to_insert = []
        for rna_biotype in uniq_rna_biotype_list:
            utrnabiotypecatalog = UTRNABiotypeCatalog( biotype = rna_biotype )
            objects_to_insert.append( utrnabiotypecatalog )
                
        try:
            SQLManagerFILT.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert,
                                                              process = 'computation of UTRNABiotypeCatalog entries' )
        except Exception as e:
            raise DenCellORFException( 'FilterStrategy().execute(): An error occurred trying to insert' +
                                       ' the biotypes in the UTRNABiotypeCatalog table.', e )        
    
        SQLManagerFILT.get_instance().close_session()
         
    
    
    # ===============================================================================
    # Methods related to gene list filtering
    # ===============================================================================
    
    ## gene_list_filter
    #  ----------------
    #
    # This methods allows to get the gene list from the file and to filter the PRO database
    # information to insert it into the FILT database.
    #
    # @throw DenCellORFException: When the format of the gene list provided is unexpected 
    #                            (has to be provided as 1-line or 1-column csv file).
    # 
    def gene_list_filter( self ):
        
        # Import the gene list
        file_content = pd.read_csv( self.gene_list, 
                                    sep = ',', 
                                    dtype = 'str', 
                                    encoding = 'utf-8', 
                                    header = None )
          
        # Identify if the list is provided as a line or a column and store the content in a list object
        # Get the number of rows and columns
        nrows = file_content.shape[ 0 ]
        ncols = file_content.shape[ 1 ]
        
        if ( ( nrows > 1 ) and ( ncols > 1 ) ):
            raise DenCellORFException( 'The gene list has to be provided either as a column' +
                                       ' or as a comma-separated values list.' )
        
        elif ( nrows > 1 ):
            # Convert the column as a list    
            gene_list = file_content.iloc[:,0].tolist()
        
        elif ( ncols > 1 ):
            # Convert the column as a list    
            gene_list = file_content.iloc[0,:].tolist()
        
        # Get the list of queries to use to insert data
        queries_list = self.get_gene_list_queries( gene_list )
        
        # Proceed to the insertion
        self.process_queries( queries_list )
    
    
    
    ## get_gene_list_queries
    #  ---------------------
    #
    # This methods allows to generate the list of appropriate queries to 
    # be used to get the content of the PRO database information using the 
    # selected ORF annotations and necessary to perform the insertion in 
    # the FILT database.
    #
    # @param gene_list: List - The list of gene symbols, aliases or IDs 
    #                          to use to filter the database.
    # 
    # @return lists_to_insert: List - The list of queries to be used in order to filter
    #                                 the content of the PRO database to insert in the 
    #                                 FILT database.
    # 
    def get_gene_list_queries( self, gene_list ):
        
        # NB: In order to facilitate the query on the PRO database, 
        #     the filters are created by concatenation
        filter_common = ''
        
        ## Gene and GeneAlias
        #  ------------------
        # Get the IDs of all the PROGene entries associated 
        # at least with one of the aliases.
        all_gene_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                            PROGeneAlias.gene_id  
                                                                        ).filter( 
                                                                                    PROGeneAlias.alias.in_( gene_list )
                                                                                ).distinct().all()
        
        # Get all the PROGene entries related to these ORFTranscriptAsso IDs
        filter_common = '.filter( PROGene.gene_id.in_(' + str( all_gene_ids ) + ') )' + filter_common
        all_gene = self.query_PRO( 'PROGene', filter_common )
        
        # Get all the PROGeneAlias entries related to the PROGene entries selected
        filter_genealias = '.filter( PROGeneAlias.gene_id == PROGene.gene_id )' + filter_common
        all_genealias = self.query_PRO( 'PROGeneAlias', filter_genealias )
        
        
        ## Processed
        #  ---------
        
        # Get the Transcript entries
        filter_common = '.filter( Transcript.gene_id == PROGene.gene_id )' + filter_common
        all_transcript = self.query_PRO( 'Transcript', filter_common )
        
        # Get the TranscriptDSAsso entries
        filter_transcriptdsasso = '.filter( TranscriptDSAsso.transcript_id == Transcript.id )' + filter_common
        all_transcriptds_asso = self.query_PRO( 'TranscriptDSAsso', filter_transcriptdsasso )
        
        
        # Get the ORFTranscriptAsso entries
        filter_ota = '.filter( ORFTranscriptAsso.transcript_id == Transcript.id )' + filter_common
        all_orftranscriptasso = self.query_PRO( 'ORFTranscriptAsso', filter_ota )
        
        # Get the ORFTranscriptAssoDSAsso entries
        filter_otadsasso = '.filter( ORFTranscriptAssoDSAsso.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_otadsasso = self.query_PRO( 'ORFTranscriptAssoDSAsso', filter_otadsasso )
        
        
        # Get the ORF entries
        filter_orf = '.filter( ORF.id == ORFTranscriptAsso.orf_id )' + filter_ota
        all_orf = self.query_PRO( 'ORF', filter_orf )
        
        # Get the ORFDSAsso entries
        filter_orfdsasso = '.filter( ORFDSAsso.orf_id == ORF.id )' + filter_orf
        all_orfdsasso = self.query_PRO( 'ORFDSAsso', filter_orfdsasso )
        
            
        ## Category, Cell context and FLOSS
        #  --------------------------------
        
        # Get the ORFCategory entries
        filter_orfcat = '.filter( ORFCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_orfcategory = self.query_PRO( 'ORFCategory', filter_orfcat )
        
        # Get the ORFCategoryCatalog entries
        filter_orfcatcatalog = '.filter( ORFCategoryCatalog.category == ORFCategory.orf_category )' + filter_orfcat
        all_orfcatcatalog = self.query_PRO( 'ORFCategoryCatalog', filter_orfcatcatalog )
        
        
        # Get the CellContext entries
        filter_cellcontext = '.filter( CellContext.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_cellcontext = self.query_PRO( 'CellContext', filter_cellcontext )
        
        # Get the CellContextCatalog entries
        filter_cellcontextcatalog = '.filter( CellContextCatalog.context == CellContext.cell_context )' + filter_cellcontext
        all_cellcontextcatalog = self.query_PRO( 'CellContextCatalog', filter_cellcontextcatalog )

        
        # Get the ProvidedCategory entries
        filter_providedcat = '.filter( ProvidedCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_providedcat = self.query_PRO( 'ProvidedCategory', filter_providedcat )
        
        # Get the ProvidedCategoryCatalog entries
        filter_providedcatcatalog = '.filter( ProvidedCategoryCatalog.category == ProvidedCategory.provided_category )' + filter_providedcat
        all_providedcatcatalog = self.query_PRO( 'ProvidedCategoryCatalog', filter_providedcatcatalog )

        
        # Get the FLOSSClass entries
        filter_floss = '.filter( FLOSSClass.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_floss = self.query_PRO( 'FLOSSClass', filter_floss )
        
        # Get the FLOSSClassCatalog entries
        filter_flosscatalog = '.filter( FLOSSClassCatalog.floss_class == FLOSSClass.floss_class )' + filter_floss
        all_flosscatalog = self.query_PRO( 'FLOSSClassCatalog', filter_flosscatalog )
        
        
        # Get the ORFAnnotation entries
        filter_orfannotation = '.filter( ORFAnnotation.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_ota
        all_orfannotation = self.query_PRO( 'ORFAnnotation', filter_orfannotation )
        
        # Get the ORFAnnotationCatalog entries
        filter_orfannotationcatalog = '.filter( ORFAnnotationCatalog.annotation == ORFAnnotation.orf_annotation )' + filter_orfannotation
        all_orfannotationcatalog = self.query_PRO( 'ORFAnnotationCatalog', filter_orfannotationcatalog )

        
        # Return the list of queries containing all the data related to the gene symbol / ID / name
        # previously collected from the PRO database 
        lists_to_insert = [ all_gene, all_genealias,
                            all_orf, all_orfdsasso, 
                            all_transcript, all_transcriptds_asso,
                            all_orftranscriptasso, all_otadsasso,
                            all_cellcontextcatalog, all_cellcontext, 
                            all_providedcatcatalog, all_providedcat,
                            all_flosscatalog, all_floss,
                            all_orfcatcatalog, all_orfcategory,
                            all_orfannotationcatalog, all_orfannotation ]
        
        return lists_to_insert
         
    
    
    # ===============================================================================
    # Methods related to cell context filtering
    # =============================================================================== 
    
    ## cell_context_filter
    #  -------------------
    #
    # This methods allows to filter the PRO database information using the provided 
    # list of cell contexts and to insert it into the FILT database.
    # 
    def cell_context_filter( self ):
        
        # Get the list of queries to use to insert data
        queries_list = self.get_cell_ctxt_queries()
        
        # Proceed to the insertion
        self.process_queries( queries_list )
    
    
    
    ## get_cell_ctxt_queries
    #  ---------------------
    #
    # This methods allows to generate the list of appropriate queries to 
    # be used to get the content of the PRO database information using the 
    # selected cell contexts and necessary to perform the insertion in 
    # the FILT database.
    # 
    # @return lists_to_insert: List - The list of queries to be used in order to filter
    #                                 the content of the PRO database to insert in the 
    #                                 FILT database.
    #
    def get_cell_ctxt_queries( self ):
        
        # NB: In order to facilitate the query on the PRO database, 
        # the filters are created by concatenation
        filter_common = ''
        
        ## CellContextCatalog and CellContext
        #  ----------------------------------                                                                     
        # If there is one single entry in the list of cell contexts or if the filtering
        # type has been set on 'union', then get the IDs of all the ORFTranscriptAsso 
        # entries associated at least with one of the cell contexts.
        if ( self.filt_type == Constants.FILTER_UNION ):
            all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                CellContext.orftranscriptasso_id 
                                                                            ).filter( 
                                                                                        CellContext.cell_context.in_( self.cell_context )
                                                                                    ).distinct().all()
        
        # Otherwise, get the IDs of the ORFTranscriptAsso entries that have been 
        # associated with ALL the cell contexts of the list.
        else:
            # For each of the context selected, get the list of OTA IDs 
            # related to it, and compute the intersection with the lists
            # get using the contexts already processed.
            all_ota_ids_intersect = set()
            for ctxt in self.cell_context:
                all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    CellContext.orftranscriptasso_id 
                                                                                ).filter( 
                                                                                            CellContext.cell_context == ctxt 
                                                                                        ).distinct().all()
                all_ota_ids = set( GeneralUtil.query_result_to_list( all_ota_ids ) )
                # Get the intersection
                if ( all_ota_ids_intersect ):
                    all_ota_ids_intersect = all_ota_ids.intersection( all_ota_ids_intersect )
                else:
                    all_ota_ids_intersect = all_ota_ids
            
            # Convert the set of OTA IDs associated with all of the categories
            # into a list
            all_ota_ids = list( all_ota_ids_intersect )
        
        # Get all the CellContext entries related to these ORFTranscriptAsso IDs
        filter_common = '.filter( CellContext.orftranscriptasso_id.in_(' + str( all_ota_ids ) + ') )' + filter_common
        all_cellcontext = self.query_PRO( 'CellContext', filter_common )
        
        # Get all the CellContextCatalog entries that have at least one ORF
        # registered in the selected cell contexts
        filter_cellcontextcatalog = '.filter( CellContextCatalog.context == CellContext.cell_context )' + filter_common
        all_cellcontextcatalog = self.query_PRO( 'CellContextCatalog', filter_cellcontextcatalog )
        
        
        ## Processed
        #  ---------
        
        # Get the ORFTranscriptAsso entries
        filter_common = '.filter( ORFTranscriptAsso.id == CellContext.orftranscriptasso_id )' + filter_common
        all_orftranscriptasso = self.query_PRO( 'ORFTranscriptAsso', filter_common )
        
        # Get the ORFTranscriptAssoDSAsso entries
        filter_otadsasso = '.filter( ORFTranscriptAssoDSAsso.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_otadsasso = self.query_PRO( 'ORFTranscriptAssoDSAsso', filter_otadsasso )
        
        
        # Get the ORF entries
        filter_orf = '.filter( ORF.id == ORFTranscriptAsso.orf_id )' + filter_common
        all_orf = self.query_PRO( 'ORF', filter_orf )
        
        # Get the ORFDSAsso entries
        filter_orfdsasso = '.filter( ORFDSAsso.orf_id == ORF.id )' + filter_orf
        all_orfdsasso = self.query_PRO( 'ORFDSAsso', filter_orfdsasso )
        
        
        # Get the Transcript entries
        filter_transcript = '.filter( Transcript.id == ORFTranscriptAsso.transcript_id )' + filter_common
        all_transcript = self.query_PRO( 'Transcript', filter_transcript )
        
        # Get the TranscriptDSAsso entries
        filter_transcriptdsasso = '.filter( TranscriptDSAsso.transcript_id == Transcript.id )' + filter_transcript
        all_transcriptds_asso = self.query_PRO( 'TranscriptDSAsso', filter_transcriptdsasso )
        
        
        ## Gene and GeneAlias
        #  ------------------
        
        # Get the PROGene entries
        filter_gene = '.filter( PROGene.gene_id == Transcript.gene_id )' + filter_transcript
        all_gene = self.query_PRO( 'PROGene', filter_gene )
        
        # Get the PROGeneAlias entries
        filter_genealias = '.filter( PROGeneAlias.gene_id == PROGene.gene_id )' + filter_gene
        all_genealias = self.query_PRO( 'PROGeneAlias', filter_genealias )
        
        
        ## Category, Cell context and FLOSS
        #  --------------------------------
                
        # Get the ProvidedCategory entries
        filter_providedcat = '.filter( ProvidedCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_providedcat = self.query_PRO( 'ProvidedCategory', filter_providedcat )
        
        # Get the ProvidedCategoryCatalog entries
        filter_providedcatcatalog = '.filter( ProvidedCategoryCatalog.category == ProvidedCategory.provided_category )' + filter_providedcat
        all_providedcatcatalog = self.query_PRO( 'ProvidedCategoryCatalog', filter_providedcatcatalog )

        
        # Get the ORFCategory entries
        filter_orfcat = '.filter( ORFCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_orfcategory = self.query_PRO( 'ORFCategory', filter_orfcat )
        
        # Get the ORFCategoryCatalog entries
        filter_orfcategorycatalog = '.filter( ORFCategoryCatalog.category == ORFCategory.orf_category )' + filter_orfcat
        all_orfcategorycatalog = self.query_PRO( 'ORFCategoryCatalog', filter_orfcategorycatalog )

        
        # Get the ORFAnnotation entries
        filter_orfannotation = '.filter( ORFAnnotation.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_orfannotation = self.query_PRO( 'ORFAnnotation', filter_orfannotation )
        
        # Get the ORFAnnotationCatalog entries
        filter_orfannotationcatalog = '.filter( ORFAnnotationCatalog.annotation == ORFAnnotation.orf_annotation )' + filter_orfannotation
        all_orfannotationcatalog = self.query_PRO( 'ORFAnnotationCatalog', filter_orfannotationcatalog )
        
        
        # Get the FLOSSClass entries
        filter_floss = '.filter( FLOSSClass.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_floss = self.query_PRO( 'FLOSSClass', filter_floss )
        
        # Get the FLOSSClassCatalog entries
        filter_flosscatalog = '.filter( FLOSSClassCatalog.floss_class == FLOSSClass.floss_class )' + filter_floss
        all_flosscatalog = self.query_PRO( 'FLOSSClassCatalog', filter_flosscatalog )
        
        
        # Return the list of queries containing all the data related to the cell context 
        # previously collected from the PRO database 
        lists_to_insert = [ all_gene, all_genealias,
                            all_orf, all_orfdsasso, 
                            all_transcript, all_transcriptds_asso,
                            all_orftranscriptasso, all_otadsasso,
                            all_cellcontextcatalog, all_cellcontext,
                            all_providedcatcatalog, all_providedcat,
                            all_orfcategorycatalog, all_orfcategory,
                            all_orfannotationcatalog, all_orfannotation,
                            all_flosscatalog, all_floss ]
        
        return lists_to_insert
         
    
    
    # ===============================================================================
    # Methods related to ORF category filtering
    # =============================================================================== 
    
    ## orf_categories_filter
    #  ---------------------
    #
    # This methods allows to filter the PRO database information using the provided 
    # list of ORF category and to insert it into the FILT database.
    # 
    def orf_categories_filter( self ):
        
        # Get the list of queries to use to insert data
        queries_list = self.get_orf_cat_queries()
        
        # Proceed to the insertion
        self.process_queries( queries_list )
    
    
    
    ## get_orf_cat_queries
    #  -------------------
    #
    # This methods allows to generate the list of appropriate queries to 
    # be used to get the content of the PRO database information using the 
    # selected ORF categories and necessary to perform the insertion in 
    # the FILT database.
    # 
    # @return lists_to_insert: List - The list of queries to be used in order to filter
    #                                 the content of the PRO database to insert in the 
    #                                 FILT database.
    #
    def get_orf_cat_queries( self ):
        
        # NB: In order to facilitate the query on the PRO database, 
        # the filters are created by concatenation
        filter_common = ''
        
        ## ORFCategoryCatalog and ORFCategory
        #  ----------------------------------                                                                               
        # If there is one single entry in the list of categories or if the filtering
        # type has been set on 'union', then get the IDs of all the ORFTranscriptAsso 
        # entries associated at least with one of the categories.
        if ( self.filt_type == Constants.FILTER_UNION ):
            all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                ORFCategory.orftranscriptasso_id 
                                                                            ).filter( 
                                                                                        ORFCategory.orf_category.in_( self.orf_categories )
                                                                                    ).distinct().all()
        
        # Otherwise, get the IDs of the ORFTranscriptAsso entries that have been 
        # associated with ALL the categories of the list.
        else:
            # For each of the category selected, get the list of OTA IDs 
            # related to it, and compute the intersection with the lists
            # get using the categories already processed.
            all_ota_ids_intersect = set()
            for orf_cat in self.orf_categories:
                all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    ORFCategory.orftranscriptasso_id 
                                                                                ).filter( 
                                                                                            ORFCategory.orf_category == orf_cat 
                                                                                        ).distinct().all()
                all_ota_ids = set( GeneralUtil.query_result_to_list( all_ota_ids ) )
                # Get the intersection
                if ( all_ota_ids_intersect ):
                    all_ota_ids_intersect = all_ota_ids.intersection( all_ota_ids_intersect )
                else:
                    all_ota_ids_intersect = all_ota_ids
            
            # Convert the set of OTA IDs associated with all of the categories
            # into a list
            all_ota_ids = list( all_ota_ids_intersect )
        
        # Get all the ORFCategory entries related to these ORFTranscriptAsso IDs
        filter_common = '.filter( ORFCategory.orftranscriptasso_id.in_(' + str( all_ota_ids ) + ') )' + filter_common
        all_orfcategory = self.query_PRO( 'ORFCategory', filter_common )
        
        # Get all the ORFCategoryCatalog entries that have at least one ORF
        # registered in the selected category
        filter_orfcategorycatalog = '.filter( ORFCategoryCatalog.category == ORFCategory.orf_category )' + filter_common
        all_orfcategorycatalog = self.query_PRO( 'ORFCategoryCatalog', filter_orfcategorycatalog )
                      
        
        ## Processed
        #  ---------
        
        # Get the ORFTranscriptAsso entries
        filter_common = '.filter( ORFTranscriptAsso.id == ORFCategory.orftranscriptasso_id )' + filter_common
        all_orftranscriptasso = self.query_PRO( 'ORFTranscriptAsso', filter_common )
        
        # Get the ORFTranscriptAssoDSAsso entries
        filter_otadsasso = '.filter( ORFTranscriptAssoDSAsso.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_otadsasso = self.query_PRO( 'ORFTranscriptAssoDSAsso', filter_otadsasso )
        
        
        # Get the ORF entries
        filter_orf = '.filter( ORF.id == ORFTranscriptAsso.orf_id )' + filter_common
        all_orf = self.query_PRO( 'ORF', filter_orf )
        
        # Get the ORFDSAsso entries
        filter_orfdsasso = '.filter( ORFDSAsso.orf_id == ORF.id )' + filter_orf
        all_orfdsasso = self.query_PRO( 'ORFDSAsso', filter_orfdsasso )
        
        
        # Get the Transcript entries
        filter_transcript = '.filter( Transcript.id == ORFTranscriptAsso.transcript_id )' + filter_common
        all_transcript = self.query_PRO( 'Transcript', filter_transcript )
        
        # Get the TranscriptDSAsso entries
        filter_transcriptdsasso = '.filter( TranscriptDSAsso.transcript_id == Transcript.id )' + filter_transcript
        all_transcriptds_asso = self.query_PRO( 'TranscriptDSAsso', filter_transcriptdsasso )
        
        
        ## Gene and GeneAlias
        #  ------------------
        
        # Get the PROGene entries
        filter_gene = '.filter( PROGene.gene_id == Transcript.gene_id )' + filter_transcript
        all_gene = self.query_PRO( 'PROGene', filter_gene )
        
        # Get the PROGeneAlias entries
        filter_genealias = '.filter( PROGeneAlias.gene_id == PROGene.gene_id )' + filter_gene
        all_genealias = self.query_PRO( 'PROGeneAlias', filter_genealias )
        
        
        ## Category, Cell context and FLOSS
        #  --------------------------------
                                
        # Get the CellContext entries
        filter_cellcontext = '.filter( CellContext.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_cellcontext = self.query_PRO( 'CellContext', filter_cellcontext )
        
        # Get the CellContextCatalog entries
        filter_cellcontextcatalog = '.filter( CellContextCatalog.context == CellContext.cell_context )' + filter_cellcontext
        all_cellcontextcatalog = self.query_PRO( 'CellContextCatalog', filter_cellcontextcatalog )
        
                
        # Get the ProvidedCategory entries
        filter_providedcat = '.filter( ProvidedCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_providedcat = self.query_PRO( 'ProvidedCategory', filter_providedcat )
        
        # Get the ProvidedCategoryCatalog entries
        filter_providedcatcatalog = '.filter( ProvidedCategoryCatalog.category == ProvidedCategory.provided_category )' + filter_providedcat
        all_providedcatcatalog = self.query_PRO( 'ProvidedCategoryCatalog', filter_providedcatcatalog )

        
        # Get the ORFAnnotation entries
        filter_orfannotation = '.filter( ORFAnnotation.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_orfannotation = self.query_PRO( 'ORFAnnotation', filter_orfannotation )
        
        # Get the ORFAnnotationCatalog entries
        filter_orfannotationcatalog = '.filter( ORFAnnotationCatalog.annotation == ORFAnnotation.orf_annotation )' + filter_orfannotation
        all_orfannotationcatalog = self.query_PRO( 'ORFAnnotationCatalog', filter_orfannotationcatalog )
        
        
        # Get the FLOSSClass entries
        filter_floss = '.filter( FLOSSClass.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_floss = self.query_PRO( 'FLOSSClass', filter_floss )
        
        # Get the FLOSSClassCatalog entries
        filter_flosscatalog = '.filter( FLOSSClassCatalog.floss_class == FLOSSClass.floss_class )' + filter_floss
        all_flosscatalog = self.query_PRO( 'FLOSSClassCatalog', filter_flosscatalog )
        
        
        # Return the list of queries containing all the data related to the ORF category
        # previously collected from the PRO database 
        lists_to_insert = [ all_gene, all_genealias,
                            all_orf, all_orfdsasso,
                            all_transcript, all_transcriptds_asso, 
                            all_orftranscriptasso, all_otadsasso,
                            all_orfcategorycatalog, all_orfcategory,
                            all_cellcontextcatalog, all_cellcontext,
                            all_providedcatcatalog, all_providedcat, 
                            all_orfannotationcatalog, all_orfannotation,
                            all_flosscatalog, all_floss ]
                
        return lists_to_insert
         
    
    
    # ===============================================================================
    # Methods related to ORF annotation filtering
    # ===============================================================================
        
    ## orf_annotations_filter
    #  ----------------------
    #
    # This methods allows to filter the PRO database information using the provided 
    # list of ORF annotations and to insert it into the FILT database.
    # 
    def orf_annotations_filter( self ):
        
        # Get the list of queries to use to insert data
        queries_list = self.get_orf_annot_queries()
        
        # Proceed to the insertion
        self.process_queries( queries_list )
    
    
    
    ## get_orf_annot_queries
    #  ---------------------
    #
    # This methods allows to generate the list of appropriate queries to 
    # be used to get the content of the PRO database information using the 
    # selected ORF annotations and necessary to perform the insertion in 
    # the FILT database.
    # 
    # @return lists_to_insert: List - The list of queries to be used in order to filter
    #                                 the content of the PRO database to insert in the 
    #                                 FILT database.
    #
    def get_orf_annot_queries( self ):
        
        # NB: In order to facilitate the query on the PRO database, 
        # the filters are created by concatenation
        filter_common = ''
        
        
        ## ORFAnnotationCatalog and ORFAnnotation
        #  --------------------------------------                                                                        
        # If there is one single entry in the list of annotations or if the filtering
        # type has been set on 'union', then get the IDs of all the ORFTranscriptAsso 
        # entries associated at least with one of the annotation.
        if ( self.filt_type == Constants.FILTER_UNION ):
            all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                ORFAnnotation.orftranscriptasso_id 
                                                                            ).filter( 
                                                                                        ORFAnnotation.orf_annotation.in_( self.orf_annotations )
                                                                                    ).distinct().all()
        
        # Otherwise, get the IDs of the ORFTranscriptAsso entries that have been 
        # associated with ALL the annotations of the list.
        else:
            # For each of the annotation selected, get the list of OTA IDs 
            # related to it, and compute the intersection with the lists
            # get using the annotations already processed.
            all_ota_ids_intersect = set()
            for orf_annot in self.orf_annotations:
                all_ota_ids = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    ORFAnnotation.orftranscriptasso_id 
                                                                                ).filter( 
                                                                                            ORFAnnotation.orf_annotation == orf_annot 
                                                                                        ).distinct().all()
                all_ota_ids = set( GeneralUtil.query_result_to_list( all_ota_ids ) )
                # Get the intersection
                if ( all_ota_ids_intersect ):
                    all_ota_ids_intersect = all_ota_ids.intersection( all_ota_ids_intersect )
                else:
                    all_ota_ids_intersect = all_ota_ids
            
            # Convert the set of OTA IDs associated with all 
            # of the annotations into a list
            all_ota_ids = list( all_ota_ids_intersect )
        
        # Get all the ORFAnnotation entries related to these ORFTranscriptAsso IDs
        filter_common = '.filter( ORFAnnotation.orftranscriptasso_id.in_(' + str( all_ota_ids ) + ') )' + filter_common
        all_orfannotation = self.query_PRO( 'ORFAnnotation', filter_common )
        
        # Get all the ORFAnnotationCatalog entries that have at least one ORF
        # registered in the selected annotation
        filter_orfannotationcatalog = '.filter( ORFAnnotationCatalog.annotation == ORFAnnotation.orf_annotation )' + filter_common
        all_orfannotationcatalog = self.query_PRO( 'ORFAnnotationCatalog', filter_orfannotationcatalog )
                
        
        ## Processed
        #  ---------
        
        # Get the ORFTranscriptAsso entries
        filter_common = '.filter( ORFTranscriptAsso.id == ORFAnnotation.orftranscriptasso_id )' + filter_common
        all_orftranscriptasso = self.query_PRO( 'ORFTranscriptAsso', filter_common )
        
        # Get the ORFTranscriptAssoDSAsso entries
        filter_otadsasso = '.filter( ORFTranscriptAssoDSAsso.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_otadsasso = self.query_PRO( 'ORFTranscriptAssoDSAsso', filter_otadsasso )
        
        
        # Get the ORF entries
        filter_orf = '.filter( ORF.id == ORFTranscriptAsso.orf_id )' + filter_common
        all_orf = self.query_PRO( 'ORF', filter_orf )
        
        # Get the ORFDSAsso entries
        filter_orfdsasso = '.filter( ORFDSAsso.orf_id == ORF.id )' + filter_orf
        all_orfdsasso = self.query_PRO( 'ORFDSAsso', filter_orfdsasso )
        
        
        # Get the Transcript entries
        filter_transcript = '.filter( Transcript.id == ORFTranscriptAsso.transcript_id )' + filter_common
        all_transcript = self.query_PRO( 'Transcript', filter_transcript )
        
        # Get the TranscriptDSAsso entries
        filter_transcriptdsasso = '.filter( TranscriptDSAsso.transcript_id == Transcript.id )' + filter_transcript
        all_transcriptds_asso = self.query_PRO( 'TranscriptDSAsso', filter_transcriptdsasso )
        
        
        ## Gene and GeneAlias
        #  ------------------
        
        # Get the PROGene entries
        filter_gene = '.filter( PROGene.gene_id == Transcript.gene_id )' + filter_transcript
        all_gene = self.query_PRO( 'PROGene', filter_gene )
        
        # Get the PROGeneAlias entries
        filter_genealias = '.filter( PROGeneAlias.gene_id == PROGene.gene_id )' + filter_gene
        all_genealias = self.query_PRO( 'PROGeneAlias', filter_genealias )
        
        
        ## Category, Cell context and FLOSS
        #  --------------------------------
                                
        # Get the CellContext entries
        filter_cellcontext = '.filter( CellContext.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_cellcontext = self.query_PRO( 'CellContext', filter_cellcontext )
        
        # Get the CellContextCatalog entries
        filter_cellcontextcatalog = '.filter( CellContextCatalog.context == CellContext.cell_context )' + filter_cellcontext
        all_cellcontextcatalog = self.query_PRO( 'CellContextCatalog', filter_cellcontextcatalog )
        
                
        # Get the ProvidedCategory entries
        filter_providedcat = '.filter( ProvidedCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_providedcat = self.query_PRO( 'ProvidedCategory', filter_providedcat )
        
        # Get the ProvidedCategoryCatalog entries
        filter_providedcatcatalog = '.filter( ProvidedCategoryCatalog.category == ProvidedCategory.provided_category )' + filter_providedcat
        all_providedcatcatalog = self.query_PRO( 'ProvidedCategoryCatalog', filter_providedcatcatalog )
        
                
        # Get the ORFCategory entries
        filter_orfcategory = '.filter( ORFCategory.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_orfcategory = self.query_PRO( 'ORFCategory', filter_orfcategory )
        
        # Get the ORFCategoryCatalog entries
        filter_orfcategorycatalog = '.filter( ORFCategoryCatalog.category == ORFCategory.orf_category )' + filter_orfcategory
        all_orfcategorycatalog = self.query_PRO( 'ORFCategoryCatalog', filter_orfcategorycatalog )
        
        
        # Get the FLOSSClass entries
        filter_floss = '.filter( FLOSSClass.orftranscriptasso_id == ORFTranscriptAsso.id )' + filter_common
        all_floss = self.query_PRO( 'FLOSSClass', filter_floss )
        
        # Get the FLOSSClassCatalog entries
        filter_flosscatalog = '.filter( FLOSSClassCatalog.floss_class == FLOSSClass.floss_class )' + filter_floss
        all_flosscatalog = self.query_PRO( 'FLOSSClassCatalog', filter_flosscatalog )
        
        
        # Return the list of queries containing all the data related to the ORF annotation
        # previously collected from the PRO database 
        lists_to_insert = [ all_gene, all_genealias,
                            all_orf, all_orfdsasso, 
                            all_transcript, all_transcriptds_asso,
                            all_orftranscriptasso, all_otadsasso,
                            all_orfannotationcatalog, all_orfannotation,
                            all_cellcontextcatalog, all_cellcontext,
                            all_providedcatcatalog, all_providedcat, 
                            all_orfcategorycatalog, all_orfcategory,
                            all_flosscatalog, all_floss ]
                
        return lists_to_insert
    
    
        
    # ===============================================================================
    # Common methods to perfom the query and insert data from the PRO database into 
    # the FILT database
    # =============================================================================== 
    
    ## query_PRO
    #  ---------
    #
    # This method allows to build a particular query to the PRO database,
    # using a filter built by concatenation and querying a particular table.
    #
    # @param classname: String - The name of the DenCellORF class to query.
    #                            e.g. PROGene.
    # @param filter: String - The filter to apply on the query.
    #                         e.g. '.filter( PROGeneAlias.alias == "GADD34" )'
    # 
    # @return SQLAlchemy Query - SQLManagerPRO.get_instance().get_session().query( classname ).filter
    #                            e.g. SQLManagerPRO.get_instance().get_session().query( PROGene \
    #                                                            ).filter( PROGeneAlias.alias == "GADD34" )
    # 
    def query_PRO( self, classname, filter ):
        
        return eval( 'SQLManagerPRO.get_instance().get_session().query( ' + classname + ')' + filter + '.distinct()' )
        
    
    
    ## process_queries
    #  ---------------
    #
    # This methods allows to process a list of queries previously 
    # generated and that allows to filter the content of the 
    # PRO database that needs to be used in the FILT database.
    # 
    def process_queries( self, queries_list ):
    
        # Get the total number of queries to process and reset 
        # the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( queries_list ) )
            
        for query in queries_list:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            self.PRO_to_FILT( query )
    
    
    
    ## PRO_to_FILT
    #  -----------
    #
    # This method allows to get all the object reported by a query on the PRO database, 
    # detach them from the session and insert them in the FILT database.
    #
    # @param query: SQLAlchemy Query - The SQLAlchemy query allowing to get the 
    #                                  entries to insert in the FILT database.
    #
    # @throw DenCellORFException: When an exception as been raised trying to insert the data
    #                             and commit the changes.
    # 
    def PRO_to_FILT( self, query ):
        
        if ( query and ( query.count() != 0 ) ):
            # Expunge the session to the PRO database to detach the objects in the list from the session
            SQLManagerPRO.get_instance().get_session().expunge_all()
            SQLManagerPRO.get_instance().close_session()
            
            # Insert the objects of the list in the FILT database
            for entry in query.all():
                try:
                    SQLManagerFILT.get_instance().get_session().merge( entry )
                except Exception as e:
                    raise DenCellORFException( 'FilterStrategy().PRO_to_FILT(): An exception occurred' +
                                               ' trying to insert the data in the FILT database' +
                                               ' (using the session.merge() method).', e )
                
            try: 
                SQLManagerFILT.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'FilterStrategy().PRO_to_FILT(): An exception occurred' +
                                           ' trying to commit changes after insertion of data in' +
                                           ' the FILT database.', e )
                
        SQLManagerFILT.get_instance().close_session()
    