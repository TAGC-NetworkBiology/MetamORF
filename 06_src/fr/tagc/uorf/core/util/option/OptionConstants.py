# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql import SQLConstants


# ===============================================================================
# Name of the various options
# ===============================================================================

# Common options
OPTION_DB_TYPE = 'database_type'
OPTION_CONFIG_FILE_PATH = 'configfile_path'
OPTION_FORCE_OVERWRITE = 'force_overwrite'
OPTION_VERBOSITY = 'verbosity'
OPTION_THREAD_NB = 'thread_nb'

# Options allowing the connection to the database
OPTION_DB_NAME = 'database_name'
OPTION_DB_FOLDER = 'database_folder'
OPTION_DB_MYSQL_USER = 'database_user'
OPTION_DB_MYSQL_PASSWD = 'database_password'
OPTION_DB_MYSQL_HOST_IP = 'database_host_ip'
OPTION_DB_MYSQL_PORT = 'database_port'

# Options related to list of data sources
OPTION_SOURCE_NAME = 'source'

# Options related to the model used (e.g. DS, PRO)
OPTION_DATABASE_MODEL = 'database_model'

# Options related to Merge strategy
OPTION_CHECK_DSOTA_COHERENCE = 'check_dsota_coherence'
OPTION_COMPUTE_SQCE_CONSENSUS = 'compute_sqce_consensus'
OPTION_RESUME_STEP_NAME = 'resume_after_step_name'

# Options related to ComputeMissingInfo strategy
OPTION_DOWNLOAD_MISSING_INFO = 'download_missing_info'

# Options related to the AnnotateORF strategy
OPTION_ANNOTATE_ORF_FROM_PROV = 'annotate_orf_from_prov_cat'
OPTION_ANNOTATE_ORF_FROM_COORD = 'annotate_orf_from_coordinates'

# Options related to the AddReleaseVersion strategy
OPTION_DB_RELEASE_NB = 'database_release_version_name'
OPTION_DB_RELEASE_DESC = 'database_release_version_description'

# Options related to Backup strategy
OPTION_OUTPUT_FOLDER = 'output_folder'
OPTION_FILE_PREFIX = 'file_prefix'

# Options related to Restore strategy
OPTION_INPUT_FOLDER = 'input_folder'

# Options related to GenerateBEDFile strategy
OPTION_BED_FILENAME = 'bed_filename'
OPTION_BED_GENERATE_CONTENT = 'bed_generate_content'
OPTION_BED_TRACK_LINE = 'bed_track_line'
OPTION_BED_NON_CONV_CHR = 'bed_non_conv_chr'
OPTION_BED_EXTENDED = 'bed_extended_version'
OPTION_CONVERT_TO_BIGBED = 'convert_to_bigbed'

# Options related to GenerateTrackDbFile strategy
OPTION_TRACK_FILENAME = 'trackDb_filename'
OPTION_TRACK_GENERATE_BB = 'trackDb_generate_bigBed'

# Options related to GenerateGFFFile strategy
OPTION_GFF_FILENAME = 'gff_filename'

# Options related to GenerateFastaFile strategy
OPTION_FASTA_FILENAME = 'fasta_filename'
OPTION_FASTA_SEQ_TYPE = 'fasta_sequence_type'
OPTION_FASTA_QUERY_TABLE = 'fasta_query_table'
OPTION_FASTA_EXCLUDE_SQCES_WITH_STOP = 'fasta_exclude_sqces_with_stop'
OPTION_FASTA_LONG_HEADERS = 'fasta_long_headers'

# Options related to AssessDatabaseContent strategy
OPTION_ASSESS_FILENAME = 'assess_filename'


# ===============================================================================
# Definition of the options
# ===============================================================================

# For a given strategy, options have to be written as lists according to this model:
# [ '-ShortTag', '--LongTag', action, type, dest, default, help ]

# Define options shared by all / the majority of the strategies
  # Database type
OPTION_SUBLIST_DATABASE_TYPE =      [ '-T', '--databaseType', 'store', 'string', OPTION_DB_TYPE, None, 'The type of the database to use (' + ', '.join( SQLConstants.AUTORIZED_DB_TYPES ) + ').' ]
  # Verbosity
OPTION_SUBLIST_VERBOSITY =          [ '-v', '--verbosity', 'store', 'string', OPTION_VERBOSITY, Constants.LOG_MODE_INFO, 'The level of verbosity. This must be in the list: ' + ', '.join( Constants.LOG_MODES.keys() ) + '.' ]
  # Config file
OPTION_SUBLIST_CONFIGFILE =         [ '-c', '--configfile', 'store', 'string', OPTION_CONFIG_FILE_PATH, None, 'The path to the config file to use.' ]
  # Number of threads
