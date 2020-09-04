# -*- coding: utf-8 -*-

import itertools


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.genetics.GeneticsUtil import GeneticsUtil
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *


## MergeDSOTA
#  ==========
#
# This contains static methods allowing to create the appropriate objects 
# to merge DSORFTranscriptAsso entries (DS database).
# NB: This class has been optimized for multi-processing.
#
class MergeDSOTA( object ):
                
    ## Class variables
    #  ---------------
    #
    # List of attributes that needs to be compared to merge 
    # several DSORFTranscriptAsso entries together
    DSORFTRANSCRIPTASSO_ATTRIBUTES_TO_COMPARE = [ 'id', 'data_source', 'predicted', 'ribo_seq', 
                                                  'cell_context', 'raw_sequence', 'raw_sequence_aa',
                                                  'start_codon_seq', 'kozak_context', 'orf_length_nt',
                                                  'orf_length', 'provided_category', 'ms_info',
                                                  'orf_score', 'phylocsf', 'phastcons', 'floss', 
                                                  'floss_class' ]
    
    # List of values for the Kozak context attributes to consider as true or false
    KOZAK_CTXT_TRUE = [ '1', True ]
    KOZAK_CTXT_FALSE = [ '0', False ]

        
    # ================================================================================
    # INFORMATION TO DEVELOPERS
    #
    # In order to faster the execution of the source code, the following methods 
    # have been build such as they could be serialized, and they do not need to
    # access shared objects, allowing them to run as totally independent processes
    # on multiple CPUs at the same time. The source code has been built taking 
    # advantage of classes and methods implemented in the pathos package.
    # The followed methods are intended to be run in pools.
    # Please see the documentation of the MergeStrategy class for more information.
    #
    # ================================================================================

    
    
    # ===============================================================================
    # Methods to get the DSORFTranscriptAsso entries to merge
    # ===============================================================================
    
    # Methods deprecated
    
    
    # ===============================================================================
    # Methods related to merge the DSORFTranscriptAsso entries
    # =============================================================================== 
    
    ## merge_dsota
    #  -----------
    #
    # This static method allows to merge a group of entries from 
    # the DSORFTranscriptAsso table of the DS database.
    # 
    # @param args_for_merging: 7-tuple - A 7-elements tuple that contains the following information:
    #                                - ota_id: Integer (>0) - An unique integer to use as ID for the new 
    #                                                         ORFTranscriptAsso entry.
    #                                - orf_tr_asso: Tuple - A tuple containing the IDs of the ORF and 
    #                                                       the Transcript entries related to the new 
    #                                                       ORFTranscriptAsso entry ( orf_id, transcript_id ).
    #                                - dsorftranscriptasso_list: List of DSORFTranscriptAsso - The list of 
    #                                                            DSORFTranscriptAsso entries to merge.
    #                                - check_dsota_coherence: Boolean - Does the coherence between the attributes 
    #                                                                   of a DSORFTranscriptAsso needs to be checked?
    #                                - compute_consensus: Boolean - Does the consensus needs to be computed when 
    #                                                               several sequences are provided?
    #                                - sqce_consensus_ambig_threshold: Float [0,1] - The value of the threshold to 
    #                                                               use when computing the consensus sequence if 
    #                                                               this option has been selected.
    #                                - max_len_diff_dsota_clust: Integer (>0) - The maximal difference between the 
    #                                                            max. and min. lengths of DSORFTranscriptAsso 
    #                                                            entries to belong to the same "cluster".
    #    
    # @return 6-tuple - A 6-elements tuple that contains the following information:
    #                     - objects_to_insert: List - The list of new objects to insert and that CAN NOT be
    #                                                 instantiated by any concurrent process.
    #                     - cell_ctxt_catalog_to_insert: List - The list CellContextCatalog entries instantiated by
    #                                                           the process (and that could eventually have been 
    #                                                           instantiated by concurrent processes)
    #                     - provided_cat_catalog_to_insert: List - The list ProvidedCategoryCatalog entries 
    #                                                              instantiated by the process (and that could 
    #                                                              eventually have been instantiated by concurrent 
    #                                                              processes)
    #                     - floss_class_catelog_to_insert: List - The list FlossClassCatalog entries instantiated by
    #                                                             the process (and that could eventually have been 
    #                                                             instantiated by concurrent processes)
    #                     - error_messages_to_log: List - The list of messages instantiated by the process and that
    #                                                     must be logged at the error level.
    #                     - warning_messages_to_log: List - The list of messages instantiated by the process and that
    #                                                       must be logged at the warning level.
    #
    @staticmethod
    def merge_dsota( args_for_merging ):
        
        # Parse the arguments
        ( ota_id,
          orf_tr_asso,
          dsorftranscriptasso_list,
          check_dsota_coherence,
          compute_consensus,
          sqce_consensus_ambig_threshold,
          max_len_diff_dsota_clust ) = args_for_merging
        
        # Instantiate a list of new entries
        # NB: The objects added to this list MUST be unique entries of the PRO database, 
        #     i.e. entries that could NOT be instantiated by a parallel process for which 
        #     the provided arguments would be different. This exclude the "catalog" entries.
        objects_to_insert = []
        
        # The new CellContextCatalog, ProvidedCategoryCatalog and FlossClassCatalog 
        # entries are stored in separate dictionaries.
        cell_ctxt_catalog_to_insert = {}
        provided_cat_catalog_to_insert = {}
        floss_class_catelog_to_insert = {}
        
        # Error and warning messages expected to be logged 
        # are stored in separate lists and returned
        error_messages_to_log = []
        warning_messages_to_log = []
        
        # Get the IDs of ORF and Transcript
        ( orf_id, transcript_id ) = orf_tr_asso
        
        # NB: 
        # - The original ORF IDs (from data source or generated during 
        #   the parsing / insertion) are not registered in the PRO database.
        # - The information about the equality between the genomic length
        #   of the ORF and the actual length of the ORF has not been yet 
        #   computed at this stage and will be computed later.
                        
        # When the checkDSOTA option has been selected,
        # for each DSORFTranscriptAsso check the raw nucleic and 
        # amino acid sequences agree with each other. If there is some 
        # incoherence between them, the information will be logged and 
        # the non-according attributes of the object will be set to None.
        # NB: See the documentation of the check_dsorftrasso_coherence() method
        #     for more information.
        if check_dsota_coherence:
            dsorftranscriptasso_updated_list = []
            for dsorftranscriptasso in dsorftranscriptasso_list:
                ( checked_dsota, checked_error_to_log, checked_warning_to_log ) = MergeDSOTA.check_dsorftrasso_coherence( dsorftranscriptasso )
                dsorftranscriptasso_updated_list.append( checked_dsota )
                error_messages_to_log += checked_error_to_log
                warning_messages_to_log += checked_warning_to_log
        else:
            dsorftranscriptasso_updated_list = dsorftranscriptasso_list
            
        # If there is one single DSORFTranscriptAsso in the list, then create 
        # a new ORFTranscriptAsso using the information of its attributes
        if ( len( dsorftranscriptasso_updated_list ) == 1 ):
            
            dsorftranscriptasso = dsorftranscriptasso_updated_list[ 0 ]
            
            # If the value of an attribute is ambiguous,
            # set it to None for the merging
            for att in MergeDSOTA.DSORFTRANSCRIPTASSO_ATTRIBUTES_TO_COMPARE:
                                    
                att_value = getattr( dsorftranscriptasso, att ) 
                                   
                if ( att_value == Constants.DENCELLORFOBJ_AMBIGUOUS_ATT ):
                    setattr( dsorftranscriptasso, att, None )
            
            ## Instantiate a new ORFTranscriptAsso object
            predicted = dsorftranscriptasso.predicted
            if ( predicted == None ):
                predicted = False
                
            ribo_seq = dsorftranscriptasso.ribo_seq
            if ( ribo_seq == None ):
                ribo_seq = False
                
            ms_info = dsorftranscriptasso.ms_info
            if ( ms_info == None ):
                ms_info = False
            
            # Get the start codon sequence
            if ( dsorftranscriptasso.start_codon_seq != None ):
                start_codon_seq = dsorftranscriptasso.start_codon_seq
            else:
                if ( dsorftranscriptasso.raw_sequence != None ):
                    start_codon_seq = dsorftranscriptasso.raw_sequence[ :3 ]
                else:
                    start_codon_seq = None
            
            # Get information about the Kozak context
            if ( str( dsorftranscriptasso.kozak_context ) in MergeDSOTA.KOZAK_CTXT_TRUE ):
                kozak_context = True
            elif ( str( dsorftranscriptasso.kozak_context ) in MergeDSOTA.KOZAK_CTXT_FALSE ):
                kozak_context = False
            else:
                kozak_context = None
                
            # Define the count_prov_length attribute
            if ( dsorftranscriptasso.orf_length != None ):
                count_prov_lengths = 1
            else:
                count_prov_lengths = 0
            
            # Instantiate the new object
            orftranscriptasso = ORFTranscriptAsso( id = ota_id,
                                                   orf_id = orf_id,
                                                   transcript_id = transcript_id,
                                                   predicted = predicted,
                                                   ribo_seq = ribo_seq,
                                                   ms_info = ms_info,
                                                   sequence_nt = dsorftranscriptasso.raw_sequence,
                                                   sequence_aa = dsorftranscriptasso.raw_sequence_aa,
                                                   start_codon_seq = start_codon_seq,
                                                   kozak_context = kozak_context,
                                                   length_nt_min = dsorftranscriptasso.orf_length_nt,
                                                   length_nt_max = dsorftranscriptasso.orf_length_nt,
                                                   length_nt_median = dsorftranscriptasso.orf_length_nt,
                                                   length_nt_values = dsorftranscriptasso.orf_length_nt,                                                   
                                                   length_aa_min = dsorftranscriptasso.orf_length,
                                                   length_aa_max = dsorftranscriptasso.orf_length,
                                                   length_aa_median = dsorftranscriptasso.orf_length,
                                                   length_aa_values = dsorftranscriptasso.orf_length,
                                                   orf_score_min = dsorftranscriptasso.orf_score,
                                                   orf_score_max = dsorftranscriptasso.orf_score,
                                                   orf_score_median = dsorftranscriptasso.orf_score,
                                                   orf_score_values = dsorftranscriptasso.orf_score,                                                   
                                                   phylocsf_min = dsorftranscriptasso.phylocsf,
                                                   phylocsf_max = dsorftranscriptasso.phylocsf,
                                                   phylocsf_median = dsorftranscriptasso.phylocsf,
                                                   phylocsf_values = dsorftranscriptasso.phylocsf,
                                                   phastcons_min = dsorftranscriptasso.phastcons,
                                                   phastcons_max = dsorftranscriptasso.phastcons,
                                                   phastcons_median = dsorftranscriptasso.phastcons,
                                                   phastcons_values = dsorftranscriptasso.phastcons,                                                   
                                                   floss_min = dsorftranscriptasso.floss,
                                                   floss_max = dsorftranscriptasso.floss,
                                                   floss_median = dsorftranscriptasso.floss,
                                                   floss_values = dsorftranscriptasso.floss,
                                                   count_ds = 1,
                                                   count_computed_clusters = 1,
                                                   count_prov_lengths = count_prov_lengths,
                                                   computed_clusters = str( [[ dsorftranscriptasso.id ]] ),
                                                   gen_len_eq_orf_len = None )
            objects_to_insert.append( orftranscriptasso )
            
            # Create new entries in the CellContext table to register the
            # cellular contexts related to the ORFTranscriptAsso entry
            if dsorftranscriptasso.cell_context:
                
                # Split the cellular contexts that can eventually have been
                # concatenated by the source or during the data insertion
                list_cell_context =  dsorftranscriptasso.cell_context.split( ',' )
                    
                # Get the set of unique values for the cellular context
                list_uniq_cell_context = set( list_cell_context )
                
                for cell_ctxt in list_uniq_cell_context:
                    
                    # If the CellContextCatalog entry has not yet been instantiated, 
                    # then create a new entry in this table.
                    cell_ctxt_catalog = CellContextCatalog( context = cell_ctxt )
                    
                    existing_cell_ctxt_catalog = cell_ctxt_catalog_to_insert.get( cell_ctxt_catalog )                   
                    if ( not existing_cell_ctxt_catalog ):
                        cell_ctxt_catalog_to_insert[ cell_ctxt_catalog ] = cell_ctxt_catalog
                    
                    # Create a new entry in the CellContext table
                    cellcontext = CellContext( orftranscriptasso_id = ota_id,
                                               cell_context = cell_ctxt )
                    objects_to_insert.append( cellcontext )
            
            
            # Create new entries in the ProvidedCategory table to register the 
            # ORF categories provided by the data source for this 
            # ORF - transcript association                
            if dsorftranscriptasso.provided_category:
                
                # Split the categories that can eventually have been 
                # concatenated by the source or during data insertion
                # Replace the blanks by underscores in the provided categories
                list_provided_category = dsorftranscriptasso.provided_category.replace( '/', ',' ).replace( ' ', '_' ).split( ',' )
                                    
                # Get the set of unique values for the cellular context
                list_uniq_provided_category = set( list_provided_category )
                
                for prov_cat in list_uniq_provided_category:
                    
                    if not GeneralUtil.is_empty( prov_cat ):
                    
                        # If the ORFCatagoryCatalog entry has not yet been instantiated, 
                        # then create a new entry in this table.
                        provided_cat_catalog = ProvidedCategoryCatalog( category = prov_cat )
                                               
                        existing_provided_cat_catalog = provided_cat_catalog_to_insert.get( provided_cat_catalog )                   
                        if ( not existing_provided_cat_catalog ):
                            provided_cat_catalog_to_insert[ provided_cat_catalog ] = provided_cat_catalog
                        
                        # Create a new entry in the ProvidedCategory table
                        providedcategory = ProvidedCategory( orftranscriptasso_id = ota_id,
                                                             provided_category = prov_cat )
                        objects_to_insert.append( providedcategory )
                        
                        
            # Create new entries in the FLOSSClass table to register
            # the FLOSS categories provided by the data source
            if dsorftranscriptasso.floss_class:                    
                    
                # If the FLOSSClassCatalog entry has not yet been instantiated, 
                # then create a new entry in this table.
                floss_class_cat = FLOSSClassCatalog( floss_class = dsorftranscriptasso.floss_class )
                                               
                existing_floss_class_cat = floss_class_catelog_to_insert.get( floss_class_cat )                   
                if ( not existing_floss_class_cat ):
                    floss_class_catelog_to_insert[ floss_class_cat ] = floss_class_cat
                
                # Create a new entry in the FLOSSClass table
                flossclass = FLOSSClass( orftranscriptasso_id = ota_id,
                                         floss_class = dsorftranscriptasso.floss_class )
                objects_to_insert.append( flossclass )
                
                
            # Create the new ORFTranscriptAssoDSAsso
            orftranscriptassodsasso = ORFTranscriptAssoDSAsso( orftranscriptasso_id = ota_id,
                                                               dsorftranscriptasso_id = dsorftranscriptasso.id,
                                                               data_source = dsorftranscriptasso.data_source )
            objects_to_insert.append( orftranscriptassodsasso )
        
            
        # Otherwise, if there are several DSORFTranscriptAsso to merge in the list, 
        # then create a new ORFTranscriptAsso merging the information of their 
        # attributes
        else:
            ## Build a dictionary that contains as keys the name of the attributes 
            #  to merge and as values the actual value(s) for the related attribute
            dsorftranscriptasso_dict = {}
            
            for att in MergeDSOTA.DSORFTRANSCRIPTASSO_ATTRIBUTES_TO_COMPARE:
                
                dsorftranscriptasso_dict[ att ] = []
                
                for dsorftranscriptasso in dsorftranscriptasso_updated_list:
                    att_value = getattr( dsorftranscriptasso, att )
                    
                    # Store the value in the list only if it is not None and not ambiguous
                    if ( ( att_value != None )
                         and ( att_value != Constants.DENCELLORFOBJ_AMBIGUOUS_ATT ) ):
                        dsorftranscriptasso_dict.get( att ).append( att_value )
                        
                # Remove the empty lists from the dictionary
                if ( dsorftranscriptasso_dict.get( att ) == [] ):
                    del dsorftranscriptasso_dict[ att ]
                    
            
            ## Merge the DSORFTranscriptAsso together
            
            # If the ORF - Transcript association has been at least predicted once,
            # then set the attribute to True
            predicted = dsorftranscriptasso_dict.get( 'predicted', False )
            if predicted:
                predicted = any( predicted )
            
            # If the ORF - Transcript association has been at least detected once by 
            # Ribo-seq, then set the attribute to True
            ribo_seq = dsorftranscriptasso_dict.get( 'ribo_seq', False )
            if ribo_seq:
                ribo_seq = any( ribo_seq )
            
            # If the ORF - Transcript association has been at least detected once by 
            # mass spectrometry, then set the attribute to True
            ms_info = dsorftranscriptasso_dict.get( 'ms_info', False )
            if ms_info:
                ms_info = any( ms_info )
            
            # Find a consensus on the nucleic sequence
            sqce_nt_consensus = dsorftranscriptasso_dict.get( 'raw_sequence', None )
            if sqce_nt_consensus:
                # If the computeConsensus option has been selected, find a consensus. 
                if compute_consensus:
                    sqce_nt_consensus = GeneticsUtil.find_sqce_consensus( list_of_sequences = dsorftranscriptasso_dict.get( 'raw_sequence' ), 
                                                                          sqce_type = Constants.SEQUENCE_TYPE_DNA, 
                                                                          threshold = sqce_consensus_ambig_threshold,
                                                                          fasta_end_name = str( ota_id ) + '_nt' )
                # Otherwise, instead of the sequence, store the number of sequences 
                # that would have been used to compute the consensus
                else:
                    sqce_nt_consensus = len( sqce_nt_consensus )
            
            # Find a consensus on the amino acid sequence
            sqce_aa_consensus = dsorftranscriptasso_dict.get( 'raw_sequence_aa', None )
            if sqce_aa_consensus:
                # If the computeConsensus option has been selected, find a consensus. 
                if compute_consensus:
                    sqce_aa_consensus = GeneticsUtil.find_sqce_consensus( list_of_sequences = dsorftranscriptasso_dict.get( 'raw_sequence_aa' ),
                                                                          sqce_type = Constants.SEQUENCE_TYPE_PROT,
                                                                          threshold = sqce_consensus_ambig_threshold,
                                                                          fasta_end_name = str( ota_id ) + '_aa' )
                # Otherwise, instead of the sequence, store the number of sequences 
                # that would have been used to compute the consensus
                else:
                    sqce_aa_consensus = len( sqce_aa_consensus )
            
            # If a consensus has been computed for the nucleic sequence, store the three first 
            # letters of the nucleic sequence consensus as the start codon sequence.
            # Otherwise, try to compute it from the start_codon_seq attributes if they are provided.
            if ( sqce_nt_consensus
                 and ( not isinstance( sqce_nt_consensus, int ) )
                 and ( len( sqce_nt_consensus ) >= 3 ) ):
                sqce_start_codon_consensus = sqce_nt_consensus[ :3 ]
            else:
                sqce_start_codon_consensus = dsorftranscriptasso_dict.get( 'start_codon_seq', None )                
                if sqce_start_codon_consensus:
                    sqce_start_codon_consensus = GeneticsUtil.find_codon_consensus( sequences = sqce_start_codon_consensus, 
                                                                                    threshold = sqce_consensus_ambig_threshold )
                else:
                    sqce_start_codon_consensus = None
                
            
            # Get the Kozak context for the start of the ORF - Transcript association.
            # - By default, the Kozak context is set equal to None,
            # - If the Kozak context has been at least reported once, 
            #   then the attribute value is set to True,
            # - Otherwise, if it has already been reported that there is no Kozak context
            #   for the start of this ORF - Transcript association ( AND if a Kozak context 
            #   has never been reported for this association), then it is set to False.
            kozak_context_list = dsorftranscriptasso_dict.get( 'kozak_context', None )
            
            if kozak_context_list:
                key_iterator = iter( kozak_context_list )
                k_ctxt = next( key_iterator, None )
                
                kozak_context = None
                while ( k_ctxt != None ) and ( kozak_context != True ):
                
                    if str( k_ctxt ) in MergeDSOTA.KOZAK_CTXT_TRUE:
                        kozak_context = True
                        
                    elif str( k_ctxt ) in MergeDSOTA.KOZAK_CTXT_FALSE:
                        kozak_context = False
                        
                    k_ctxt = next( key_iterator, None )
                    
            else:
                kozak_context = None
            
            
            # Compute the values of the amino acid ORF lengths
            orf_length_values_list = dsorftranscriptasso_dict.get( 'orf_length' )
            ( length_aa_min, length_aa_max, length_aa_median ) = GeneralUtil.min_max_median_of_list( list_of_values = orf_length_values_list, fct = 'int' )
            length_aa_values = GeneralUtil.list_to_string( list_to_convert = orf_length_values_list,
                                                           sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                           not_none = False )
                                    
            # Compute the values of the nucleic ORF lengths
            orf_length_nt_values_list = dsorftranscriptasso_dict.get( 'orf_length_nt' )
            ( length_nt_min, length_nt_max, length_nt_median ) = GeneralUtil.min_max_median_of_list( list_of_values = orf_length_nt_values_list, fct = 'int' )
            length_nt_values = GeneralUtil.list_to_string( list_to_convert = orf_length_nt_values_list,
                                                           sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                           not_none = False )
            
            # Compute the values for the ORF scores
            orfscore_values_list = dsorftranscriptasso_dict.get( 'orf_score' )
            ( orfscore_min, orfscore_max, orfscore_median ) = GeneralUtil.min_max_median_of_list( list_of_values = orfscore_values_list, fct = 'float' )
            orfscore_values = GeneralUtil.list_to_string( list_to_convert = orfscore_values_list,
                                                          sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                          not_none = False )
                      
            # Compute the values for the PhyloCSF scores
            phylocsf_values_list = dsorftranscriptasso_dict.get( 'phylocsf' )
            ( phylocsf_min, phylocsf_max, phylocsf_median ) = GeneralUtil.min_max_median_of_list( list_of_values = phylocsf_values_list, fct = 'float' )
            phylocsf_values = GeneralUtil.list_to_string( list_to_convert = phylocsf_values_list,
                                                          sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                          not_none = False )
            
            # Compute the values for the PhastCons scores
            phastcons_values_list = dsorftranscriptasso_dict.get( 'phastcons' )
            ( phastcons_min, phastcons_max, phastcons_median ) = GeneralUtil.min_max_median_of_list( list_of_values = phastcons_values_list, fct = 'float' )
            phastcons_values = GeneralUtil.list_to_string( list_to_convert = phastcons_values_list,
                                                           sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                           not_none = False )
            
            # Compute the values for the FLOSS scores
            floss_values_list = dsorftranscriptasso_dict.get( 'floss' )
            ( floss_min, floss_max, floss_median ) = GeneralUtil.min_max_median_of_list( list_of_values = floss_values_list, fct = 'float' )
            floss_values = GeneralUtil.list_to_string( list_to_convert = floss_values_list,
                                                       sep = Constants.OTA_LIST_VALUES_SEPARATOR,
                                                       not_none = False )
                        
            
            
            ## For all the DSORFTranscriptAsso of the list, try to identify if there
            #  are several "clusters", i.e. if several DSORFTranscriptAsso are being 
            #  merged together while it seems they actually describe different ORF -
            #  transcript associations.
            #  NB: This guess is performed using only the amino acid length as this 
            #      is the most often provided feature and one of the most relevant 
            #      (with the sequences) to do this.
            #  NB: See the documentation of the find_best_dsota_subpop() method for
            #      more information.
            orf_length_list = dsorftranscriptasso_dict.get( 'orf_length' )
            
            if orf_length_list:
                list_of_clusters = MergeDSOTA.find_best_dsota_subpop( dsorftranscriptasso_updated_list,
                                                                      max_len_diff_dsota_clust )
                
                # Get the number of ORF amino acid lengths that have actually been 
                # used to compute the "clusters"
                count_prov_lengths = len( orf_length_list )
            
            else:
                list_of_clusters = [ dsorftranscriptasso_updated_list ]
                count_prov_lengths = 0
            
            # Get the number of computed "clusters"
            count_clusters = len( list_of_clusters )
            
            # Record the computed "clusters" using the IDs
            list_of_clusters_with_ids = []
            
            for cluster in list_of_clusters:
                # Get the IDs of DSORFTranscriptAsso that belong to the 
                # same "cluster" and add a new cluster to the list
                list_of_clusters_with_ids.append( [ str( dsota.id ) for dsota in cluster ] )
                
            
            ## Instantiate a new ORFTranscriptAsso object
            orftranscriptasso = ORFTranscriptAsso( id = ota_id,
                                                   orf_id = orf_id,
                                                   transcript_id = transcript_id,
                                                   predicted = predicted,
                                                   ribo_seq = ribo_seq,
                                                   ms_info = ms_info,
                                                   sequence_nt = sqce_nt_consensus,
                                                   sequence_aa = sqce_aa_consensus,
                                                   start_codon_seq = sqce_start_codon_consensus,
                                                   kozak_context = kozak_context,
                                                   length_nt_min = length_nt_min,
                                                   length_nt_max = length_nt_max,
                                                   length_nt_median = length_nt_median,
                                                   length_nt_values = length_nt_values,
                                                   length_aa_min = length_aa_min,
                                                   length_aa_max = length_aa_max,
                                                   length_aa_median = length_aa_median,
                                                   length_aa_values = length_aa_values,                                                   
                                                   orf_score_min = orfscore_min,
                                                   orf_score_max = orfscore_max,
                                                   orf_score_median = orfscore_median,
                                                   orf_score_values = orfscore_values,                                                   
                                                   phylocsf_min = phylocsf_min,
                                                   phylocsf_max = phylocsf_max,
                                                   phylocsf_median = phylocsf_median,
                                                   phylocsf_values = phylocsf_values,                                                   
                                                   phastcons_min = phastcons_min,
                                                   phastcons_max = phastcons_max,
                                                   phastcons_median = phastcons_median,
                                                   phastcons_values = phastcons_values,                                                   
                                                   floss_min = floss_min,
                                                   floss_max = floss_max,
                                                   floss_median = floss_median,
                                                   floss_values = floss_values,
                                                   count_ds = len( dsorftranscriptasso_list ),
                                                   count_computed_clusters = count_clusters,
                                                   count_prov_lengths = count_prov_lengths,
                                                   computed_clusters = str( list_of_clusters_with_ids ),
                                                   gen_len_eq_orf_len = None )
            objects_to_insert.append( orftranscriptasso )
            
            
            # Create new entries in the CellContext table to register the
            # cellular contexts related to the ORFTranscriptAsso entry
            cell_context_list = dsorftranscriptasso_dict.get( 'cell_context' )
            
            if cell_context_list:
                
                # Split the cellular contexts that can eventually have been
                # concatenated by the source or during the data insertion
                list_cell_context = []
                for cell_ctxt in cell_context_list:
                    list_cell_context += cell_ctxt.split( ',' )
                    
                # Get the set of unique values for the cellular context
                list_uniq_cell_context = set( list_cell_context )
                
                for cell_ctxt in list_uniq_cell_context:
                    
                    # If the CellContextCatalog entry has not yet been instantiated, 
                    # then create a new entry in this table.
                    cell_ctxt_catalog = CellContextCatalog( context = cell_ctxt )
                    
                    existing_cell_ctxt_catalog = cell_ctxt_catalog_to_insert.get( cell_ctxt_catalog )                   
                    if ( not existing_cell_ctxt_catalog ):
                        cell_ctxt_catalog_to_insert[ cell_ctxt_catalog ] = cell_ctxt_catalog
                    
                    # Create a new entry in the CellContext table
                    cellcontext = CellContext( orftranscriptasso_id = ota_id,
                                               cell_context = cell_ctxt )
                    objects_to_insert.append( cellcontext )
                
                
            # Create new entries in the ProvidedCategory table to register the 
            # ORF categories provided by the data sources for this 
            # ORF - transcript association
            provided_category_list = dsorftranscriptasso_dict.get( 'provided_category' )
            
            if provided_category_list:
                
                # Split the categories that can eventually have been 
                # concatenated by the source or during data insertion
                list_provided_category = []
                for prov_cat in provided_category_list:
                    # Replace the blanks by underscores in the provided categories
                    list_provided_category += prov_cat.replace( '/', ',' ).replace( ' ', '_' ).split( ',' )
                
                
                # Get the set of unique values for the cellular context
                list_uniq_provided_category = set( list_provided_category )
                
                for prov_cat in list_uniq_provided_category:
                    
                    if not GeneralUtil.is_empty( prov_cat ):
                    
                        # If the ORFCatagoryCatalog entry has not yet been instantiated, 
                        # then create a new entry in this table.
                        provided_cat_catalog = ProvidedCategoryCatalog( category = prov_cat )
                        
                        existing_provided_cat_catalog = provided_cat_catalog_to_insert.get( provided_cat_catalog )                   
                        if ( not existing_provided_cat_catalog ):
                            provided_cat_catalog_to_insert[ provided_cat_catalog ] = provided_cat_catalog
                        
                        # Create a new entry in the ProvidedCategory table
                        providedcategory = ProvidedCategory( orftranscriptasso_id = ota_id,
                                                             provided_category = prov_cat )
                        objects_to_insert.append( providedcategory )
                
                
            # Create new entries in the FLOSSClass table to register
            # the FLOSS categories provided by the data sources
            flossclass_list = dsorftranscriptasso_dict.get( 'floss_class' )
            if flossclass_list:
                
                # Get the set of unique values for the FLOSS classes
                list_uniq_flossclass = set( flossclass_list )
                
                for floss_cls in list_uniq_flossclass:
                    
                    
                    # If the FLOSSClassCatalog entry has not yet been instantiated, 
                    # then create a new entry in this table.
                    floss_class_cat = FLOSSClassCatalog( floss_class = floss_cls )
                                                   
                    existing_floss_class_cat = floss_class_catelog_to_insert.get( floss_class_cat )                   
                    if ( not existing_floss_class_cat ):
                        floss_class_catelog_to_insert[ floss_class_cat ] = floss_class_cat                              
                    
                    # Create a new entry in the FLOSSClass table
                    flossclass = FLOSSClass( orftranscriptasso_id = ota_id,
                                             floss_class = floss_cls )
                    objects_to_insert.append( flossclass )
                
                
            # Create the new ORFTranscriptAssoDSAsso
            for k in range( len( dsorftranscriptasso_list ) ):
                orftranscriptassodsasso = ORFTranscriptAssoDSAsso( orftranscriptasso_id = ota_id,
                                                                   dsorftranscriptasso_id = dsorftranscriptasso_list[ k ].id,
                                                                   data_source = dsorftranscriptasso_list[ k ].data_source )
                objects_to_insert.append( orftranscriptassodsasso )
        
        # Turn dictionary of instantiated CellContextCatalog, ProvidedCategoryCatalog 
        # and FlossClassCatalog objects into lists
        cell_ctxt_catalog_to_insert = cell_ctxt_catalog_to_insert.keys()
        provided_cat_catalog_to_insert = provided_cat_catalog_to_insert.keys()
        floss_class_catelog_to_insert = floss_class_catelog_to_insert.keys()
        
        return ( objects_to_insert, cell_ctxt_catalog_to_insert, provided_cat_catalog_to_insert, 
                 floss_class_catelog_to_insert, error_messages_to_log, warning_messages_to_log )
        
    
    
    ## check_dsorftrasso_coherence
    #  ---------------------------
    #
    # This is a static method that allows to check the coherence of the data 
    # contained in a DSORFTranscriptAsso object.
    # It checks:
    # - The agreement between the nucleic and amino acid sequences.
    # - The agreement between the provided nucleic sequence and length.
    # - The agreement between the provided amino acid sequence and length.
    # - The agreement between the nucleic and amino acid lengths.
    # If there is conflicting information, a warning is logged and the 
    # concerned attributes are removed from the entry.
    #
    # @param dsorftranscriptasso: DSORFTranscriptAsso - The entry to check.
    #
    # @return 3-tuple - A 3-elements tuple that contains the following information:
    #                     - dsorftranscriptasso: DSORFTranscriptAsso - The updated entry.
    #                     - error_messages_to_log: List - The list of messages instantiated by the process and that
    #                                                     must be logged at the error level.
    #                     - warning_messages_to_log: List - The list of messages instantiated by the process and that
    #                                                       must be logged at the warning level.
    # 
    @staticmethod
    def check_dsorftrasso_coherence( dsorftranscriptasso ):
        
        error_messages_to_log = []
        warning_messages_to_log = []
        
        ## Check the nucleic and amino acid sequences agree with each other        
        # Get the nucleic and amino acid sequences 
        # (set them to None if an ambiguous flag has been registered for these)
        if ( dsorftranscriptasso.raw_sequence == Constants.DENCELLORFOBJ_AMBIGUOUS_ATT ):
            dsorftranscriptasso.raw_sequence = None
        
        if ( dsorftranscriptasso.raw_sequence_aa == Constants.DENCELLORFOBJ_AMBIGUOUS_ATT ):
            dsorftranscriptasso.raw_sequence_aa = None
        
        sequence_nt = dsorftranscriptasso.raw_sequence
        sequence_aa = dsorftranscriptasso.raw_sequence_aa
            
        
        if ( sequence_nt and sequence_aa ):
            
            # Translate the DNA sequence
            try:
                translated_sequence = GeneticsUtil.translate_dna( dna_seq = sequence_nt, 
                                                                  include_stop = False,
                                                                  to_stop = False )
            except TranslateDNAException as e:
                translated_sequence = e.get_aa_seq()
                error_messages_to_log.append( 'The length of the nucleic sequence of the' +
                                              ' DSORFTranscriptAsso with ID "' + str( dsorftranscriptasso.id ) + 
                                              '" is not a multiple of three. Hence, the sequence has been' +
                                              ' translated ignoring the last ' + str( e.get_remainder() ) + 
                                              ' nucleotides.' +
                                              ' Warning code: ' + LogCodes.WARN_TRANSL_SEQSIZE_NOT3 + '.' )
            
            
            
            # Some of the data sources have replaced the first amino acid of the ORF 
            # sequence by a methionine (e.g. the TTG codon is usually expected to be 
            # translated as a leucine while some data source have replaced it as a 
            # methonine; see for instance the ORF with original ID "andreev_2015:128701" 
            # from sORFs.org, Human database). Hence, when the DNA and amino acid 
            # sequences agree with each other excepted about the 1st amino acid, the 
            # sequences are considered as agreeing with each other.
            # NB: It would make sense to first look if the whole translated and amino 
            #     acid sequences agree with each other, and only then when they do not 
            #     to look if this is only the first amino acid which is different. 
            #     Nevertheless, in order to reduce the computation time, the algorithm
            #     first compares the first amino acid of the two sequences:
            #         - and if this is the same, it compares the whole sequences,
            #             - and if they are the same, the two sequences are kept.
            #             - otherwise if they are different the two sequences are removed 
            #               from the entry as they do not agree with each other.
            #         - and if the first amino acid is not the same in the sequences, 
            #           it then compares the sequence omitting the first amino acid,
            #             - and if they are the same, the two sequences are kept, considering 
            #               they actually agree with each other despite a difference on the 
            #               first amino acid.
            #             - otherwise if they are different the two sequences are removed from 
            #               the entry as they do not agree with each other.
            remove_both_sequence = False
            
            if ( translated_sequence[ 0 ] == sequence_aa[ 0 ] ):
                if ( translated_sequence != sequence_aa ):
                    remove_both_sequence = True
                                    
            else:
                if ( translated_sequence[ 1: ] != sequence_aa[ 1: ] ):
                    remove_both_sequence = True
            
            if remove_both_sequence:
                warning_messages_to_log.append( 'The nucleic and amino acid sequences of the' +
                                                ' DSORFTranscriptAsso with ID "' + 
                                                str( dsorftranscriptasso.id ) + 
                                                '" do not agree with each other. Hence, these sequences' +
                                                ' will not be considered to create the ORFTranscriptAsso' +
                                                ' entries (in the PRO database).'  +
                                                ' Warning code: ' + LogCodes.WARN_DCORF_DSOTA_CONFL_SEQ + '.' )
                
                dsorftranscriptasso.raw_sequence = None
                dsorftranscriptasso.raw_sequence_aa = None

                
        # Else, if there is only the nucleic sequence which is provided, 
        # then translate it to get the amino acid sequence
        elif sequence_nt:
            
            # Translate the DNA sequence
            try:
                dsorftranscriptasso.raw_sequence_aa = GeneticsUtil.translate_dna( dna_seq = sequence_nt, 
                                                                                  include_stop = False,
                                                                                  to_stop = False )
            except TranslateDNAException as e:
                dsorftranscriptasso.raw_sequence_aa = e.get_aa_seq()
                warning_messages_to_log.append( 'The length of the nucleic sequence of the' +
                                                ' DSORFTranscriptAsso with ID "' + str( dsorftranscriptasso.id ) + 
                                                '" is not a multiple of three. Hence, the sequence has been' +
                                                ' translated ignoring the last ' + str( e.get_remainder() ) + 
                                                ' nucleotides.' +
                                                ' Warning code: ' + LogCodes.WARN_TRANSL_SEQSIZE_NOT3 + '.' )
            
        
        ## Compare the nucleic sequence and its length        
        sequence_nt = dsorftranscriptasso.raw_sequence
        length_nt = dsorftranscriptasso.orf_length_nt
        
        if ( sequence_nt and ( length_nt != None ) ):
            length_sequence_nt = len( sequence_nt )
            length_nt = int( length_nt )
            
            if ( length_sequence_nt != length_nt ):
                warning_messages_to_log.append( 'The provided nucleic length (' + str( length_nt ) + 
                                                ') and the length of the nucleic sequence (' + 
                                                str( length_sequence_nt ) + 
                                                ') of the DSORFTranscriptAsso with ID "' + 
                                                str( dsorftranscriptasso.id ) + '" are not the same.' +
                                                ' Hence, this length and this sequence will not be considered' +
                                                ' to create the ORFTranscriptAsso entries (in the PRO database).'  +
                                                ' Warning code: ' + LogCodes.WARN_DCORF_DSOTA_CONFL_NTLEN + '.' )
                
                dsorftranscriptasso.raw_sequence = None
                dsorftranscriptasso.orf_length_nt = None
                
        # Else, if the nucleic sequence is provided but not the length, 
        # then compute the length from it
        elif sequence_nt:
            dsorftranscriptasso.orf_length_nt = len( sequence_nt )
            
        
        ## Compare the amino acid sequence and its length        
        sequence_aa = dsorftranscriptasso.raw_sequence_aa
        length_aa = dsorftranscriptasso.orf_length
        
        if ( sequence_aa and ( length_aa != None ) ):
            length_sequence_aa = len( sequence_aa )
            length_aa = int( length_aa )
            
            if ( length_sequence_aa != length_aa ):
                warning_messages_to_log.append( 'The provided amino acid length (' + str( length_aa ) + 
                                                ') and the length of the amino acid sequence (' + 
                                                str( length_sequence_aa ) + 
                                                ') of the DSORFTranscriptAsso with ID "' + 
                                                str( dsorftranscriptasso.id ) + '" are not the same.' +
                                                ' Hence, this length and this sequence will not be considered' +
                                                ' to create the ORFTranscriptAsso entries (in the PRO database).' +
                                                ' Warning code: ' + LogCodes.WARN_DCORF_DSOTA_CONFL_AALEN + '.' ) 
                
                dsorftranscriptasso.raw_sequence_aa = None
                dsorftranscriptasso.orf_length = None
                
        # Else, if the nucleic sequence is provided but not the length, 
        # then compute the length from it
        elif sequence_aa:
            dsorftranscriptasso.orf_length = len( sequence_aa )
            
        
        ## Compare the amino acid and nucleic lengths
        length_nt = dsorftranscriptasso.orf_length_nt
        length_aa = dsorftranscriptasso.orf_length
        
        if ( ( length_nt != None ) and ( length_aa != None ) ):
            length_nt = int( length_nt )
            length_aa = int( length_aa )
            length_aa_in_nt = int( ( length_aa + 1 ) * 3 )
            
            if ( length_nt != length_aa_in_nt ):
                warning_messages_to_log.append( 'The provided amino acid length (' + str( length_aa ) + 
                                                ') and nucleic length (' + str( length_nt ) +
                                                + ') of the DSORFTranscriptAsso with ID "' + 
                                                str( dsorftranscriptasso.id ) + '" do not agree with each' +
                                                ' other. Hence, these lengths will not be considered' +
                                                ' to create the ORFTranscriptAsso entries (in the PRO database).' +
                                                ' Warning code: ' + LogCodes.WARN_DCORF_DSOTA_CONFL_AANTLEN + '.' ) 
                
                dsorftranscriptasso.orf_length_nt = None
                dsorftranscriptasso.orf_length = None
                
        # Else, if the nucleic length is provided but not the amino acid length, 
        # then compute the amino acid length from it
        elif ( ( length_nt != None ) and ( length_aa == None ) ):
            length_nt = int( length_nt )
            dsorftranscriptasso.orf_length = ( ( length_nt / 3 ) - 1 )
            
        # Else, if the amino acid length is provided but not the nucleic length, 
        # then compute the nucleic length from it
        elif ( ( length_nt == None ) and ( length_aa != None ) ): 
            length_aa = int( length_aa )
            dsorftranscriptasso.orf_length_nt = ( ( length_aa + 1 ) * 3 )
        
        return ( dsorftranscriptasso, warning_messages_to_log, error_messages_to_log )
        
    
    
    ## find_best_dsota_subpop
    #  ----------------------
    #
    # This method allows to compute "clusters" of DSORFTranscriptAsso entries
    # according to their similarity in amino acid ORF length.
    # 
    # @param dsorftranscriptasso_list: List - The list of DSORFTranscriptAsso objects from which the 
    #                                         clusters have to be computed.
    # @param max_len_diff_dsota_clust: Integer - The maximal length difference allowed between
    #                                            two DSOTA entries that belong to the same cluster.
    #
    # @return all_sublists: List of lists - The list of DSORFTranscriptAsso regrouped by lists of 
    #                                       the entries defining the "cluster".
    #
    @staticmethod
    def find_best_dsota_subpop( dsorftranscriptasso_list, max_len_diff_dsota_clust ):
                
        # Compute the best "clusters" of DSORFTranscriptAsso 
        # based upon the ORF amino acid length
        # NB: See the documentation of the split_dsota_using_length()
        #     method for more information.
        prev_all_sublists = dsorftranscriptasso_list
        all_sublists = MergeDSOTA.split_dsota_using_length( prev_all_sublists )
        
        # While this is still possible to identify several clusters 
        # according to the method used, run the process
        while ( all_sublists != prev_all_sublists ):
            
            prev_all_sublists = all_sublists
            all_sublists = []
            
            for sublist in prev_all_sublists:
                all_sublists += MergeDSOTA.split_dsota_using_length( dsorftranscriptasso_list = sublist, 
                                                                        max_len_diff = max_len_diff_dsota_clust )
                    
        return all_sublists
        
    
    
    ## split_dsota_using_length
    #  ------------------------
    #
    # This is a static method that allows to split a list of DSORFTranscriptAsso 
    # entries into several sublists if the differences between amino acid ORF 
    # length exceed a threshold. If there are DSORFTranscriptAsso missing their 
    # ORF lengths, then they are not considered to build in the "clusters".
    # 
    # @param dsorftranscriptasso_list: List of DSORFTranscriptAsso - The list of DSORFTranscriptAsso 
    #                                                                instances to split into clusters.
    # @param max_len_diff: Integer - The maximal difference between the maximal and minimal lengths 
    #                                of DSORFTranscriptAsso so they belong to the same group (value 
    #                                included).
    #                                e.g. If max_len_diff = 3, Two DSORFTranscriptAsso will be considered
    #                                     as being part of two different "clusters" if the difference of 
    #                                     their length exceed 4.
    #
    # @return sublists_dsota: List of list of DSORFTranscriptAsso - The list of DSORFTranscriptAsso 
    #                                                               objects grouped by similar lengths.
    #
    @staticmethod
    def split_dsota_using_length( dsorftranscriptasso_list, max_len_diff=Constants.DEFAULT_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS ):
        
        # Build a dictionary that associate to each DSORFTranscriptAsso 
        # its length when it is provided
        length_dict = {}
        for dsorftranscriptasso in dsorftranscriptasso_list:
            # Fill in the dictionary if the DSORFTranscriptAsso has a length
            if ( dsorftranscriptasso.orf_length != None ):
                length_dict[ dsorftranscriptasso ] = int( dsorftranscriptasso.orf_length )
        
        # Get the sorted list of lengths and get the maximal and minimal values for these lengths
        length_list_sorted = sorted( length_dict.values() )
        max_len = max( length_list_sorted )
        min_len = min( length_list_sorted )
        
        # If the absolute difference between the maximal and minimal length is
        # higher than the threshold, then one may consider the ORF should not 
        # have been merged. Then, regroup the DSORFTranscriptAsso that belong 
        # to the "same group".
        if ( abs( max_len - min_len ) > max_len_diff ):
            
            # Compute the difference between each consecutive value
            list_of_length_diff = []
            
            for k in range( len( length_list_sorted ) - 1 ):
                list_of_length_diff.append( length_list_sorted[ k + 1 ] - length_list_sorted[ k ] )
                
            # Find the highest difference(s) in the list
            max_diff = max( list_of_length_diff )
            
            # Split the list of lengths into several lists, using the maximal difference
            # as the point of separation
            sublists_of_lengths = [ [] ]
            list_nb = 0
            
            for k in range( len( length_list_sorted ) ):
                
                sublists_of_lengths[ list_nb ].append( length_list_sorted[ k ] )
                
                if ( ( k < len( list_of_length_diff )
                       and ( list_of_length_diff[ k ] == max_diff ) ) ):
                    list_nb += 1
                    sublists_of_lengths.append( [] )
        
            # Recover the DSORFTranscriptAsso corresponding to these lengths
            # Instantiate an empty list that aims to receive the lists of "clusters"
            sublists_dsota = []
            
            for sublist in sublists_of_lengths:
                
                # Get a list of unique values
                subls = list( set( sublist ) )
                
                all_corresp_dsota = []
                
                for dsota_len_subls in subls:
                    # Get all DSORFTranscriptAsso belonging to this sublist
                    corresponding_dsota = [ dsota for ( dsota, dsota_len ) in length_dict.items() if ( dsota_len == dsota_len_subls ) ]
                    all_corresp_dsota += corresponding_dsota
                
                sublists_dsota.append( all_corresp_dsota )
        
        # Otherwise, all the DSORFTranscriptAsso belong to the same unique "cluster"
        else:
            sublists_dsota = [ dsorftranscriptasso_list ]
        
        return sublists_dsota
        