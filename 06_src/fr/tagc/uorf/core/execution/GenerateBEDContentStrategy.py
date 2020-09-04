# -*- coding: utf-8 -*-

import os
import subprocess
import pandas as pd
from sqlalchemy import or_, func


from fr.tagc.uorf.core.model.PRO import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# ===============================================================================
# Description of the BED file
# ===============================================================================

# References:
# - http://genome-euro.ucsc.edu/FAQ/FAQformat.html#format3
# - https://genome.ucsc.edu/goldenPath/help/customTrack.html#TRACK
# - https://software.broadinstitute.org/software/igv/TrackLine

# Tab-delimited or whitespace-delimited file
# Undefined fields: '.'
# NB: BigBed data format should be used for BED-like files over 50 MB.
#     Header line can be added but is not accepted by most BED file-related tools (e.g. bedToBigBed).

# For each row:
# Mandatory fields
# [0] chrom: String - The name of the chromosome (with 'chr' prefix) or scaffold.
# [1] chromStart: Integer - The starting position of the feature in the chromosome (or scaffold).
#                           The first base in a chromosome is numbered 0.
# [2] chromEnd: Integer - The ending position of the feature in the chromosome (or scaffold).
#                         The chromEnd base is NOT included in the display of the feature, however 
#                         the position in number format will be represented.
# NB: For example, the first 100 bases of chromosome 1 are defined as chrom=1, chromStart=0, chromEnd=100, 
#     and span the bases numbered 0-99 in UCSC software (not 0-100), but will represent the position 
#     notation chr1:1-100.

# Optional fields
# [3] name: String - The name of the BED line (displayed on the left on genome browsers).
# [4] score: Integer <0-1000> - A score between 0 and 1000.
#                               If the track line useScore attribute is set to 1 for the
#                               annotation data set, the score value will determine the level 
#                               of gray in which the feature is displayed.
#                               Ranges of gray's shades:
#                               [0,166], [167-277], [278-388], [389-499], [500-611], 
#                               [612-722], [723-833], [834-944], [945-1000]
# [5] strand: String - Strand of the feature (+/-).
# [6] thickStart: The starting position at which the feature is drawn thickly 
#                 (in coordinates relative to the chromosome start).
# [7] thickEnd: The ending position at which the feature is drawn thickly
#                 (in coordinates relative to the chromosome start).
# [8] itemRgb: A RGB value in the format R,G,B (e.g. 255,0,0).
#              If the track line itemRgb is set to 'On', the RGB value will determine 
#              the display color of the data contained in the BED line.
#              NB: It is recommended to use less than 8 colors to avoid overwhelming 
#                  the color resources of the genome browser.
# [9] blockCount - The number of blocks (exons) in the BED line.
# [10] blockSizes - A comma-separated list of the block sizes.
# [11] blockStarts - A comma-separated list of block starts. All of the blockStart 
#                    positions have to be relative to chromStart.
# NB: The first blockStart value must be 0. 
#     The last blockStart value + the final blockSize value must equal chromEnd.
#     Blocks may not overlap.

# For the additional description of BED files (track lines, BigBed format...), 
# see the documentation of the GenerateBEDFileStrategy class.




# ===============================================================================
# Strategy
# ===============================================================================
        