OPTION_NUMBER_OF_THREADS =          [ '-t', '--threads', 'store', 'string', OPTION_THREAD_NB, None, 'The number of threads that can be used.' ]
  # Connection parameters
OPTION_SUBLIST_DATABASE_NAME =      [ '-N', '--databaseName', 'store', 'string', OPTION_DB_NAME, None, 'The name of the database to use.' ]
OPTION_SUBLIST_DATABASE_FOLDER =    [ '-F', '--databaseFolder', 'store', 'string', OPTION_DB_FOLDER, None, 'The folder of the database (for SQLite databases only).' ]
OPTION_SUBLIST_DATABASE_HOST =      [ '-H', '--databaseHost', 'store', 'string', OPTION_DB_MYSQL_HOST_IP, None, 'The IP of the database host (for MySQL databases only).']
OPTION_SUBLIST_DATABASE_PORT =      [ '-P', '--databasePort', 'store', 'string', OPTION_DB_MYSQL_PORT, None, 'The port to use to establish the connection to the database (for MySQL databases only, 3306 by default).' ]
OPTION_SUBLIST_DATABASE_USER =      [ '-u', '--databaseUser', 'store', 'string', OPTION_DB_MYSQL_USER, None, 'The username to use to connect to MySQL server (for MySQL databases only).' ]
OPTION_SUBLIST_DATABASE_PASSWD =    [ '-p', '--databasePassword', 'store', 'string', OPTION_DB_MYSQL_PASSWD, None, 'The password to use to connect to MySQL server (for MySQL databases only).' ]
  # Database model (PRO / DS)
OPTION_SUBLIST_DATABASE_MODEL =     [ '-M', '--databaseModel', 'store', 'string', OPTION_DATABASE_MODEL, None, 'The schema of database used (PRO / DS).' ]

