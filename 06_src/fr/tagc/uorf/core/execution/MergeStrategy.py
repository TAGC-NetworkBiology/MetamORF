# -*- coding: utf-8 -*-

import ConfigParser
import os
import pandas as pd
import itertools

from sqlalchemy import func
from sqlalchemy import or_, and_

from multiprocessing import cpu_count
from pathos.multiprocessing import ProcessingPool as Pool


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.execution.merge import *

from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.genetics.GeneticsUtil import GeneticsUtil
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# ================================================================================
# GENERAL INFORMATION REGARDING THE MULTI-PROCESSING
#
# In order to lower as most as possible the highly time-consuming steps of 
# this strategy, some processed are run concurrently.
# 
# Here are some generics important information regarding the multi-processing:
# - Multi-processing has been chosen instead of multi-threading, in particular 
#   to side-step the GIL (Global Interpreter Lock).
# - The processes use all available / provided CPUs to run.
# - The pathos package has been chosen as it allows to serialize functions which 
#   are not top-level ones, such as class static methods (contrary to the 
#   multiprocessing built-in package for instance).
# - Unless contrary information, the processes are run in pools which is one of 
#   the most convenient mean to parallelize the execution of a function across 
#   multiple inputs. The Pool map() method is used to do so.
# - As access of objects shared by the several processes (using locks and semaphores 
#   for instance), could slower a lot the speed of execution when the process 
#   regularly need to access these variables, it has been decided to do not access 
#   to shared resources. Usually several lists of objects are returned by the 
#   parallelized processed in order to ensure database integrity. Please see the 
#   documentation of the methods for more information about this. 
# - In order to use efficiently the Pool map() method, the arguments needed by the
#   forked function are embedded into tuples of fixed-size. See the documentation
#   of the methods used with map for more information about its expected parameter.
#
# ================================================================================


