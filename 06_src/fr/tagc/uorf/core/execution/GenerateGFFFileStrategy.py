# -*- coding: utf-8 -*-

import os
import pandas as pd
from sqlalchemy import or_


from fr.tagc.uorf.core.model.PRO import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# ===============================================================================
# Description of the GFF3 file
# ===============================================================================

# References:
# - https://www.ensembl.org/info/website/upload/gff3.html
# - http://gmod.org/wiki/GFF3
# - https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md
# - http://www.sequenceontology.org/so_wiki/index.php/Category:SO:SOFA

# Tab-separated file
# First line: '##gff-version 3'
# Undefined fields: '.'
# Human-readable comments could be included using '#' (end of line comments not allowed).
# Header is not expected to be included in the file.

# For each row:
# [0] seqid: String - Name of the chromosome or scaffold (without 'chr' prefix, 
#                     must be one used within Ensembl).
# [1] source: String - Name of the current project / database.
# [2] type: String - Type of feature (term or accession number from SOFA sequence 
#                    ontology). Here 'ORF', 'start_codon', 'stop_codon' or 'exon'.
# [3] start: Integer - The start position of the feature (with sequence numbering 
#                      starting at 1).
# [4] end: Integer - The end position of the feature (with sequence numbering 
#                    starting at 1).
#                    NB: start is always less than or equal to end.
# [5] score: Float - Here left empty.
# [6] strand: String - Strand of the feature '+' (forward) or '-' (reverse).
#                      '.' for unstranded features. 
#                      '?' for features whose strandedness is relevant but unknown.
# [7] phase: Integer <0,1,2> - Required for all features of type 'CDS'.
#                              Indicates where the feature begins with reference to the 
#                              reading frame. The phase indicates the number of bases 
#                              that should be removed from the beginning of the feature
#                              to reach the first base of the next codon.
#                              0 indicates the next codon begins at the first base of 
#                              the region, 1 at the second base and 2 at the third base.
#                              NB: This is NOT to be confused with the frame. The frame is 
#                                  calculated as a value for a given base relative to the start 
#                                  of the complete ORF or the codon (e.g. modulo 3), while CDS 
#                                  phase describes the start of the next codon relative to a given 
#                                  CDS feature.
#                                  For + strand features, phase is counted from the start field.
#                                  For - strand features, phase is counted from the end field.
# [8] attributes: String - A semi-colon separated list of tag-value pairs, providing
#                          additional information about each feature.
#                          Multiple attributes of the same type are indicated by 
#                          separating the values with a comma.
#                          NB: The following characters have reserved meanings and 
#                              must be escaped when used in other contexts: 
#                              ';', '=', '&', ','
#                              Tab must be replaced by '%09'.
#                              Attributes values should not be quoted.
#                              Attributes are case sensitive.
#                 List of tags:
#                 - ID: ID of the feature. Required for features that have children 
#                   or that span multiple lines. ID of each feature must be unique.
#                   For discontinuous features, the same ID may appear on multiple 
#                   lines.
#                 - Name: Name of the feature (to be displayed to the user).
#                 - Alias: Secondary name of the feature (e.g. accession number).
#                 - Parent: Indicates the parent of the feature (e.g. allows to 
#                   group exons into transcripts, transcripts into genes...).
#                 - Target: Target of a nucleotide-to-nucleotide or protein-to-nucleotide
#                   alignment. Format: "target_id start end [strand]"
#                 - Gap: Aligment of the feature to the target if the two are not collinear.
#                 - Derives_from: Disambiguate relationship between two features when the 
#                   relationship is a temporal one rather than a purely structural one.
#                 - Note: Free text note.
#                 - Dbxref: Database cross reference.
#                 - Ontology_term: Cross reference to an ontology term.
#                 - Is_circular: Indicate whether a feature is circular.
#                 NB: Parent, Alias, Note, Dbxref and Ontology_term can have multiple values.




# ===============================================================================
# Strategy
# ===============================================================================
        

