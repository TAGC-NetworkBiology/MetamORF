# -*- coding: utf-8 -*-

import ConfigParser
import os

import requests
import pyensembl

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.genetics.GeneticsUtil import GeneticsUtil
from fr.tagc.uorf.core.util.ensembl.EnsemblUtil import EnsemblUtil
from fr.tagc.uorf.core.util.ensembl.EnsemblRestClient import EnsemblRestClient
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## ComputeMissingInfoStrategy
#  ==========================
#
# This class is a strategy aiming to:
# - Compute the ORF genomic length and compare these to ORFTranscriptAsso entries.
# - Merge the similar CellContext together.
# - Download extensive information about the ORF and Transcript (sequences, missing
#   coordinates...) from Ensembl.
#
class ComputeMissingInfoStrategy( object ):
                
    ## Class variables
    #  ---------------
    #
    # HTTP Error codes for which a new attempt of download should be performed.
    # More information on error codes may be found at: 
    #         https://github.com/Ensembl/ensembl-rest/wiki/HTTP-Response-Codes
    # - 403: Forbidden (Access to the service temporarily forbidden due to too many requests).
    # - 408: Timeout (The request was not processed in time).
    # - 429: Too Many Requests.
    # - 503: Service Unavailable (Service temporarily down).
    HTTP_ERRORS_ALLOW_RETRY = [ '403', '408', '429', '503' ]
    
    # HTTP Error codes for which a new attempt of download is not allowed.
    # - 400: Bad Request (Unable to find an ID).
    # - 404: Not Found (Badly formatted request).
    HTTP_ERRORS_NOT_ALLOW_RETRY = [ '400', '404' ]
    
    
    ## Constructor of ComputeMissingInfoStrategy
    #  -----------------------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - cell_context_dict: Dictionary - The dictionary that associates to lists of cell contexts
    #                                       (lists of strings - values of the dictionary) new cell context
    #                                       names (strings - keys of the dictionary).
    #     - default_context_dict: Boolean - Does the dictionary used is the default one 
    #                                       (defined in the Constants module)?
    #     - force_overwrite: Boolean - Does the computation needs to be performed again?
    #                                  If True:
    #                                      - The genomic lengths (ORF table entries) will be computed again.
    #                                      - The genomic lengths (ORF table entries) will be compared to the
    #                                        nucleic lengths of the related ORFTranscriptAsso entries
    #                                      - All the entries of the UTRNABiotypeCatalog will be deleted and 
    #                                        the content of this table will be computed again. 
    #     - downloadMissingInfo: Boolean - Do the missing information needs to be downloaded from external
    #                                      server? This includes the ORF and Transcript sequences.
    #     - species: String - The "short" name of the species (e.g. 'Hsapiens').
    #     - current_annotation: String - The annotation version used in the database (e.g. GRCh38).
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
                                       ' See the documentation for more information.' )

        # Check if the forceOverwrite option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
            self.force_overwrite = True
        else:
            self.force_overwrite = False
            
        # Check if the downloadMissingInfo option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_DOWNLOAD_MISSING_INFO, not_none = False ):
            self.download_missing = True
        else:
            self.download_missing = False
        
        self.species = None
        self.current_annotation = None



    ## parse_config
    #  ------------
    #
    # Parse the config file to retrieve required information.
    #
    # @throw DenCellORFException: When the cell_context_dict string ("cell context dictionary") 
    #                             cannot be converted into a Python dictionary.
    #
    def parse_config( self ):
        
        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
        
        # Get the dictionary to use to merge the CellContext entries
        if config.has_option( Constants.CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS, Constants.CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS_ITEM_CELLCONTEXT_DICT ):
            self.cell_context_dict = config.get( Constants.CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS, 
                                                 Constants.CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS_ITEM_CELLCONTEXT_DICT )
            try:
                self.cell_context_dict = eval( self.cell_context_dict )
            except Exception as e:
                raise DenCellORFException( 'ComputeMissingInfoStrategy.parse_config():' +
                                           ' An error occurred trying to convert the cell context dictionary' +
                                           ' provided as a string into an actual Python dictionary.', e )
            self.default_context_dict = False
        
        else:
            self.cell_context_dict = Constants.DEFAULT_CELL_CONTEXT_DICT
            self.default_context_dict = True
            Logger.get_instance().debug( 'ComputeMissingInfoStrategy.parse_config():' +
                                         ' As there was no dictionary provided to merge the cell context' +
                                         ' in the config file, the default dictionary (' + 
                                         str( Constants.DEFAULT_CELL_CONTEXT_DICT ) + ') will be used.' )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete missing information.
    #
    # @throw DenCellORFException: When an exception has been raised whilst checking the PRO database.
    # @throw DenCellORFException: When the ORFTranscriptAsso table is empty.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check PRO database is reachable and use
        # the appropriate models prior to the merging of data.
        Logger.get_instance().info( 'Checking the PRO database prior to compute missing information...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( ' An error occurred whilst checking the database prior to' +
                                       ' compute missing information.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        
        # Check there is at least one ORFTranscriptAsso entry in the database prior 
        # to compute the missing information.
        orftranscriptasso_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
        if ( orftranscriptasso_count == 0 ):
            raise DenCellORFException( 'There is not any entry in the ORFTranscriptAsso table of the ' + 
                                       SQLManagerPRO.get_instance().db_name + ' database (PRO database).' +
                                       ' Hence, the computation of missing information will be stopped.' )
        
        # Compute the ORF lengths based upon genomic coordinates and 
        # compare them with ORFTranscriptAsso nucleic lengths
        # NB: This step is only performed if there is no ORF with 
        #     genomic length or if the forceOverwrite has been selected.
        orf_gen_len_count = SQLManagerPRO.get_instance().get_session().query( ORF ).filter( ORF.genomic_length != None ).count()
        SQLManagerPRO.get_instance().close_session()
        
        if ( ( orf_gen_len_count == 0 ) or ( self.force_overwrite ) ):
            # Compute all the ORF length based upon their genomic coordinates
            self.compute_orf_gen_len()
            
            # Compare the ORFTranscriptAsso nucleic length to the genomic length
            # of its related ORF
            self.compare_gen_orf_len()
        
        # Rename cell contexts and/or merge the similar cell contexts together if necessary
        if self.cell_context_dict:
            
            # Get the list of all the cell context registered in the CellContextCatalog
            all_contexts_in_cellcontextcatalog = SQLManagerPRO.get_instance().get_session().query( CellContextCatalog.context ).all()
            all_contexts_in_cellcontextcatalog = GeneralUtil.query_result_to_list( all_contexts_in_cellcontextcatalog )
            
            # If there are entries of the CellContextCatalog which are not included in the list
            # of all 'new' cell contexts and cell contexts to keep, then perform the merging
            # of cell contexts. Otherwise skip this step.
            catalog_included_in_dict_keys = set( all_contexts_in_cellcontextcatalog ).issubset( self.cell_context_dict.keys() )
            
            if not catalog_included_in_dict_keys:
                self.merge_cell_context()
            else:
                Logger.get_instance().info( 'The CellularContextCatalog table does not contain any' +
                                            ' cell context to merge or re-annotate. Hence the merging' +
                                            ' and re-annotation of the cellular contexts will be skipped.' )
           
        
        # If the option has been selected, download missing information 
        # in the ORF and Transcript tables
        if self.download_missing:
            self.download_missing_info()
        
        # Complete the UTRNABiotypeCatalog table with all unique RNA biotypes
        self.complete_utrnabiotypecatalog_table()
         
    
    
    # ===============================================================================
    # Methods to the compare the ORF genomic length with the ORFTranscriptAsso lengths
    # =============================================================================== 
        
    ## compute_gen_orf_len
    #  -------------------
    #
    # This method allows to compute the genomic length of the ORFs using
    # their genomic coordinates and splicing information.
    # 
    def compute_orf_gen_len( self ):
        
        Logger.get_instance().info( 'Starting the computation of ORF genomic lengths.')
            
        all_orf_query = SQLManagerPRO.get_instance().get_session().query( ORF )
        all_orf_count = all_orf_query.count()
        all_orf = all_orf_query.all()
        SQLManagerPRO.get_instance().close_session()
        
        # Get the number total number of entries expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = all_orf_count )
        
        objects_to_update = []
        
        for orf in all_orf:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # If the ORF is not spliced 
            # or if there is no information about the splicing status of this ORF,
            # or if the splicing coordinates are missing,
            # then compute the genomic length using the start and stop coordinates.
            if ( ( not orf.spliced )
                 or ( orf.splice_starts == None ) 
                 or ( orf.splice_ends == None ) ):
                orf.genomic_length = orf.stop_pos - orf.start_pos + 1
                
            # If the splicing coordinates have been replaced by "TOO_LONG", then
            # set the value of the genomic length to None
            elif ( orf.splice_starts == Constants.REPLACE_TOO_LONG_STRINGS ):
                orf.genomic_length = None
            
            # Otherwise, compute the length of each "exon" and sum them to get the genomic length
            else:
                sp_starts = map( int, 
                                 orf.splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                sp_ends = map( int, 
                               orf.splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                
                exon_lengths = []
                for k in range( len( sp_starts ) ):
                    exon_lengths.append( abs( sp_ends[ k ] - sp_starts[ k ] ) + 1 )
                    
                orf.genomic_length = sum( exon_lengths )
                
            objects_to_update.append( orf )
        
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_update, 
                                     process = 'compute_orf_gen_len(): Computation of ORF genomic lengths' )
        
        
        
    ## compare_gen_orf_len
    #  -------------------
    #
    # This method allows to compare the nucleic length of each entry of the ORFTranscriptAsso table 
    # to the genomic length of its related entries in the ORF table (previously computed from 
    # genomics coordinates using the compute_gen_orf_len() method).
    # 
    def compare_gen_orf_len( self ):
        
        Logger.get_instance().info( 'Starting the comparison of ORFTranscriptAsso lengths' +
                                    ' to ORF genomic lengths.')
        
        # Get all the entries of the ORFTranscriptAsso table
        all_orftranscriptasso_query = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso )
        all_orftranscriptasso = all_orftranscriptasso_query.all()
        
        # Get all the entries of the ORF table and create a dictionary that associates to
        # each ORF id its genomic length
        all_orfs = SQLManagerPRO.get_instance().get_session().query( ORF ).all()
        all_orf_gen_len = {}
        for orf in all_orfs:
            all_orf_gen_len[ orf.id ] = orf.genomic_length
        
        # Get the number total number of entries expected to be treated and reset the ProgressionBar instance
        # to follow the progression
        ProgressionBar.get_instance().reset_instance( total = all_orftranscriptasso_query.count() )
        SQLManagerPRO.get_instance().close_session()
        
        for orftranscriptasso in all_orftranscriptasso:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # For each entry, try to gets the unique nucleic length
            if ( not orftranscriptasso.length_nt_max ):
                orftranscriptasso.gen_len_eq_orf_len = None
                
            elif ( orftranscriptasso.length_nt_min == orftranscriptasso.length_nt_max ):
                    
                    # Get the unique length
                    uniq_orftranscriptasso_len = orftranscriptasso.length_nt_min
                    
                    # Get the ORF corresponding to this ORFTranscriptAsso
                    orf_len = all_orf_gen_len.get( orftranscriptasso.orf_id )
                    
                    # Compare the lengths
                    if ( orf_len == Constants.REPLACE_TOO_LONG_STRINGS ):
                        orftranscriptasso.gen_len_eq_orf_len = None 
                    elif ( uniq_orftranscriptasso_len == orf_len ):
                        orftranscriptasso.gen_len_eq_orf_len = True
                    else:
                        orftranscriptasso.gen_len_eq_orf_len = False
                    
            else:
                orftranscriptasso.gen_len_eq_orf_len = False
                    
        self.batch_insert_to_PRO_db( objects_to_insert = all_orftranscriptasso, 
                                     process = 'compare_gen_orf_len(): Comparison of ORF genomic lengths' )

    
    
    # ===============================================================================
    # Merge the similar cell contexts together
    # ===============================================================================
    
    ## merge_cell_context
    #  ------------------
    #
    # This method allow to merge together the entries of the CellContext table 
    # are considered as similar.
    #
    # @throw DenCellORFException: When an error occurs trying to delete the initial CellContext entries.
    # @throw DenCellORFException: When an error occurs trying to delete the CellContextCatalog without
    #                             children.
    # 
    def merge_cell_context( self ):
        
        Logger.get_instance().info( 'Starting to merge and re-annotate the cellular contexts.')
        
        # Get the appropriate dictionary if the default dictionary is used
        self.species = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        if self.default_context_dict:
            self.cell_context_dict = self.cell_context_dict[ self.species ]        
        
        # Get all the entries of the CellContext table
        DataManager.get_instance().store_PRO_query_result( Constants.DM_ALL_CELL_CONTEXT, 'query( CellContext ).all()' )
        all_cellcontext = DataManager.get_instance().get_data( Constants.DM_ALL_CELL_CONTEXT )
        
        # Get the list of all the contexts registered in the CellContextCatalog table
        all_contexts_in_cellcontextcatalog = SQLManagerPRO.get_instance().get_session().query( CellContextCatalog.context ).all()
        all_contexts_in_cellcontextcatalog = GeneralUtil.query_result_to_list( all_contexts_in_cellcontextcatalog )
        
        # Get the total number of cell contexts expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        total_to_process = len( self.cell_context_dict.keys() )
        ProgressionBar.get_instance().reset_instance( total = total_to_process )
        
        for ( new_context, context_list ) in self.cell_context_dict.items():
            
            objects_to_insert = []
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # If the new context name does not yet exists in the CellContextCatalog,
            # create a new entry:
            if ( new_context not in all_contexts_in_cellcontextcatalog ):
                cellcontextcatalog = CellContextCatalog( context = new_context )
                objects_to_insert.append( cellcontextcatalog )

                # Keep record of this new entry
                all_contexts_in_cellcontextcatalog.append( new_context )
                
            # Get all the entries using one of the context of the list of 
            # contexts to update.
            # For each of these entries, delete them from the database, 
            # create a new instance using the ORFTranscriptAsso IDs of these entries, 
            # and the "new" cell_context value, and get the list of unique entries 
            # to insert in the database.
            
            # Get the entries using the cellular context to replace.
            all_cellcontext_to_update_query = SQLManagerPRO.get_instance().get_session().query( CellContext ).filter( CellContext.cell_context.in_( context_list ) )
            all_cellcontext_to_update_all = all_cellcontext_to_update_query.all()
            
            # Delete them from the database
            try:
                all_cellcontext_to_update_query.delete( synchronize_session = 'fetch' )
                SQLManagerPRO.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'ComputeMissingInfoStrategy.merge_cell_context():' +
                                           ' An error occurred trying to remove the entries of the' +
                                           ' CellContext table using the following cell contexts: ' + 
                                           ', '.join( context_list ) + 
                                           ' from the session and to commit changes.', e )
                        
            # Update them using the "new" cellular context, 
            # and get the list of unique entries
            for c in all_cellcontext_to_update_all:
                cell_context = CellContext( orftranscriptasso_id = c.orftranscriptasso_id,
                                            cell_context = new_context )
                if ( all_cellcontext.get( cell_context ) == None ):
                    all_cellcontext[ cell_context ] = cell_context
                    objects_to_insert.append( cell_context )
                
            # Add the new entries to the database
            if ( objects_to_insert != [] ):
                self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert, 
                                             process = ( 'merge_cell_context(): Re-annotation of cellular' +
                                                         ' contexts (' + ', '.join( context_list ) + ')' ) )
        
        # Delete all entries of the CellContextCatalog that are left without child
        cellcontextcatalog_wo_children_query = SQLManagerPRO.get_instance().get_session().query( CellContextCatalog ).filter( CellContextCatalog.CellContext_list == None )
        cellcontextcatalog_wo_children_count = cellcontextcatalog_wo_children_query.count()
        
        if ( cellcontextcatalog_wo_children_count != 0 ):
            Logger.get_instance().debug( str( cellcontextcatalog_wo_children_count ) + 
                                         ' entries of the CellContextCatalog table have been found' +
                                         ' without children and will be deleted.' )
            
            entries_to_delete_str = ', '.join( [ c.context for c in cellcontextcatalog_wo_children_query.all() ] )
            try:
                cellcontextcatalog_wo_children_query.delete( synchronize_session = 'fetch' )
                SQLManagerPRO.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'ComputeMissingInfoStrategy.merge_cell_context():' +
                                           ' An error occurred trying to remove the following' +
                                           ' CellContextCatalog entries from the session' +
                                           ' and to commit changes: ' + entries_to_delete_str + '.', e )
        
        # Close the session
        SQLManagerPRO.get_instance().close_session()
                
    
    
    # ===============================================================================
    # Methods to download the missing information in ORF and Transcript tables
    # =============================================================================== 
    
    ## download_missing_info
    #  ---------------------
    #
    # This method allows to download the missing information in ORF and Transcript tables.
    #
    # @throw DenCellORFException: When an error occurs trying to add a new PROMetadata entry (with current
    #                             ensembl release number) to the database.
    # @throw DenCellORFException: When an error occurs trying to update the PROMetadata entry containing 
    #                             current ensembl release number.
    #  
    def download_missing_info( self ):
        
        # Get the current genome version
        prometadata_query = SQLManagerPRO.get_instance().get_session().query( PROMetadata ).filter( PROMetadata.parameter == Constants.METATABLE_CURRENT_ANNOTATION )
        prometadata_count = prometadata_query.count()
        
        if ( prometadata_count == 1 ):
            prometadata = prometadata_query.one()
            self.current_annotation = prometadata.value
        else:
            Logger.get_instance().critical( 'The annotation version used in the database is expected to be' +
                                            ' provided in the PROMetadata table under the parameter ' + 
                                            Constants.METATABLE_CURRENT_ANNOTATION + 
                                            '. Please see the documentation for more information.' )
        
        
        # Get the current Ensembl release database
        sp = DataManager.get_instance().get_data( Constants.SPECIES_FULL )
        pyensembl_release = EnsemblUtil.get_ensembl_db( sp = sp, 
                                                        annotation_version = Constants.CURRENT_ENSEMBL_RELEASE )
        
        # Save the name of the Ensembl release currently used in the PROMetadata table
        prometadata_query = SQLManagerPRO.get_instance().get_session().query( PROMetadata ).filter( PROMetadata.parameter == Constants.METATABLE_CURRENT_ENSEMBL_RELEASE )
        prometadata_count = prometadata_query.count()
        
        if ( prometadata_count == 0 ):
            metadata_current_ensembl_release = PROMetadata( parameter = Constants.METATABLE_CURRENT_ENSEMBL_RELEASE,
                                                            value = Constants.CURRENT_ENSEMBL_RELEASE,
                                                            description = Constants.METATABLE_CURRENT_ENSEMBL_RELEASE_DESCRIPTION )
            try:
                SQLManagerPRO.get_instance().get_session().add( metadata_current_ensembl_release )
                SQLManagerPRO.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'ComputeMissingInfoStrategy.download_missing_info():' +
                                           ' An error occurred trying to add the PROMetadata entry containing' +
                                           ' the ensembl release information and committing the session.', e )
                
        else:
            metadata_current_ensembl_release = prometadata_query.one()
            if ( metadata_current_ensembl_release.value != str( Constants.CURRENT_ENSEMBL_RELEASE ) ):
                Logger.get_instance().warning( 'An Ensembl release different from the one used by the program (' +
                                               str( Constants.CURRENT_ENSEMBL_RELEASE ) + 
                                               ') has been found in the PROMetadata table (' +
                                               Constants.METATABLE_CURRENT_ENSEMBL_RELEASE + ': ' +
                                               str( metadata_current_ensembl_release.value ) + 
                                               '). Hence, this entry of the PROMetadata table will be updated.' +
                                               ' Warning code: ' + LogCodes.WARN_META_ENSEMBL_RELEASE_CONFL + '.' )
                metadata_current_ensembl_release.value = Constants.CURRENT_ENSEMBL_RELEASE
                metadata_current_ensembl_release.description = Constants.METATABLE_CURRENT_ENSEMBL_RELEASE_DESCRIPTION
                try:
                    SQLManagerPRO.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'ComputeMissingInfoStrategy.download_missing_info():' +
                                               ' An error occurred trying to update the PROMetadata entry' +
                                               ' containing the ensembl release information and committing the session.', e )
                    
        SQLManagerPRO.get_instance().close_session()
        
        # Download the ORF sequences
        self.download_orf_sequences()
        
        # Complete the transcript table
        self.complete_transcript_table( pyensembl_release )
        
        
    
    ## download_orf_sequences
    #  ----------------------
    #
    # This method allows to download the nucleic sequences for each entry of the ORF table.
    #  
    def download_orf_sequences( self ):
        
        ## Download the nucleic sequence
        #  -----------------------------
        
        Logger.get_instance().info( 'Starting to download the ORF sequences.')
        
        # Keep track of the ORFs that need to be discard for the download of sequence.
        # For all ORFs, one try to get it sequence at least once. If the sequence cannot be download due to 
        # technical reason (e.g. too high number of request in a short time or the server is unavailable), 
        # one will re-try to get it later; but if the sequence cannot be download for an other reason 
        # (e.g. the value of the start coordinate is lower than the value of the stop coordinate), then 
        # the ORF will be discarded from the list of ORFs for which it is necessary to try again to get
        # the sequence.
        orf_ids_to_discard = []
        
        # Get all the ORF IDs to process
        if self.force_overwrite:
            all_orf_ids_query = SQLManagerPRO.get_instance().get_session().query( ORF.id )
        else:
            all_orf_ids_query = SQLManagerPRO.get_instance().get_session().query( ORF.id ).filter( ORF.sequence == None )   
            
        all_orf_ids_count = all_orf_ids_query.count()
        all_orf_ids = all_orf_ids_query.all()
        SQLManagerPRO.get_instance().close_session()
                
        Logger.get_instance().debug( 'ComputeMissingInfoStrategy.download_orf_sequences():' +
                                     ' Starting to download ORF nucleic sequences.' )
        
        # Download the ORF sequences
        number_of_attempt = 0
        while( all_orf_ids_count > 0 ):
                                    
            # Reset the ProgressionBar instance to follow the progression
            ProgressionBar.get_instance().reset_instance( total = all_orf_ids_count )
            
            # If this is not the first attempt to download the sequence, then log it
            number_of_attempt += 1
            if ( number_of_attempt > 1 ):
                Logger.get_instance().debug( 'ComputeMissingInfoStrategy.download_orf_sequences():' +
                                             ' Re-trying to download the ORF sequences for ' +
                                             str( all_orf_ids_count ) + ' entries of the ORF table' +
                                             ' (Attempt number: ' + str( number_of_attempt )+ ').' )
            
            # Get the list of all the ORF IDs that need to be treated
            all_orf_ids = GeneralUtil.query_result_to_list( all_orf_ids )
            
            # In order to limit the number of entries updated in the same session,
            # to limit the time a session is opened, treat the list of ORFs by
            # batch of a given size
            # Define the minimal index of the list of ORFs to treat
            min_bound = 0
            while( min_bound < len( all_orf_ids ) ):
                
                # Defined the maximal index of the list of ORFs to treat
                max_bound = min( min_bound + Constants.MAX_COMMIT_BATCH_SIZE, 
                                 len( all_orf_ids ) )
                
                # Get the list of IDs of the ORFs to process
                orf_ids_to_process = all_orf_ids[ min_bound : max_bound ]
                
                # Get the ORFs corresponding to these indexes
                orfs_to_process = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    ORF 
                                                                                    ).filter( 
                                                                                                ORF.id.in_( orf_ids_to_process ) 
                                                                                            ).all()
                SQLManagerPRO.get_instance().close_session()
                
                objects_to_update = []
                
                for orf in orfs_to_process:
                    
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Download the sequence
                    try:
                        orf.sequence = self.download_orf_seq( orf = orf, 
                                                              genome_version = self.current_annotation )
                    except HTTPException as e:
                        orf.sequence = None
                        # Discard the ORF if the exception raised is related to the attributes of the ORF itself
                        # (and not to the server availability)
                        if ( e.get_code() in ComputeMissingInfoStrategy.HTTP_ERRORS_ALLOW_RETRY ):
                            Logger.get_instance().debug( 'ComputeMissingInfoStrategy.download_orf_sequences():' +
                                                         ' An error occurred trying to download the sequence' +
                                                         ' for the ORF with ID "' + str( orf.id ) + '": \n' + 
                                                         e.get_message() + '\n An other attempt to download the' +
                                                         ' sequence should be performed later.' )
                        else:
                            orf_ids_to_discard.append( orf.id )
                            Logger.get_instance().error( 'ComputeMissingInfoStrategy.download_orf_sequences():' +
                                                         ' An error occurred trying to download the sequence' +
                                                         ' for the ORF with ID "' + str( orf.id ) + '": \n' + 
                                                         e.get_message() + '\n Hence, the sequence of this ORF' +
                                                         ' will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_DOWNLOAD_SEQ + '.',
                                                         ex = False )
                    except DenCellORFException as e:
                        orf.sequence = None
                        Logger.get_instance().debug( 'ComputeMissingInfoStrategy.download_orf_sequences():' +
                                                     ' An error occurred trying to download the sequence' +
                                                     ' for the ORF with ID "' + str( orf.id ) + '": \n' + 
                                                     e.get_message() + '\n An other attempt to download the' +
                                                     ' sequence should be performed later.' )
                    else:
                        # If the sequence cannot be translated due to availability of ORF 
                        # attributes (e.g. a position is missing), discard the ORF
                        if ( orf.sequence == None ):
                            orf_ids_to_discard.append( orf.id )
                    
                                            
                    # Translate the sequence
                    if orf.sequence:
                        try:
                            orf.sequence_aa = GeneticsUtil.translate_dna( dna_seq = orf.sequence, 
                                                                          include_stop = False,
                                                                          to_stop = False )
                        except TranslateDNAException as e:
                            orf.sequence_aa = e.get_aa_seq()
                            Logger.get_instance().warning( 'The length of the sequence of the ORF with ID "' +
                                                           str( orf.id ) + '" is not a multiple of three.' +
                                                           ' Hence, the sequence has been translated ignoring' +
                                                           ' the last ' + str( e.get_remainder() ) + 
                                                           ' nucleotides.' +
                                                           ' Warning code: ' + LogCodes.WARN_TRANSL_SEQSIZE_NOT3 + '.' )
                            
                    objects_to_update.append( orf )
                            
                # Add objects to the session and commit changes
                self.batch_insert_to_PRO_db( objects_to_update,
                                             process = 'Download of ORF sequences' )
                
                # Redefine the minimum bound of the interval
                min_bound = max_bound
        
            # Update the query to get all the ORF entries that needs to be re-processed
            all_orf_ids_query = SQLManagerPRO.get_instance().get_session().query( ORF.id ).filter(
                                                                                                    ORF.sequence == None,
                                                                                                    ORF.id.notin_( orf_ids_to_discard )
                                                                                                    )
            all_orf_ids_count = all_orf_ids_query.count()
            all_orf_ids = all_orf_ids_query.all()
            SQLManagerPRO.get_instance().close_session()
        
        
    
    ## download_orf_seq
    #  ----------------
    #
    # This is a static method that allows to download the nucleic sequence of an ORF, 
    # considering the splicing when the coordinates are provided.
    #
    # @param orf: ORF - An ORF instance (PRO model).
    # @param genome_version: String - The genome annotation version to use.
    #
    # @return String / None - The nucleic sequence of the ORF 
    #                         (or None if it cannot be downloaded).
    #
    @staticmethod
    def download_orf_seq( orf, genome_version ):
        
        # If the ORF is not spliced, download the sequence between the start and the stop
        if ( orf.spliced == False ):
            return ComputeMissingInfoStrategy.download_seq_from_ensembl( chr = orf.chromosome, 
                                                                         strand = orf.strand, 
                                                                         start = orf.start_pos, 
                                                                         stop = orf.stop_pos, 
                                                                         genome_version = genome_version )
        
        # Otherwise, try to get the sequence of each "exon" and concatenate them
        elif orf.spliced:
            if ( ( orf.splice_starts != None ) and ( orf.splice_ends != None ) ):
                
                # Get the list of starts and end coordinates 
                starts_pos = orf.splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                ends_pos = orf.splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
            
                # If the ORF is on the '-' strand, permute the start and stop coordinates 
                # in order to make sure the start position is lower than the stop one
                if ( orf.strand == '-' ):
                    ( starts_pos, ends_pos ) = ( ends_pos, starts_pos )
                    
                # Download the sequence of each "exon"
                sequence = []
                impossible_download = False
                idx = 0
                
                while ( ( not impossible_download ) and ( idx < len( starts_pos) ) ):
                    
                    exon_seq = ComputeMissingInfoStrategy.download_seq_from_ensembl( chr = orf.chromosome,
                                                                                     strand = orf.strand, 
                                                                                     start = starts_pos[ idx ], 
                                                                                     stop = ends_pos[ idx ], 
                                                                                     genome_version = genome_version )

                    if ( exon_seq == None ):
                        impossible_download = True
                        sequence = None
                    
                    else:
                        idx += 1
                        sequence.append( exon_seq )
                            
                # Concatenate the sequences and return it
                if sequence:
                    return ''.join( sequence )
            
            # If some of the splicing coordinates are missing, set the sequence equals to None
            else:
                return None
            
        else:
            return None
        
        
    
    ## complete_transcript_table
    #  -------------------------
    #
    # This method allows to download the missing information for each entry of the Transcript table.
    #
    # @param pyensembl_release: EnsemblRelease - The EnsemblRelease to query to find the information 
    #                                            associated with the transcript IDs / names.
    #
    def complete_transcript_table( self, pyensembl_release ):
        
        Logger.get_instance().info( 'Starting to download missing information in Transcript table.' )
        
        # Get all the Transcript entries
        all_transcripts_query = SQLManagerPRO.get_instance().get_session().query( Transcript )
        
        # Get the number total number of entries expected to be treated 
        # and reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = all_transcripts_query.count() )
        
        # Get all the Transcript entries
        all_transcripts = all_transcripts_query.all()
        SQLManagerPRO.get_instance().close_session()
        
        objects_to_update = []
        
        Logger.get_instance().debug( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                     ' Starting the completion of Transcript table.' )
        
        for transcript in all_transcripts:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # If the transcript ID is known, try to get information about it from Ensembl
            get_info_from_ensembl = False
                
            if ( transcript.transcript_id != Constants.UNKNOWN_TRANSCRIPT ):
                # Try to query Ensembl using the transcript_id as an actual ID
                try:
                    pyensembl_tr = pyensembl_release.transcript_by_id( transcript.transcript_id )
                except:
                    # Try to query Ensembl using the transcript_id as a transcript name
                    try:
                        pyensembl_tr = pyensembl_release.transcript_by_name( transcript.transcript_id )
                    except:
                        Logger.get_instance().warning( 'Query in Ensembl database for the transcript with' +
                                                       ' official ID / name ' + str( transcript.transcript_id ) + 
                                                       ' (ID in Transcript table: ' + str( transcript.id ) +
                                                       ') failed.' +
                                                       ' Warning code: ' + LogCodes.WARN_ENSEMBL_TR_NOT_FOUND + '.' )
                    else:
                        if ( len( pyensembl_tr ) == 1 ):
                            pyensembl_tr = pyensembl_tr[ 0 ]
                            get_info_from_ensembl = True
                        else:
                            Logger.get_instance().warning( 'Query in Ensembl database for the transcript with' +
                                                           ' official ID / name ' + str( transcript.transcript_id ) + 
                                                           ' (ID in Transcript table: ' + str( transcript.id ) +
                                                           ') failed.' +
                                                           ' Warning code: ' + LogCodes.WARN_ENSEMBL_TR_NOT_FOUND + '.' )
                            
                else:
                    get_info_from_ensembl = True

            
            # When feasible, use pyensembl to recover missing information
            if get_info_from_ensembl:
                
                # NB: The following information may be recover using pyensembl
                #     - The transcript strand 
                #     - The transcript start and stop positions
                #     - The transcript sequence
                #     - The transcript biotype
                #     - The CDS start and stop codon positions
                
                transcript.transcript_name = pyensembl_tr.name
                
                tr_strand = pyensembl_tr.strand
                tr_start_pos = pyensembl_tr.start
                tr_end_pos = pyensembl_tr.end
                tr_rna_biotype = pyensembl_tr.biotype
                tr_sequence = pyensembl_tr.sequence                     # Spliced cDNA sequence of transcript
                                                                        # (includes 5' UTR, coding sequence, and 3' UTR)
                try:
                    # The cds_genomic_length is in nucleotides, includes the stop codon 
                    # and excludes the introns
                    tr_cds_genomic_length = len( pyensembl_tr.coding_sequence )
                except:
                    tr_cds_genomic_length = None
                
                # If some of the attributes are already known but different 
                # from the information get from Ensembl, then log a warning 
                # and save the information from Ensembl
                for att in [ 'strand', 'start_pos', 'end_pos', 'rna_biotype', 'sequence', 'cds_genomic_length' ]:
                    transcript_att_value = getattr( transcript, att )
                    pyensembl_tr_att_value = eval( 'tr_' + att )
                    
                    if pyensembl_tr_att_value:
                        
                        if ( ( transcript_att_value != None ) and ( pyensembl_tr_att_value != transcript_att_value ) ):
                            Logger.get_instance().warning( 'The transcript with official ID ' + 
                                                           str( transcript.transcript_id ) +
                                                           ' has been found having the value ' + 
                                                           str( transcript_att_value ) + 
                                                           ' for the attribute ' + att +
                                                           ' in the database, whilst Ensembl provides the value ' + 
                                                           str( pyensembl_tr_att_value ) + ' for this transcript.' +
                                                           ' Warning code: ' + LogCodes.WARN_DCORF_TR_CONFL + '.' )
                            
                        setattr( transcript, att, pyensembl_tr_att_value )
                        
                        
                # The Transcript table store the CDS start and stop positions such as:
                # - For '+'-strand transcripts:
                #    - The cds_start_pos contains the location of the first nucleotide of the start codon
                #    - The cds_stop_pos contains the location of the last nucleotide of the stop codon
                # - For '-'-strand transcripts:
                #    - The cds_start_pos contains the location of the last nucleotide of the stop codon
                #    - The cds_stop_pos contains the location of the first nucleotide of the start codon
                if ( transcript.strand == '+' ):
                    try:
                        tr_cds_start_pos = pyensembl_tr.start_codon_positions[ 0 ]
                    except:
                        tr_cds_start_pos = None
                        
                    try:
                        tr_cds_stop_pos = pyensembl_tr.stop_codon_positions[ 2 ]
                    except:
                        tr_cds_stop_pos = None
                        
                elif ( transcript.strand == '-' ):
                    try:
                        tr_cds_start_pos = pyensembl_tr.stop_codon_positions[ 0 ]
                    except:
                        tr_cds_start_pos = None
                        
                    try:
                        tr_cds_stop_pos = pyensembl_tr.start_codon_positions[ 2 ]
                    except:
                        tr_cds_stop_pos = None
                
                # If some of the attributes are already known but different 
                # from the information get from Ensembl, then log a warning 
                # and save the information from Ensembl
                for att in [ 'cds_start_pos', 'cds_stop_pos' ]:
                    transcript_att_value = getattr( transcript, att )
                    pyensembl_tr_att_value = eval( 'tr_' + att )
                    
                    if pyensembl_tr_att_value:
                        
                        if ( ( transcript_att_value != None ) and ( pyensembl_tr_att_value != transcript_att_value ) ):
                            Logger.get_instance().warning( 'The transcript with official ID ' + 
                                                           str( transcript.transcript_id ) +
                                                           ' has been found having the value ' + 
                                                           str( transcript_att_value ) + 
                                                           ' for the attribute ' + att +
                                                           ' in the database, whilst Ensembl provide the value ' + 
                                                           str( pyensembl_tr_att_value ) + ' for this transcript.' +
                                                           ' Warning code: ' + LogCodes.WARN_DCORF_TR_CONFL + '.' )
                            
                        setattr( transcript, att, pyensembl_tr_att_value )
                        
            objects_to_update.append( transcript )
            
        # Commit the session
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_update,
                                     process = 'Transcript information' )
            
            
        Logger.get_instance().info( 'Starting to download missing sequences in Transcript table.' )
    
        # Keep track of the transcripts that need to be discard for the download of sequence.
        # For all transcripts, one try to get it sequence at least once. If the sequence cannot be 
        # download due to technical reason (e.g. too high number of request in a short time or the server 
        # is unavailable), one will try to get the sequence later but if the sequence cannot be downloaded 
        # for an other reason (e.g. the value of the start coordinate is lower than the value of the stop 
        # coordinate), then the transcript will be discarded from the list of Transcripts for which it is 
        # necessary to try again to get the sequence.
        transcripts_to_discard = []
    
        # Get all the Transcript IDs that miss their sequence
        if self.force_overwrite:
            all_transcript_ids_query = SQLManagerPRO.get_instance().get_session().query( Transcript.id ).filter( 
                                                                                                                    Transcript.id.notin_( transcripts_to_discard ),
                                                                                                                    Transcript.strand != None,
                                                                                                                    Transcript.start_pos != None,
                                                                                                                    Transcript.end_pos != None
                                                                                                                 )
        else:
            all_transcript_ids_query = SQLManagerPRO.get_instance().get_session().query( Transcript.id ).filter( 
                                                                                                                    Transcript.sequence == None,
                                                                                                                    Transcript.id.notin_( transcripts_to_discard ),
                                                                                                                    Transcript.strand != None,
                                                                                                                    Transcript.start_pos != None,
                                                                                                                    Transcript.end_pos != None
                                                                                                                 )
            
        all_transcript_ids_count = all_transcript_ids_query.count()
        all_transcript_ids = all_transcript_ids_query.all()
        SQLManagerPRO.get_instance().close_session()
            
        Logger.get_instance().debug( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                     ' Starting to download transcript sequences.' )
        
        # Download the transcript sequence
        number_of_attempt = 0
        while ( all_transcript_ids_count > 0 ):
            
            # Get the number total number of entries expected to be treated and 
            # reset the ProgressionBar instance to follow the progression
            ProgressionBar.get_instance().reset_instance( total = all_transcript_ids_count )
            
            # If this is not the first attempt to download the sequence, then log it
            number_of_attempt += 1
            if number_of_attempt > 1:
                Logger.get_instance().debug( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                             ' Re-trying to download the transcript sequences for ' +
                                             str( all_transcript_ids_query.count() ) + ' entries of the Transcript table' +
                                             ' (Attempt number: ' + str( number_of_attempt )+ ').' )
            
            # Get the list of all the transcripts IDs that needs to be treated
            all_transcript_ids = GeneralUtil.query_result_to_list( all_transcript_ids )
                        
            # In order to limit the number of entries updated in the same session,
            # to limit the time a session is opened, treat the list of transcripts 
            # by batch of a given size.
            # Define the minimal index of the list of ORFs to treat.
            min_bound = 0
            while( min_bound < len( all_transcript_ids ) ):
                
                # Defined the maximal index of the list of transcripts to treat
                max_bound = min( min_bound + Constants.MAX_COMMIT_BATCH_SIZE, 
                                 len( all_transcript_ids ) )
                
                # Get the list of IDs of the ORFs to process
                transcript_ids_to_process = all_transcript_ids[ min_bound : max_bound ]
                
                # Get the Transcripts corresponding to these indexes
                transcripts_to_process = SQLManagerPRO.get_instance().get_session().query( 
                                                                                            Transcript 
                                                                                         ).filter( 
                                                                                                    Transcript.id.in_( transcript_ids_to_process ) 
                                                                                                  ).all()
                SQLManagerPRO.get_instance().close_session()
                
                objects_to_update = []
                
                for transcript in transcripts_to_process:
                    
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Get the chromosome of the gene related to this transcript
                    transcript_chromosome = SQLManagerPRO.get_instance().get_session().query( 
                                                                                                PROGene.chromosome 
                                                                                            ).filter( 
                                                                                                        PROGene.gene_id == transcript.gene_id 
                                                                                                    ).one()
                    transcript_chromosome = transcript_chromosome[ 0 ]
                    SQLManagerPRO.get_instance().close_session()
                
                    # Download the sequence
                    try:
                        transcript.sequence = ComputeMissingInfoStrategy.download_seq_from_ensembl( chr = transcript_chromosome,
                                                                                                    strand = transcript.strand,
                                                                                                    start = transcript.start_pos,
                                                                                                    stop = transcript.end_pos,
                                                                                                    genome_version = self.current_annotation )
                    except HTTPException as e:
                        transcript.sequence = None
                        # Discard the transcript if the exception raised is related to the attributes of the
                        # transcript itself (and not to the server availability)
                        if e.get_code() in ComputeMissingInfoStrategy.HTTP_ERRORS_ALLOW_RETRY:
                            Logger.get_instance().debug( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                                         ' An error occurred trying to download the sequence' +
                                                         ' for the transcript with ID "' + str( transcript.id ) + 
                                                         '": \n' + e.get_message() + '\n An other attempt to' +
                                                         ' download the sequence should be performed.' )
                        else:
                            transcripts_to_discard.append( transcript.id )
                            Logger.get_instance().error( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                                         ' An error occurred trying to download the sequence' +
                                                         ' for the transcript with ID "' + str( transcript.id )+
                                                         '": \n' + e.get_message() + '\n Hence, the sequence' +
                                                         ' of this transcript will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_DOWNLOAD_SEQ,
                                                         ex = False )
                    except DenCellORFException as e:
                        transcript.sequence = None
                        Logger.get_instance().debug( 'ComputeMissingInfoStrategy.complete_transcript_table():' +
                                                     ' An error occurred trying to download the sequence' +
                                                     ' for the transcript with ID "' + str( transcript.id ) + 
                                                     '": \n' + e.get_message() + '\n An other attempt to' +
                                                     ' download the sequence should be performed.' )
                    
                    objects_to_update.append( transcript )
                        
                # Commit the changes
                self.batch_insert_to_PRO_db( objects_to_insert = objects_to_update,
                                             process = 'Download transcript sequences' )
                
                # Redefine the minimum bound of the interval
                min_bound = max_bound
            
            # Update the query to get all the Transcript entries that needs to be re-processed
            all_transcript_ids_query = SQLManagerPRO.get_instance().get_session().query( Transcript.id ).filter( 
                                                                                                                    Transcript.sequence == None,
                                                                                                                    Transcript.id.notin_( transcripts_to_discard ),
                                                                                                                    Transcript.strand != None,
                                                                                                                    Transcript.start_pos != None,
                                                                                                                    Transcript.end_pos != None
                                                                                                                 )
            all_transcript_ids_count = all_transcript_ids_query.count()
            all_transcript_ids = all_transcript_ids_query.all()
            SQLManagerPRO.get_instance().close_session()
                        
        SQLManagerPRO.get_instance().close_session()
    
    
    
    ## download_seq_from_ensembl
    #  -------------------------
    #
    # This method allows to download a nucleic sequence from Ensembl.
    #
    # @param chr: String - The chromosome name (without 'chr' prefix).
    # @param strand: String - The DNA strand.
    # @param start: Integer or String - The genomic coordinates of the first position.
    # @param stop: Integer or String - The genomic coordinates of the last position.
    # @param genome_version: String - The NCBI genome version (e.g. GRCh38).
    #
    # @return seq: String - The nucleic sequence of the region (in uppercase).
    #
    # @throw HTTPException: When a HTTP error occurred while trying to download the sequence 
    #                       using the EnsemblRestClient.
    # @throw DenCellORFException: When an Exception has been raised trying to download the sequence 
    #                             using the EnsemblRestClient.
    #
    @staticmethod
    def download_seq_from_ensembl( chr, strand, start, stop, genome_version ):
        
        # Get the species short name
        species = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
                
        try:
            seq = EnsemblRestClient.get_instance().get_sequence( chr = chr, 
                                                                 strand = strand,
                                                                 start = start, 
                                                                 stop = stop,
                                                                 sp = species,
                                                                 genome_version = genome_version )
        except HTTPException as e:
            raise HTTPException( 'ComputeMissingInfoStrategy.download_seq_from_ensembl():' +
                                 ' A HTTP error occurred trying to get the sequence at' + 
                                 ' chr' + str( chr ) + strand + ':' + str( start ) + '-' + str( stop ) + 
                                 ', on annotation version ' + genome_version + '.', 
                                 e, e.code )
        except Exception as e:
            raise DenCellORFException( 'ComputeMissingInfoStrategy.download_seq_from_ensembl():' +
                                       ' An error occurred trying to get the sequence at' + 
                                       ' chr' + str( chr ) + strand + ':' + str( start ) + '-' + str( stop ) +
                                       ', on annotation version ' + genome_version + '.' + 
                                       ' Error code: ' + LogCodes.ERR_DOWNLOAD_SEQ + '.', e )
        
        return seq
    
    
    
    ## complete_utrnabiotypecatalog_table
    #  ----------------------------------
    #
    # This method allows to complete the UTRNABiotypeCatalog table with all unique 
    # biotypes registered in the Transcript table.
    #
    # @throw DenCellORFException: When an error occurs trying to delete the UTRNABiotypeCatalog
    #                             entries (when the "-f" option has been selected).
    #
    def complete_utrnabiotypecatalog_table( self ):
        
        Logger.get_instance().debug( 'Starting to complete the UTRNABiotypeCatalog table.')
        
        # First, reset the UTRNABiotypeCatalog content if necessary
        if self.force_overwrite:
            utrnabiotypecatalog_query = SQLManagerPRO.get_instance().get_session().query( UTRNABiotypeCatalog )
            utrnabiotypecatalog_count = utrnabiotypecatalog_query.count()
            
            if ( utrnabiotypecatalog_count != 0 ):
                Logger.get_instance().info( str( utrnabiotypecatalog_count ) + 
                                            ' entries have been found in the UTRNABiotypeCatalog table' +
                                            ' and will be deleted prior to the completion of this table.' )
                
                entries_to_delete_str = ', '.join( [ utrna.biotype for utrna in utrnabiotypecatalog_query.all() ] )
                try:
                    utrnabiotypecatalog_query.delete( synchronize_session='fetch' )
                    SQLManagerPRO.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'ComputeMissingInfoStrategy.complete_utrnabiotypecatalog_table():' +
                                               ' An error occurred trying to remove the following' +
                                               ' UTRNABiotypeCatalog entries from the session' +
                                               ' and to commit changes: ' + entries_to_delete_str + '.', e )
                    
                SQLManagerPRO.get_instance().close_session()
        
        # Get the list of unique biotypes from the Transcript entries
        all_uniq_rna_biotype = SQLManagerPRO.get_instance().get_session().query( Transcript.rna_biotype ).filter( Transcript.rna_biotype != None ).distinct().all()
        uniq_rna_biotype_list = GeneralUtil.query_result_to_list( all_uniq_rna_biotype )
        
        # Get all the entries of the UTRNABiotypeCatalog table
        DataManager.get_instance().store_PRO_query_result( Constants.DM_ALL_UTRNABIOTYPECATALOG, 
                                                           'query( UTRNABiotypeCatalog ).all()' )
        all_utrnabiotypecatalog = DataManager.get_instance().get_data( Constants.DM_ALL_UTRNABIOTYPECATALOG )
        
        objects_to_insert = []
        for rna_biotype in uniq_rna_biotype_list:
            
            utrnabiotypecatalog = UTRNABiotypeCatalog( biotype = rna_biotype )
            
            # Create a new entry if necessary
            existing_utrnabiotypecatalog = all_utrnabiotypecatalog.get( utrnabiotypecatalog )
            if ( not existing_utrnabiotypecatalog ):
                objects_to_insert.append( utrnabiotypecatalog )
        
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert, 
                                     process = ( 'complete_utrnabiotypecatalog_table():' +
                                                 ' Completion of the UTRNABiotypeCatalog table' ) )
        SQLManagerPRO.get_instance().close_session()
        
                
    
    # ===============================================================================
    # Common methods
    # ===============================================================================    

    ## batch_insert_to_PRO_db
    #  ----------------------
    # 
    # This method allows to insert a list of objects in the database.
    # Large sets of objects are split into several batches which are inserted one at a time.
    #
    # @param objects_to_insert: List - The list of objects to insert in the database.
    # @param process: String - The name of the process that generated this list.
    #
    @staticmethod
    def batch_insert_to_PRO_db( objects_to_insert, process='Undefined process' ):
                
        SQLManagerPRO.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert,
                                                         process = process )
    