## MergeStrategy
#  =============
#
# This class is a strategy aiming to create a new PRO database 
# by merging the data from the DS database.
#
class MergeStrategy( object ):
                
    ## Class variables
    #  ---------------
    #    
    # List of attributes to look at for merging the same DSORFs together
    ATTRIBUTES_FOR_MERGING_SAME_DSORF = [ 'chromosome', 'strand', 'start_pos', 'stop_pos', 'spliced', 
                                          'spliced_parts_count', 'splice_starts', 'splice_ends' ]
    
    # List of attributes to look at for merging the similar DSORFs together
    ATTRIBUTES_FOR_MERGING_SIMILAR_DSORF = ATTRIBUTES_FOR_MERGING_SAME_DSORF
    
    # List of attributes to look at for merging DSTranscripts together
    ATTRIBUTES_FOR_MERGING_SIMILAR_DSTRANSCRIPT = [ 'strand', 'start_pos', 'end_pos', 
                                                    'cds_start_pos', 'cds_stop_pos' ]
    
    # List of attributes for which the values needs to be check 
    # prior to merge two DSTranscript entries together
    ATT_TO_CHECK_FOR_MERGING_SAME_DSTRANSCRIPT = [ 'strand', 'start_pos', 'end_pos', 
                                                   'cds_start_pos', 'cds_stop_pos', 'rna_biotype' ]
    

    ## Constructor of MergeStrategy
    #  ----------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - species: String - The name of the species in the database.
    #     - sqce_consensus_ambig_threshold: Float[0,1] - The threshold to use to compute the 
    #                                                    sequence consensus interval.
    #     - max_len_diff_dsota_clust: Integer (>0) - The maximal difference between the max. 
    #                                                and min. lengths of DSORFTranscriptAsso 
    #                                                entries to belong to the same "cluster".
    #     - thread_nb: Integer (>0) - The number of threads that can be use.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    # @throw DenCellORFException: If the number of threads provided is not an integer.
    # @throw DenCellORFException: If the number of threads provided is not a positive integer.
    #
    def __init__( self ):

        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, not_none=True )

        if configfile:
            self.configfile = configfile
            if not os.path.exists( configfile ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            self.parse_config()
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' See the documentation for more information.' )
            
        # Check if the checkDSOTA option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_CHECK_DSOTA_COHERENCE, not_none = False ):
            self.check_dsota_coherence = True
        else:
            self.check_dsota_coherence = False
            
        # Check if the computeConsensus option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_COMPUTE_SQCE_CONSENSUS, not_none = False ):
            self.compute_consensus = True
        else:
            self.compute_consensus = False
            
        # Get the number of threads available
        self.thread_nb = OptionManager.get_instance().get_option( OptionConstants.OPTION_THREAD_NB, 
                                                                  not_none = False )
        available_thread_nb = cpu_count()
        if self.thread_nb:
            try:
                self.thread_nb = int( self.thread_nb )
            except:
                raise DenCellORFException( 'MergeStrategy: The value provided for the number of threads' +
                                           ' needs to be an integer (provided value: ' + 
                                           str( self.thread_nb ) + ').' )
            else:
                if ( self.thread_nb < 1 ):
                    raise DenCellORFException( 'MergeStrategy: The value provided for the number of threads' +
                                               ' needs to be an integer greater than 1 (provided value: ' + 
                                               str( self.thread_nb ) + ').' )
                    
                if ( self.thread_nb > available_thread_nb ):
                    Logger.get_instance().info( 'The number of threads provided (' + str( self.thread_nb ) +
                                                ') is greater than the number of threads actually' +
                                                ' available(' +  str( available_thread_nb ) +
                                                '). Hence, ' + str( available_thread_nb ) +
                                                ' threads will be used for the computation.' )
        else:
            self.thread_nb = available_thread_nb
            
        Logger.get_instance().debug( 'MergeStrategy: ' + str( self.thread_nb ) + 
                                     ' threads will be used during the merging.' )



    ## parse_config
    #  ------------
    #
    # Parse the config file to retrieve required information.
    #
    # @throw DenCellORFException: When expected sections / options are not provided in the config file.
    # @throw DenCellORFException: When the threshold to use as value for the minimal absolute difference 
    #                             in genomic lengths at which the DSORF entries should not be considered
    #                             to build the PRO database cannot be converted into an interger or is a 
    #                             negative value different to -1.
    # @throw DenCellORFException: When the threshold to use to compute the sequence consensus cannot
    #                             be converted into a float or is outside of the [0,1] interval.
    # @throw DenCellORFException: When the value of the maximal difference between the max. and min.
    #                             lengths of DSORFTranscriptAsso entries to belong to the same "cluster"
    #                             cannot be converted into an integer or is negative.
    #
    def parse_config( self ):
        
        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
        
        # Get the value of the minimal absolute difference in genomic 
        # lengths at which the DSORF entries should not be considered 
        # to build the PRO database
        if config.has_option( Constants.CONFIG_SECTION_MERGE_PARAMETERS, Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_GEN_LEN_DIFF_THRESHOLD ):
            self.gen_len_diff_threshold = config.get( Constants.CONFIG_SECTION_MERGE_PARAMETERS, 
                                                      Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_GEN_LEN_DIFF_THRESHOLD )
            try:
                self.gen_len_diff_threshold = int( self.gen_len_diff_threshold )
            except:
                raise DenCellORFException( 'MergeStrategy.parse_config(): The threshold to used as minimal' +
                                           ' value for the absolute difference in genomic lengths at which' +
                                           ' the DSORF entries should be not be considered to build the' +
                                           ' PRO database needs to be a float (provided value: ' + 
                                           str( self.gen_len_diff_threshold ) + ' ).' )
            else:
                if ( ( self.gen_len_diff_threshold < 0 ) 
                     and ( self.gen_len_diff_threshold != Constants.GEN_LEN_DIFF_THRESHOLD_IGNORE ) ):
                    raise DenCellORFException( 'MergeStrategy.parse_config(): The threshold to used as minimal' +
                                               ' value for the absolute difference in genomic lengths at which' +
                                               ' the DSORF entries should be not be considered to build the' +
                                               ' PRO database needs to be a positive float (provided value: ' + 
                                               str( self.gen_len_diff_threshold ) + ' ).' )
        else:
            self.gen_len_diff_threshold = Constants.DEFAULT_MERGE_GEN_LEN_DIFF_THRESHOLD
            Logger.get_instance().debug( 'MergeStrategy.parse_config(): As there was no value provided' +
                                         ' for the threshold the absolute difference in genomic lengths' +
                                         ' at which the DSORF entries should be not be considered to' +
                                         ' build the PRO database in the config file, the default value' +
                                         ' of ' + str( Constants.DEFAULT_MERGE_GEN_LEN_DIFF_THRESHOLD ) + 
                                         ' will be used.' )
        
        
        # Get the value of the threshold to use when computing 
        # the consensus sequence if it is provided
        if config.has_option( Constants.CONFIG_SECTION_MERGE_PARAMETERS, Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_SQCE_CONSENSUS_AMBIG_THRESHOLD ):
            self.sqce_consensus_ambig_threshold = config.get( Constants.CONFIG_SECTION_MERGE_PARAMETERS, 
                                                              Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_SQCE_CONSENSUS_AMBIG_THRESHOLD )
            try:
                self.sqce_consensus_ambig_threshold = float( self.sqce_consensus_ambig_threshold )
            except:
                raise DenCellORFException( 'MergeStrategy.parse_config(): The threshold to use to compute' +
                                           ' the sequence consensus needs to be a float (provided value: ' + 
                                           str( self.sqce_consensus_ambig_threshold ) + ' ).' )
            else:
                if ( ( self.sqce_consensus_ambig_threshold < 0 ) 
                     or ( self.sqce_consensus_ambig_threshold > 1 ) ):
                    raise DenCellORFException( 'MergeStrategy.parse_config(): The threshold to use to' +
                                               ' compute the sequence consensus needs to be a float' +
                                               ' between 0 and 1 (provided value: ' + 
                                               str( self.sqce_consensus_ambig_threshold ) + ' ).' )
        else:
            self.sqce_consensus_ambig_threshold = Constants.DEFAULT_SQCE_CONSENSUS_AMBIG_THRESHOLD
            Logger.get_instance().debug( 'MergeStrategy.parse_config(): As there was no value provided' +
                                         ' for the threshold to use to compute the sequence consensus' +
                                         ' in the config file, the default value of ' + 
                                         str( Constants.DEFAULT_SQCE_CONSENSUS_AMBIG_THRESHOLD ) + 
                                         ' will be used.' )
    
        # Get the value for the maximal difference between the 
        # max. and min. lengths of DSORFTranscriptAsso to make them belong 
        # to the same "cluster"
        if config.has_option( Constants.CONFIG_SECTION_MERGE_PARAMETERS, Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS ):
            self.max_len_diff_dsota_clust = config.get( Constants.CONFIG_SECTION_MERGE_PARAMETERS, 
                                                        Constants.CONFIG_SECTION_MERGE_PARAMETERS_ITEM_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS )
            try:
                self.max_len_diff_dsota_clust = int( self.max_len_diff_dsota_clust )
            except:
                raise DenCellORFException( 'MergeStrategy.parse_config(): The value for the maximal' +
                                           ' difference between the max. and min. lengths of' +
                                           ' DSORFTranscriptAsso to make them belong to the same "cluster"' +
                                           ' needs to be an integer (provided value: ' + 
                                           str( self.max_len_diff_dsota_clust ) + ' ).' )
            else:
                if ( self.max_len_diff_dsota_clust < 0 ):
                    raise DenCellORFException( 'MergeStrategy.parse_config(): The value for the maximal' +
                                               ' difference between the max. and min. lengths of' +
                                               ' DSORFTranscriptAsso to make them belong to the same "cluster"' +
                                               ' needs to be a positive integer (provided value: ' +  
                                               str( self.sqce_consensus_ambig_threshold ) + ' ).' )
        else:
            self.max_len_diff_dsota_clust = Constants.DEFAULT_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS
            Logger.get_instance().debug( 'MergeStrategy.parse_config(): As there was no value for the' +
                                         ' maximal difference between the max. and min. lengths of' +
                                         ' DSORFTranscriptAsso to make them belong to the same "cluster"' +
                                         ' in the config file, the default value of ' + 
                                         str( Constants.DEFAULT_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS ) + 
                                        ' will be used.' )
            
            
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete missing information and merge the data.
    # 
    # @throw DenCellORFException: When an exception has been raised during the DatabaseCheck.
    # @throw DenCellORFException: When the DSORFTranscriptAsso table does not contain any entry.
    # @throw DenCellORFException: When the DSORF table does not contain any entry with start 
    #                             position coordinates.
    # @throw DenCellORFException: When the PRO database is not empty.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check the DS and PRO databases 
        # are reachable prior to the merging of data
        Logger.get_instance().info( 'Checking the databases prior to the merging step...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( 'An error occurred whilst checking the database prior to' +
                                       ' merging step.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        
        # Check there is at least one DSORFTranscriptAsso entry 
        # in the database prior to merge the data.
        dsorftranscriptasso_count = SQLManagerDS.get_instance().get_session().query( DSORFTranscriptAsso ).count()
        SQLManagerDS.get_instance().close_session()
        
        if ( dsorftranscriptasso_count == 0 ):
            raise DenCellORFException( 'There is not any entry found in the DSORFTranscriptAsso' +
                                       ' table of the ' + SQLManagerDS.get_instance().get_db_name() + 
                                       ' database (DS database). Hence, the merging of data will' +
                                       ' be stopped.' )
        
        
        # Check if the lift over has been performed (check on the start position)
        dsorf_with_liftov_coord_count = SQLManagerDS.get_instance().get_session().query( DSORF ).filter( DSORF.start_pos != None ).count()
        SQLManagerDS.get_instance().close_session()
        
        if ( dsorf_with_liftov_coord_count == 0 ):
            raise DenCellORFException( 'It seems that the lift over has not been performed on the' +
                                       ' DS database. Make sure to run the LiftOver strategry prior to use' +
                                       ' the MergeStrategy (see the documentation for more information).' +
                                       ' The merging of data will thus be stopped.' )
        
        
        # Check there is no entries in the tables of the PRO database prior to merge the data.
        progene_count = SQLManagerPRO.get_instance().get_session().query( PROGene ).count()
        prometadata_count = SQLManagerPRO.get_instance().get_session().query( PROMetadata ).count()
        orf_count = SQLManagerPRO.get_instance().get_session().query( ORF ).count()
        transcript_count = SQLManagerPRO.get_instance().get_session().query( Transcript ).count()
        orftranscriptasso_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
        SQLManagerPRO.get_instance().close_session()
        
        if ( progene_count, prometadata_count, orf_count, transcript_count, orftranscriptasso_count ) != ( 0, 0, 0, 0, 0 ):
            raise DenCellORFException( 'Entries have been found in the PRO database.' +
                                       ' Make sure to use an empty PRO database prior to run the merge' +
                                       ' strategy or to use the "-f" option.' +
                                       ' Please see the documentation for more information.' )
            
        # Register the name of the DS database used to create the PRO one
        metadata_ds_db_name = PROMetadata( parameter = Constants.METATABLE_DS_ORIGIN,
                                           value = SQLManagerDS.get_instance().get_db_name(),
                                           description = Constants.METATABLE_DS_ORIGIN_DESCRIPTION )
        SQLManagerPRO.get_instance().get_session().add( metadata_ds_db_name )
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        
        # Regroup the same ORFs together
        self.copy_conserved_tables()
        
        # Regroup the same ORFs together
        self.merge_dsorfs()
        
        # Regroup the same transcripts together
        self.merge_dstranscripts()
        
        # Recover all the DSORFTranscriptAsso, 
        # and associate them with their actual ORFs and transcript
        self.merge_dsorftranscriptasso()
        
        # Clean the database by removing parent entries that have no child
        self.clean_pro_database()
        
    
    
    ## copy_conserved_tables
    #  ---------------------
    #
    # This methods aims to "copy" the content of the DS database tables
    # for which there is no need to merge the data, into the PRO database.
    # The content of the following tables is treated:
    #  - Metadata table (copied into PROMetadata)
    #  - Gene table (copied into PROGene)
    #  - GeneAlias table (copied into PROGeneAlias)
    #
    # NB: For some of these entries, only a part of the attributes is copied.
    # 
    def copy_conserved_tables( self ):
        
        ## Copy all the entries of:
        #  - Metadata table (into PROMetadata)
        #  - Gene table (into PROGene)
        #  - GeneAlias table (into PROGeneAlias)
        
        # The entries of these tables are just copied from the DS database
        # to the corresponding tables of the PRO database.
        
        Logger.get_instance().info( 'Copying the entries of the gene-related and metadata-related' +
                                    ' tables into the PRO database.')

        objects_to_insert = []
                    
        # Copy all the Metadata entries
        ds_metadata_all = SQLManagerDS.get_instance().get_session().query( Metadata ).all()
        
        for ds_metadata in ds_metadata_all:
            pro_metadata = PROMetadata( parameter = ds_metadata.parameter,
                                        value = ds_metadata.value,
                                        description = ds_metadata.description )        
            objects_to_insert.append( pro_metadata )
        
        
        # Copy all the Gene entries
        ds_gene_all = SQLManagerDS.get_instance().get_session().query( Gene ).all()
        
        for ds_gene in ds_gene_all:
            pro_gene = PROGene( gene_id = ds_gene.gene_id,
                                chromosome = ds_gene.chromosome )            
            objects_to_insert.append( pro_gene )
        
        
        # Copy all the GeneAlias entries
        ds_genealias_all = SQLManagerDS.get_instance().get_session().query( GeneAlias ).all()
        
        for ds_genealias in ds_genealias_all:
            pro_genealias = PROGeneAlias( gene_id = ds_genealias.gene_id,
                                          alias = ds_genealias.alias )            
            objects_to_insert.append( pro_genealias )
            
        
        # Insert the newly created objects in the database
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert,
                                     filename = 'conserved_tables',
                                     process = 'copy the content of the "conserved" tables' )
        SQLManagerDS.get_instance().close_session()
        
        Logger.get_instance().info( 'The entries of the gene and metadata tables have been copied.')

    
    
    # ===============================================================================
    # Methods related to the merging of DSORFs
    # ===============================================================================        
        
    ## merge_dsorfs
    #  ------------
    #
    # This methods aims to merge the similar entries of the DSORF table 
    # (DS database) into new entries of the ORF table (PRO database).
    #
    def merge_dsorfs( self ):
        
        Logger.get_instance().info( 'Starting to merge the entries of the DSORF table.')
        
        ## Regroup the exact same ORFs together
        #  ------------------------------------
                
        # First, 
        # - Get the list of DSORFs regrouped by ORFs sharing the same values for 
        #   the following attributes: chromosome, strand, start position, stop position, 
        #   spliced, spliced parts count, splice starts and ends, AND such as the values 
        #   of ALL of these attributes are provided (i.e. not NULL).
        # - For each entry of the list (i.e. grouped DSORF entries), create a new ORF 
        #   entry in the PRO database
        #
        Logger.get_instance().info( 'Starting to regroup the perfectly identical entries of the DSORF' +
                                    ' table (DS database) into new ORF entries (PRO database).' )
        
        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Querying the DS database' +
                                     ' to regroup the exact same ORFs together.')
        grouped_dsorf_wo_any_null_base_query = SQLManagerDS.get_instance().get_session().query(
                                                                                                    DSORF.chromosome,
                                                                                                    DSORF.strand,
                                                                                                    DSORF.start_pos,
                                                                                                    DSORF.stop_pos,
                                                                                                    DSORF.spliced,
                                                                                                    DSORF.spliced_parts_count,
                                                                                                    DSORF.splice_starts,
                                                                                                    DSORF.splice_ends,
                                                                                                    func.group_concat( DSORF.id ),
                                                                                                    func.group_concat( DSORF.data_source ),
                                                                                                    func.count( DSORF.id )
                                                                                                ).filter(
                                                                                                            DSORF.chromosome != None,
                                                                                                            DSORF.strand != None,
                                                                                                            DSORF.start_pos != None,
                                                                                                            DSORF.stop_pos != None,
                                                                                                            DSORF.spliced != None,
                                                                                                            DSORF.spliced_parts_count != None,
                                                                                                            DSORF.splice_starts != None,
                                                                                                            DSORF.splice_ends != None
                                                                                                        )
        
        # If necessary, filter out all the DSORF entries that have a difference
        # between their genomic lengths exceeding the provided threshold
        if ( self.gen_len_diff_threshold != Constants.GEN_LEN_DIFF_THRESHOLD_IGNORE ):
            grouped_dsorf_wo_any_null_excl_diff_ov_th = grouped_dsorf_wo_any_null_base_query.filter( 
                                                                                                        DSORF.genomic_length_diff < self.gen_len_diff_threshold 
                                                                                                    )
        else:
            grouped_dsorf_wo_any_null_excl_diff_ov_th = grouped_dsorf_wo_any_null_base_query
            
        grouped_dsorf_wo_any_null_all = grouped_dsorf_wo_any_null_excl_diff_ov_th.group_by(
                                                                                                DSORF.chromosome,
                                                                                                DSORF.strand,
                                                                                                DSORF.start_pos,
                                                                                                DSORF.stop_pos,
                                                                                                DSORF.spliced,
                                                                                                DSORF.spliced_parts_count,
                                                                                                DSORF.splice_starts,
                                                                                                DSORF.splice_ends
                                                                                            ).all()
                    
                                                                               
        # Get the number total number of elements expected to be treated and
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( grouped_dsorf_wo_any_null_all ) )
        
        # Keep track of the IDs of all DSORFs that have already been merged
        grouped_dsorf_all_processed_ids = []
                
        # Instantiate the list of new objects to be added to the PRO database
        objects_to_insert = []
                         
        # For each unique component of this list (i.e. each merged element, i.e. each ORF 
        # identified as unique), create a new ORF in the PRO database
        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Regrouping the perfectly' +
                                     ' identical entries of the DSORF table (DS database) into' +
                                     ' new ORF entries (PRO database).' )
        
        # NB: The merging of perfectly identical DSORF is multi-processed 
        
        # Instantiate the pool
        p = Pool( self.thread_nb )
        
        # For each group of DSORF to merge, run the MergeDSORF.merge_exact_same_dsorf()
        # static method that will instantiate all the appropriate ORF and ORFDSAsso to 
        # insert in the PRO database
        m = MergeDSORF()
        all_objects_to_insert = p.map( m.merge_exact_same_dsorf, grouped_dsorf_wo_any_null_all )
        p.close()
        # Wait for all processes to be completed
        p.join()
                
        # Get the new objects to add to the session
        for obj_to_insert in all_objects_to_insert:
            
            ProgressionBar.get_instance().increase_and_display()
            
            # Parse the output of the MergeDSORF.merge_exact_same_dsorf() method
            # and add the entries to the list to insert to the database
            ( new_objects, processed_ids ) = obj_to_insert
        
            objects_to_insert += new_objects
            grouped_dsorf_all_processed_ids += processed_ids           
        
        # Delete the pool instance
        p.clear()  
            
        # Insert the newly created objects in the database
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert,
                                     filename = 'exact_same_orfs',
                                     process = 'grouping exact same ORFs' )
        SQLManagerPRO.get_instance().close_session()
        SQLManagerDS.get_instance().close_session()
        
                    
        ## Regroup the same ORFs together
        #  ------------------------------
        
        # NB: This process is not multi-processed. Please see the documentation of the
        #     MergeDSORF class for more information.
        
        # Then, 
        # - Excluding all the DSORF that have already been processed in the first step, 
        #   get the list of DSORFs regrouped by ORFs sharing the same values for the following 
        #   attributes: chromosome, strand, start position, stop position, spliced, spliced 
        #   parts count, splice starts and ends, 
        #   AND such as the values of the following attributes are provided (i.e. not NULL): 
        #   chromosome, strand, start position stop position and spliced.
        # - For each entry of the list (i.e. grouped DSORF entries), if they can be merged 
        #   with one of the previously created ORF do it, otherwise, create a new entry.
        #
        Logger.get_instance().info( 'Starting to regroup the identical entries of the DSORF' +
                                    ' table (DS database) into new ORF entries (PRO database).' )
        
        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Querying the DS database' +
                                     ' to regroup the same ORFs together.')
        
        grouped_dsorf_wo_null_base_query = SQLManagerDS.get_instance().get_session().query(
                                                                                                DSORF.chromosome,
                                                                                                DSORF.strand,
                                                                                                DSORF.start_pos,
                                                                                                DSORF.stop_pos,
                                                                                                DSORF.spliced,
                                                                                                DSORF.spliced_parts_count,
                                                                                                DSORF.splice_starts,
                                                                                                DSORF.splice_ends,
                                                                                                func.group_concat( DSORF.id ),
                                                                                                func.group_concat( DSORF.data_source ),
                                                                                                func.count( DSORF.id )
                                                                                            ).filter( 
                                                                                                        DSORF.id.notin_( grouped_dsorf_all_processed_ids )
                                                                                                    ).filter(
                                                                                                                DSORF.chromosome != None,
                                                                                                                DSORF.strand != None,
                                                                                                                DSORF.start_pos != None,
                                                                                                                DSORF.stop_pos != None,
                                                                                                                or_( and_( DSORF.spliced == True,
                                                                                                                           DSORF.splice_starts != None,
                                                                                                                           DSORF.splice_ends != None ),
                                                                                                                     DSORF.spliced == False )                                                                                                                     
                                                                                                            )
        
        # If necessary, filter out all the DSORF entries that have a difference
        # between their genomic lengths exceeding the provided threshold
        if ( self.gen_len_diff_threshold != Constants.GEN_LEN_DIFF_THRESHOLD_IGNORE ):            
            grouped_dsorf_wo_null_excl_diff_ov_th = grouped_dsorf_wo_null_base_query.filter( 
                                                                                                or_( DSORF.genomic_length_diff < self.gen_len_diff_threshold,
                                                                                                     DSORF.genomic_length_diff == None )
                                                                                            )
        else:
            grouped_dsorf_wo_null_excl_diff_ov_th = grouped_dsorf_wo_null_base_query
            
        grouped_dsorf_wo_null_all = grouped_dsorf_wo_null_excl_diff_ov_th.group_by(
                                                                                        DSORF.chromosome,
                                                                                        DSORF.strand,
                                                                                        DSORF.start_pos,
                                                                                        DSORF.stop_pos,
                                                                                        DSORF.spliced,
                                                                                        DSORF.spliced_parts_count,
                                                                                        DSORF.splice_starts,
                                                                                        DSORF.splice_ends,
                                                                                    ).all()
        
        
        # For each unique component of this list (i.e. each merged element), 
        # check if there is an existing ORF entry sharing the same properties in the 
        # PRO database for all available properties.
        # If there are ORFs sharing the same properties in the PRO database, 
        # merge them together. Otherwise, create a new ORF entry in the PRO database.
        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Regrouping the same DSORFs' +
                                     ' to merge them with existing ORF entries (PRO database)'+
                                     ' or to create new ORF entries (PRO database).' )
        
        # Get the number total number of elements expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( grouped_dsorf_wo_null_all ) )
        
        for grouped_dsorf_wo_null in grouped_dsorf_wo_null_all:
        
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            objects_to_insert = []
            
            # Parse the list to get the necessary attributes to instantiate an ORF object
            orf_chromosome = grouped_dsorf_wo_null[ 0 ]
            orf_strand = grouped_dsorf_wo_null[ 1 ]
            orf_start_pos = grouped_dsorf_wo_null[ 2 ]
            orf_stop_pos = grouped_dsorf_wo_null[ 3 ]
            orf_spliced = grouped_dsorf_wo_null[ 4 ]
            orf_spliced_parts_count = grouped_dsorf_wo_null[ 5 ]
            orf_splice_starts = grouped_dsorf_wo_null[ 6 ]
            orf_splice_ends = grouped_dsorf_wo_null[ 7 ]
            orf_related_dsorfs_ids = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf_wo_null[ 8 ], 
                                                                 fct = 'int' )
            orf_related_datasources = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf_wo_null[ 9 ] )
            nb_of_dsorfs_grouped = grouped_dsorf_wo_null[ 10 ]
                        
            # Keep track of all the IDs regrouped in this ORF
            grouped_dsorf_all_processed_ids += orf_related_dsorfs_ids
            
            # If there is already an ORF looking like this one in the database, 
            # then merge these two ORFs i.e. create a new ORFDSAsso entry, keep 
            # record of the relationship with the corresponding ORF, and increase 
            # of one the count of (non-ambiguous) DSORFs associated to it.
            
            # Get the list of attributes which are not null for the current element 
            # of the list (i.e. the elements that do not equal None) and that should 
            # be used as filter to query the ORF table
            attributes_to_use_for_filter = {}
            
            for att in MergeStrategy.ATTRIBUTES_FOR_MERGING_SAME_DSORF:
                # Get the value of the attribute
                att_value = eval( 'orf_' + att )
                # Add the attribute as a filter to use only if it is not null
                if ( att_value != None ):
                    attributes_to_use_for_filter[ att ] = att_value
            
            # Query the PRO database to the the ORF(s) that look like the current entry
            existing_orf_query = SQLManagerPRO.get_instance().get_session().query( ORF )
            # Sequentially apply the filters on the query
            for ( att, value ) in attributes_to_use_for_filter.items():
                existing_orf_query = existing_orf_query.filter( eval( 'ORF.' + att ) == value )
            
            existing_orf = existing_orf_query.all()
                                                                                            

            # If there is at least one ORF returned, i.e. if there is at least one 
            # ORF entry in the PRO database that may match the current element of the 
            # list, then merge the DSORF(s) of the current element of the list with each 
            # of these ORF entries. In other words, for each ORF entry that matches with 
            # the current DSORF(s), create a new ORFDSAsso entry, keep track of the 
            # relationship to it and increase of one the count of DSORFs associated to it.
            if ( len( existing_orf ) > 0 ):
                
                for orf in existing_orf:
                
                    # Increase the DS count of one
                    orf.count_ds += 1
                    objects_to_insert.append( orf )
                    
                    # Create the new ORFDSAsso
                    for k in range( len( orf_related_dsorfs_ids ) ):
                        orfdsasso = ORFDSAsso( orf_id = orf.id,
                                               dsorf_id = orf_related_dsorfs_ids[ k ],
                                               data_source = orf_related_datasources[ k ],
                                               ambiguous = False )
                        objects_to_insert.append( orfdsasso )

            # Otherwise create a new ORF entry, using the provided attributes
            else:
                
                # The lowest ID of all DSORFs regrouped will be used 
                # as unique ID of the new ORF object
                orf_id = min( orf_related_dsorfs_ids )
                
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
                
                # Register in the ORFDSAsso table the relationship between this ORF and
                # the DSORF from which it derives
                for k in range( len( orf_related_dsorfs_ids ) ):
                    
                    orfdsasso = ORFDSAsso( orf_id = orf.id,
                                           dsorf_id = orf_related_dsorfs_ids[ k ],
                                           data_source = orf_related_datasources[ k ],
                                           ambiguous = False )
                    objects_to_insert.append( orfdsasso )
                
            
            # Add the new objects to the session (PRO database), and flush the session
            # so the query on the next step will return up-to-date results
            SQLManagerPRO.get_instance().add_and_flush( objects_to_add = objects_to_insert, 
                                                        process = 'grouping same ORFs' )
        
        # Commit the changes and close the session
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        SQLManagerDS.get_instance().close_session()
                
        
                
        ## Regroup the ORFs that look similar together
        #  -------------------------------------------
        
        # NB: This process is not multi-processed. Please see the documentation of the
        #     MergeDSORF class for more information.
        
        # Finally, 
        # - Group all the DSORFs that have not already been processed in the previous 
        #   steps but sharing the same values for the following attributes:
        #   chromosome, strand, start position, stop position, spliced, 
        #   spliced parts count, splice starts and ends, 
        #   AND such as the chromosome name of the ORF is known 
        #   AND for which at least two of the following attributes are provided (i.e. not NULL):
        #   strand, start, stop position
        # - For each entry of the list (i.e. grouped DSORF entries) , search if these DSORFs can
        #   be merged with one (some) of the previously created ORF entry (entries).
        #
        Logger.get_instance().info( 'Starting to regroup the similar entries of the DSORF' +
                                    ' table (DS database) into existing ORF entries (PRO database).' )

        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Querying the DS database' +
                                     ' to regroup the similar ORFs together.')
        
        grouped_dsorf_all = SQLManagerDS.get_instance().get_session().query( 
                                                                                DSORF.chromosome,
                                                                                DSORF.strand,
                                                                                DSORF.start_pos,
                                                                                DSORF.stop_pos,
                                                                                DSORF.spliced,
                                                                                DSORF.spliced_parts_count,
                                                                                DSORF.splice_starts,
                                                                                DSORF.splice_ends,
                                                                                func.group_concat( DSORF.id ),
                                                                                func.group_concat( DSORF.data_source ),
                                                                                func.count( DSORF.id )
                                                                            ).filter( 
                                                                                        DSORF.id.notin_( grouped_dsorf_all_processed_ids )
                                                                                    ).filter(
                                                                                                and_(
                                                                                                        DSORF.chromosome != None,
                                                                                                        or_(
                                                                                                                and_( DSORF.strand != None, DSORF.start_pos != None ),
                                                                                                                and_( DSORF.strand != None, DSORF.stop_pos != None ),
                                                                                                                and_( DSORF.start_pos != None, DSORF.stop_pos != None )
                                                                                                            )
                                                                                                    )
                                                                                            ).group_by(
                                                                                                        DSORF.chromosome,
                                                                                                        DSORF.strand,
                                                                                                        DSORF.start_pos,
                                                                                                        DSORF.stop_pos,
                                                                                                        DSORF.spliced,
                                                                                                        DSORF.spliced_parts_count,
                                                                                                        DSORF.splice_starts,
                                                                                                        DSORF.splice_ends,
                                                                                                       ).all()
                
        
        # For each unique component of this list (i.e. each merged element), 
        # check if there is an ORF sharing the same (provided) properties 
        # in the PRO database
        Logger.get_instance().debug( 'MergeStrategy.merge_dsorfs(): Regrouping the similar' +
                                     ' entries of the DSORF table (DS database) with existing' +
                                     ' ORF entries (PRO database).' )
        
        # Get the number total number of elements expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( grouped_dsorf_all ) )
        
        for grouped_dsorf in grouped_dsorf_all:
        
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            objects_to_update = []
            
            # Parse the list to get the necessary attributes to instantiate an ORF object
            orf_chromosome = grouped_dsorf[ 0 ]
            orf_strand = grouped_dsorf[ 1 ]
            orf_start_pos = grouped_dsorf[ 2 ]
            orf_stop_pos = grouped_dsorf[ 3 ]
            orf_spliced = grouped_dsorf[ 4 ]
            orf_spliced_parts_count = grouped_dsorf[ 5 ]
            orf_splice_starts = grouped_dsorf[ 6 ]
            orf_splice_ends = grouped_dsorf[ 7 ]
            orf_related_dsorfs_ids = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf[ 8 ], 
                                                                 fct = 'int' )
            orf_related_datasources = GeneralUtil.string_to_list( str_to_convert = grouped_dsorf[ 9 ] )
            nb_of_dsorfs_grouped = grouped_dsorf[ 10 ]
            
            # If there is already an ORF looking like this one in the database, 
            # then merge these two ORFs, i.e. create a new ORFDSAsso entry, 
            # to keep record of the relationship with the corresponding ORF,
            # and increase the count of ambiguous DSORFs associated to it of one.
            
            # Get the list of attributes which are not null for the current element 
            # of the list (i.e. that do not equal None) and that should be use as 
            # filter to query the ORF table
            attributes_to_use_for_filter = {}
            
            for att in MergeStrategy.ATTRIBUTES_FOR_MERGING_SIMILAR_DSORF:
                # Get the value of the attribute
                att_value = eval( 'orf_' + att )
                # Add the attribute as a filter to use only if it is not null
                if ( att_value != None ):
                    attributes_to_use_for_filter[ att ] = att_value
            
            # Query the PRO database to get the ORF(s) that look like the current entry
            existing_orf_query = SQLManagerPRO.get_instance().get_session().query( ORF )
            # Sequentially apply the filters on the query
            for ( att, value ) in attributes_to_use_for_filter.items():
                existing_orf_query = existing_orf_query.filter( eval( 'ORF.' + att ) == value )
            
            existing_orf = existing_orf_query.all()                                                                 

            # If there is at least one ORF returned, i.e. if there is at least one 
            # ORF entry in the PRO database that may match the current element of the 
            # list, then merge the DSORF(s) of the current element of the list with each 
            # of these ORF entries. In other words, for each ORF that may match with the
            # current DSORF(s), create a new ORFDSAsso entry, keep track of the relationship 
            # to it and increase of one the count of ambiguous DSORFs associated to it.
            # Otherwise the DSORFs grouped together are not registered in the PRO database 
            # (as too many essential information are missing to create a new entry).
            if ( len( existing_orf ) > 0 ):
                
                for orf in existing_orf:
                
                    # Increase the DS ambiguous count of one
                    orf.count_ds_ambiguous += 1
                    objects_to_update.append( orf )
                    
                    # Create the new ORFDSAsso
                    for k in range( len( orf_related_dsorfs_ids ) ):
                        orfdsasso = ORFDSAsso( orf_id = orf.id,
                                               dsorf_id = orf_related_dsorfs_ids[ k ],
                                               data_source = orf_related_datasources[ k ],
                                               ambiguous = True )
                        objects_to_update.append( orfdsasso )
            
                # Add the updated objects to the session (PRO database), and flush the session, 
                # so the query on the next step will return up-to-date results
                SQLManagerPRO.get_instance().add_and_flush( objects_to_add = objects_to_update, 
                                                            process = 'grouping similar ORFs' )
        
        # Commit the changes and close the session
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        SQLManagerDS.get_instance().close_session()

    
    
    # ===============================================================================
    # Methods related to the merging of DSTranscripts
    # =============================================================================== 
    
    ## merge_dstranscripts
    #  -------------------
    #
    # This methods aims to merge the similar entries of the DSTranscript table 
    # (DS database) into new entries of the Transcript table (PRO database).
    # 
    def merge_dstranscripts( self ):
        
        Logger.get_instance().info( 'Starting to merge the entries of the DSTranscript table.')
        
        objects_to_insert = []
            
        ## Regroup the same transcripts together
        #  -------------------------------------
        
        # First, 
        # - Get the list of DSTranscripts regrouped by transcripts sharing the same ID
        #   and such as the transcript does not start with the "UNKNOWN_TRANSCRIPT_" prefix 
        #   (i.e. the transcript is not a "fake" transcript).
        #   NB: This only happens when an official ID (e.g. NCBI or Ensembl transcript ID) 
        #       has been provided by the data source.
        # - For each entry of the list (i.e. grouped DSTranscript entries), create a new
        #   Transcript entry in the PRO database.
        #
        Logger.get_instance().info( 'Starting to regroup the entries of the DSTranscript table' +
                                    ' (DS database) with the same official ID into new Transcript' +
                                    ' entries (PRO database).' )
        
        Logger.get_instance().debug( 'MergeStrategy.merge_dstranscripts(): Querying the DS database' +
                                     ' to regroup the transcripts with same official ID together.')
        grouped_dstranscripts_by_ids_all = SQLManagerDS.get_instance().get_session().query(
                                                                                            DSTranscript.transcript_id,
                                                                                            DSTranscript.gene_id,
                                                                                            func.group_concat( DSTranscript.strand ),
                                                                                            func.group_concat( DSTranscript.start_pos ),
                                                                                            func.group_concat( DSTranscript.end_pos ),
                                                                                            func.group_concat( DSTranscript.cds_start_pos ),
                                                                                            func.group_concat( DSTranscript.cds_stop_pos ),
                                                                                            func.group_concat( DSTranscript.rna_biotype ),
                                                                                            func.group_concat( DSTranscript.id ),
                                                                                            func.group_concat( DSTranscript.data_source ),
                                                                                            func.count( DSTranscript.id )
                                                                                        ).filter(
                                                                                                    DSTranscript.transcript_id.notlike( Constants.PREFIX_FAKE_TRANSCRIPT + '%' )
                                                                                                ).group_by(
                                                                                                            DSTranscript.transcript_id,
                                                                                                            DSTranscript.gene_id
                                                                                                            ).order_by(
                                                                                                                        DSTranscript.transcript_id.desc()
                                                                                                                        ).all()
                                                                                                        
        # For each unique component of this list (i.e. each merged element, i.e. each 
        # transcript identified as unique), create a new Transcript in the PRO database
        Logger.get_instance().debug( 'MergeStrategy.merge_dstranscripts(): Regrouping the' +
                                     ' entries of the DSTranscript table (DS database) with' +
                                     ' the same official IDs into new Transcript entries (PRO database).' )
        
        # Get the number total number of elements expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( grouped_dstranscripts_by_ids_all ) )
        
        if ( len( grouped_dstranscripts_by_ids_all ) != 0 ):
            previous_transcript_id = grouped_dstranscripts_by_ids_all[ 0 ][ 0 ]
            all_gene_ids_for_transcript = [ grouped_dstranscripts_by_ids_all[ 0 ][ 1 ] ]
        
        for grouped_dstranscripts_by_ids in grouped_dstranscripts_by_ids_all:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
                        
            # Parse the list into a dictionary to get the necessary 
            # attributes to instantiate a Transcript object
            transcript_val = {
                                'transcript_id': grouped_dstranscripts_by_ids[ 0 ],
                                'gene_id': grouped_dstranscripts_by_ids[ 1 ],
                                'strand': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 2 ] ),
                                'start_pos': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 3 ], fct = 'int' ),
                                'end_pos': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 4 ], fct = 'int' ),
                                'cds_start_pos': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 5 ], fct = 'int' ),
                                'cds_stop_pos': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 6 ], fct = 'int' ),
                                'rna_biotype': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 7 ] ) ,
                                'related_dstranscript_ids': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 8 ], fct = 'int' ),
                                'related_datasources': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 9 ] ),
                                'nb_of_dstranscripts_grouped': grouped_dstranscripts_by_ids[ 10 ]
                              }
            
            # The lowest transcript ID of all DSTranscripts regrouped will be used 
            # as unique ID of the new Transcript object
            transcript_id = min( transcript_val.get( 'related_dstranscript_ids' ) )
            
            # If there are attributes that are provided (i.e. different to None) and do not agree with each other, set them to None
            for att in MergeStrategy.ATT_TO_CHECK_FOR_MERGING_SAME_DSTRANSCRIPT:
                
                att_value = transcript_val.get( att )
                if ( att_value != None ):
                    
                    # Remove any ambiguous flag from the list of values
                    att_value = [ v for v in att_value if ( v != Constants.DENCELLORFOBJ_AMBIGUOUS_ATT ) ]
                    
                    # If there is one single element different from None, 
                    # use this value to instantiate the new Transcript
                    if ( len( att_value ) == 1 ):
                        transcript_val[ att ] = att_value[ 0 ]
                        
                    # Otherwise, look if all provided elements are equals. 
                    # If not, set the value of the new Transcript attribute to None 
                    # and log a warning.
                    else:
                        if all( ( ( e == None ) or ( ( e != None ) and ( e == att_value[ 0 ] ) ) ) for e in att_value ):
                           transcript_val[ att ] = att_value[ 0 ]
                           
                        else:
                            transcript_val[ att ] = None
                            Logger.get_instance().warning( 'Several values have been found for the' +
                                                           ' attribute ' + str( att ) + ' whilst creating' +
                                                           ' the Transcript with ID "' + str( transcript_id ) + 
                                                           '" by merging the DSTranscript with IDs "' + 
                                                            ', '.join( transcript_val[ 'related_dstranscript_ids' ] ) + 
                                                            '" (' + str( [ e for e in att_value if ( e != None ) ] ) + ').' +
                                                            ' Hence the value of this attribute has been set to None.' +
                                                            ' Warning code: ' + LogCodes.WARN_MERG_CONFL_TR + '.' )
            
            # Instantiate the new transcript
            transcript = Transcript( id = transcript_id,
                                     transcript_id = transcript_val.get( 'transcript_id' ),
                                     gene_id = transcript_val.get( 'gene_id' ),
                                     strand = transcript_val.get( 'strand' ),
                                     start_pos = transcript_val.get( 'start_pos' ),
                                     end_pos = transcript_val.get( 'end_pos' ),
                                     cds_start_pos = transcript_val.get( 'cds_start_pos' ),
                                     cds_stop_pos = transcript_val.get( 'cds_stop_pos' ),
                                     rna_biotype = transcript_val.get( 'rna_biotype' ),
                                     count_ds = transcript_val.get( 'nb_of_dstranscripts_grouped' ),
                                     count_ds_ambiguous = 0 )
            objects_to_insert.append( transcript )
            
            # Register in the TranscriptDSAsso the relationship between this Transcript
            # and the DSTranscript entries from which it has been created
            for k in range( len( transcript_val[ 'related_dstranscript_ids' ] ) ):
                
                transcrtipdsasso = TranscriptDSAsso( transcript_id = transcript.id,
                                                     dstranscript_id = transcript_val.get( 'related_dstranscript_ids' )[ k ],
                                                     data_source = transcript_val.get( 'related_datasources' )[ k ],
                                                     ambiguous = False )
                objects_to_insert.append( transcrtipdsasso )
                                        
            
            # If the same transcript ID is found associated with several Gene IDs, log a warning 
            if ( transcript_val.get( 'transcript_id' ) != previous_transcript_id ):
                
                # If the previous transcript ID was associated wit several gene IDs, log a warning 
                if ( len( all_gene_ids_for_transcript ) != 1 ):
                    Logger.get_instance().warning( 'The official transcript ID "' + 
                                                   str( previous_transcript_id ) +
                                                   '" has been found associated with several genes: "' + 
                                                   ', '.join( all_gene_ids_for_transcript ) + 
                                                   '". Hence, several distinct entries will be created in' +
                                                   ' the Transcripts table (PRO database).' +
                                                   ' Warning code: ' + LogCodes.WARN_MERG_CONFL_GENE_ASSO_TR + '.' )
                
                # Keep the record of all the genes associated with this transcript id
                all_gene_ids_for_transcript = [ transcript_val.get( 'gene_id' ) ]
                
                # Store the value of this new transcript ID
                previous_transcript_id = transcript_val.get( 'transcript_id' )
                
            else:
                # Keep record of any new gene ID associated with this transcript
                if ( transcript_val.get( 'gene_id' ) not in all_gene_ids_for_transcript ):
                    all_gene_ids_for_transcript.append( transcript_val.get( 'gene_id' ) )
        
        
        # Insert the newly created objects in the database
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert, 
                                     filename = 'transcripts_with_same_off_id',
                                     process = 'grouping transcripts with same official ID' )
        SQLManagerPRO.get_instance().close_session()
        SQLManagerDS.get_instance().close_session()
        
        
        
        objects_to_insert = []
        
        ## Regroup the transcripts that look similar together
        #  --------------------------------------------------
        
        # Then, 
        # - Group all the DSTranscripts that have not already been processed 
        #   (i.e. all the transcript having the "UNKNOWN_TRANSCRIPT_" prefix) 
        #   together by related gene ID.
        # - When the information about the transcript start and end is provided, 
        #   try to see if the transcript can be merged with one of the previously 
        #   created Transcript. If this is not possible or if the start and end are
        #   missing, create a new Transcript entry with ID [ "UNKNOWN_" + gene_id ].
        #
        Logger.get_instance().info( 'Starting to regroup the entries of the DSTranscript table' +
                                    ' (DS database) with the same "unknown" ID into new Transcript' +
                                    ' entries (PRO database).' )
        
        Logger.get_instance().debug( 'MergeStrategy.merge_dstranscripts(): Querying the DS database' +
                                     ' to regroup the same "unknown" transcripts together.')
        
        grouped_dstranscripts_by_gene_all = SQLManagerDS.get_instance().get_session().query(
                                                                                                DSTranscript.gene_id,
                                                                                                DSTranscript.strand,
                                                                                                DSTranscript.start_pos,
                                                                                                DSTranscript.end_pos,
                                                                                                DSTranscript.cds_start_pos,
                                                                                                DSTranscript.cds_stop_pos,
                                                                                                func.group_concat( DSTranscript.rna_biotype ),
                                                                                                func.group_concat( DSTranscript.transcript_id ),
                                                                                                func.group_concat( DSTranscript.id ),
                                                                                                func.group_concat( DSTranscript.data_source ),
                                                                                                func.count( DSTranscript.id )
                                                                                            ).filter(
                                                                                                        DSTranscript.transcript_id.like( Constants.PREFIX_FAKE_TRANSCRIPT + '%' )
                                                                                                    ).group_by(
                                                                                                                DSTranscript.gene_id,
                                                                                                                DSTranscript.strand,
                                                                                                                DSTranscript.start_pos,
                                                                                                                DSTranscript.end_pos,
                                                                                                                DSTranscript.cds_start_pos,
                                                                                                                DSTranscript.cds_stop_pos,
                                                                                                               ).all()
        
        # For each unique component of the list (i.e. each merged element), check if there is a Transcript
        # sharing the same gene ID, start and stop positions in the PRO database
        Logger.get_instance().debug( 'MergeStrategy.merge_dstranscripts(): Regrouping the' +
                                     ' entries of the DSTranscript table (DS database) with' +
                                     ' the "unknown" IDs into new Transcript entries (PRO database).' )
        
        # Get the number total number of elements expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( grouped_dstranscripts_by_gene_all ) )
        
        for grouped_dstranscripts_by_gene in grouped_dstranscripts_by_gene_all:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            objects_to_insert = []
            
            # Parse the list into a dictionary to get the necessary attributes 
            # to search for or instantiate a Transcript object
            transcript_val = {
                                'gene_id': grouped_dstranscripts_by_gene[ 0 ],
                                'strand': grouped_dstranscripts_by_gene[ 1 ],
                                'start_pos': grouped_dstranscripts_by_gene[ 2 ],
                                'end_pos': grouped_dstranscripts_by_gene[ 3 ],
                                'cds_start_pos': grouped_dstranscripts_by_gene[ 4 ],
                                'cds_stop_pos': grouped_dstranscripts_by_gene[ 5 ],
                                'rna_biotype': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_ids[ 6 ] ) ,
                                'related_dstranscript_tr_ids': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_gene[ 7 ] ),
                                'related_dstranscript_ids': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_gene[ 8 ], fct = 'int' ),
                                'related_datasources': GeneralUtil.string_to_list( str_to_convert = grouped_dstranscripts_by_gene[ 9 ] ),
                                'nb_of_dstranscripts_grouped': grouped_dstranscripts_by_gene[ 10 ]
                              }
            
            
            # If there is already an Transcript entry looking like this one in the database, 
            # then merge these two Transcripts, i.e. create a new TranscriptDSAsso entry to 
            # keep record of the relationship with the corresponding Transcript,
            # and increase of one the count of ambiguous Transcripts associated to it.
            
            # Query the Transcript table for entries that have the same gene ID
            existing_transcript_query_on_gene = SQLManagerPRO.get_instance().get_session().query( Transcript ).filter( 
                                                                                                                        Transcript.gene_id == transcript_val.get( 'gene_id' )
                                                                                                                      )
            
            
            # Get the list of attributes which are not null for the current element 
            # of the list (i.e. that do not equal None) and that should be use as 
            # filter to query the Transcript table
            attributes_to_use_for_filter = {}
            
            for att in MergeStrategy.ATTRIBUTES_FOR_MERGING_SIMILAR_DSTRANSCRIPT:
                # Get the value of the attribute
                att_value = transcript_val.get( att )
                # Add the attribute as a filter to use only if it is not null
                if ( att_value != None ):
                    attributes_to_use_for_filter[ att ] = att_value
                    
            # Query the PRO database to get the Transcript entrie(s)
            # that look like the current entry
            existing_transcript_query_on_all = existing_transcript_query_on_gene
            # Sequentially apply the filter on the query
            for ( att, value ) in attributes_to_use_for_filter.items():
                existing_transcript_query_on_all = existing_transcript_query_on_all.filter( eval( 'DSTranscript.' + att ) == value )
            
            existing_transcript = existing_transcript_query_on_all.all()
            
            # If there is at least one Transcript returned, i.e. if there is at 
            # least one Transcript in the PRO database that may match the current 
            # element of the list, and such as the two transcript share at least 
            # two characteristics (strand, start, end, CDS start and stop positions), 
            # then merge the DSTranscript(s) of the current element of the list with 
            # each of these Transcript entries. In other words, for each Transcript 
            # entry that may match with the current DSDSTranscript(s), create a new 
            # TranscriptDSAsso entry, keep the relationship with it and increase of 
            # one the count of ambiguous DSDSTranscripts associated to it. 
            if ( ( len( attributes_to_use_for_filter.keys() ) > 1 )
                 and ( len( existing_transcript ) > 1 ) ):
                
                for transcript in existing_transcript:
                    
                    # Increase the non-ambiguous count of one
                    transcript.count_ds_ambiguous += 1
                
                    # Create the new TranscriptDSAsso
                    for k in range( len( transcript_val.get( 'related_dstranscript_ids' ) ) ):
                        transcriptdsasso = TranscriptDSAsso( transcript_id = transcript.id,
                                                             dstranscript_id = transcript_val.get( 'related_dstranscript_ids' )[ k ],
                                                             data_source = transcript_val.get( 'related_datasources' )[ k ],
                                                             ambiguous = True )
                        objects_to_insert.append( transcriptdsasso )
                        
                    objects_to_insert.append( transcript )
        

            # Otherwise create a new Transcript
            else:
                
                transcript_id = min( transcript_val.get( 'related_dstranscript_ids' ) )
                
                # Create the new Transcript
                transcript = Transcript( id = transcript_id,
                                         transcript_id = Constants.UNKNOWN_TRANSCRIPT,
                                         gene_id = transcript_val.get( 'gene_id' ),
                                         strand = transcript_val.get( 'strand' ),
                                         start_pos = transcript_val.get( 'start_pos' ),
                                         end_pos = transcript_val.get( 'end_pos' ),
                                         cds_start_pos = transcript_val.get( 'cds_start_pos' ),
                                         cds_stop_pos = transcript_val.get( 'cds_stop_pos' ),
                                         rna_biotype = transcript_val.get( 'rna_biotype' ),
                                         count_ds = 0,
                                         count_ds_ambiguous = transcript_val.get( 'nb_of_dstranscripts_grouped' ) )
                
                # Create the new TranscriptDSAsso
                for k in range( len( transcript_val.get( 'related_dstranscript_ids' ) ) ):
                    transcriptdsasso = TranscriptDSAsso( transcript_id = transcript.id,
                                                         dstranscript_id = transcript_val.get( 'related_dstranscript_ids' )[ k ],
                                                         data_source = transcript_val.get( 'related_datasources' )[ k ],
                                                         ambiguous = True )
                    objects_to_insert.append( transcriptdsasso )
                    
                objects_to_insert.append( transcript )

            # Add the new objects to the session (PRO database), and flush the session
            # so the query on the next step will return up-to-date results
            SQLManagerPRO.get_instance().add_and_flush( objects_to_add = objects_to_insert, 
                                                        process = 'grouping transcripts with same "unknown" ID' )
        
        # Commit the changes and close the session
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        SQLManagerDS.get_instance().close_session()

    
    
    # ===============================================================================
    # Methods related to the merging of DSORFTranscriptAssos
    # =============================================================================== 
    
    ## merge_dsorftranscriptasso
    #  -------------------------
    #
    # This method aims to process the entries of the DSORFTranscriptAsso table 
    # (DS database) to fill in the ORFTranscriptAsso table (PRO database).
    # It first gets the list of all ( ORF, Transcript ) couples that exist and 
    # for each of them it gets the list of all DSORFTranscriptAsso corresponding 
    # to the couple. Then it merges the DSORFTranscriptAsso together in order to
    # create one single entry associated with the couple in the ORFTranscriptAsso 
    # table (PRO database).
    # 
    def merge_dsorftranscriptasso( self ):
        
        Logger.get_instance().info( 'Starting to merge the entries of the DSORFTranscriptAsso table.' )
        
        # Get all the existing ( ORF, Transcript ) couples for which this 
        # is necessary to merge all the related DSORFTranscriptAsso
        self.get_dsorftranscriptasso_to_merge()
        
        # Merge the entries of the DSORFTranscriptAsso table        
        self.merge_dsota()
        
        
    
    ## get_dsorftranscriptasso_to_merge
    #  --------------------------------
    #
    # This method allows to generate a dictionary that associates to each unique 
    # ( ORF ID (PRO), Transcript ID (PRO) ) couple that exists, a list of all the 
    # DSORFTranscriptAsso (DS) that are related to it; and to store this dictionary
    # in the DataManager main dictionary.
    # 
    def get_dsorftranscriptasso_to_merge( self ):
        
        # NB: This step is multi-processed
        #     - As access of objects shared by the several processes (using locks and 
        #       semaphores for instance), could slower a lot the speed of execution when the
        #       process regularly need to access these variables, it has been decided to do
        #       not access to shared resources. Then the progression bar is not displayed on 
        #       screen for this step.
        
        # Instantiate a dictionary in the Data Manager that get as:
            # - keys the ( ORF ID (PRO), Transcript ID (PRO) ) couples that exist,
            # - values the list of all DSORFTranscriptAsso (DS) related to these ORF and Transcript IDs.
        Logger.get_instance().debug( 'MergeStrategy.get_dsorftranscriptasso_to_merge():' +
                                     ' Getting all the existing ( ORF ID, Transcript ID ) couples' +
                                     ' and the list of DSORFTranscriptAsso IDs corresponding to these.' +
                                     ' This might take some time...' )
        
        # Get all the entries of the ORFDSAsso (PRO) table and build a dictionary
        # that associate to each DSORF ID (DS) the related ORF IDs (PRO)
        # NB: This allows to avoid making highly numerous queries to the PRO database, 
        #     allowing to shorten the computation time.
        orfdsasso_groupby_orfid = SQLManagerPRO.get_instance().get_session().query( 
                                                                                        ORFDSAsso.dsorf_id,
                                                                                        func.group_concat( ORFDSAsso.orf_id ) 
                                                                                    ).group_by(
                                                                                                    ORFDSAsso.dsorf_id
                                                                                                ).all()
        SQLManagerPRO.get_instance().close_session()
        
        orfdsasso_dict = {}
        for orfdsasso in orfdsasso_groupby_orfid:
            dsorf_id = orfdsasso[ 0 ]
            orf_ids = orfdsasso[ 1 ].split( ',' )
            orfdsasso_dict[ dsorf_id ] = orf_ids
                
        # Get all the entries of the TranscriptDSAsso (PRO) table and build a dictionary 
        # that associate to each DSTranscript ID (DS) the related Transcript IDs (PRO)
        # NB: This allows to avoid making highly numerous queries to the PRO database, 
        #     allowing to shorten the computation time.
        transcriptdsasso_groupby_trid = SQLManagerPRO.get_instance().get_session().query(
                                                                                            TranscriptDSAsso.dstranscript_id,
                                                                                            func.group_concat( TranscriptDSAsso.transcript_id )
                                                                                        ).group_by(
                                                                                                        TranscriptDSAsso.dstranscript_id
                                                                                                    ).all()
        SQLManagerPRO.get_instance().close_session()
        
        transcriptdsasso_dict = {}
        for transcriptdsasso in transcriptdsasso_groupby_trid:
            dstranscript_id = transcriptdsasso[ 0 ]
            transcript_ids = transcriptdsasso[ 1 ].split( ',' )
            transcriptdsasso_dict[ dstranscript_id ] = transcript_ids
        
        
        # Get all the DSORFTranscriptAsso entries (DS database)
        dsota_query = SQLManagerDS.get_instance().get_session().query( DSORFTranscriptAsso )
        dsota_all = dsota_query.all()
        SQLManagerDS.get_instance().close_session()
        
        # Create a list of 3-element tuples containing:
        # - The ORFTranscriptAsso object
        # - The value of the orf_id attribute
        # - The value of the transcript_id attribute
        dsota_ids_asso_list = [ ( dsota, dsota.uniq_orf_id, dsota.transcript_id ) for dsota in dsota_all ]
        
        # Replace each element of the list by a 3-elements list 
        # that contains:
        # - The ORFTranscriptAsso object
        # - The list of ORF IDs (PRO) related to it 
        #   (or an empty list if the DSORF ID is not used in the PRO database)
        # - The list of Transcript IDs (PRO) related to it
        #   (or an empty list if the DSTranscript ID is not used in the PRO database)
        dsota_ids_asso_list = map( lambda t: [ t[0], 
                                               orfdsasso_dict.get( t[1], [] ), 
                                               transcriptdsasso_dict.get( t[2], [] ) ], 
                                   dsota_ids_asso_list )
        
        # Compute the Cartesian product of ORF and Transcript lists of IDs
        # i.e. compute all the tuples of ( ORF, Transcript ) IDs (PRO) that 
        # are associated to this DSORFTranscriptAsso (DS) and add it as the 
        # fourth element of each lists.
        dsota_ids_asso_list = map( lambda t: t + [ list( itertools.product( t[1], t[2] ) ) ],
                                   dsota_ids_asso_list )
        
        # Create a dictionary that associate to each unique ( ORF id (PRO), Transcript ID (PRO) )
        # the list of DSORFTranscriptAsso (DS) to merge
        DataManager.get_instance().store_data( Constants.DM_ALL_EXISTING_ORF_TR_ASSO_DICT, {} )
        all_existing_orf_tr_asso_dict = DataManager.get_instance().get_data( Constants.DM_ALL_EXISTING_ORF_TR_ASSO_DICT )
        
        for t in dsota_ids_asso_list:
            dsota = t[0]
            cartesian_prod = t[3]
            
            for ( orf_id, tr_id ) in cartesian_prod:
                exist_orf_tr_asso = all_existing_orf_tr_asso_dict.get( ( orf_id, tr_id ) ) 
                if exist_orf_tr_asso:
                    exist_orf_tr_asso.append( dsota )
                else:
                    all_existing_orf_tr_asso_dict[ ( orf_id, tr_id ) ] = [ dsota ]
        
        
        # Compute the dictionary that associate to each DSORFTranscriptAsso
        # the number of ORF and Transcript related to it.
        # NB: This dictionary is absolutely NOT necessary to perform the merging
        #     but will be saved in a csv file for further analysis.
        all_orf_tr_count_for_dsota_dict = { dsota.id : ( len( orf_ids ),
                                                         len( transcript_ids ),
                                                         len( orf_tr_asso_list ) ) \
                                            for (dsota, orf_ids, transcript_ids, orf_tr_asso_list ) in dsota_ids_asso_list }
        
        
        # From the 'all_existing_orf_tr_asso_dict' dictionary, compute a new dictionary that 
        # associate to each ( ORF ID (PRO), Transcript ID (PRO) ) couple, the  list of 
        # DSORFTranscriptAsso IDs (DS) related to it and save it into a file. 
        # This file may then be used by the ResumeMerge strategy to re-start the 
        # merging after the computation of these couples if something goes wrong during
        # the execution of the merge_dsota() method.
        Logger.get_instance().debug( 'Starting to compute the dictionary that associates the ( ORF (PRO),' +
                                     ' Transcript (PRO) ) IDs to the lists of DSORFTranscriptAsso (DS) IDs.' )
        all_existing_orf_tr_asso_ids = {}
        for ( ( orf_id, tr_id ), dsota_list ) in all_existing_orf_tr_asso_dict.items():
            all_existing_orf_tr_asso_ids[ ( orf_id, tr_id ) ] = map( lambda x: x.id, dsota_list )
            
        try:
            FileHandlerUtil.save_obj_to_file( objects_to_save = all_existing_orf_tr_asso_ids, 
                                              filename = Constants.ALL_EXISTING_ORF_TR_ASSO_IDS_FILENAME, 
                                              output_folder = Constants.MERGED_DATA_FOLDER )
        except Exception as e:
            Logger.get_instance().error( 'An error occurred trying to save the dictionary that associates' +
                                         ' to each (ORF ID (PRO), Transcript ID (PRO) ) couple the IDs of' +
                                         ' the list of DSORFTranscriptAsso related to it. \n' +
                                         str( e )  +
                                         ' Error code: ' + LogCodes.ERR_FILEHAND + '.', 
                                         ex = False )
        
        
        # Store into an other data frame the number of DSORFTranscriptAsso (DS) 
        # associated with each existing ( ORF (PRO), Transcript (PRO) ) tuple
        Logger.get_instance().debug( 'Computing the number of DSORFTranscriptAsso (DS) associated' +
                                     ' with each existing ( ORF (PRO), Transcript (PRO) ) tuple.' )
        dsota_count_for_orf_tr_df = pd.DataFrame( columns = [ 'orf_id', 
                                                             'transcript_id', 
                                                             'dsota_count' ] )
        
        dsota_count_for_orf_tr_dict = { ( orf_id, tr_id ) : len( dsota_list ) \
                                        for ( ( orf_id, tr_id ), dsota_list ) in all_existing_orf_tr_asso_dict.items() }
        
        # Save the data frames in CSV files
        Logger.get_instance().info( 'The number of ORF (PRO) and Transcript (PRO) entries associated' +
                                    ' with each existing DSORFTranscriptAsso (DS) will be saved in a' +
                                    ' CSV file (' + Constants.MERGE_DATA_ANALYSIS_FOLDER +
                                    ' folder, orf_tr_count_for_dsota.csv file).' )
        try:
            FileHandlerUtil.dict_to_csv( output_folder = Constants.MERGE_DATA_ANALYSIS_FOLDER,
                                         filename = 'orf_tr_count_for_dsota',
                                         file_desc = ( 'Number of ORF (PRO) and Transcript (PRO) entries' +
                                                       ' associated with each DSORFTranscriptAsso (DS)' ),
                                         dict = all_orf_tr_count_for_dsota_dict,
                                         hdr = [ 'dsota_id', 
                                                 'orf_count', 
                                                 'transcript_count', 
                                                 'cartesian_prod_count' ],
                                         val_func = lambda v: map( str, v ),
                                         sep = ',',
                                         sort = True, 
                                         unlist_val = True )
        except Exception as e:
            Logger.get_instance().error( 'An error occurred trying to save the number of ORF (PRO)' +
                                         ' and Transcript (PRO) entries associated with each existing' +
                                         ' DSORFTranscriptAsso (DS) in the CSV file. \n' +
                                         str( e ) +
                                         ' Error code: ' + LogCodes.ERR_FILEHAND + '.',
                                         ex = False )
        
        Logger.get_instance().info( 'The number of DSORFTranscriptAsso (DS) associated with each' +
                                    ' ( ORF (PRO), Transcript (PRO) ) existing tuple will be saved' +
                                    ' in a CSV file (' + Constants.MERGE_DATA_ANALYSIS_FOLDER +
                                    ' folder, dsota_count_for_orf_tr.csv file).' )
        try:
            FileHandlerUtil.dict_to_csv( output_folder = Constants.MERGE_DATA_ANALYSIS_FOLDER,
                                         filename = 'dsota_count_for_orf_tr', 
                                         file_desc = ( 'Number of DSORFTranscriptAsso (DS) associated with' +
                                                       ' each ( ORF (PRO), Transcript (PRO) ) existing tuple' ),
                                         dict = dsota_count_for_orf_tr_dict,
                                         hdr = [ 'orf_id',
                                                 'transcript_id',
                                                 'dsota_count' ],
                                         key_func = lambda k: map( str, k ),
                                         sep = ',',
                                         sort = True,
                                         unlist_key = True )
        except Exception as e:
            Logger.get_instance().error( 'An error occurred trying to save the number of' +
                                         ' DSORFTranscriptAsso (DS) associated with each' +
                                         ' ( ORF (PRO), Transcript (PRO) ) existing tuple in the CSV file. \n' +
                                         str( e ) +
                                         ' Error code: ' + LogCodes.ERR_FILEHAND + '.',
                                         ex = False )
        
        
            
    ## merge_dsota
    #  -----------
    #
    # This method allows to merge the entries of the DSORFTranscriptAsso table.
    # NB: It needs the 'all_existing_orf_tr_asso_dict' dictionary stored into the 
    #     DataManager in order to work properly. See the documentation of the 
    #     get_dsorftranscriptasso_to_merge() method for more information.
    # 
    def merge_dsota( self ):
        
        # NB: This step is multi-processed
        # - As access of objects shared by the several processes (using locks and 
        #   semaphores for instance), could slower a lot the speed of execution when the
        #   process regularly need to access these variables, it has been decided to do
        #   not access to shared resources. Then an object corresponding to a common entry 
        #   (e.g. CellContextCatalog entry) may be instantiated by several processes at 
        #   the same time. In order to respect the database integrity, several list of 
        #   objects expected to be redundant are checked to discard this redundancy prior
        #   to perform to the insertion in the database.
        # - As forked processes require a copy of parent address space, they could be
        #   highly memory-consuming processes. In order to limit the number of elements
        #   stored in memory, the merging is performed by "batch" of pre-defined size.
        # - As locks are not used, the progression bar displayed on the terminal is not
        #   instantaneously updated, but instead is updated at the end of each batch.
        
        # Get all the existing ( ORF, Transcript ) associations 
        # previously computed
        all_existing_orf_tr_asso_dict = DataManager.get_instance().get_data( Constants.DM_ALL_EXISTING_ORF_TR_ASSO_DICT )
                
        
        ## For each existing ( ORF, Transcript ) association, 
        #  merge all the related DSORFTranscriptAsso
        #  --------------------------------------------------
        Logger.get_instance().info( 'Starting to merge the DSORFTranscriptAsso entries' +
                                    ' for all existing ( ORF ID, Transcript ID ) couples.' )
        
        # Register all the new cell context, provided category 
        # and FLOSS classification in dictionaries
        DataManager.get_instance().store_PRO_query_result( Constants.DM_ALL_CELL_CTXT_CAT, 
                                                           'query( CellContextCatalog ).all()' )
        DataManager.get_instance().store_PRO_query_result( Constants.DM_ALL_PROVIDED_CAT_CAT, 
                                                           'query( ProvidedCategoryCatalog ).all()' )
        DataManager.get_instance().store_PRO_query_result( Constants.DM_ALL_FLOSS_CLASS_CAT, 
                                                           'query( FLOSSClassCatalog ).all()' )
        SQLManagerPRO.get_instance().close_session()
        
        all_cell_ctxt_dict = DataManager.get_instance().get_data( Constants.DM_ALL_CELL_CTXT_CAT )
        all_provided_cat_dict = DataManager.get_instance().get_data( Constants.DM_ALL_PROVIDED_CAT_CAT )
        all_floss_dict = DataManager.get_instance().get_data( Constants.DM_ALL_FLOSS_CLASS_CAT )
        
        
        # Get the number total number of elements expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = len( all_existing_orf_tr_asso_dict.keys() ) )
        ProgressionBar.get_instance().display()
        
        
        # During the merging of the DSORFTranscriptAsso entries, a consensus of the
        # amino acid and nucleic sequences needs to be computed. As this step uses
        # MUSCLE, it needs to write the sequences and alignment in a fasta file. 
        # Hence, the fasta files are saved in a temporary folder. In order to avoid 
        # any conflict related to the creation of the directory by the first parallel 
        # processes at the same time, this folder is created prior to run the processes.
        if ( not os.path.exists( DefaultTemporaryFolder.TEMPORARY_FOLDER ) ):
            os.makedirs( DefaultTemporaryFolder.TEMPORARY_FOLDER )
            
        # Instantiate the list of tuple-embedded arguments necessary 
        # to create the new PRO entries 
        # As the same DSORFTranscriptAsso may be merged into several 
        # ORFTranscriptAsso, the ID is build by incrementing a counter.
        args_for_merging_list = []
        
        # If there is any entry existing in the ORFTranscriptAsso table, 
        # get the value of the highest ID
        ota_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
        if ( ota_count != 0 ):
            max_ota_id = SQLManagerPRO.get_instance().get_session().query( func.max( ORFTranscriptAsso.id ) ).one()[0]
            ota_id = max_ota_id + 1
        else:
            ota_id = 1
        
        for ( orf_tr_asso, dsorftranscriptasso_list ) in all_existing_orf_tr_asso_dict.items():
            # Append to the list the tuple required by the MergeDSOTA.merge_dsota() method
            # (see the documentation of this method for more information)
            args_for_merging_list.append( ( ota_id,
                                            orf_tr_asso, 
                                            dsorftranscriptasso_list,
                                            self.check_dsota_coherence,
                                            self.compute_consensus,
                                            self.sqce_consensus_ambig_threshold,
                                            self.max_len_diff_dsota_clust ) )
            ota_id += 1
        
        
        # Split the list into sublists of defined sizes, such as processes
        # are run by sequential "batches" of pools
        args_for_merging_sublists = [ args_for_merging_list[ min_bound : min_bound + 
                                                             Constants.MAX_POOL_SIZE ] \
                                      for min_bound in xrange( 0, 
                                                               len( args_for_merging_list ), 
                                                               Constants.MAX_POOL_SIZE ) ]
        
        # Instantiate the pool
        p = Pool( self.thread_nb )
            
        # Sequentially process these "batches"
        for args_for_merging_sublist in args_for_merging_sublists:
            
            Logger.get_instance().debug( 'MergeStrategy.merge_dsota(): ' + str( len( args_for_merging_sublist ) ) +
                                         ' subprocess will be started to perform the merging of the' +
                                         ' DSORFTranscriptAsso entries.' )
            
            # Instantiate the list of new objects to be added
            # to the database
            objects_to_insert = []
                    
            # For each group of DSORFTranscriptAsso to merge, run the MergeDSOTA.merge_dsota() 
            # static method that will instantiate all the appropriate objects to insert in the 
            # PRO database
            m = MergeDSOTA()
            all_objects_to_insert = p.map( m.merge_dsota, args_for_merging_sublist )
            p.close()
            # Wait for all processes to be completed
            p.join()
            
        
            # Get the new objects to add to the session
            for obj_to_insert_sublist in all_objects_to_insert:
                
                # Parse the output of the MergeDSOTA.merge_dsota() method
                ( new_objects, 
                  cell_ctxt_catalog_to_insert, 
                  provided_cat_catalog_to_insert, 
                  floss_class_catelog_to_insert, 
                  error_messages_to_log, 
                  warning_messages_to_log ) = obj_to_insert_sublist
                
                # For each of the CellContextCatalog, ProvidedCategoryCatalog and 
                # FlossClassCatalog instances, only add them to the list of objects
                # to insert if if they are not yet existing in the database and if
                # they have not already been added to the session.
                for new_cell_ctxt in cell_ctxt_catalog_to_insert:
                    if ( not all_cell_ctxt_dict.get( new_cell_ctxt ) ):
                        all_cell_ctxt_dict[ new_cell_ctxt ] = new_cell_ctxt
                        objects_to_insert.append( new_cell_ctxt )
                
                for new_provided_cat in provided_cat_catalog_to_insert:
                    if ( not all_provided_cat_dict.get( new_provided_cat ) ):
                        all_provided_cat_dict[ new_provided_cat ] = new_provided_cat
                        objects_to_insert.append( new_provided_cat )
                
                for new_floss in floss_class_catelog_to_insert:
                    if ( not all_floss_dict.get( new_floss ) ):
                        all_floss_dict[ new_floss ] = new_floss
                        objects_to_insert.append( new_floss )
                
                # NB: The new entries are the last to be added to the list of objects
                #     to add to the session, as parent entries that required to be 
                #     existing could have been instantiated by the function (and thus 
                #     added to one of the previous lists).
                objects_to_insert += new_objects
                    
                # Log the messages instantiated during the execution 
                # of the MergeDSOTA.merge_dsota() method
                for warning_message in warning_messages_to_log:
                    Logger.get_instance().warning( warning_message )
                    
                for error_message in error_messages_to_log:
                    Logger.get_instance().error( error_message, ex = None)
                    
            # Display the progression on the terminal
            ProgressionBar.get_instance().increase_and_display( add_val = Constants.MAX_POOL_SIZE )
            
            # Insert the new objects in the PRO database and commit the changes
            self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert,
                                         filename = 'orftranscriptasso',
                                         process = 'grouping DSORFTranscriptAsso entries' )
            SQLManagerPRO.get_instance().close_session()
            
            # Restart the pool
            p.restart()
            
        # Delete the pool instance
        p.clear()

                    
                    
    
    # ===============================================================================
    # Methods dedicated to the cleaning of the PRO database
    # ===============================================================================
    
    ## clean_pro_database
    #  ------------------
    #
    # This method aims to clean the PRO database by removing all the parent entries
    # of the ORF and Transcript tables that have no child in the ORFTranscriptAsso table.
    #
    # @throw DenCellORFException: When an exception has been raised trying to delete the 
    #                             entries of the ORF table without children.
    # @throw DenCellORFException: When an exception has been raised trying to delete the 
    #                             entries of the Transcript table without children.
    # 
    def clean_pro_database( self ):
        
        Logger.get_instance().info( 'Starting to clean the PRO database.')
        
        # Delete all ORF entries without ORFTranscriptAsso children
        # NB: The ORFDSAsso entries related to these are expected to be 
        #     automatically removed in regard to the relational integrity
        orf_wo_children_query = SQLManagerPRO.get_instance().get_session().query( ORF ).filter( ORF.ORFTranscriptAsso_list == None )
        orf_wo_children_count = orf_wo_children_query.count()
        
        if ( orf_wo_children_count != 0 ):
            Logger.get_instance().info( str( orf_wo_children_count ) + ' entries of the ORF table' +
                                        ' have been found without children and will be deleted.' )
            try:
                orf_wo_children_query.delete( synchronize_session='fetch' )
                SQLManagerPRO.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'MergeStrategy.clean_pro_database(): An error occurred trying' +
                                           ' to remove the ORF entries without children from the session' +
                                           ' and to commit changes.', e )
        
        # Delete all Transcript entries without ORFTranscriptAsso children
        # NB: The TranscriptDSAsso entries related to these are expected to be 
        #     automatically removed in regard to the relational integrity
        transcript_wo_children_query = SQLManagerPRO.get_instance().get_session().query( Transcript ).filter( Transcript.ORFTranscriptAsso_list == None )
        transcript_wo_children_count = transcript_wo_children_query.count()
        
        if ( transcript_wo_children_count != 0 ):
            Logger.get_instance().info( str( transcript_wo_children_count ) + ' entries of the Transcript' +
                                        ' table have been found without children and will be deleted.' )
            try:
                transcript_wo_children_query.delete( synchronize_session = 'fetch' )
                SQLManagerPRO.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'MergeStrategy.clean_pro_database(): An error occurred trying' +
                                           ' to remove the Transcript entries without children from the' +
                                           ' session and to commit changes.', e )
        SQLManagerPRO.get_instance().close_session()
                
                    
        
    # ===============================================================================
    # Common methods
    # ===============================================================================
    
    ## batch_insert_to_PRO_db
    #  ----------------------
    #
    # This method allows to insert a list of objects in the PRO database. 
    # 
    # @param objects_to_insert: List - The list of objects to insert in the database.
    # @param filename: String - The name of the filename where data are saved.
    # @param process: String - The name of the process that generated these objects.
    #                          'Undefined process' by default.
    # 
    def batch_insert_to_PRO_db( self, objects_to_insert, filename, process='Undefined process' ):
        
        # Save into a temporary file the data that should be inserted.
        self.save_list_of_obj( objects_to_insert = objects_to_insert, 
                               filename = filename )
            
        # Insert the objects in the database
        SQLManagerPRO.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert, 
                                                         process = process )
    
    
    
    
    ## save_list_of_obj
    #  ----------------
    #
    # This is a static method that allows to save in a file a list of objects
    # expected to be added or that have been added to the PRO database.
    #
    # NB: So far there is NOT any strategy that allows to use these files 
    #     to retry the insertion of data into the PRO database if it failed. 
    #     Nevertheless, if necessary it would be feasible to create a new 
    #     strategy similar to the InsertionStrategy that uses the content 
    #     of these file to retry the insertion into the PRO database; saving
    #     the computation time if the merging occurred successfully but an 
    #     exception has been raised during the insertion into the database.
    # 
    # @param objects_to_insert: List - The list of objects to insert in the database.
    # @param filename: String - The name of the filename where data are saved.
    # 
    @staticmethod
    def save_list_of_obj( objects_to_insert, filename ):
        
        try:
            FileHandlerUtil.save_obj_to_file( objects_to_save = objects_to_insert,
                                              filename = 'objects_from_' + filename,
                                              output_folder = Constants.MERGED_DATA_FOLDER )
        except Exception as e:
            Logger.get_instance().error( 'MergeStrategy.batch_insert_to_PRO_db():' +
                                         ' An error occurred trying to save data from ' + 
                                         process + ': \n' + str( e ) +
                                         '\n Error code: ' + LogCodes.ERR_FILEHAND + '.',
                                         ex = False )
    