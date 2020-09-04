# -*- coding: utf-8 -*-

import os
import pandas as pd


from fr.tagc.uorf.core.model.PRO import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.genetics import GeneticsConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger



# ===============================================================================
# Description of the FASTA file
# ===============================================================================

# For each sequence, a header and one or several lines containing
# the ORF sequence is written is the FASTA file, such as:
#
# - The first line is a header, starting with '>':
#
#     - If the query is performed using the ORF table, then the header contains:
#         - Three following pipe-separated values:
#             - [0] The alias of the database / the source - String
#             - [1] The ORF ID (with the 'ORF' prefix) - String (e.g. ORF246)
#             - [2] The ORF ID (with the 'ORF' prefix) followed by the taxon code - String
#                   (e.g. ORF246_HUMAN)
#
#         - Optionally (for long titles only) the following values are added, 
#           separated by one space character (using a key=value notation):
#             - The taxon scientific name. e.g. OS=Homo sapiens
#             - The chromosome (or scaffold) name. e.g. chr=6
#             - The strand. e.g. strand=+
#             - The absolute genomic start position. e.g. start_pos=32972748
#             - The absolute genomic stop position. e.g. stop_pos=32972927
#             - The number of exons. e.g. exons=1
#             - The full name of the database. e.g. database=MetamORF
#             - The URL of the database. url=http://example.com
#             - The version of the database (when available). e.g. release=1.1
#
#     - If the query is performed using the ORFTranscriptAsso table, 
#       then the header contains:
#         - Three following pipe-separated values:
#             - [0] The alias of the database / the source - String
#             - [1] The ORFTranscriptAsso ID (with the 'OTA' prefix) - String (e.g. OTA520)
#             - [2] The ORFTranscriptAsso ID (with the 'OTA' prefix) 
#                   followed by the taxon code - String (e.g. ORFTranscriptAsso520_HUMAN)
#
#         - Optionally (for long titles only) the following values are added, 
#           separated by one space character (using a key=value notation):
#             - The taxon scientific name. e.g. OS=Homo sapiens
#             - The relative start position. e.g. start_pos=25
#             - The relative stop position. e.g. stop_pos=72
#             - The ORF ID related to the entry. e.g. orf_id=120
#             - The Transcript ID related to the entry. e.g. transcript_id=128
#             - The full name of the database. e.g. database=MetamORF
#             - The URL of the database. url=http://example.com
#             - The version of the database (when available). e.g. release=1.1
#
# - The following line(s) contains the sequence, split every 60 characters




# ===============================================================================
# Strategy
# ===============================================================================
        