## GenerateGFFFileStrategy
#  =======================
#
# This class is a strategy aiming to generate a GFF3 file using the 
# information contained in the ORF table of the PRO database.
# NB: Information related to the transcripts are not integrated in 
#     the GFF file generated.
#
class GenerateGFFFileStrategy( object ):
    
    ## Class variables
    #  ---------------
    # GFF3 extension
    GFF_FILE_EXTENSION = '.gff3'
    
    # GFF3 headers
    GFF_HEADER_SEQID = 'seqid'
    GFF_HEADER_SOURCE = 'source'
    GFF_HEADER_TYPE = 'type'
    GFF_HEADER_START = 'start'
    GFF_HEADER_END = 'end'
    GFF_HEADER_SCORE = 'score'
    GFF_HEADER_STRAND = 'strand'
    GFF_HEADER_PHASE = 'phase'
    GFF_HEADER_ATTRIBUTES = 'attributes'
    
    # Column order
    GFF_HEADER_LIST = [ GFF_HEADER_SEQID,
                        GFF_HEADER_SOURCE,
                        GFF_HEADER_TYPE,
                        GFF_HEADER_START,
                        GFF_HEADER_END,
                        GFF_HEADER_SCORE,
                        GFF_HEADER_STRAND,
                        GFF_HEADER_PHASE,
                        GFF_HEADER_ATTRIBUTES ]
    
    # GFF3 prefix
    GFF_FIRST_ROW = '##gff-version 3'
    
    # Constants columns
      # Empty value / Missing information
    GFF_UNDEFINED_FIELD = '.'
      # Source
    GFF_SOURCE_NAME = Constants.PROJECT_NAME
      # Types
    GFF_TYPE_ORF = 'ORF'
    GFF_TYPE_START_CODON = 'start_codon'
    GFF_TYPE_STOP_CODON = 'stop_codon'
    GFF_TYPE_EXON = 'exon'

   

    ## Constructor of GenerateGFFFileStrategy
    #  --------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - output_folder: String - The name of the folder where to export the GFF file.
    #     - filename: String - The name of the GFF file.
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
        # By default, save the file in a GFF folder
        if ( not self.output_folder ):
            self.output_folder = Constants.GFF_FOLDER
        
        # Get the eventual filename
        self.filename = OptionManager.get_instance().get_option( OptionConstants.OPTION_GFF_FILENAME, 
                                                                 not_none = False )
        # By default, name the file 'DenCellORF_ORF'
        if ( not self.filename ):
            self.filename = Constants.DEFAULT_GFF_FILENAME
    
        
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the GFF3 file.
    # 
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    #
    def execute( self ):
        
        # Create a session to the "PRO-like" database
        SQLManagerPRO.get_instance().set_db_settings( self.db_settings )

        try:
            SQLManagerPRO.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'GenerateGFFFileStrategy.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        SQLManagerPRO.get_instance().close_session()
        
        
        Logger.get_instance().info( 'Starting to build the GFF3 file.' )
        
        # Create the output folder if it does not yet exist
        # (and its parent folders if necessary )
        if ( not os.path.isdir( self.output_folder ) ):
            os.makedirs( self.output_folder )
            
        file_path = os.path.join( self.output_folder, self.filename ) + self.GFF_FILE_EXTENSION
        
        # Create the GFF3 file with the prefix(es)
        try:
            with open( file_path, 'w' ) as gff_file:
                gff_file.write( self.GFF_FIRST_ROW + '\n' )
        except Exception as e:
            raise DenCellORFException( 'GenerateGFFFileStrategy.execute(): An error occurred trying' +
                                       ' to create the GFF3 file at ' + file_path + 
                                       ' and/or writing the GFF3 prefix(es)', e )
        else:
            Logger.get_instance().debug( 'GenerateGFFFileStrategy.execute(): ' + 
                                         ' An empty GFF3 file have been created at ' + 
                                         file_path + '.' )
        
        
        # In order to reduce the computation time, 
        # the GFF file is build sequentially by:
        # - Adding the following information for all the entries of the ORF table:
        #     - 1 line for the ORF (chr, start and stop positions, unique ID)
        #     - 1 line for the start codon
        #     - 1 line for the stop codon
        # - Adding the following information only for the spliced ORFs:
        #     - 1 line for each exon (start and end positions, unique ID of the ORF)
        
        # First get all the entries of the ORF table with the features
        # usefull to build the GFF file
        all_orfs_query = SQLManagerPRO.get_instance().get_session().query( ORF.id, 
                                                                           ORF.chromosome, 
                                                                           ORF.strand, 
                                                                           ORF.start_pos,
                                                                           ORF.stop_pos )
        all_orfs_df = pd.read_sql( all_orfs_query.statement, 
                                   SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        
        # 'ORF' features
        # --------------
        Logger.get_instance().debug( 'Starting to compute the "ORF" features of the GFF file.' )
        
        # Instantiate a data frame that aims to contain the 'ORF' features
        gff_content_orfs = all_orfs_df
        
        # Add the 'attributes' column to the data frame
        attributes_col = gff_content_orfs.apply( self.compute_orf_row_attributes, axis=1 ).to_frame()
        attributes_col = attributes_col.rename( columns = { 0: self.GFF_HEADER_ATTRIBUTES } )
        gff_content_orfs = pd.concat( [ gff_content_orfs, attributes_col ], 
                                      axis=1 )
        
        # Rename columns
        gff_content_orfs = gff_content_orfs.rename( columns = { 'chromosome': self.GFF_HEADER_SEQID,
                                                                 'start_pos': self.GFF_HEADER_START,
                                                                 'stop_pos': self.GFF_HEADER_END } )
        
        # Add the columns with constant values
        gff_content_orfs[ self.GFF_HEADER_SOURCE ] = self.GFF_SOURCE_NAME
        gff_content_orfs[ self.GFF_HEADER_TYPE ] = self.GFF_TYPE_ORF
        gff_content_orfs[ self.GFF_HEADER_SCORE ] = self.GFF_UNDEFINED_FIELD
        gff_content_orfs[ self.GFF_HEADER_PHASE ] = self.GFF_UNDEFINED_FIELD
        
        # Reorder the columns of the data frame
        # NB: An extra-column ID is left in order to allow the sorting of the rows
        #     after the merging of all the data frames constituting the GFF file.
        gff_content_orfs = gff_content_orfs[ self.GFF_HEADER_LIST + [ 'id' ] ]             
                 
         
        # 'start_codon' features
        # ----------------------
        Logger.get_instance().debug( 'Starting to compute the "start_codon" features of the GFF file.' )
        
        # Instantiate a data frame that aims to contain the 'start_codon' features
        gff_content_start = all_orfs_df
        
        # Compute the 'start', 'end' and 'attributes' columns of the data frame
        # and add them to the data frame
        start_col = gff_content_start.apply( self.compute_start_start, axis=1 ).to_frame()
        start_col = start_col.rename( columns = { 0: self.GFF_HEADER_START } )
        
        end_col = gff_content_start.apply( self.compute_start_end, axis=1 ).to_frame()
        end_col = end_col.rename( columns = { 0: self.GFF_HEADER_END } )
        
        attributes_col = gff_content_start.apply( self.compute_start_attributes, axis=1 ).to_frame()
        attributes_col = attributes_col.rename( columns = { 0: self.GFF_HEADER_ATTRIBUTES } )
        
        gff_content_start = pd.concat( [ gff_content_start, start_col, end_col, attributes_col ], 
                                       axis=1 )
        
        # Rename columns
        gff_content_start = gff_content_start.rename( columns = { 'chromosome': self.GFF_HEADER_SEQID } )  
        
        # Add the columns with constant values
        gff_content_start[ self.GFF_HEADER_SOURCE ] = self.GFF_SOURCE_NAME
        gff_content_start[ self.GFF_HEADER_TYPE ] = self.GFF_TYPE_START_CODON
        gff_content_start[ self.GFF_HEADER_SCORE ] = self.GFF_UNDEFINED_FIELD
        gff_content_start[ self.GFF_HEADER_PHASE ] = self.GFF_UNDEFINED_FIELD
        
        # Select and reorder the columns of the data frame
        gff_content_start = gff_content_start[ self.GFF_HEADER_LIST + [ 'id' ] ]                
                 
         
        # 'stop_codon' features
        # ---------------------
        Logger.get_instance().debug( 'Starting to compute the "stop_codon" features of the GFF file.' )
        
        # Instantiate a data frame that aims to contain the 'stop_codon' features
        gff_content_stop = all_orfs_df
        
        # Compute the 'start', 'end' and 'attributes' columns of the data frame
        # and add them to the data frame
        start_col = gff_content_stop.apply( self.compute_stop_start, axis=1 ).to_frame()
        start_col = start_col.rename( columns = { 0: self.GFF_HEADER_START } )
        
        end_col = gff_content_stop.apply( self.compute_stop_end, axis=1 ).to_frame()
        end_col = end_col.rename( columns = { 0: self.GFF_HEADER_END } )
        
        attributes_col = gff_content_stop.apply( self.compute_stop_attributes, axis=1 ).to_frame()
        attributes_col = attributes_col.rename( columns = { 0: self.GFF_HEADER_ATTRIBUTES } )
        
        gff_content_stop = pd.concat( [ gff_content_stop, start_col, end_col, attributes_col ], 
                                      axis=1 )
        
        # Rename columns
        gff_content_stop = gff_content_stop.rename( columns = { 'chromosome': self.GFF_HEADER_SEQID } )
        
        # Add columns of fixed value
        gff_content_stop[ self.GFF_HEADER_SOURCE ] = self.GFF_SOURCE_NAME
        gff_content_stop[ self.GFF_HEADER_TYPE ] = self.GFF_TYPE_STOP_CODON
        gff_content_stop[ self.GFF_HEADER_SCORE ] = self.GFF_UNDEFINED_FIELD
        gff_content_stop[ self.GFF_HEADER_PHASE ] = self.GFF_UNDEFINED_FIELD
        
        # Select and reorder the columns of the data frame
        gff_content_stop = gff_content_stop[ self.GFF_HEADER_LIST + [ 'id' ] ]
        
        
        # 'exon' features
        # ---------------
        Logger.get_instance().debug( 'Starting to compute the "exon" features of the GFF file.' )
        
        # Get all the ORFs that are reported as spliced and for which the
        # exon coordinates are provided
        all_spliced_orfs_query = SQLManagerPRO.get_instance().get_session().query( ORF ).filter( ORF.spliced == True,
                                                                                                 ORF.splice_starts != None,
                                                                                                 ORF.splice_ends != None )
        all_spliced_orfs_df = pd.read_sql( all_spliced_orfs_query.statement,
                                           SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        # Get the number of ORFs expected to be treated and 
        # reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = all_spliced_orfs_df.shape[ 0 ] )
        
        # Instantiate an empty data frame with all the GFF columns
        # and an additive 'id' column
        gff_content_exons = pd.DataFrame( columns = ( self.GFF_HEADER_LIST + [ 'id' ] ) )
        
        # For each ORF spliced
        for ( index, row ) in all_spliced_orfs_df.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Get the start and ends of all the "exons", and register 
            # a new line in the GFF file for each of them
            sp_starts = map( int, 
                             row[ 'splice_starts' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR ) ) 
            sp_ends = map( int, 
                           row[ 'splice_ends' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
            
            # For each exon, create a new line in the GFF file
            for k in range( int( row[ 'spliced_parts_count' ] ) ):
                
                # Reverse the start and stop positions for the ORFs 
                # located on the minus strand
                start_exon = sp_starts[ k ]
                end_exon = sp_ends[ k ]
                # If the exon is located on the negative strand,
                # reverse the start and end position as the start
                # has to be smaller than the stop in the GFF
                if ( row[ 'strand' ]== '-' ):
                    ( start_exon, end_exon ) = ( end_exon, start_exon )
                
                gff_content_exons = gff_content_exons.append( { self.GFF_HEADER_SEQID: row[ 'chromosome' ],
                                                                self.GFF_HEADER_SOURCE: self.GFF_SOURCE_NAME,
                                                                self.GFF_HEADER_TYPE: self.GFF_TYPE_EXON,
                                                                self.GFF_HEADER_START: start_exon,
                                                                self.GFF_HEADER_END: end_exon,
                                                                self.GFF_HEADER_SCORE: self.GFF_UNDEFINED_FIELD,
                                                                self.GFF_HEADER_STRAND: row[ 'strand' ],
                                                                self.GFF_HEADER_PHASE: self.GFF_UNDEFINED_FIELD,
                                                                self.GFF_HEADER_ATTRIBUTES: ( 'ID=' + str( row[ 'id' ] ) + '.' + str( k ) +
                                                                                              ';Parent=' + str( row[ 'id' ] ) ) },
                                                                ignore_index = True )
        
        
        
        # Merge df
        # --------
        # Merge all the data frames containing the data of the GFF
        gff_full_content = pd.concat( [ gff_content_orfs, 
                                        gff_content_start, 
                                        gff_content_stop, 
                                        gff_content_exons ] )
        
        # Reorder the rows by chromosome, then ID, then type, 
        # then start position, then attributes.
        # This allows the features to be ordered by (in this order):
        # - Chromosome (seqid)
        # - ORF to which they are related to
        # - Type of feature (ORF, start, stop, exon)
        # - Start position (useful for ORFs with several exons)
        # - End position (useful for ORFs with several exons)
        # - Attributes
        # Hence, the features describing the features describing 
        # the same ORF located in the same 'area' of the file.
        gff_full_content = gff_full_content.sort_values( by = [ self.GFF_HEADER_SEQID,
                                                                'id',
                                                                self.GFF_HEADER_TYPE,
                                                                self.GFF_HEADER_END,
                                                                self.GFF_HEADER_ATTRIBUTES ] )
        
        # Remove the ID column which is no longer useful
        # and not expected to be present in the GFF file
        gff_full_content = gff_full_content.drop( [ 'id' ], axis=1 )
        
        
        # Add the content of the GFF file to the file,
        # after the prefix
        FileHandlerUtil.pandas_df_to_csv( output_folder = self.output_folder, 
                                          filename = self.filename,
                                          df = gff_full_content,
                                          file_desc = 'GFF file content',
                                          sep = '\t',
                                          ext = self.GFF_FILE_EXTENSION,
                                          mode = 'a',
                                          hdr = False )
        
        Logger.get_instance().info( 'The GFF file has been successfully generated and stored in the ' +
                                    self.output_folder + ' directory.' )
        
        
        
    ## compute_orf_row_attributes
    #  --------------------------
    #
    # This is a static method allowing to compute the value
    # of the 'attributes' column for a row of the 'ORF' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the ORF Pandas data frame.
    # 
    # @return attributes: String - The attributes value.
    #
    @staticmethod
    def compute_orf_row_attributes( row ):
        
        attributes = 'ID=' + str( row[ 'id' ] )
        
        return attributes
        
        
        
    ## compute_start_attributes
    #  ------------------------
    #
    # This is a static method allowing to compute the value
    # of the 'attributes' column for a row of the 'start_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the start codons
    #                             Pandas data frame.
    # 
    # @return attributes: String - The attributes value.
    #
    @staticmethod
    def compute_start_attributes( row ):
        
        attributes = 'ID=' + str( row[ 'id' ] ) + '.start;Parent=' + str( row[ 'id' ] )
        
        return attributes
                
        
    ## compute_start_start
    #  -------------------
    #
    # This is a static method allowing to compute the value
    # of the 'start' column for a row of the 'start_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the start codons
    #                             Pandas data frame.
    # 
    # @return start: String - The start value.
    #
    @staticmethod
    def compute_start_start( row ):
        
        strand = row[ 'strand' ]
        
        if ( strand == '+' ):
            start = row[ 'start_pos' ]
        elif ( strand == '-' ):
            start = row[ 'stop_pos' ] - 2
        
        return start
                
        
    ## compute_start_end
    #  -----------------
    #
    # This is a static method allowing to compute the value
    # of the 'end' column for a row of the 'start_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the start codons
    #                             Pandas data frame.
    # 
    # @return end: String - The end value.
    #
    @staticmethod
    def compute_start_end( row ):
        
        strand = row[ 'strand' ]
        
        if ( strand == '+' ):
            end = row[ 'start_pos' ] + 2
        elif ( strand == '-' ):
            end = row[ 'stop_pos' ]
        
        return end
        
        
        
    ## compute_stop_attributes
    #  -----------------------
    #
    # This is a static method allowing to compute the value
    # of the 'attributes' column for a row of the 'stop_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the stop codons
    #                             Pandas data frame.
    # 
    # @return attributes: String - The attributes value.
    #
    @staticmethod
    def compute_stop_attributes( row ):
        
        attributes = 'ID=' + str( row[ 'id' ] ) + '.stop;Parent=' + str( row[ 'id' ] )
        
        return attributes
        
        
    ## compute_stop_start
    #  ------------------
    #
    # This is a static method allowing to compute the value
    # of the 'start' column for a row of the 'stop_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the stop codons
    #                             Pandas data frame.
    # 
    # @return start: String - The start value.
    #
    @staticmethod
    def compute_stop_start( row ):
        
        strand = row[ 'strand' ]
        
        if ( strand == '+' ):
            start = row[ 'stop_pos' ] - 2
        elif ( strand == '-' ):
            start = row[ 'start_pos' ]
        
        return start  
        
        
    ## compute_stop_end
    #  ----------------
    #
    # This is a static method allowing to compute the value
    # of the 'end' column for a row of the 'stop_codon' 
    # features data frame.
    # 
    # @param row: Pandas Series - A row from the stop codons
    #                             Pandas data frame.
    # 
    # @return end: String - The end value.
    #
    @staticmethod
    def compute_stop_end( row ):
        
        strand = row[ 'strand' ]
        
        if ( strand == '+' ):
            end = row[ 'stop_pos' ]
        elif ( strand == '-' ):
            end = row[ 'start_pos' ] + 2
        
        return end
    