# List of available options for each strategy
OPTION_LIST = {  'DatabaseCheck' : [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete any existing DS and PRO database(s) and build a new one prior to run the strategy.']
                ],
                'Insertion': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete any existing database and build a new one prior to run the strategy.']
                ],
                'Deletion': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    [ '-s', '--dataSource', 'store', 'string', OPTION_SOURCE_NAME, None, 'The name of the data source(s) to remove of the database (comma-separated list).']
                ],                
                'ForceInsertion': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    [ '-s', '--dataSource', 'store', 'string', OPTION_SOURCE_NAME, None, 'The name of the data source(s) to insert of the database using the temporary files (comma-separated list).']
                ],
                'LiftOver': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE
                ],
                'Merge': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    OPTION_NUMBER_OF_THREADS,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete any existing database and build a new one prior to run the strategy.'],
                    [ '-d', '--checkDSOTA', 'store_true', None, OPTION_CHECK_DSOTA_COHERENCE, False, 'Should the content of the DSORFTranscriptAsso table need to be check prior to run the strategy? Please note that selecting this option may be highly time-consuming.' ],
                    [ '-s', '--computeConsensus', 'store_true', None, OPTION_COMPUTE_SQCE_CONSENSUS, False, 'Should a consensus of the DSORFTranscriptAsso sequences be computed? Please note that selecting this option may be highly time-consuming.' ]
                ],
                'ResumeMerge': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    OPTION_NUMBER_OF_THREADS,
                    [ '-d', '--checkDSOTA', 'store_true', None, OPTION_CHECK_DSOTA_COHERENCE, False, 'Should the content of the DSORFTranscriptAsso table need to be check prior to run the strategy? Please note that selecting this option may be highly time-consuming.' ],
                    [ '-s', '--computeConsensus', 'store_true', None, OPTION_COMPUTE_SQCE_CONSENSUS, False, 'Should a consensus of the DSORFTranscriptAsso sequences be computed? Please note that selecting this option may be highly time-consuming.' ],
                    [ '-a', '--resumeAtStep', 'store', 'string', OPTION_RESUME_STEP_NAME, None, 'The name of the last step that has been completed successfully (after_conserved, after_orf, after_transcript, after_ota_id_asso, during_ota, after_ota). Please see the documentation for more information.' ]
                ],
                'ComputeMissingInfo': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete all the entries of the ORFCategory and ORFCategoryCatalog tables (PRO database) prior to run the strategy.'],
                    [ '-d', '--downloadMissingInfo', 'store_true', None, OPTION_DOWNLOAD_MISSING_INFO, False, 'Download the missing information (such as ORF and Transcript sequences) from Ensembl database. Please note that selecting this option may be highly time-consuming.' ]
                ],
                'ComputeRelCoord': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    OPTION_NUMBER_OF_THREADS,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Should any existing relative coordinates be re-computed?' ]
                ],
                'ComputeKozakContext': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Should any existing computed Kozak context be re-computed?' ]
                ],
                'AnnotateORF': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete all the entries of the ORFCategory and ORFCategoryCatalog and/or of the ORFAnnotation and ORFAnnotationCatalog tables (PRO database, depending on the other selected options) prior to run the strategy.'],
                    [ '-s', '--computeCatFromSource', 'store_true', None, OPTION_ANNOTATE_ORF_FROM_PROV, False, 'Compute the ORF categories from the categories provided by the datasource (ORFCatagory table)?' ],
                    [ '-a', '--computeAnnot', 'store_true', None, OPTION_ANNOTATE_ORF_FROM_COORD, False, 'Annotate ORFs using both datasource and transcript information (ORFAnnotation table)?' ]
                ],
                'AddReleaseVersion': [ 
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    OPTION_SUBLIST_DATABASE_MODEL,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'If a version has already been declared, replace it with the provided value.'],
                    [ '-r', '--releaseNumber', 'store', 'string', OPTION_DB_RELEASE_NB, None, 'The number of the version.' ],
                    [ '-d', '--releaseDescription', 'store', 'string', OPTION_DB_RELEASE_DESC, None, 'The description of the version.' ]
                ],
                'Backup': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    OPTION_SUBLIST_DATABASE_MODEL,
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which the files have to be saved.' ],
                    [ '-x', '--filePrefix', 'store', 'string', OPTION_FILE_PREFIX, None, 'The prefix for file names where data is saved.' ]
                ],
                'Restore': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    OPTION_SUBLIST_DATABASE_MODEL,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Does the program has to re-initialize the provided database prior the restoration? This will erase any existing data.'],
                    [ '-i', '--inputFolder', 'store', 'string', OPTION_INPUT_FOLDER, None, 'The absolute path to the folder in which the files are located.' ],
                    [ '-x', '--filePrefix', 'store', 'string', OPTION_FILE_PREFIX, None, 'The prefix used when generated the files with the Restore strategy.' ]
                ],
                'AssessDatabaseContent': [       
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,
                    OPTION_SUBLIST_DATABASE_MODEL,
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which all the files generated have to be saved.' ],
                    [ '-f', '--filename', 'store', 'string', OPTION_ASSESS_FILENAME, None, 'The name for the log file generated (DatabaseAssessment by default).' ]
                ],
                'GenerateBEDContent': [             
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD
                ],
                'GenerateBEDFile': [             
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,           
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which the BED file has to be saved.' ],
                    [ '-b', '--bedFilename', 'store', 'string', OPTION_BED_FILENAME, None, 'The name for the BED file generated (without ".bed").' ],
                    [ '-a', '--generateBEDTableContent', 'store_true', None, OPTION_BED_GENERATE_CONTENT, False, 'Should the content of the UTBEDContent table be removed and computed again?' ],
                    [ '-l', '--trackLine', 'store_true', None, OPTION_BED_TRACK_LINE, False, 'Should the track line be included at the beginning of the file?' ],
                    [ '-n', '--includeNonConventionalChr', 'store_true', None, OPTION_BED_NON_CONV_CHR, False, 'Should the ORFs located on "non conventional" chromosomes (e.g. mitochondrial, scaffold) be included in the file?' ],
                    [ '-e', '--extendBed', 'store_true', None, OPTION_BED_EXTENDED, False, 'Should the bed file be extended (12+ format)?' ],
                    [ '-g', '--bigBed', 'store_true', None, OPTION_CONVERT_TO_BIGBED, False, 'Should the BED file be converted at bigBed format?' ]
                ],
                'GenerateTrackDbFile': [             
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,           
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which the trackDb file has to be saved.' ],
                    [ '-f', '--trackFilename', 'store', 'string', OPTION_TRACK_FILENAME, None, 'The name for the trackDb file generated (without ".txt").' ],
                    [ '-g', '--bigBed', 'store_true', None, OPTION_TRACK_GENERATE_BB, None, 'Should the bigBed file be created a the same time? If selected, the bigBed file will be created in the same folder.' ]
                ],
                'GenerateGFFFile': [             
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD,           
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which the GFF file has to be saved.' ],
                    [ '-g', '--gffFilename', 'store', 'string', OPTION_GFF_FILENAME, None, 'The name for the GFF file generated (DenCellORF_ORF by default, without ".gff" or ".gff3").' ]
                ],
                'GenerateFastaFile': [             
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_DATABASE_NAME,
                    OPTION_SUBLIST_DATABASE_FOLDER,
                    OPTION_SUBLIST_DATABASE_HOST,
                    OPTION_SUBLIST_DATABASE_PORT,
                    OPTION_SUBLIST_DATABASE_USER,
                    OPTION_SUBLIST_DATABASE_PASSWD, 
                    [ '-s', '--seqType', 'store', 'string', OPTION_FASTA_SEQ_TYPE, None, 'The type of sequences to include in the FASTA file (' + Constants.SEQUENCE_TYPE_DNA + ' or ' + Constants.SEQUENCE_TYPE_PROT + ', ' + Constants.SEQUENCE_TYPE_PROT + ' by default).' ],
                    [ '-q', '--queryTable', 'store', 'string', OPTION_FASTA_QUERY_TABLE, None, 'The table to query to generate the FASTA file (ORF or OTA, ORF by default).' ],
                    [ '-e', '--excludeSqcesWithStop', 'store_true', None, OPTION_FASTA_EXCLUDE_SQCES_WITH_STOP, False, 'Should the sequences that contains stop codons (at any other place that their end) be excluded of the fasta file?' ],
                    [ '-l', '--longHeader', 'store_true', None, OPTION_FASTA_LONG_HEADERS, False, 'Use this option to get more informative fasta headers. By default, the headers only contain the ORF or OTA ID and the taxonomic code. \
                                                                                                   By selecting this option, additionnal information, such as start and stop positions of the ORF or database release will be added. Please see the documentation for more information.' ],
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which the GFF file has to be saved.' ],
                    [ '-a', '--fastaFilename', 'store', 'string', OPTION_FASTA_FILENAME, None, 'The name for the FASTA file generated (DenCellORF_ORF by default, without ".fa" or ".fasta").' ]
                ],
                'GenerateStatFiles': [        
                    OPTION_SUBLIST_VERBOSITY,
                    [ '-o', '--outputFolder', 'store', 'string', OPTION_OUTPUT_FOLDER, None, 'The absolute path to the folder in which all the files generated have to be saved.' ],
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Does the program has to overwrite the existing files? If not selected, all the files that have already been generated will not be generated again.']
                ],
                'Filter': [
                    OPTION_SUBLIST_DATABASE_TYPE,
                    OPTION_SUBLIST_VERBOSITY,
                    OPTION_SUBLIST_CONFIGFILE,
                    [ '-f', '--forceOverwrite', 'store_true', None, OPTION_FORCE_OVERWRITE, False, 'Delete any existing FILT database (PRO model) and build a new one prior to run the strategy.']
                ]
               }

