# -*- coding: utf-8 -*-

import os

from fr.tagc.uorf.core.model.PRO import *

from fr.tagc.uorf.core.execution.GenerateBEDFileStrategy import GenerateBEDFileStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# ===============================================================================
# Track hub documentation
# ===============================================================================

# References:
# - https://genome.ucsc.edu/goldenPath/help/hubQuickStart.html
# - http://genome.ucsc.edu/goldenPath/help/trackDb/trackDbHub.html
# - http://genome-euro.ucsc.edu/cgi-bin/hgHubConnect
#
# This strategy aim to generate the trackDb file ONLY.
# The other files need to be prepared manually (refer to UCSC documentation).
#
# We advice to use a tree similar to the following one:
#
# html
# └── tackHub
#     └── hubDirectory
#         ├── hub.txt                // General settings and inform where to find the genome assemblies
#         │                             Example at http://genome.ucsc.edu/goldenPath/help/examples/hubDirectory/hub.txt
#         ├── genomes.txt            // Provide information about genome assemblies to use
#         │                             Example at http://genome.ucsc.edu/goldenPath/help/examples/hubDirectory/genomes.txt
#         ├── MetamorfHub.html       // Descriptive page of the tracks
#         └── hg38                   // For H. sapiens hg38 for instance
#             ├── Example.bb         // BigBed file (generated using the GenerateBEDFile strategy, with the "-e" option)
#             └── trackDb.text       // The file generated by the current strategy
#
# For more information about Bed file format, please see the 
# documentation of the GenerateBEDFileStrategy. 
# The BigBed file is expected to be at the 12 + 5 format.




# ===============================================================================
# Strategy
# ===============================================================================
        

