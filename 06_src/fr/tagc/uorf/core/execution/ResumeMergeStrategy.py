# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy
from fr.tagc.uorf.core.execution.MergeStrategy import MergeStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## ResumeMergeStrategy
#  ===================
#
# This class inherits from MergeStrategy and is a strategy aiming to re-start 
# the merging from the checkpoint preceding its fail. 
# It can resume at one of these points:
# - After having successfully copying the content of "conserved" tables.
# - After having successfully computed and inserted the content of the ORF table.
# - After having successfully computed and inserted the content of the Transcript table.
# - After having successfully computed the ( ORF ID (PRO), Transcript ID (PRO) ) couples
#   and saved the information in pickled files.
#   NB: Resuming at this stage assumes that the dictionary that associates to each unique 
#       ( ORF ID (PRO), Transcript ID (PRO) ) couples to the list of all the DSORFTranscriptAsso 
#       (DS) that are related to it has already been successfully computed and saved.
# - During the merging of the DSORFTranscriptAsso entries (assuming it failed).
#   NB: Resuming at this stage assumes that the dictionary that associates to each unique 
#       ( ORF ID (PRO), Transcript ID (PRO) ) couples to the list of all the DSORFTranscriptAsso 
#       (DS) that are related to it has already been successfully computed and saved.
# - After having successfully computed and inserted the content of the ORFTranscriptAsso
#   table.
#
# NB: To run this strategy you need to ensure both the DS and PRO database have not 
#     been altered since (i.e. no strategy run since the merging that failed) and that
#     temporary files (.dcorf) have not been compromised, renamed or move from their
#     original location.
#
class ResumeMergeStrategy( MergeStrategy ):
                
    ## Class variables
    #  ---------------
    #
    # Resume after having successfully copying the content 
    # of "conserved" tables
    RESUME_AFTER_CONSERVED = 'after_conserved'
    
    # Resume after having successfully computed and inserted 
    # the content of the ORF table.  
    RESUME_AFTER_ORF = 'after_orf'
    
    # Resume after having successfully computed and inserted 
    # the content of the Transcript table.
    RESUME_AFTER_TRANSCRIPT = 'after_transcript'
    
    # Resume after having successfully computed the 
    # ( ORF ID (PRO), Transcript ID (PRO) ) couples
    RESUME_AFTER_OTA_ID_ASSO = 'after_ota_id_asso'
    
    # Resume during the merging of DSORFTranscriptAsso entries
    RESUME_DURING_OTA = 'during_ota'
    
    # Resume after having successfully computed and inserted the content of the 
    # ORFTranscriptAsso table
    RESUME_AFTER_OTA = 'after_ota'
    
    # List of stages
    RESUME_STAGES_LIST = [ RESUME_AFTER_CONSERVED, RESUME_AFTER_ORF, RESUME_AFTER_TRANSCRIPT, 
                           RESUME_AFTER_OTA_ID_ASSO, RESUME_DURING_OTA, RESUME_AFTER_OTA ]


    ## Constructor of ResumeMergeStrategy
    #  ----------------------------------
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
    # @throw DenCellORFException - When the name of the step at which resume the merging
    #                              is unknown.
    #
    def __init__( self ):

        MergeStrategy.__init__( self )
        
        # Get the stage at which the Merge strategy has to be resumed
        self.resume_at_stage = OptionManager.get_instance().get_option( OptionConstants.OPTION_RESUME_STEP_NAME,
                                                                        not_none = True )
        if ( self.resume_at_stage not in ResumeMergeStrategy.RESUME_STAGES_LIST ):
            raise DenCellORFException( 'The name of the last step successfully completed provided (' + 
                                       self.resume_at_stage + ') is not allowed.' +
                                       ' Please use one of the following list: ' +
                                       ', '.join( ResumeMergeStrategy.RESUME_STAGES_LIST ) + '.' )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete the ORFTranscriptAsso table (PRO database)
    # by merging the entries of the DSORFTranscriptAsso table (DS database).
    # 
    # @throw DenCellORFException - When an exception has been raised during the DatabaseCheck.
    # @throw DenCellORFException - When a table that is expected to be filled in is empty.
    # @throw DenCellORFException - When an error occurred during the execution of a MergeStrategy
    #                              method.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check the DS and PRO databases are 
        # reachable prior to resume the merging
        Logger.get_instance().info( 'Checking the databases prior to resume the merging...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( 'An error occurred whilst checking the database prior to' +
                                       ' merge the DSORFTranscriptAsso entries.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        
        # Delete the content of some tables if necessary
        # ----------------------------------------------
            
        # Remove the eventual content of the ORF table and of its children
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED ] ):
            try:
                SQLManagerPRO.get_instance().get_session().query( ORF ).delete()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' delete all the entries of the ORF table.' , e )
            else:
                SQLManagerPRO.get_instance().commit()
            
        # Remove the eventual content of the Transcript table and of its children
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF ] ):
            try:
                SQLManagerPRO.get_instance().get_session().query( Transcript ).delete()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' delete all the entries of the Transcript table.' , e )
            else:
                SQLManagerPRO.get_instance().commit()
            
        # Remove the eventual content of the ORFTranscriptAsso table and of its children
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO ] ):
            try:
                SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).delete()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' delete all the entries of the ORFTranscriptAsso table.' , e )
            else:
                SQLManagerPRO.get_instance().commit()
        
        
        # Check the content of tables that are expected 
        # to contain entries
        # ---------------------------------------------
                              
        # Check the conserved tables 
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                       ResumeMergeStrategy.RESUME_DURING_OTA,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA ] ):
            prometadata_count = SQLManagerPRO.get_instance().get_session().query( PROMetadata ).count()
            progene_count = SQLManagerPRO.get_instance().get_session().query( PROGene ).count()
            progenealias_count = SQLManagerPRO.get_instance().get_session().query( PROGeneAlias ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( ( prometadata_count == 0 ) 
                 or ( progene_count == 0 )
                 or ( progenealias_count == 0 ) ):
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): One of the "conserved" table' +
                                           ' is empty when it is expected to be filled in (PROMetadata: ' +
                                           str( prometadata_count ) + ', PROGene: ' + str( progene_count ) +
                                           ', PROGeneAlias: ' + str( progenealias_count ) )
                
        # Check the ORF table
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                       ResumeMergeStrategy.RESUME_DURING_OTA,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA ] ):
            orf_count = SQLManagerPRO.get_instance().get_session().query( ORF ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( orf_count == 0 ):
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): The ORF table does not contain' +
                                           ' any entry whilst the merging of DSORFs is expected to have' +
                                           ' been completed successfully.' )
                
        # Check the Transcript table
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                       ResumeMergeStrategy.RESUME_DURING_OTA,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA ] ):
            transcript_count = SQLManagerPRO.get_instance().get_session().query( Transcript ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( transcript_count == 0 ):
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): The Transcript table does not' +
                                           ' contain any entry whilst the merging of DSTranscripts is' +
                                           ' expected to have been completed successfully.' )
                
        # Check the ORFTranscriptAsso table
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_OTA ] ):
            ota_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( ota_count == 0 ):
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): The ORFTranscriptAsso table does not' +
                                           ' contain any entry whilst the merging of DSORFTranscriptAsso is' +
                                           ' expected to have been completed successfully.' )
        
        # Resume the merging
        # ------------------
        
        # Merge the same ORFs together
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED ] ):
            try:
                self.merge_dsorfs()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' merge the DSORF entries.', e )
                
                
        # Merge the same transcripts together
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF ] ):
            try:
                self.merge_dstranscripts()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' merge the DSTranscript entries.', e )
        
        
        # Recover all the DSORFTranscriptAsso, and associate them with their actual ORFs and transcript
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                       ResumeMergeStrategy.RESUME_DURING_OTA ] ):
            try:
                self.merge_dsorftranscriptasso()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' merge the DSORFTranscriptAsso entries.', e )
        
        
        # Clean the database by removing parent entries that have no child
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                       ResumeMergeStrategy.RESUME_DURING_OTA,
                                       ResumeMergeStrategy.RESUME_AFTER_OTA ] ):
            try:
                self.clean_pro_database()
            except Exception as e:
                raise DenCellORFException( 'ResumeMergeStrategy.execute(): An error occurred trying to' +
                                           ' clean the database after merging.', e )
                
                
    
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
        # If they have not yet been computed, then do it
        if ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_CONSERVED,
                                       ResumeMergeStrategy.RESUME_AFTER_ORF,
                                       ResumeMergeStrategy.RESUME_AFTER_TRANSCRIPT ] ):
            self.get_dsorftranscriptasso_to_merge()
            
        # Otherwise import them from the .dcorf file
        elif ( self.resume_at_stage in [ ResumeMergeStrategy.RESUME_AFTER_OTA_ID_ASSO,
                                         ResumeMergeStrategy.RESUME_DURING_OTA ] ):
            self.import_dsorftranscriptasso_to_merge()
        
        # Any other case that is not handle should raise a programming exception
        else:
            raise DenCellORFException( 'ResumeMergeStrategy.merge_dsorftranscriptasso(): The case ' +
                                       self.resume_at_stage + ' is not properly handled in the method!' +
                                       ' Please contact the developer if you see this message.' )
        
        # Merge the entries of the DSORFTranscriptAsso table        
        self.merge_dsota()
        
        
    
    ## import_dsorftranscriptasso_to_merge
    #  -----------------------------------
    #
    # This method allows to generate the dictionary that associates to each unique 
    # ( ORF ID (PRO), Transcript ID (PRO) ) couple that exists the list of all 
    # the DSORFTranscriptAsso (DS) that are related to it using the dictionary of 
    # IDs saved during the initial run of the Merge strategy and to to store this 
    # dictionary in the DataManager main dictionary.
    # 
    def import_dsorftranscriptasso_to_merge( self ):
        
        Logger.get_instance().debug( 'ResumeMergeStrategy.get_dsorftranscriptasso_to_merge():' +
                                     ' Getting the dictionary that associate to each existing' +
                                     ' ( ORF ID, Transcript ID ) couples the list of DSORFTranscriptAsso' +
                                     ' (DS) IDs and converting lists of IDs into list of objects.')
        
        # Get the dictionary that associates to each unique ( ORF ID (PRO), 
        # Transcript ID (PRO) ) couple that exists the list of the IDs of 
        # all the DSORFTranscriptAsso (DS) that are related to it 
        all_existing_orf_tr_asso_ids = FileHandlerUtil.get_obj_from_file( input_folder = Constants.MERGED_DATA_FOLDER,
                                                                          filename = Constants.ALL_EXISTING_ORF_TR_ASSO_IDS_FILENAME )
        
        # Convert the dictionary in order to change the list of IDs
        # by lists of corresponding DSORFTranscriptAsso objects
        all_dsota = SQLManagerDS.get_instance().get_session().query( DSORFTranscriptAsso ).all()
        SQLManagerDS.get_instance().close_session()
        
        all_dsota_dict = {}
        for dsota in all_dsota:
            all_dsota_dict[ dsota.id ] = dsota
        
        existing_orf_tr_asso_all = {}
        for ( ( orf_id, tr_id ), dsota_ids_list ) in all_existing_orf_tr_asso_ids.items():
            existing_orf_tr_asso_all[ ( orf_id, tr_id ) ] = map( lambda x: all_dsota_dict.get( x ), dsota_ids_list )
        
        # If the merging of DSORFTranscriptAsso entries has already 
        # been started once and failed, then remove from the list 
        # all the (ORF ID, Transcript ID) couples already processed 
        if ( self.resume_at_stage == ResumeMergeStrategy.RESUME_DURING_OTA ):
            all_processed_ota = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).all()
            SQLManagerPRO.get_instance().close_session()
            
            all_processed_ids = [ ( ota.orf_id, ota.transcript_id ) for ota in all_processed_ota ]
            
            existing_orf_tr_asso_all_to_process = { key : val \
                                                    for ( key, val ) in existing_orf_tr_asso_all.items() \
                                                    if ( ( int( key[0] ), int( key[1] ) ) not in all_processed_ids ) }
            
            existing_orf_tr_asso_all = existing_orf_tr_asso_all_to_process
            
            Logger.get_instance().debug( 'ResumeMergeStrategy.import_dsorftranscriptasso_to_merge(): ' +
                                         str( len( all_processed_ota ) ) + ' couples have already been' +
                                         ' processed and ' + str( len( existing_orf_tr_asso_all.keys() ) ) + 
                                         ' remains to be processed.' )
        
        # Store the dictionary in the DataManager main dictionary
        DataManager.get_instance().store_data( Constants.DM_ALL_EXISTING_ORF_TR_ASSO_DICT, existing_orf_tr_asso_all )
        