## GenerateBEDContentStrategy
#  ==========================
#
# This class is a strategy aiming to generate a BED line for entry
# of the ORF table and to store it in the UTBEDContent table.
# NB: The export of the content of this table is performed by the
#     GenerateBEDFileStrategy.
#
class GenerateBEDContentStrategy( object ):
    
    ## Class variables
    #  ---------------
    # BED headers
    BED_HEADER_CHROM = 'chrom'
    BED_HEADER_CHROM_START = 'chromStart'
    BED_HEADER_CHROM_END = 'chromEnd'
    BED_HEADER_NAME = 'name'
    BED_HEADER_SCORE = 'score'
    BED_HEADER_STRAND = 'strand'
    BED_HEADER_THICK_START = 'thickStart'
    BED_HEADER_THICK_END = 'thickEnd'
    BED_HEADER_RGB = 'itemRgb'
    BED_HEADER_BLOCK_COUNT = 'blockCount'
    BED_HEADER_BLOCK_SIZES = 'blockSizes'
    BED_HEADER_BLOCK_STARTS = 'blockStarts'
    
    # Additional headers
    BED_HEADER_TRANSCRIPTS = 'transcripts'
    BED_HEADER_RNA_BIOTYPES = 'rna_biotypes'
    BED_HEADER_CELL_TYPES = 'cell_types'
    BED_HEADER_ORF_ANNOTATIONS = 'orf_annotations'
    BED_HEADER_KOZAK_CONTEXTS = 'kozak_contexts'
    
    # Column order
    BED_HEADER_LIST = [ BED_HEADER_CHROM,
                        BED_HEADER_CHROM_START,
                        BED_HEADER_CHROM_END,
                        BED_HEADER_NAME,
                        BED_HEADER_SCORE,
                        BED_HEADER_STRAND,
                        BED_HEADER_THICK_START,
                        BED_HEADER_THICK_END,
                        BED_HEADER_RGB,
                        BED_HEADER_BLOCK_COUNT,
                        BED_HEADER_BLOCK_SIZES,
                        BED_HEADER_BLOCK_STARTS ]
    
    BED_HEADER_ADD_LIST = [ BED_HEADER_TRANSCRIPTS,
                            BED_HEADER_RNA_BIOTYPES,
                            BED_HEADER_CELL_TYPES,
                            BED_HEADER_ORF_ANNOTATIONS,
                            BED_HEADER_KOZAK_CONTEXTS ]
        
    # Constants columns
      # Empty value / Missing information
    BED_UNDEFINED_FIELD = '.'
    BED_DEFAULT_SCORE = 0
      # RGB colors depending on strand
    BED_DEFAULT_RGB_PLUS_STRAND = '255,0,0'
    BED_DEFAULT_RGB_MINUS_STRAND = '0,0,255'
    
    # List of chromosomes accepted in the BED file
    # By default all chromosome with a number in the 1-23 range are accepted,
    # as well as X and Y chromosomes. Hence mitochondrial chromosomes and
    # scaffolds are excluded.
    AUTHORIZED_CHR_LIST = ( map( str, range( 23 ) ) + 
                            [ Constants.CHROMOSOME_X, Constants.CHROMOSOME_Y ] )
    

    ## Constructor of GenerateBEDContentStrategy
    #  -----------------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
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
        
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the content of the UTBEDContent table.
    #
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    # 
    def execute( self ):
        
        # Create a session to the "PRO-like" database
        SQLManagerPRO.get_instance().set_db_settings( self.db_settings )

        try:
            SQLManagerPRO.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'GenerateBEDContentStrategy.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        SQLManagerPRO.get_instance().close_session()
        
        self.compute_bed_content()
        
    
    
    ## compute_bed_content
    #  -------------------
    #
    # Generate the content of the UTBEDContent table and fill the table.
    # 
    def compute_bed_content( self ):        
        
        Logger.get_instance().info( 'Starting to compute the content of the BEDContent table.' )
        
        # Remove the content of the UTBEDContent table prior to compute it again
        try:
            SQLManagerPRO.get_instance().get_session().query( UTBEDContent ).delete()
            SQLManagerPRO.get_instance().commit()
        except Exception as e:
            raise DenCellORFException( 'GenerateBEDContentStrategy.execute(): An error occurred trying to' +
                                       ' delete the existing content of the UTBEDContent table.', e )
        SQLManagerPRO.get_instance().close_session()
        
        
        # In order to reduce the computation time, 
        # the BED file is build sequentially by:
        # - Adding the information related to the non-spliced ORFs
        # - Adding the information related to the ORFs harboring several exons        
        
        # Unspliced ORFs
        # --------------
        Logger.get_instance().debug( 'Starting to compute the BED lines for all unspliced ORFs.' )
        
        # First get all the entries of the ORF table without splicing information
        all_orfs_not_spliced_query = SQLManagerPRO.get_instance().get_session().query(  ORF.id, 
                                                                                        ORF.chromosome, 
                                                                                        ORF.strand, 
                                                                                        ORF.start_pos,
                                                                                        ORF.stop_pos,
                                                                                        ORF.spliced,
                                                                                        ORF.genomic_length
                                                                                       ).filter( 
                                                                                                 or_( ORF.spliced == None,
                                                                                                      ORF.spliced == False,
                                                                                                      ORF.splice_starts == None,
                                                                                                      ORF.splice_ends == None ) )
        all_orfs_not_spliced_df = pd.read_sql( all_orfs_not_spliced_query.statement, 
                                               SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
                
        # Set name of the line as the ORF ID with 'ORF' prefix
        all_orfs_not_spliced_df[ self.BED_HEADER_NAME ] = map( lambda id: 'ORF' + str( id ),
                                                               all_orfs_not_spliced_df[ 'id' ] )
        
        # Add the 'chr' prefix to chromosome names
        all_orfs_not_spliced_df[ 'chromosome' ] = map( lambda x: 'chr' + x, 
                                                       all_orfs_not_spliced_df[ 'chromosome' ] )
        
        # As the start position of chromosome equals 0 in BED files,
        # remove 1 from the absolute genomic coordinates to get 
        # the appropriate coordinates
        all_orfs_not_spliced_df[ self.BED_HEADER_CHROM_START ] = map( lambda x: int( x ) - 1,
                                                                      all_orfs_not_spliced_df[ 'start_pos' ] )
        # NB: Stop positions are left unmodified as chromEnd is one-based
                
        # Unspliced ORFs obviously contain one single exon, 
        # then draw thickly the whole feature
        all_orfs_not_spliced_df[ self.BED_HEADER_THICK_START ] = all_orfs_not_spliced_df[ self.BED_HEADER_CHROM_START ]
        all_orfs_not_spliced_df[ self.BED_HEADER_THICK_END ] = all_orfs_not_spliced_df[ 'stop_pos' ]
        # and define one single block
        all_orfs_not_spliced_df[ self.BED_HEADER_BLOCK_COUNT ] = 1
        all_orfs_not_spliced_df[ self.BED_HEADER_BLOCK_STARTS ] = 0
            # If  the genomic lengths have already been computed, then use them.  
        if ( any( [ ( gen_len != None ) for gen_len in all_orfs_not_spliced_df[ 'genomic_length' ] ] ) ):
            all_orfs_not_spliced_df[ self.BED_HEADER_BLOCK_SIZES ] = all_orfs_not_spliced_df[ 'genomic_length' ]
        else:
            all_orfs_not_spliced_df[ self.BED_HEADER_BLOCK_SIZES ] = all_orfs_not_spliced_df[ 'stop_pos' ] - all_orfs_not_spliced_df[ 'start_pos' ] + 1

        # Compute the RGB column
        rgb_col = all_orfs_not_spliced_df.apply( self.compute_color, axis=1 ).to_frame()
        rgb_col = rgb_col.rename( columns = { 0: self.BED_HEADER_RGB } )
        all_orfs_not_spliced_df = pd.concat( [ all_orfs_not_spliced_df, rgb_col ],
                                             axis = 1 )
        
        # Leave the score columns empty
        all_orfs_not_spliced_df[ self.BED_HEADER_SCORE ] = self.BED_DEFAULT_SCORE
        
        # Rename columns
        all_orfs_not_spliced_df = all_orfs_not_spliced_df.rename( columns = { 'chromosome': self.BED_HEADER_CHROM,
                                                                              'stop_pos': self.BED_HEADER_CHROM_END } )
        
        # Select and reorder the columns of the data frame
        all_orfs_not_spliced_df = all_orfs_not_spliced_df[ [ 'id' ] + self.BED_HEADER_LIST ]
                
        
        # Spliced ORFs
        # ------------
        Logger.get_instance().debug( 'Starting to compute the BED lines for all spliced ORFs.' )
        
        # First get all the entries of the ORF table without splicing information
        all_orfs_spliced_query = SQLManagerPRO.get_instance().get_session().query(  ORF.id, 
                                                                                    ORF.chromosome, 
                                                                                    ORF.strand, 
                                                                                    ORF.start_pos,
                                                                                    ORF.stop_pos,
                                                                                    ORF.spliced_parts_count,
                                                                                    ORF.splice_starts,
                                                                                    ORF.splice_ends
                                                                                  ).filter( ORF.spliced == True,
                                                                                            ORF.splice_starts != None,
                                                                                            ORF.splice_ends != None )
        all_orfs_spliced_df = pd.read_sql( all_orfs_spliced_query.statement,
                                           SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        # Set name of the line as the ORF ID with 'ORF' prefix
        all_orfs_spliced_df[ self.BED_HEADER_NAME ] = map( lambda id: 'ORF' + str( id ),
                                                           all_orfs_spliced_df[ 'id' ] )
        
        # Add the 'chr' prefix to chromosome names
        all_orfs_spliced_df[ 'chromosome' ] = map( lambda x: 'chr' + x, 
                                                   all_orfs_spliced_df[ 'chromosome' ] )
        
        # As the start position of chromosome equals 0 in BED files,
        # remove 1 from the absolute genomic coordinates to get 
        # the appropriate coordinates
        all_orfs_spliced_df[ self.BED_HEADER_CHROM_START ] = map( lambda x: int( x ) - 1,
                                                                  all_orfs_spliced_df[ 'start_pos' ] )
        # NB: Stop positions are left unmodified as chromEnd is one-based
          
        # Draw thickly the whole feature
        all_orfs_spliced_df[ self.BED_HEADER_THICK_START ] = all_orfs_spliced_df[ self.BED_HEADER_CHROM_START ]
        all_orfs_spliced_df[ self.BED_HEADER_THICK_END ] = all_orfs_spliced_df[ 'stop_pos' ]
        
        # Define the block-related values
        all_orfs_spliced_df[ self.BED_HEADER_BLOCK_COUNT ] = all_orfs_spliced_df[ 'spliced_parts_count' ]
        
        # Get the comma-separated lists of the exon start positions
        block_starts_col = all_orfs_spliced_df.apply( self.compute_block_starts, axis=1 ).to_frame()
        block_starts_col = block_starts_col.rename( columns = { 0: self.BED_HEADER_BLOCK_STARTS } )
        all_orfs_spliced_df = pd.concat( [ all_orfs_spliced_df, block_starts_col ],
                                         axis = 1 )
        
        # Compute the comma-separated list of the exon sizes
        block_sizes_col = all_orfs_spliced_df.apply( self.compute_block_sizes, axis=1 ).to_frame()
        block_sizes_col = block_sizes_col.rename( columns = { 0: self.BED_HEADER_BLOCK_SIZES } )
        all_orfs_spliced_df = pd.concat( [ all_orfs_spliced_df, block_sizes_col ],
                                         axis = 1 )
        
        # Leave the RGB and score columns empty
        all_orfs_spliced_df[ self.BED_HEADER_RGB ] = map( self.compute_color_from_strd,
                                                          all_orfs_spliced_df[ 'strand' ] )
        all_orfs_spliced_df[ self.BED_HEADER_SCORE ] = self.BED_DEFAULT_SCORE
        
        # Rename columns
        all_orfs_spliced_df = all_orfs_spliced_df.rename( columns = { 'chromosome': self.BED_HEADER_CHROM,
                                                                      'stop_pos': self.BED_HEADER_CHROM_END } )
        
        # Select and reorder the columns of the data frame
        all_orfs_spliced_df = all_orfs_spliced_df[ [ 'id' ] + self.BED_HEADER_LIST ]
        
        
        # Merge the two data frames
        # -------------------------
        # Merge all the data frames containing the data of the BED
        bed_full_content = pd.concat( [ all_orfs_not_spliced_df, 
                                        all_orfs_spliced_df ] )
        
        
        # Add extra columns
        # -----------------
        Logger.get_instance().debug( 'Starting to compute the additional columns for bed detail format.' )     
        
        # For each feature, add the list of distinct official 
        # transcript IDs corresponding to the ORF
        transcript_id_orf_asso_qr = SQLManagerPRO.get_instance().get_session().query( 
                                                                                        ORF.id,
                                                                                        func.group_concat( Transcript.transcript_id.distinct().op( 'ORDER BY' )( Transcript.transcript_id ) ).label( self.BED_HEADER_TRANSCRIPTS )
                                                                                    ).filter(
                                                                                                Transcript.id == ORFTranscriptAsso.transcript_id,
                                                                                                ORFTranscriptAsso.orf_id == ORF.id
                                                                                            ).group_by( 
                                                                                                        ORF.id 
                                                                                                      )
        transcript_id_orf_asso_df = pd.read_sql( transcript_id_orf_asso_qr.statement,
                                                 SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        bed_full_content = bed_full_content.merge( transcript_id_orf_asso_df,
                                                   on = 'id',
                                                   how = 'left',
                                                   validate = 'one_to_one' )
        
        # For each feature, add the list of distinct
        # RNA biotypes corresponding to the ORF
        rna_biotypes_orf_asso_qr = SQLManagerPRO.get_instance().get_session().query( 
                                                                                        ORF.id,
                                                                                        func.group_concat( Transcript.rna_biotype.distinct().op( 'ORDER BY' )( Transcript.rna_biotype ) ).label( self.BED_HEADER_RNA_BIOTYPES )
                                                                                    ).filter(
                                                                                                Transcript.id == ORFTranscriptAsso.transcript_id,
                                                                                                ORFTranscriptAsso.orf_id == ORF.id
                                                                                            ).group_by( 
                                                                                                        ORF.id 
                                                                                                      )
        rna_biotypes_orf_asso_df = pd.read_sql( rna_biotypes_orf_asso_qr.statement,
                                                SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        bed_full_content = bed_full_content.merge( rna_biotypes_orf_asso_df,
                                                   on = 'id',
                                                   how = 'left',
                                                   validate = 'one_to_one' )
        
        
        
        # For each feature, add the list of distinct cellular
        # contexts corresponding to the ORF
        cell_context_orf_asso_qr = SQLManagerPRO.get_instance().get_session().query( 
                                                                                        ORF.id,
                                                                                        func.group_concat( CellContext.cell_context.distinct().op( 'ORDER BY' )( CellContext.cell_context ) ).label( self.BED_HEADER_CELL_TYPES )
                                                                                    ).filter(
                                                                                                CellContext.orftranscriptasso_id == ORFTranscriptAsso.id,
                                                                                                ORFTranscriptAsso.orf_id == ORF.id
                                                                                            ).group_by( 
                                                                                                        ORF.id 
                                                                                              )
        cell_context_orf_asso_df = pd.read_sql( cell_context_orf_asso_qr.statement,
                                                SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        # Replace any splace or tabulation in cell context names
        # by underscores
        cell_context_orf_asso_df[ 'cell_types' ] = map( lambda x: x.replace( ' ', '_' ).replace( '\t', '_' ),
                                                        cell_context_orf_asso_df[ 'cell_types' ] )
        
        bed_full_content = bed_full_content.merge( cell_context_orf_asso_df,
                                                   on = 'id',
                                                   how = 'left',
                                                   validate = 'one_to_many' )
        
        
        # For each feature, add the list of distinct ORF annotations
        # corresponding to the ORF
        orf_annot_orf_asso_qr = SQLManagerPRO.get_instance().get_session().query(
                                                                                    ORF.id,
                                                                                    func.group_concat( ORFAnnotation.orf_annotation.distinct().op( 'ORDER BY' )( ORFAnnotation.orf_annotation ) ).label( self.BED_HEADER_ORF_ANNOTATIONS )
                                                                                  ).filter(
                                                                                                ORFAnnotation.orftranscriptasso_id == ORFTranscriptAsso.id,
                                                                                                ORFTranscriptAsso.orf_id == ORF.id
                                                                                            ).group_by( 
                                                                                                        ORF.id 
                                                                                              )
        orf_annot_orf_asso_df = pd.read_sql( orf_annot_orf_asso_qr.statement,
                                             SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        bed_full_content = bed_full_content.merge( orf_annot_orf_asso_df,
                                                   on = 'id',
                                                   how = 'left',
                                                   validate = 'one_to_many' )
        
        
        # For each feature, add the list of distinct Kozak contexts
        # corresponding to the ORF
        kozak_ctxt_orf_asso_qr = SQLManagerPRO.get_instance().get_session().query(
                                                                                    ORF.id,
                                                                                    func.group_concat( ORFTranscriptAsso.kozak_context_comp.distinct().op( 'ORDER BY' )( ORFTranscriptAsso.kozak_context_comp ) ).label( self.BED_HEADER_KOZAK_CONTEXTS )
                                                                                  ).filter(
                                                                                                ORFTranscriptAsso.orf_id == ORF.id
                                                                                            ).group_by( 
                                                                                                        ORF.id 
                                                                                              )
        kozak_ctxt_orf_asso_df = pd.read_sql( kozak_ctxt_orf_asso_qr.statement,
                                              SQLManagerPRO.get_instance().get_engine() )
        SQLManagerPRO.get_instance().close_session()
        
        bed_full_content = bed_full_content.merge( kozak_ctxt_orf_asso_df,
                                                   on = 'id',
                                                   how = 'left',
                                                   validate = 'one_to_many' )
            
            
        
        # Save the content of the data frame
        # ----------------------------------
        # Replace missing values by '.'
        bed_full_content.fillna( value = self.BED_UNDEFINED_FIELD,
                                 inplace = True )
        
        # Reorder the rows by chromosome, then start and stop positions, then ID.
        # This allows the features to be ordered by (in this order):
        # - Chromosome (chrom)
        # - Start position (chromStart)
        # - End position (chromEnd)
        # - ID (name)
        bed_full_content = bed_full_content.sort_values( by = [ self.BED_HEADER_CHROM,
                                                                self.BED_HEADER_CHROM_START,
                                                                self.BED_HEADER_CHROM_END,
                                                                self.BED_HEADER_NAME ] )
        bed_full_content.reset_index( drop = True,
                                      inplace = True )
        
        # Create an entry for each ORF in the UTBEDContent table
        objects_to_insert = []
        for ( index, row ) in bed_full_content.iterrows():
            
            bed_col = '\t'.join( map( str,
                                      row[ self.BED_HEADER_LIST ].tolist() ) )
            bed_add_col = '\t'.join( map( str,
                                          row[ self.BED_HEADER_ADD_LIST ].tolist() ) )
            
            utbedcontent = UTBEDContent( orf_id = row[ 'id' ],
                                         bed_index = index,
                                         bed_col = bed_col,
                                         bed_add_col = bed_add_col )
            objects_to_insert.append( utbedcontent )
        
        SQLManagerPRO.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert,
                                                         process = 'BED content' )
        
        
    ## compute_color
    #  -------------
    #
    # This is a static method allowing to compute the RGB color 
    # to give to the feature depending on the ORF strand and 
    # splicing status.
    # 
    # @param row: Pandas Series - A row from a Pandas data frame.
    # 
    # @return color: String <R,G,B>- The color at RGB format.
    #
    @staticmethod
    def compute_color( row ):
        
        # Display the ORF in red if it is located on plus strand 
        # and in blue if it is located on the minus strand
        
        # If the ORF is spliced but the start and end 
        # positions of the exons are missing, 
        # then display an intermediate color.
        if ( row[ 'spliced' ] == True ):
            if ( row[ 'strand' ] == '+' ):
                return '255,100,0'
            elif ( row[ 'strand' ] == '-' ):
                return '0,200,255'
            else:
                return '0,0,0'
        else:
            return GenerateBEDContentStrategy.compute_color_from_strd( row[ 'strand' ] )
        
        
        
    ## compute_color_from_strd
    #  -----------------------
    #
    # This is a static method allowing to compute the RGB color 
    # to give to the feature depending on the ORF strand.
    # 
    # @param strd: String - The ORF strand.
    # 
    # @return color: String <R,G,B>- The color at RGB format.
    #
    @staticmethod
    def compute_color_from_strd( strd ):
        
        if ( strd == '+' ):
            return GenerateBEDContentStrategy.BED_DEFAULT_RGB_PLUS_STRAND 
        elif ( strd == '-' ):
            return GenerateBEDContentStrategy.BED_DEFAULT_RGB_MINUS_STRAND
        else:
            return '0,0,0'
        
        
        
    ## compute_block_starts
    #  --------------------
    #
    # This is a static method allowing to compute the value
    # of the 'blockStarts' column for a row of the data 
    # frame containing information related to spliced ORFs.
    # 
    # @param row: Pandas Series - A row from the 'spliced ORFs'
    #                             Pandas data frame.
    # 
    # @return block_starts: String - The blockStarts value.
    #
    @staticmethod
    def compute_block_starts( row ):
        
        # Get the appropriate exon start positions, depending on the ORF strand
        if ( row[ 'strand' ] == '+' ):
            block_starts = row[ 'splice_starts' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR )
            
        else:
            block_starts = row[ 'splice_ends' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR )
            # Get the position in the increasing order
            block_starts.reverse()
            
        # Compute the positions relative to the start position 
        # (which may correspond to the actual stop of the ORF)
        block_starts = map( lambda x: str( int( x ) - int( row[ 'start_pos' ] ) ),
                            block_starts )
        
        # Build a string of the start positions
        block_starts = ','.join( block_starts )
        
        return block_starts
        
        
        
    ## compute_block_sizes
    #  -------------------
    #
    # This is a static method allowing to compute the value
    # of the 'blockSizes' column for a row of the data 
    # frame containing information related to spliced ORFs.
    # 
    # @param row: Pandas Series - A row from the 'spliced ORFs'
    #                             Pandas data frame.
    # 
    # @return block_sizes: String - The blockSizes value.
    #
    @staticmethod
    def compute_block_sizes( row ):
        
        # Get the lists of start and end positions of the exons
        sp_starts = map( int,
                         row[ 'splice_starts' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
        sp_ends = map( int, 
                       row[ 'splice_ends' ].split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
        
        # Compute the genomic lengths of the exons
        exon_lengths = []
        for k in range( len( sp_starts ) ):
            exon_lengths.append( str( abs( sp_ends[ k ] - sp_starts[ k ] ) + 1 ) )
        
        # Reverse the order of exons for the ORFs located on the minus strand
        if ( row[ 'strand' ] == '-' ):
            exon_lengths.reverse()
        
        # Build a string of the exon lengths
        block_sizes = ','.join( exon_lengths )
        
        return block_sizes
        