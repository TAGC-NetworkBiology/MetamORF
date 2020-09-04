# -*- coding: utf-8 -*-

import ConfigParser
import os
import pandas as pd

from sqlalchemy import or_

import subprocess

from multiprocessing import cpu_count
from pathos.multiprocessing import ProcessingPool as Pool
        

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## ComputeRelCoordStrategy
#  =======================
#
# This class is a strategy aiming to compute the ORF (and CDS) 
# relative coordinates from their absolute coordinates and the 
# available information relative to their transcripts.
#
class ComputeRelCoordStrategy( object ):
                
    ## Class variables
    #  ---------------
    
    # Path to the Rscript allowing the preparation 
    # of the annotation package necessary to the 
    # coordinates conversion
    R_SCRIPT_BUILD_ANNOT_PACKAGE_PATH = os.path.join( os.environ['PYTHONPATH'], 
                                                      'fr', 'tagc', 'uorf', 'core', 
                                                      'execution', 'relative_coord', 
                                                      'BuildEnsemblAnnotPackage.R' )
    
    # Path to the Rscript allowing the conversion
    # of absolute coordinates into relative ones
    R_SCRIPT_CONVERT_COORD_PATH = os.path.join( os.environ['PYTHONPATH'], 
                                                'fr', 'tagc', 'uorf', 'core', 
                                                'execution', 'relative_coord', 
                                                'ConvertAbsoluteCoord.R' )
        
    # Folder in which the temporary csv files generated 
    # have to be stored
    RELATIVE_COORD_CSV_FOLDER = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER, 
                                              'relative_coord_csv_files' )
    
    # Prefix to use for the CSV files
    OTA_CSV_FILE_PREFIX = 'ota_'
    TRANSCRIPT_CSV_FILE_PREFIX = 'transcript_'
        
    
    
    ## Constructor of ComputeRelCoordStrategy
    #  --------------------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - force_overwrite: Boolean - Does the computation needs to be performed again?
    #                                  If True:
    #                                      - The relative coordinates of the ORFs (ORFTranscriptAsso 
    #                                        table entries) will be computed again.
    #                                      - The relative coordinates of the CDSs (Transcript table
    #                                        entries) will be computed again.
    #     - species: String - The "short" name of the species (e.g. 'Hsapiens').
    #     - ensembl_release_version: String - The Ensembl release version used in the database (e.g. 90).
    #     - thread_nb: Integer (>0) - The number of threads that can be use.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    # @throw DenCellORFException: If the number of threads provided is not an integer.
    # @throw DenCellORFException: If the number of threads provided is not a positive integer.
    #
    def __init__( self ):
        
        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none = True )
            
        if configfile:
            self.configfile = configfile
            if ( not os.path.exists( configfile ) ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' See the documentation for more information.' )

        # Check if the forceOverwrite option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
            self.force_overwrite = True
        else:
            self.force_overwrite = False
        
        self.species = None
        self.ensembl_release_version = None
        
        
        # Get the number of threads available
        self.thread_nb = OptionManager.get_instance().get_option( OptionConstants.OPTION_THREAD_NB, 
                                                                  not_none = False )
        available_thread_nb = cpu_count()
        if self.thread_nb:
            try:
                self.thread_nb = int( self.thread_nb )
            except:
                raise DenCellORFException( 'ComputeRelCoordStrategy: The value provided for the number'
                                           ' of threads needs to be an integer (provided value: ' + 
                                           str( self.thread_nb ) + ').' )
            else:
                if ( self.thread_nb < 1 ):
                    raise DenCellORFException( 'ComputeRelCoordStrategy: The value provided for the number' +
                                               ' of threads needs to be an integer greater than 1 (provided value: ' + 
                                               str( self.thread_nb ) + ').' )
                    
                if ( self.thread_nb > available_thread_nb ):
                    Logger.get_instance().info( 'The number of threads provided (' + str( self.thread_nb ) +
                                                ') is greater than the number of threads actually' +
                                                ' available(' +  str( available_thread_nb ) +
                                                '). Hence, ' + str( available_thread_nb ) +
                                                ' threads will be used for the computation.' )
        else:
            self.thread_nb = available_thread_nb
            
        Logger.get_instance().debug( 'ComputeRelCoordStrategy: ' + str( self.thread_nb ) + ' threads' +
                                     ' will be used for the computation of relative coordinates.' )
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete missing information.
    #
    # @throw DenCellORFException: When an exception has been raised whilst checking the PRO database.
    # @throw DenCellORFException: When the ORFTranscriptAsso table is empty.
    # 
    def execute( self ):
        
        Logger.get_instance().info( 'IMPORTANT: This strategy has been built in order to be able to' +
                                    ' convert exclusively coordinates related to a Transcript entry that' +
                                    ' has an Ensembl transcript ID as "transcript_id" attribute.' +
                                    ' Hence, if the database contains IDs related to another database,' +
                                    ' then the source code of this strategy has to be modified in order to' +
                                    ' convert these IDs into Ensembl IDs.' )
        
        # Run DatabaseCheck in order to check PRO database is reachable and use
        # the appropriate models prior to the merging of data.
        Logger.get_instance().info( 'Checking the PRO database prior to compute missing information...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( ' An error occurred whilst checking the database prior to' +
                                       ' compute missing information.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        # Get the name of the species used in the database
        self.species = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        
        # Get the Ensembl release version used in the database
        prometadata_ensembl_release = SQLManagerPRO.get_instance().get_session().query( 
                                                                                            PROMetadata 
                                                                                        ).filter( 
                                                                                                    PROMetadata.parameter == Constants.METATABLE_CURRENT_ENSEMBL_RELEASE 
                                                                                                ).one()
        self.ensembl_release_version = prometadata_ensembl_release.value
        
        
        # Check there is at least one ORFTranscriptAsso entry in the database prior 
        # to try to convert the absolute coordinates into relative coordinates.
        # NB: The presence of entries in the Transcript tables will obviously be
        #     implicitly checked at the same time.
        orftranscriptasso_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
        if ( orftranscriptasso_count == 0 ):
            raise DenCellORFException( 'There is not any entry in the ORFTranscriptAsso table of the ' + 
                                       SQLManagerPRO.get_instance().db_name + ' database (PRO database).' +
                                       ' Hence, the conversion of absolute coordinates into relative' +
                                       ' coordinates will be stopped.' )
        SQLManagerPRO.get_instance().close_session()
        
        
        # Set the R_LIBS_USER environment package to install new R 
        # packages in a folder where the user has the writing right
        if ( not os.path.exists( Constants.CUSTOM_R_LIBRARY_FOLDER ) ):
            os.makedirs( Constants.CUSTOM_R_LIBRARY_FOLDER )
        os.environ['R_LIBS_USER'] = Constants.CUSTOM_R_LIBRARY_FOLDER
        
        
        # As the computation of relative coordinates is performed
        # using R scripts relying on the ensembldb packages and
        # annotation packages, first make sure the appropriate 
        # annotation package is available. If not build it.
        Logger.get_instance().debug( 'ComputeRelCoordStrategy.execute(): Preparing the R annotation' +
                                     ' package to perform the computation of relative coordinates' +
                                     ' (ensembl release: ' + str( self.ensembl_release_version ) + ')...' )
        self.prepare_r_annotation_package( species_short_name = self.species,
                                           species_full_name = Constants.SPECIES_CATALOG_FULL_NAMES_WITH_CAPS[ self.species ],
                                           species_common_name = Constants.SPECIES_CATALOG_COMMON_NAMES[ self.species ], 
                                           ensembl_release_version = self.ensembl_release_version )  
        
        # Create a new folder that will be used to create temporary 
        # csv files necessary to the computation of relative coordinates  
        if ( not os.path.exists( ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER ) ):
            os.makedirs( ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER )
        
        
        # ================================================================================
        # INFORMATION ABOUT THE MULTI-PROCESSING
        #
        # In order to lower as most as possible the computation time, the computation 
        # of relative coordinates is multi-processed (concurrent R scripts subprocesses
        # run in parallel).
        # 
        # Important information regarding the multi-processing:
        # - Multi-processing has been chosen instead of multi-threading, in particular 
        #   to side-step the GIL (Global Interpreter Lock).
        # - The processes use all available / provided CPUs to run.
        # - The pathos package has been chosen as it allows to serialize functions which 
        #   are not top-levels, such as class static methods (contrary to the 
        #   multiprocessing built-in package for instance).
        # - The processes are run in pools which is one of the most convenient mean to 
        #   parallelize the execution of a function across multiple inputs. The Pool 
        #   map() method is used to do so.
        # - As access of objects shared by the several processes (using locks and 
        #   semaphores for instance), could slower a lot the speed of execution when the
        #   process regularly need to access these variables, it has been decided to do
        #   not access to shared resources. Then the progression bar is not displayed on 
        #   screen for this step.
        # - In order to use efficiently the Pool map() method, the arguments needed by the
        #   forked function are embedded into tuples of fixed-size.
        #
        # ================================================================================
        
        # Compute the the start and stop relative coordinates 
        # in the ORFTranscriptAsso table
        self.compute_ota_relative_coordinates()
        
        
        # Compute the the start and stop CDS relative coordinates 
        # in the Transcript table
        self.compute_tr_cds_relative_coordinates()
                
    
    
    # ===============================================================================
    # Methods to compute the relative coordinates in the Transcript
    # and ORFTranscriptAsso tables
    # =============================================================================== 
    
    # As the tool used to perform the conversion is provided as a R package,
    # and as the integration of R code in Python could lower the computational
    # efficiency, the necessary data are exported in temporary csv files
    # and open in R which in turn build other temporary csv files which are
    # then opened by Python.
    
    ## compute_ota_relative_coordinates
    #  --------------------------------
    #
    # This method allows to compute the relative positions of the ORF
    # on the transcript (i.e. the ORFTranscriptAsso rel_start_pos and
    # rel_start_pos attributes) using information from the related ORF 
    # and Transcript entries.
    # NB: This function run a R script as subprocess.
    #
    def compute_ota_relative_coordinates( self ):
        
        Logger.get_instance().info( 'Starting the computation of relative ORF start and stop coordinates' +
                                    ' (registered in the ORFTranscriptAsso table).')
        
        # Get information related to the ORF
        # Query the database in order to get, for each unique entry of the ORFTranscriptAsso table:
        # - Its unique ID in the database
        # - The ID of its ORF-related entry, as well as the chromosome, 
        #   start and stop positions of the ORF
        # NB: Query is performed using raw SQL statement for better efficiency
        orf_info_sql_statement = 'SELECT ORFTranscriptAsso.id, ORFTranscriptAsso.orf_id,\
                                         ORF.chromosome, ORF.start_pos, ORF.stop_pos AS end_pos \
                                  FROM ORF \
                                  INNER JOIN ORFTranscriptAsso ON ORFTranscriptAsso.orf_id = ORF.id'
        if ( not self.force_overwrite ):
            orf_info_sql_statement += ' WHERE ( ORFTranscriptAsso.rel_start_pos IS NULL ) \
                                              OR ( ORFTranscriptAsso.rel_stop_pos IS NULL)'
        orf_info_df = pd.read_sql( orf_info_sql_statement, SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        
        # Get information related to the transcript
        # Query the database in order to get, for each unique entry of the ORFTranscriptAsso table:
        # - Its unique ID in the database
        # - The ID of its Transcript-related entry
        # NB: All "UNKNOWN_TRANSCRIPT" entries are excluded as an official ID is needed to perform
        #     the conversion.
        # NB: Query is performed using raw SQL statement for better efficiency
        transcript_info_sql_statement = "SELECT ORFTranscriptAsso.id, ORFTranscriptAsso.transcript_id, \
                                                Transcript.transcript_id AS tr_id \
                                         FROM Transcript \
                                         INNER JOIN ORFTranscriptAsso ON ORFTranscriptAsso.transcript_id = Transcript.id \
                                         WHERE Transcript.transcript_id != '" + Constants.UNKNOWN_TRANSCRIPT + "'"        
        transcript_info_df = pd.read_sql( transcript_info_sql_statement, SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        
        # Merge information from the two data frames in order to get
        # a data frame with the following columns:
        # - id: The ORFTranscriptAsso unique ID
        # - orf_id: The ORF unique ID
        # - chromosome: The ORF chromosome name
        # - start_pos: The ORF start position
        # - end_pos: The ORF stop position
        # - transcript_id: The Transcript unique ID
        # - tr_id: The transcript official ID (e.g. Ensembl ID)
        ota_info_df = orf_info_df.merge( transcript_info_df, 
                                         on='id', 
                                         how = 'inner', 
                                         validate = 'one_to_one' )
        Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_ota_relative_coordinates(): ' +
                                     str( ota_info_df.shape[0] ) + ' ORFTranscriptAsso entries are' +
                                     ' expected to be processed.')
        
        # As the conversion of coordinates in R may be highly time-consuming,
        # split the data frame into small data frames and multi-process the 
        # computation
        # Split the data frame into smaller data frames that can be processed 
        # independently from each other
        subset_data_frames = [ ota_info_df[ min_bound : min_bound + Constants.MAX_ENTRIES_PER_DATAFRAME ] \
                               for min_bound in xrange( 0, 
                                                        ota_info_df.shape[ 0 ], 
                                                        Constants.MAX_ENTRIES_PER_DATAFRAME ) ]
        
        # For each of the subset data frame, process it with R in order
        # to build a dataset containing the start and stop relative
        # coordinates.
        # Instantiate the list of tuple-embedded arguments necessary to
        # compute the relative coordinates
        args_to_run_r = []
        filename_prefix = self.OTA_CSV_FILE_PREFIX
        filename_suffix = 0
        for df in subset_data_frames:
            args_to_run_r.append( ( df,
                                    self.species, 
                                    self.ensembl_release_version, 
                                    filename_prefix,
                                    filename_suffix ) )
            filename_suffix += 1
                
        # Instantiate the pool of processes
        p = Pool( self.thread_nb )
        messages_to_log = p.map( self.compute_relative_coord_r, args_to_run_r )
        p.close()
        # Wait for all processes to be completed
        p.join()
        
        # Log the messages generated by the processes
        for messages in messages_to_log:
            
            ( debug_messages_to_log,
              stdout,
              stderr ) = messages
              
            for message in debug_messages_to_log:
                Logger.get_instance().debug( message )
            
            if ( stdout != '' ):
                Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_relative_coord_r():' +
                                             ' The R script returned the following standard output: \n' + 
                                             stdout )
            
            # NB: As the R function is susceptible to write not error-related 
            #     messages in stderr, these messages are also logged at the 
            #     debug level
            if ( stderr != '' ):
                Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_relative_coord_r():' +
                                             ' The R script returned the following error output: \n' + 
                                             stderr )
        
        # Sequentially open CSV files to get the relative positions
        # Instantiate a dictionary that associate to the ORFTranscriptAsso ID
        # the relative start and stop positions of the ORF
        rel_positions_dict = {}
        for file_nb in range( filename_suffix ):
            
            df = pd.read_csv( os.path.join( ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER,
                                            filename_prefix + str( file_nb ) + '.csv' ),
                              sep = ',',
                              encoding = 'utf-8' )
            
            for ( index, row ) in df.iterrows():
                rel_positions_dict[ row[ 'id' ] ] = ( row[ 'rel_start_pos' ], row[ 'rel_end_pos' ] )
        
        
        # Add the relative start and stop positions for all the ORFTranscriptAsso entries 
        all_ota = SQLManagerPRO.get_instance().get_session().query( 
                                                                        ORFTranscriptAsso 
                                                                    ).filter( 
                                                                                ORFTranscriptAsso.id.in_( rel_positions_dict.keys() ) 
                                                                            ).all()
        for ota in all_ota:
            
            # Get the start and stop positions
            positions = rel_positions_dict.get( ota.id )
            rel_start_pos = positions[ 0 ] 
            rel_stop_pos = positions[ 1 ] 
            
            if not pd.isna( rel_start_pos ):
                ota.rel_start_pos = int( rel_start_pos )
            
            if not pd.isna( rel_stop_pos ):
                ota.rel_stop_pos = int( rel_stop_pos )
        
        # Commit the updates and close the session
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        
        # Delete the pool instance
        p.clear()
    
    
    
    ## compute_tr_cds_relative_coordinates
    #  -----------------------------------
    #
    # This method allows to compute the relative positions of the CDS
    # of all transcripts.
    # NB: This function run a R script as subprocess.
    #
    def compute_tr_cds_relative_coordinates( self ):
        
        Logger.get_instance().info( 'Starting the computation of relative CDS transcript start and stop' +
                                    ' coordinates (registered in the Transcript table).')
        
        # Get all the transcript for which there are CDS 
        # start and stop positions provided 
        # NB: Query is performed using raw SQL statement for better efficiency
        transcript_info_sql_statement = 'SELECT Transcript.id, Transcript.transcript_id AS tr_id, \
                                                Transcript.gene_id, PROGene.chromosome, \
                                                Transcript.cds_start_pos AS start_pos, \
                                                Transcript.cds_stop_pos AS end_pos \
                                         FROM Transcript \
                                         INNER JOIN PROGene ON PROGene.gene_id = Transcript.gene_id \
                                         WHERE ( Transcript.cds_start_pos IS NOT NULL ) \
                                               AND ( Transcript.cds_stop_pos IS NOT NULL )'
        if ( not self.force_overwrite ):
            transcript_info_sql_statement += ' AND ( ( Transcript.rel_cds_start_pos IS NULL ) \
                                                     OR ( Transcript.rel_cds_stop_pos IS NULL ) )'
                                                
        transcript_info_df = pd.read_sql( transcript_info_sql_statement, SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_tr_cds_relative_coordinates(): ' +
                                     str( transcript_info_df.shape[0] ) + ' Transcript entries are' +
                                     ' expected to be processed.')
                
        # As the conversion of coordinates in R may be highly time-consuming,
        # split the data frame into small data frames and multi-process the 
        # computation
        # Split the data frame into smaller data frames that can be processed
        # independently from each other  
        subset_data_frames = [ transcript_info_df[ min_bound : min_bound + Constants.MAX_ENTRIES_PER_DATAFRAME ] \
                               for min_bound in xrange( 0,
                                                        transcript_info_df.shape[ 0 ],
                                                        Constants.MAX_ENTRIES_PER_DATAFRAME ) ]
        
        
        # For each of the subset data frame, process it with R in order
        # to build a dataset containing the start and stop relative
        # coordinates.
        # Instantiate the list of tuple-embedded arguments necessary to
        # compute the relative coordinates
        args_to_run_r = []
        filename_prefix = self.TRANSCRIPT_CSV_FILE_PREFIX
        filename_suffix = 0
        for df in subset_data_frames:
            args_to_run_r.append( ( df,
                                    self.species, 
                                    self.ensembl_release_version, 
                                    filename_prefix,
                                    filename_suffix ) )
            filename_suffix += 1
            
        # Instantiate the pool of processes
        p = Pool( self.thread_nb )
        messages_to_log = p.map( self.compute_relative_coord_r, args_to_run_r )
        p.close()
        # Wait for all processes to be completed
        p.join()
        
        # Log the messages generated by the processes
        for messages in messages_to_log:
            
            ( debug_messages_to_log,
              stdout,
              stderr ) = messages
              
            for message in debug_messages_to_log:
                Logger.get_instance().debug( message )
            
            if ( stdout != '' ):
                Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_relative_coord_r():' +
                                             ' The R script returned the following standard output: \n' + 
                                             stdout )
            
            # NB: As the R function is susceptible to write not error-related 
            #     messages in stderr, these messages are also logged at the 
            #     debug level
            if ( stderr != '' ):
                Logger.get_instance().debug( 'ComputeRelCoordStrategy.compute_relative_coord_r():' +
                                             ' The R script returned the following error output: \n' + 
                                             stderr )
        
        # Sequentially open CSV files to get the relative positions
        # Instantiate a dictionary that associate to the ORFTranscriptAsso ID
        # the relative start and stop positions of the ORF
        rel_positions_dict = {}
        for file_nb in range( filename_suffix ):
            
            df = pd.read_csv( os.path.join( ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER,
                                            filename_prefix + str( file_nb ) + '.csv' ),
                              sep = ',',
                              encoding = 'utf-8' )
            
            for ( index, row ) in df.iterrows():
                rel_positions_dict[ row[ 'id' ] ] = ( row[ 'rel_start_pos' ], row[ 'rel_end_pos' ] )
        
        
        # Add the relative start and stop positions for all the ORFTranscriptAsso entries 
        all_transcripts = SQLManagerPRO.get_instance().get_session().query( 
                                                                                Transcript 
                                                                            ).filter( 
                                                                                        Transcript.id.in_( rel_positions_dict.keys() ) 
                                                                                    ).all()
                                                                                    
        for transcript in all_transcripts:
            
            # Get the start and stop positions
            positions = rel_positions_dict.get( transcript.id )
            rel_cds_start_pos = positions[ 0 ] 
            rel_cds_stop_pos = positions[ 1 ] 
            
            if not pd.isna( rel_cds_start_pos ):
                transcript.rel_cds_start_pos = int( rel_cds_start_pos )
            
            if not pd.isna( rel_cds_stop_pos ):
                transcript.rel_cds_stop_pos = int( rel_cds_stop_pos )
        
        # Commit the updates and close the session
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        
        # Delete the pool instance
        p.clear()
    
    
    # ===============================================================================
    # Methods to compute the relative coordinates with R
    # ===============================================================================
    
    ## prepare_r_annotation_package
    #  ----------------------------
    #
    # This is a static method that allows to run a R script that takes 
    # as input a CSV file and convert the coordinates registered in the 
    # 'start_pos' and 'stop_pos' columns and convert the using information
    # provided by the 'chromosome' and 'tr_id' columns.
    #
    # @param species_short_name: String - The scientific short name of the species 
    #                                    (e.g. 'Hsapiens').
    # @param species_full_name: String - The scientific full name of the species 
    #                                    (e.g. 'Homo sapiens').
    # @param species_common_name: String - The common name of the species (e.g. 'human').
    # @param ensembl_release_version: Integer - The version of the ensembl release.
    #
    @staticmethod
    def prepare_r_annotation_package( species_short_name, species_full_name, species_common_name, \
                                      ensembl_release_version ):
        
        # Define temporary folder where to install the packages
        annot_package_dir = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER, 
                                          'R_ensembl_annot_packages',
                                          species_common_name + str( ensembl_release_version ) )
        if ( not os.path.exists( annot_package_dir ) ):
            os.makedirs( annot_package_dir )            
        
        # Run the R script (as a Python subprocess) 
        # to prepare the packages
        r_args = [ '--ensemblRelease=' + str( ensembl_release_version ),
                   '--speciesFullName=' + species_full_name,
                   '--speciesShortName=' + species_short_name,
                   '--speciesCommonName=' + species_common_name,
                   '--annotPackageDir=' + annot_package_dir ]
        r_command = [ 'Rscript', ComputeRelCoordStrategy.R_SCRIPT_BUILD_ANNOT_PACKAGE_PATH ] + r_args
        Logger.get_instance().debug( 'ComputeRelCoordStrategy.prepare_r_annotation_package(): The R script' +
                                     ' will be run with the following arguments ' + ' '.join( r_args ) )
        
        r_process = subprocess.Popen( r_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
        
        ( stdout, stderr ) = r_process.communicate()
        if ( stdout != '' ):
            Logger.get_instance().debug( 'ComputeRelCoordStrategy.prepare_r_annotation_package():' +
                                         ' The R script returned the following standard output: \n' + 
                                         stdout )
        if ( stderr != '' ):
            Logger.get_instance().debug( 'ComputeRelCoordStrategy.prepare_r_annotation_package():' +
                                         ' The R script returned the following error output: \n' + 
                                         stderr )
            
    
    ## compute_relative_coord_r
    #  ------------------------
    #
    # This is a static method that allows to run a R script that takes 
    # as input a CSV file and convert the coordinates registered in the 
    # 'start_pos' and 'stop_pos' columns and convert the using information
    # provided by the 'chromosome' and 'tr_id' columns.
    #
    # @param args_to_run_r: 5-tuple - A 5-elements tuple that contains the following information:
    #                                   - df: Pandas data frame - The data frame to use.
    #                                   - species: String - The name of the species. The species has to be 
    #                                                       provided at the short scientific name format
    #                                                       (e.g. 'Hsapiens').
    #                                   - ensembl_release_version: Integer - The version of the ensembl release.
    #                                   - filename_prefix: String - The prefix to use for the csv file.
    #                                   - filename_suffix: String - The suffix to use for the csv file.
    #
    # @return 3-tuple - A 3-elements tuple that contains the following information:
    #                     - debug_messages_to_log: List - The debug message to log.
    #                     - stdout: String - The stdout of the R subprocess.
    #                     - stderr: String - The stderr of the R subprocess.
    #
    @staticmethod
    def compute_relative_coord_r( args_to_run_r ):
        
        # Parse the arguments
        ( df,
          species,
          ensembl_release_version,
          filename_prefix,
          filename_suffix ) = args_to_run_r
          
        debug_messages_to_log = []   
        
        filename = filename_prefix + str( filename_suffix )
        filepath = os.path.join( ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER, filename + '.csv' )
        
        # Write the content of the data frame in a csv file
        FileHandlerUtil.pandas_df_to_csv( output_folder = ComputeRelCoordStrategy.RELATIVE_COORD_CSV_FOLDER,
                                          filename = filename,
                                          df = df,
                                          file_desc = ( str( df.shape[ 0 ] ) +
                                                        ' entries registered in the data frame' +
                                                        ' to be processed for coordinates conversion' ),
                                          hdr = True )
         
        # Run the R script (as a Python subprocess) to compute 
        # the relative coordinates
        r_args = [ '--ensembl=' + str( ensembl_release_version ),
                   '--species=' + species,
                   '--csvFile=' + filepath ]
        r_command = [ 'Rscript', ComputeRelCoordStrategy.R_SCRIPT_CONVERT_COORD_PATH ] + r_args
        debug_messages_to_log.append( 'ComputeRelCoordStrategy.compute_relative_coord_r(): The R script' +
                                      ' will be run with the following arguments ' + ' '.join( r_args ) )
    
        r_process = subprocess.Popen( r_command, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
    
        ( stdout, stderr ) = r_process.communicate()
        
        return ( debug_messages_to_log, stdout, stderr )            
        