# List of available strategies
STRATEGIES_LIST = OPTION_LIST.keys()


# ===============================================================================
# DatabaseCheck strategy
# ===============================================================================

# List of strategies calling the DatabaseCheck strategy 
# and for which the "-f" option is authorized
STRATEGIES_ALLOWING_FORCE_OVERWRITE = [ 'DatabaseCheck' ]
STRATEGIES_ALLOWING_FORCE_OVERWRITE_ON_DS_DB = STRATEGIES_ALLOWING_FORCE_OVERWRITE + [ 'Insertion' ]
STRATEGIES_ALLOWING_FORCE_OVERWRITE_ON_PRO_DB = STRATEGIES_ALLOWING_FORCE_OVERWRITE + [ 'Merge' ]
STRATEGIES_ALLOWING_FORCE_OVERWRITE_ON_FILT_DB = STRATEGIES_ALLOWING_FORCE_OVERWRITE + [ 'Filter' ]

# List of strategies that have to check the DS database
STRATEGIES_CHECKING_DS_DATABASE = [ 'DatabaseCheck', 'Insertion', 'LiftOver', 'Merge', 
                                    'ResumeMerge', 'Backup' ]

# List of strategies that have to check the PRO database
STRATEGIES_CHECKING_PRO_DATABASE = [ 'DatabaseCheck', 'Merge', 'ResumeMerge', 'ComputeMissingInfo', 
                                     'ComputeRelCoord', 'ComputeKozakContext', 'AnnotateORF', 
                                     'Filter', 'Backup' ]

# List of strategies that have to check the FILT database
STRATEGIES_CHECKING_FILT_DATABASE = [ 'Filter', 'Backup'  ]


# ===============================================================================
# Database models
# ===============================================================================

DATABASE_DECLARATIVE_DS = 'DS'
DATABASE_DECLARATIVE_PRO = 'PRO'
AVAILABLE_DATABASE_DECLARATIVE_BASES = [ DATABASE_DECLARATIVE_DS, DATABASE_DECLARATIVE_PRO ]
AVAILABLE_DATABASE_MODELS = AVAILABLE_DATABASE_DECLARATIVE_BASES + [ 'FILT' ]
