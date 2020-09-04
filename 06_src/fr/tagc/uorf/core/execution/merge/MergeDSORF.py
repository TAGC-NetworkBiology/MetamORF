# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## MergeDSORF
#  ==========
#
# This contains static methods allowing to create the appropriate objects 
# to merge DSORF entries (DS database).
# NB: All methods of this class have been optimized for multi-processing.
#
class MergeDSORF( object ):
          
    # ===============================================================================
    # Regroup the exact same ORFs together
    # ===============================================================================
           
    ## merge_exact_same_dsorf
    #  ----------------------
    #
    # This static method allows to merge a group of entries from 
    # the DSORF table of the DS database that are actually exactly 
    # describing the same ORF in an unambiguous way.
    # 
    # @param grouped_dsorf_wo_any_null: Tuple - The tuple returned by the SQLAlchemy query.
    #
    # @return 2-tuple - A 2-elements tuple that contains the following information:
    #                     - objects_to_insert: List - The list of new objects to insert and that CAN NOT be
    #                                                 instantiated by any concurrent process.
    #                     - processed_ids: List - The list of DSORF IDs that have been processed.
    #
    @staticmethod
    def merge_exact_same_dsorf( grouped_dsorf_wo_any_null ):
                
        # Instantiate a list of new entries
        # NB: The objects added to this list MUST be unique entries of the PRO database, 
        #     i.e. entries that could NOT be instantiated by a parallel process for which 
        #     the provided arguments would be different.
        objects_to_insert = []
        
        # Keep track of processed DSORF IDs
        processed_ids = []
        
        # Parse the list to get the necessary attributes to instantiate an ORF object
        orf_chromosome = grouped_dsorf_wo_any_null[ 0 ]
        orf_strand = grouped_dsorf_wo_any_null[ 1 ]
        orf_start_pos = grouped_dsorf_wo_any_null[ 2 ]
        orf_stop_pos = grouped_dsorf_wo_any_null[ 3 ]
        orf_spliced = grouped_dsorf_wo_any_null[ 4 ]
        orf_spliced_parts_count = grouped_dsorf_wo_any_null[ 5 ]
        orf_splice_starts = grouped_dsorf_wo_any_null[ 6 ]
        orf_splice_ends = grouped_dsorf_wo_any_null[ 7 ]
        orf_related_dsorfs_ids = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf_wo_any_null[ 8 ], 
                                                             fct = 'int' )
        orf_related_datasources = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf_wo_any_null[ 9 ] )
        nb_of_dsorfs_grouped = grouped_dsorf_wo_any_null[ 10 ]
                    
        # Keep track of all the IDs regrouped in this ORF
        processed_ids += orf_related_dsorfs_ids
        
        # The lowest ID of all DSORFs regrouped will be used 
        # as unique ID of the new ORF object
        orf_id = min( orf_related_dsorfs_ids )
        
        # If the ORF is not spliced and the orf_spliced_parts_count is missing,
        # then set it to 1
        if ( ( orf_spliced == False ) 
             and ( orf_spliced_parts_count == None ) ):
            orf_spliced_parts_count = 1
        
        # Instantiate the new ORF object
        orf = ORF( id = orf_id,
                   chromosome = orf_chromosome,
                   strand = orf_strand,
                   start_pos = orf_start_pos,
                   stop_pos = orf_stop_pos,
                   spliced = orf_spliced,
                   spliced_parts_count = orf_spliced_parts_count,
                   splice_starts = orf_splice_starts,
                   splice_ends = orf_splice_ends,
                   count_ds = nb_of_dsorfs_grouped,
                   count_ds_ambiguous = 0 )
        objects_to_insert.append( orf )
        
        # Register in the ORFDSAsso table the relationship between this ORF
        # and the DSORF from which it derives
        for k in range( len( orf_related_dsorfs_ids ) ):            
            orfdsasso = ORFDSAsso( orf_id = orf.id,
                                   dsorf_id = orf_related_dsorfs_ids[ k ],
                                   data_source = orf_related_datasources[ k ],
                                   ambiguous = False )
            objects_to_insert.append( orfdsasso )
            
        return ( objects_to_insert, processed_ids )
        
          
    # ===============================================================================
    # Information to developers
    # ===============================================================================
      
    # The merging of "same" and "similar" ORFs is not multi-processed 
    # (contrary the merging of "exact same" ORFs, as recurrent accesses
    # to the session with the PRO database and flush are performed. 
    # Indeed, multi-process this process would ask to use lockers 
    # many often, which should not improve in a significant way the 
    # computation time.
    