## GenerateTrackDbFileStrategy
#  ===========================
#
# This class is a strategy aiming to generate the trackDb 
# file necessary to implement a track hub on the website.
# NB: 
#
class GenerateTrackDbFileStrategy( object ):
    
    ## Class variables
    #  ---------------
    # File extension
    TRACK_DB_FILE_EXTENSION = '.txt'
    
    # Path to HTML description file (without '.html')
    TRACK_HTML_DESC_PATH = '../MetamorfHub'
    
    # Website URL (with 'http://' prefix)
    WEBSITE_URL = Constants.WEBSITE_URL
    
    # BigBed filename (without '.bb')
    BIGBED_FILENAME = Constants.DEFAULT_BED_FILENAME
    
    # Species name to use in the URL
    # TODO TO UPDATE
    WEBSITE_URL_SPECIES = { Constants.HSAPIENS: 'hsapiens',
                            Constants.MMUSCULUS: 'mmusculus' }
    

    ## Constructor of GenerateTrackDbFileStrategy
    #  ------------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - output_folder: String - The name of the folder where to export the track file.
    #     - filename: String - The name of the track file.
    #
    def __init__( self ):
        
        # Get the options necessary to establish the connection to the database
        self.db_settings = {}
        self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_TYPE )
        self.db_settings[ Constants.DB_SETTINGS_DB_NAME ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_NAME, 
                                                                                                     not_none = True )
        
        if ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_MYSQL ):
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_USER )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PASSWD )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_HOST_IP )
            self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_MYSQL_PORT )
            
        elif ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] == SQLConstants.DB_TYPE_SQLITE ):
            self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] = OptionManager.get_instance().get_option( OptionConstants.OPTION_DB_FOLDER )
        
        # Get the output folder
        self.output_folder = OptionManager.get_instance().get_option( OptionConstants.OPTION_OUTPUT_FOLDER, 
                                                                      not_none = False )
        # By default, save the file in a track folder
        if ( not self.output_folder ):
            self.output_folder = Constants.TRACK_FOLDER
        
        # Get the eventual filename
        self.filename = OptionManager.get_instance().get_option( OptionConstants.OPTION_TRACK_FILENAME, 
                                                                 not_none = False )
        # By default, name the file 'trackDb'
        if ( not self.filename ):
            self.filename = Constants.DEFAULT_TRACK_FILENAME
            
        # Should a bigBed file be generated at the same time?
        self.generate_bigbed = OptionManager.get_instance().get_option( OptionConstants.OPTION_TRACK_GENERATE_BB,
                                                                        not_none = False )
        
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the trackDb file.
    #
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    # 
    def execute( self ):
        
        # Create a session to the "PRO-like" database
        SQLManagerPRO.get_instance().set_db_settings( self.db_settings )

        try:
            SQLManagerPRO.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'GenerateTrackDbFileStrategy.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        SQLManagerPRO.get_instance().close_session()
        
        
        Logger.get_instance().info( 'Starting to build the track file.' )
        
        
        # Track header and settings
        # -------------------------        
        # Define track labels
        sp = SQLManagerPRO.get_instance().get_session().query( PROSpeciesCatalog.name ).one()[0]
        current_annotation = SQLManagerPRO.get_instance().get_session().query( 
                                                                                PROMetadata.value 
                                                                              ).filter( 
                                                                                            PROMetadata.parameter == Constants.METATABLE_CURRENT_ANNOTATION 
                                                                                        ).one()[0]
        current_ucsc_annot = Constants.CORRESPONDING_UCSC_FROM_NCBI[ current_annotation ]
        SQLManagerPRO.get_instance().close_session()
        
        track_track = '{project_name}_{species}_{annotation}'.format( project_name = Constants.PROJECT_NAME,
                                                                      species = sp,
                                                                      annotation = current_ucsc_annot )
        track_track = 'track ' + track_track
                                                                                        
        track_shortLabel = '{project_name}_{species}_{annotation}'.format( project_name = Constants.PROJECT_NAME,
                                                                           species = sp,
                                                                           annotation = current_ucsc_annot )
        track_shortLabel = 'shortLabel ' + track_shortLabel
        
        track_longLabel = '{project_name} {species} track hub ({annotation}), See {db_url} for more information regarding this track'.format( project_name = Constants.PROJECT_NAME,
                                                                                                                                              species = sp,
                                                                                                                                              annotation = current_ucsc_annot,
                                                                                                                                              db_url = self.WEBSITE_URL )
        track_longLabel = 'longLabel ' + track_longLabel
        
        # Path to HTML descriptive file
        track_html = 'html ' + self.TRACK_HTML_DESC_PATH
        
        # Path to BigBed file
        track_bigDataUrl = ( 'bigDataUrl ' + GenerateTrackDbFileStrategy.BIGBED_FILENAME + 
                             GenerateBEDFileStrategy.BIGBED_FILE_EXTENSION )
        track_type = 'type bigBed 12 +'
        
        # Track visualization
        track_default_vis = ( 'visibility full\n' +
                              'thickDrawItem on\n' +
                              'itemRgb on\n' +
                              'maxItems 100000\n' +
                              'exonArrows on\n' +
                              'exonNumbers on' )
            
        
        # Track filters
        # -------------
        
        # Transcript IDs
        all_transcript_ids = SQLManagerPRO.get_instance().get_session().query( Transcript.transcript_id.distinct() ).all()
        all_transcript_ids = sorted( GeneralUtil.query_result_to_list( all_transcript_ids ) )
        SQLManagerPRO.get_instance().close_session()
        
        transcripts_filter_values = ',\\\n'.join( all_transcript_ids )        
        track_filter_transcripts = ( 'filterType.transcripts multipleListOr\n' +
                                     'filterText.transcripts *\n' +
                                     'filterLabel.transcripts Transcript IDs\n' +
                                     'filterValues.transcripts ' + transcripts_filter_values )
        
        # RNA biotypes
        all_rna_biotypes = SQLManagerPRO.get_instance().get_session().query( 
                                                                                Transcript.rna_biotype.distinct()
                                                                            ).filter(
                                                                                        Transcript.rna_biotype != None
                                                                                    ).all()
        all_rna_biotypes = sorted( GeneralUtil.query_result_to_list( all_rna_biotypes ) )
        SQLManagerPRO.get_instance().close_session()
        
        rnabiotypes_filter_values = ',\\\n'.join( all_rna_biotypes )        
        track_filter_rnabiotypes = ( 'filterType.rna_biotypes multipleListOr\n' +
                                     'filterText.rna_biotypes *\n' +
                                     'filterLabel.rna_biotypes RNA biotypes\n' +
                                     'filterValues.rna_biotypes ' + rnabiotypes_filter_values )
                                    
        # Cell contexts
        all_cell_contexts = SQLManagerPRO.get_instance().get_session().query( CellContextCatalog.context ).all()
        all_cell_contexts = sorted( GeneralUtil.query_result_to_list( all_cell_contexts ) )
        SQLManagerPRO.get_instance().close_session()
        
        celltypes_filter_values = ',\\\n'.join( all_cell_contexts )
        track_filter_celltypes = ( 'filterType.cell_types multipleListOr\n' +
                                   'filterText.cell_types *\n' +
                                   'filterLabel.cell_types Cell types (cell lines, tissues...)\n' +
                                   'filterValues.cell_types ' + celltypes_filter_values )
                                  
        # ORF Annotations
        all_orfannotations = SQLManagerPRO.get_instance().get_session().query( ORFAnnotationCatalog.annotation ).all()
        all_orfannotations = sorted( GeneralUtil.query_result_to_list( all_orfannotations ) )
        
        orfannotations_filter_values = ',\\\n'.join( all_orfannotations )
        track_filter_orfannotations = ( 'filterType.orf_annotations multipleListOr\n' +
                                        'filterText.orf_annotations *\n' +
                                        'filterLabel.orf_annotations ORF Annotations\n' +
                                        'filterValues.orf_annotations ' + orfannotations_filter_values )
                                       
        # Kozak contexts
        all_kozak_ctxt_comp = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    ORFTranscriptAsso.kozak_context_comp.distinct() 
                                                                                ).filter(
                                                                                            ORFTranscriptAsso.kozak_context_comp != None
                                                                                        ).all()
        all_kozak_ctxt_comp = sorted( GeneralUtil.query_result_to_list( all_kozak_ctxt_comp ) )
        
        kozakcontexts_filter_values = ',\\\n'.join( all_kozak_ctxt_comp )
        track_filter_kozakcontexts = ( 'filterType.kozak_contexts multipleListOr\n' +
                                       'filterText.kozak_contexts *\n' +
                                       'filterLabel.kozak_contexts Computed Kozak context\n' +
                                       'filterValues.kozak_contexts ' + kozakcontexts_filter_values )
                          
                                       
        # URLs
        # ----
        url_name = 'name="' + self.WEBSITE_URL + '/ORF/' + self.WEBSITE_URL_SPECIES[ sp ] + '/$$' + '"'
        url_transcript = 'transcripts="' + self.WEBSITE_URL + '/transcript/' + self.WEBSITE_URL_SPECIES[ sp ] + '/$$' + '"'
        track_urls = 'urls ' + '\\\n'.join( [ url_name, url_transcript ] )
                          
                                       
        # Additional lines
        # ----------------
        track_labelFields = 'labelFields name, transcripts, rna_biotypes, cell_types, orf_annotations, kozak_contexts'
        
                                       
        # Write the trackDb file
        # ----------------------
        track_content = [ track_track,
                          track_shortLabel,
                          track_longLabel,
                          track_html,
                          track_bigDataUrl,
                          track_type,
                          track_default_vis,
                          track_filter_transcripts,
                          track_filter_rnabiotypes,
                          track_filter_celltypes,
                          track_filter_kozakcontexts,
                          track_labelFields,
                          track_urls ]
        track_content = '\n'.join( track_content ) + '\n'       
        
        # Create the output folder if necessary
        if ( not os.path.isdir( self.output_folder ) ):
            os.makedirs( self.output_folder )
        
        track_db_file_path = os.path.join( self.output_folder, self.filename + self.TRACK_DB_FILE_EXTENSION )
        with open( track_db_file_path, 'w' ) as track_db_file:
            track_db_file.write( track_content )
            
        Logger.get_instance().info( 'The trackDb file has been successfully created and saved at ' +
                                    track_db_file_path + '.' )
            
            
        # Create BigBed file if necessary
        # -------------------------------
        
        if self.generate_bigbed:
            
            # Overwrite / define some options necessary 
            # to run the GenerateBEDFile strategy
            OptionManager.get_instance().set_option( option_name = OptionConstants.OPTION_CONVERT_TO_BIGBED,
                                                     option_value = True )
            # Output folder is the same than the one of the trackDb file
            OptionManager.get_instance().set_option( option_name = OptionConstants.OPTION_OUTPUT_FOLDER,
                                                     option_value = self.output_folder )
            # Defined BigBed filename
            OptionManager.get_instance().set_option( option_name = OptionConstants.OPTION_BED_FILENAME,
                                                     option_value = GenerateTrackDbFileStrategy.BIGBED_FILENAME )
            # Set bigbed format at 12 + 5
            OptionManager.get_instance().set_option( option_name = OptionConstants.OPTION_BED_EXTENDED,
                                                     option_value = True )
            
            try:
                generatebedfilestrategy = GenerateBEDFileStrategy()
            except Exception as e:
                raise DenCellORFException( 'GenerateTrackDbFileStrategy.execute(): An error occurred' +
                                           ' trying to instantiate a GenerateBEDFileStrategy.', e )
            
            try:
                generatebedfilestrategy.execute()
            except Exception as e:
                raise DenCellORFException( 'GenerateTrackDbFileStrategy.execute(): An error occurred' +
                                           ' during the execution of the GenerateBEDFile strategy.', e )
            