## GenerateFastaFileStrategy
#  =========================
#
# This class is a strategy aiming to generate a FASTA file using 
# the information contained either in the ORF table or in the 
# ORFTranscriptAsso table of the PRO database.
#
class GenerateFastaFileStrategy( object ):
    
    ## Class variables
    #  ---------------    
    # Tables that may be used to generate the FASTA file
    ORF_TABLE = 'ORF'
    OTA_TABLE = 'OTA'
    
    # Dictionary that associates to the type of sequence and name 
    # of the table, the appropriate sequence attribute name
    SEQUENCE_ATTRIBUTES = { Constants.SEQUENCE_TYPE_DNA : { ORF_TABLE : 'sequence',
                                                            OTA_TABLE : 'sequence_nt' },
                            Constants.SEQUENCE_TYPE_PROT : { ORF_TABLE : 'sequence_aa',
                                                             OTA_TABLE : 'sequence_aa' } }
    
    # FASTA extension
    FASTA_FILE_EXTENSION = '.fasta'
    
    # Source name
    FASTA_SOURCE_NAME = Constants.PROJECT_ALIAS
    
    # Maximum number of character of the sequence 
    # to display on the same line
    MAX_SEQ_LINE_LENGTH = 60

   

    ## Constructor of GenerateFastaFileStrategy
    #  ----------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - output_folder: String - The name of the folder where to export the FASTA file.
    #     - filename: String - The name of the FASTA file.
    #     - seq_type: String - The type of sequence to use ('DNA' for nucleic sequences or 
    #                          'PROT' for amino acid sequences). 
    #     - table_type: String - The name of the table to query ('ORF' or 'OTA') 
    #                            to get the sequences.
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
        # By default, save the file in a FASTA folder
        if ( not self.output_folder ):
            self.output_folder = Constants.FASTA_FOLDER
        
        # Get the eventual filename
        self.filename = OptionManager.get_instance().get_option( OptionConstants.OPTION_FASTA_FILENAME, 
                                                                 not_none = False )
        # By default, name the file 'DenCellORF_ORF'
        if ( not self.filename ):
            self.filename = Constants.DEFAULT_FASTA_FILENAME
        
        # Get the type of sequence to use to generate the FASTA file (DNA or PROT)
        self.seq_type = OptionManager.get_instance().get_option( OptionConstants.OPTION_FASTA_SEQ_TYPE,
                                                                 not_none = False )
        # By default, generate a FASTA of amino acid sequences
        if ( not self.seq_type ):
            self.seq_type = Constants.SEQUENCE_TYPE_PROT
        
        # Get the table to query to get the sequences (ORF or ORFTranscriptAsso)
        self.table_type = OptionManager.get_instance().get_option( OptionConstants.OPTION_FASTA_QUERY_TABLE,
                                                                   not_none = False )
    
        # By default, generate the file using the content of the ORF table
        if ( not self.table_type ):
            self.table_type = self.ORF_TABLE
        
        # Get the name of the attribute to use to get the sequence
        self.seq_attribute_name = self.SEQUENCE_ATTRIBUTES[ self.seq_type ][ self.table_type ]
            
        # Get the option informing if the sequences that have stop codons have to be excluded
        self.exclude_sqce_with_stops = OptionManager.get_instance().get_option( OptionConstants.OPTION_FASTA_EXCLUDE_SQCES_WITH_STOP,
                                                                                not_none = False )
        
        # Get the option allowing to generate long headers
        self.long_header = OptionManager.get_instance().get_option( OptionConstants.OPTION_FASTA_LONG_HEADERS,
                                                                    not_none = False )        
    
        
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the FASTA file.
    # 
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    # @throw DenCellORFException: When there is no sequence to write in the file.
    #
    def execute( self ):
        
        # Create a session to the "PRO-like" database
        SQLManagerPRO.get_instance().set_db_settings( self.db_settings )
        
        try:
            SQLManagerPRO.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'GenerateFastaFileStrategy.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        SQLManagerPRO.get_instance().close_session()
        
        
        Logger.get_instance().info( 'Starting to build the FASTA file.' )
        Logger.get_instance().info( 'The fasta file will be created querying the ' + self.table_type +
                                    ' table and using the ' + self.seq_type + ' sequences.' )
        
        # Create the output folder if it does not yet exist
        # (and its parent folders if necessary )
        if ( not os.path.isdir( self.output_folder ) ):
            os.makedirs( self.output_folder )
            
        file_path = os.path.join( self.output_folder, self.filename ) + self.FASTA_FILE_EXTENSION
        
        # Get the name of the species
        sp = SQLManagerPRO.get_instance().get_session().query( PROSpeciesCatalog ).one().name
        SQLManagerPRO.get_instance().close_session()
        
        # Get the informations related to the species
        # NB: These information will be used in the headers
        taxon_sc_name = Constants.SPECIES_CATALOG_FULL_NAMES_WITH_CAPS[ sp ]
        taxon_code = Constants.SPECIES_CATALOG_CODE[ sp ]
        taxon_id = Constants.SPECIES_CATALOG_TAXON_ID[ sp ]
        
        # Get the version number of the database
        db_release = SQLManagerPRO.get_instance().get_session().query( 
                                                                        PROMetadata.value 
                                                                      ).filter( 
                                                                                    PROMetadata.parameter == Constants.METATABLE_DATABASE_VERSION_NUMBER
                                                                                ).all()
        db_release = GeneralUtil.query_result_to_list( db_release )
        if ( len( db_release ) == 1 ):
            db_release = db_release[ 0 ]
        else:
            db_release = ''
            
        
        # Create the FASTA file
        # ---------------------                
        # Get the information necessary to compute the file content
        if ( self.table_type == self.ORF_TABLE ):
            # Get the necessary information from the ORF table
            all_orfs_query = SQLManagerPRO.get_instance().get_session().query( 
                                                                                ORF.id,
                                                                                ORF.chromosome,
                                                                                ORF.strand,
                                                                                ORF.start_pos,
                                                                                ORF.stop_pos,
                                                                                ORF.spliced_parts_count,
                                                                                eval( 'ORF.' + self.seq_attribute_name ) 
                                                                               ).filter(
                                                                                            eval( 'ORF.' + self.seq_attribute_name ) != None
                                                                                        )
                
        else:
            # Get the necessary information from the ORFTranscriptAsso table
            all_orfs_query = SQLManagerPRO.get_instance().get_session().query( 
                                                                                ORFTranscriptAsso.id,
                                                                                ORFTranscriptAsso.orf_id,
                                                                                ORFTranscriptAsso.transcript_id,
                                                                                ORFTranscriptAsso.rel_start_pos,
                                                                                ORFTranscriptAsso.rel_stop_pos,
                                                                                eval( 'ORFTranscriptAsso.' + self.seq_attribute_name )
                                                                               ).filter(
                                                                                            eval( 'ORFTranscriptAsso.' + self.seq_attribute_name ) != None
                                                                                        )
        
        # Run the query and get the results as a Pandas data frame
        all_orfs_df = pd.read_sql( all_orfs_query.statement,
                                   SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        # Check the query returned a result
        total_sqce_count = all_orfs_df.shape[0]
        if ( total_sqce_count == 0 ):
            raise DenCellORFException( 'It seems that the database you are querying do not contain any' +
                                       ' entry with sequence (' + self.seq_type + ') in its ' + 
                                       self.table_type + ' table. Hence, the generation of the fasta file' +
                                       ' has been stopped.' )
        
        all_orfs_df = all_orfs_df.astype( str )
        
        # If the excludeSqcesWithStop option has been selected, 
        # then exclude from the data frame all the sequences 
        # that contains at least a stop, then remove it
        if self.exclude_sqce_with_stops:
            contains_stop_codon = all_orfs_df.apply( self.check_stop_codons_in_sqce,
                                                     seq_type = self.seq_type,
                                                     seq_attribute_name = self.seq_attribute_name,
                                                     axis=1 ).to_frame()
            contains_stop_codon = contains_stop_codon.rename( columns = { 0: 'contains_stop_codon' } )
            all_orfs_df = pd.concat( [ all_orfs_df, contains_stop_codon ],
                                     axis = 1 )
            
            # Extract from the data frame the ORF for which the sequence
            # do not contains stop codons
            all_orfs_df = all_orfs_df[ all_orfs_df.contains_stop_codon == False ]
            
            Logger.get_instance().info( str( total_sqce_count - all_orfs_df.shape[0] ) +
                                        ' sequences (/' + str( total_sqce_count ) + 
                                        ') have been removed as they were containing stop codons' )
            
        
        # For each row, build a string that will be used 
        # as header line in the FASTA file
        header = all_orfs_df.apply( self.generate_header, 
                                    axis=1,
                                    taxon_sc_name = taxon_sc_name, 
                                    taxon_code = taxon_code,
                                    taxon_id = str( taxon_id ), 
                                    table = self.table_type,
                                    db_release = db_release,
                                    long_header = self.long_header ).to_frame()
        header = header.rename( columns = { 0: 'header' } )
        all_orfs_df = pd.concat( [ all_orfs_df, header ],
                                 axis = 1 )

        # Write the FASTA file one line at a time
        with open( file_path, 'w' ) as fasta_file:
    
            for ( index, row ) in all_orfs_df.iterrows():
                                
                # Write the header line
                fasta_file.write( '>' + row[ 'header' ] + '\n' )
                
                # Write the sequence line(s)
                  # Split the sequence if it has to be written on several lines
                full_seq = row[ self.seq_attribute_name ]
                seq = '\n'.join( [ full_seq[ k : k + self.MAX_SEQ_LINE_LENGTH ] for k in range( 0, len( full_seq ), self.MAX_SEQ_LINE_LENGTH ) ] )
                  # Write the sequence line(s)
                fasta_file.write( seq + '\n' )
                
        Logger.get_instance().info( 'The fasta file has been created at ' + file_path + '.' )
                
        
        
        
    ## check_stop_codons_in_sqce
    #  -------------------------
    #
    # This is a static method allowing to check if a a sequence
    # contains stop codons.
    # 
    # @param row: Pandas Series - A row from the ORF Pandas data frame.
    # @param seq_type: String - The type of sequence (DNA or PROT).
    # @param seq_attribute_name: String - The name of the attribute 
    #                                     containing the sequence.
    # 
    # @return stop_in_seq: Boolean - True if the sequence contains a stop codon.
    #
    @staticmethod
    def check_stop_codons_in_sqce( row, seq_type, seq_attribute_name ):
        
        seq = row[ seq_attribute_name ]
        
        if seq_type == Constants.SEQUENCE_TYPE_PROT:
            stop_codons_list = [ GeneticsConstants.STOP_CODON ]
        else:
            stop_codons_list = GeneticsConstants.STOP_CODON_SEQUENCES
            
            # As the stop codons have to be found in the same frame than
            # the start codon, split the sequence into a list of 
            # 3-characters strings
            seq = [ seq[ k : k+3 ] for k in range( 0, len( seq ), 3 ) ]
            
            # Exclude of the list the last codon of the list, 
            # as it is expected to be a stop codon
            seq = seq[ :-1 ]
        
        stop_in_seq = False
        k = 0
        while ( ( not stop_in_seq ) and ( k < len( stop_codons_list ) ) ):
            stop = stop_codons_list[ k ]
            if stop in seq:
                stop_in_seq = True
            k += 1
            
        return stop_in_seq
        
        
        
    ## generate_header
    #  ---------------
    #
    # This is a static method allowing to compute 
    # the header of a sequence.
    # 
    # @param row: Pandas Series - A row from the ORF Pandas data frame.
    # @param taxon_sc_name: String - The species scientific full name (e.g. Homo sapiens).
    # @param taxon_code: String - The taxonomic code (e.g. HUMAN).
    # @param taxon_id: String - The taxonomic ID (e.g. 9606).
    # @param table: String - The table used to perform queries (ORF/OTA).
    # @param db_release: String - The database version number.
    # @param long_header: Boolean - Should long headers be generated?
    # 
    # @return header: String - The header value.
    #
    @staticmethod
    def generate_header( row, taxon_sc_name, taxon_code, taxon_id, table, db_release, long_header ):
        
        header = [ GenerateFastaFileStrategy.FASTA_SOURCE_NAME ]
        
        # Define each part of the header
        if ( table == GenerateFastaFileStrategy.ORF_TABLE ):
            header += [ 'ORF' + row[ 'id' ],
                        'ORF' + row[ 'id' ] + '_' + taxon_code,
                        'OS=' + taxon_sc_name,
                        'OX=' + taxon_id,
                        'chr=' + row[ 'chromosome' ],
                        'strand=' + row[ 'strand' ],
                        'start_pos=' + row[ 'start_pos' ],
                        'stop_pos=' + row[ 'stop_pos' ],
                        'exons=' + row[ 'spliced_parts_count' ] ]
        
        else:
            header += [ 'OTA' + row[ 'id' ],
                        'OTA' + row[ 'id' ] + '_' + taxon_code,
                        'OS=' + taxon_sc_name,
                        'OX=' + taxon_id,
                        'rel_start_pos=' + row[ 'rel_start_pos' ],
                        'rel_stop_pos=' + row[ 'rel_stop_pos' ],
                        'orf_id=' + row[ 'orf_id' ],
                        'transcript_id=' + row[ 'transcript_id' ] ]
        
        # Add the database url and version number if available
        header += [ 'database=' + Constants.PROJECT_NAME,
                    'url=' + Constants.WEBSITE_URL ]
        if ( db_release ):
            header.append( 'release=' + db_release )  
        
        # Convert the header into a string
        header_string = '|'.join( header[0:3] )
        if long_header:
            header_string += ' ' + ' '.join( header[3:] )
        
        return header_string
    