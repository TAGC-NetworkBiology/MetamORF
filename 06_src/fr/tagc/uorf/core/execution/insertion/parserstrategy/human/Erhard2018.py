# -*- coding: utf-8 -*-

import pandas as pd
import datetime


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.execution.insertion.ParserStrategy import ParserStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log import *


# ===============================================================================
# Description of the file parsed using this class
# ===============================================================================

## Source: Erhard et al., 2018
#
# NB: This file contains a header.
#     This file is expected to be in a comma separated values (CSV) format.
#
## Description of the columns of the raw data file:
#- [0]: ORF Type: ORF category - String
#- [1]: Total reads (HSV-1): Expression level for the ORF in HSV-1 infected HFF 
#                            (in reads per kilobase million, RPKM) - Float
#- [2]: Total reads (HCMV): Expression level for the ORF in HCMV infected HFF 
#                           (in reads per kilobase million, RPKM) - Float
#- [3]: Length (amino acids): ORF length (in amino acids) - Integer
#- [4]: Peptides (MHC-I Peptidome): Number of peptides detected by MS in the MHC-I peptidome - Integer
#- [5]: Peptide (Whole proteome): Number of peptides detected by MS in the whole proteome - Integer
#- [6]: Peptides (MHC-I Peptidome - new): Number of peptides detected by MS
#                                         in the novel MHC-I peptidome - Integer
#- [7]: Detected (Price): Was this ORF detected using Price algorithm? - Boolean (0/1)
#- [8]: Detected (ORF-RATER): Was this ORF detected using ORF-RATER algorithm? - Boolean (0/1)
#- [9]: Detected (Rp-Bp): Was this ORF detected using the RP-BP algorithm? - Boolean (0/1)
#- [10]: Location (hg19): Information about exon locations - String
#        Information formatted as: Chr name (without 'chr') + strand 
#                               + [ start + '-' + end ] ('|'-delimited values when several starts and ends)
#                               Start and end genomic coordinates.
#                    e.g. for 10+:696050-696118|696230-696382|696727-697173
#                                - this ORF is located on chromosome 10, + strand
#                                - the first nucleotide of the start codon (1s exon) is located at: 696050 + 1 = 696051
#                                - the last nucleotide of the stop codon (last exon) is located at: 697173
#                                - the first nucleotides of each exons are located at:
#                                        - 6960510 + 1 = 69605 
#                                        - 696230 + 1 = 696231
#                                        - and 696727 + 1 = 696728
#                                - the last nucleotides of each exons are located at:
#                                        - 696118
#                                        - 696382
#                                        - 697173
#                                - there are 68, 152 and 446 nucleotides in each exon, i.e. 666 nucleotides in the ORF 
#                                  => 222 - 1 = 221 amino acids (including the start aa but not the stop)
#
# Supplementary information
# - The chromosome name is provided without 'chr' prefix.
# - The genomic coordinates are reported on GRCh37 (Ensembl v75) annotation.
# - For '+'-strand ORFs,
#     - the first nucleotide of the start codon is located at the start position + 1.
#     - the last nucleotide of the stop codon is located at the stop position.
#  and, for each exon,
#     - the first nucleotide of the exon is located at the provided start position + 1.
#     - the last nucleotide of the exon is located at the provided stop position.
#     e.g. for 10+:696050-696118|696230-696382|696727-697173
#                the exon 1 has its first nucleotide at 696051 and its last nucleotide at 696118
#                the exon 2 has its first nucleotide at 696231 and its last nucleotide at 696382
#                the exon 3 has its first nucleotide at 696728 and its last nucleotide at 697173
# - For '-'-strand ORFs,
#     - the first nucleotide of the start codon is located at the stop position
#     - the last nucleotide of the stop codon is located at start position + 1
#  and, for each exon,
#     - the first nucleotide of the exon is located at the provided start position + 1.
#     - the last nucleotide of the exon is located at the provided stop position.
#     /!\ All the exonic position ARE REVERTED for '-' strand!
#     e.g. for 10-:134598419-134598674|134598783-134598956|134599046-134599452
#                the exon 1 has its first nucleotide at 134599452 and its last nucleotide at 134599047
#                the exon 2 has its first nucleotide at 134598956 and its last nucleotide at 134598784
#                the exon 3 has its first nucleotide at 134598674 and its last nucleotide at 134598420
# - The nucleic sequence is not provided.
# - The amino acid sequence is not provided.
# - The ORF length is in amino acids and include the start aa but not the stop.


# ===============================================================================
# File parser
# ===============================================================================


## Erhard2018
#  ==========
#
# This class inherits from ParserStrategy and allows to parse data 
# from Erhard et al., 2018.
#
class Erhard2018( ParserStrategy ):
    
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ] ]

    # Headers
    HEADER_LOCATION_COLUMN = 'Location (hg19)'
    
    HEADER_ORF_CATEGORY = 'ORF Type'
    HEADER_ORF_LENGTH = 'Length (amino acids)'
    
    HEADER_ORF_MHCI_PEPTIDOME = 'Peptides (MHC-I Peptidome)'
    HEADER_ORF_WHOLE_PROTEOME = 'Peptide (Whole proteome)'
    HEADER_ORF_NOVEL_MHCI_PEPTIDOME = 'Peptides (MHC-I Peptidome - new)'
        
    HEADER_LIST = [ HEADER_LOCATION_COLUMN, HEADER_ORF_CATEGORY, HEADER_ORF_LENGTH,
                    HEADER_ORF_MHCI_PEPTIDOME, HEADER_ORF_WHOLE_PROTEOME, 
                    HEADER_ORF_NOVEL_MHCI_PEPTIDOME ]
    
    # Constants
    DATA_SOURCE = 'Erhard2018'
    
    DOI = '10.1038/nmeth.4631'
    SOURCE_DESCRIPTION = 'Erhard et al., Nat. Meth., 2018. "Supplementary Table 3: Identified ORFs (Union of all ORFs detected either by PRICE,RP-BP or ORF-RATER, or contained in the annotation (Ensembl V75))". The two first lines of the file have to be manually removed.'
    URL = 'https://www.nature.com/articles/nmeth.4631'
    
    PREDICTED = False
    RIBO_SEQ = True
    CELL_CONTEXT = 'Primary human fibroblast (HFF)'
    
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = Constants.ANNOTATION_VERSION_GRCH37
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = 'Ensembl version 75.'
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = '75'
    


    ## Constructor of Erhard2018
    #  -------------------------
    #
    def __init__( self, data_path ):
        ParserStrategy.__init__( self, data_path )
      
        
    ## parse_last_column
    #  -----------------
    #
    # This static method aims to parse the content of the last column of the file.
    # This column contains information about the location of the ORF, which includes its chromosome,
    # its stand, its splacing status and the genomic locations of the start and end of the exonic 
    # parts of the ORF. All of these informations are stored in a dictionary.
    #
    # @param location: String - The content of the last column of the file.
    #
    # @return parsed_col: Dicionary - A dictionary that contains:
    #                                 - chr_name: String - The chromosome name on which is located the ORF.
    #                                 - strand: String - The strand of the ORF.
    #                                 - start: Integer - The location of the first nucleotide of the start codon.
    #                                 - stop: Integer - The location of the last nucleotide of the last codon.
    #                                 - spliced_parts_count: The number of "exonic parts" in the ORF.
    #                                 - splice_starts: String - The genomic coordinates of the starts.
    #                                 - splice_stops: String - The genomic coordinates of the ends.
    #
    @staticmethod
    def parse_last_column( location ):
        
        # The result are stored in a dictionary
        parsed_col = {}
        
        # First, split the content of the column to separate the genomic coordinates from the other information
        location = location.split(':')
        
        # Get the chromosome name
        parsed_col[ 'chr_name' ] = location[ 0 ][ : -1 ]
        
        # Get the strand
        parsed_col[ 'strand' ] = location[ 0 ][ -1 : ]

        # Get the start and stop codon locations as well as the genomic coordinates of the exons
          # Parse the coordinates as a list
        coordinates = []
        coord = location[ 1 ].split( '|' )
        
        for c in coord:
            coordinates.append( c.split( '-' ) )
        
          # Get the start location
        parsed_col[ 'start' ] = str( int( coordinates[ 0 ][ 0 ] ) + 1 )
        
          # Get the stop location
        parsed_col[ 'stop' ] = str( int( coordinates[ -1 ][ -1 ] ) )
        
          # Get the number of "exonic" parts in the ORF
        parsed_col[ 'spliced_parts_count' ] = len( coord )
        
          # Get the splicing status and the coordinates of the exons
        if ( len( coordinates ) == 1 ):
            parsed_col[ 'spliced' ] = False
            splice_starts = None
            splice_stops = None
            
        else:
            parsed_col[ 'spliced' ] = True
                        
            # Get a string of start and end locations of exons (separated by '_')
            splice_starts = []
            splice_stops = []
            
            for coord in coordinates:
                splice_starts.append( str( int( coord[ 0 ] ) + 1 ) )
                splice_stops.append( str( coord[ 1 ] ) )
            
            # If the ORF is on the '-' strand, reverse the order of the coordinates 
            # and exchange start and stop positions
            if ( parsed_col[ 'strand' ] == '-' ):
                ( splice_starts, splice_stops ) = ( splice_stops[ ::-1 ], splice_starts[ ::-1 ] )
            
            # Concatenate respectively the list of start and end position of the exons
            splice_starts = Constants.ORF_SPLICING_COORD_SEPARATOR.join( splice_starts )
            splice_stops = Constants.ORF_SPLICING_COORD_SEPARATOR.join( splice_stops )
            
        parsed_col[ 'splice_starts' ] = splice_starts
        parsed_col[ 'splice_stops' ] = splice_stops
        
        return parsed_col


    ## execute
    #  -------
    #
    # Execute the parsing strategy.
    # See the execute() method documentation of the ParserStrategy metaclass for 
    # more information about the main steps of the algorithm run in this method.
    #
    # @return objects_to_insert: List - List of objects to insert in the database.
    #
    # @throw DenCellORFException: When this parser cannot be used for the species of the database.
    # @throw DenCellORFException: When an exception has been raised checking the headers of the file.
    #
    def execute( self ):
        
        # Check this parser may be used for the species in the database
        sp = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        if ( sp not in self.AUTHORIZED_SPECIES ):
            raise DenCellORFException( 'The parser ' + self.data_source + 
                                       ' has been build to parse data from ' + 
                                       ', '.join( self.AUTHORIZED_SPECIES ) + 
                                       ' whilst data store in this database is related to ' + sp + '.'  )
        
        # Get the content of the file
        self.import_file_content( file_sep = ',' )
        
        # Check the headers of the file
        try:
            self.check_headers()
        except DuplicateHeaderException as e:
            Logger.get_instance().warning( e.get_message() +
                                           ' Warning code: ' + LogCodes.WARN_HEADER_DUPL + '.' )
                
        # Assign new variables to access some objects of the DataManager data dictionary
        all_dsorfs = DataManager.get_instance().get_data( Constants.DM_ALL_DSORFS_FOR_SOURCE )
        all_dstranscripts = DataManager.get_instance().get_data( Constants.DM_ALL_DSTRANSCRIPTS_FOR_SOURCE )
        all_dsota = DataManager.get_instance().get_data( Constants.DM_ALL_DSORFTRANSCRIPTASSO_FOR_SOURCE )
        
        autoincrement = DataManager.get_instance().get_data( Constants.DM_AUTOINCREMENT )
        
        # Get the appropriate Ensembl database to recover missing gene IDs
        ensembl_db = ParserStrategy.get_ensembl_db( Erhard2018.ENSEMBL_RELEASE )
                
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
        # Initialize the list of objects to insert
        objects_to_insert = []


        ## DataSource
        #  ----------
        datasource = DataSource( name = Erhard2018.DATA_SOURCE,
                                 doi = Erhard2018.DOI,
                                 description = Erhard2018.SOURCE_DESCRIPTION,
                                 url = Erhard2018.URL, 
                                 annotation_version = Erhard2018.ANNOTATION_VERSION,
                                 ensembl_release = Erhard2018.ENSEMBL_RELEASE,
                                 annotation_description = Erhard2018.ANNOTATION_DESCRIPTION )
        objects_to_insert.append( datasource )
        
        
        # Parse the content of the file and save it in appropriate objects
        start_time = datetime.datetime.now()
        for ( index, row ) in self.file_content.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Assign useful information to new variables
            location = Erhard2018.parse_last_column( row[ Erhard2018.HEADER_LOCATION_COLUMN ] )
            chr_name = location[ 'chr_name' ]
            
            orf_start = location[ 'start' ]
            orf_stop = location[ 'stop' ]
            orf_strand = location[ 'strand' ]
            
            orf_spliced = location[ 'spliced' ]
            orf_splice_starts = location[ 'splice_starts' ]
            orf_splice_ends = location[ 'splice_stops' ]
            orf_spliced_parts_count = location[ 'spliced_parts_count' ]
            
              # As there is no ORF ID in this file, an ORF ID is created in the following format:
              #    (index + 2) + '_' + Chromosome + ':' + start + '-' + stop + ':' + strand
            orf_id = ( str( index + 2 ) + '_' + 'chr' + chr_name + ':' +
                       location[ 'start' ] + '-' + location[ 'stop' ] + ':' +
                       location[ 'strand' ] )
            
              # Replace too long strings of coordinates by "TOO_LONG"
            if ( ( orf_spliced != None )
                 and ( len( str( orf_splice_starts ) ) > Constants.MAX_LEN_STRING ) ):
                Logger.get_instance().warning( 'The splicing information for the ORF "' + orf_id + 
                                               '" in ' + self.data_source +
                                                ' was too long to be store in the database (raw splice starts: ' +
                                                orf_splice_starts + ', raw splice ends: ' + orf_splice_ends + 
                                                '), hence these values will be changed for "' + 
                                                Constants.REPLACE_TOO_LONG_STRINGS + '".' +
                                                ' Warning code: ' + LogCodes.WARN_SPLIC_TOOLONG + '.' )
                orf_splice_starts = Constants.REPLACE_TOO_LONG_STRINGS
                orf_splice_ends = Constants.REPLACE_TOO_LONG_STRINGS
            
            # Reset the chr_name, symbol and transcript_id if necessary
            ( chr_name, symbol, transcript_id ) = self.initialize_ids( ensembl_db = ensembl_db,
                                                                       orf_id = orf_id,
                                                                       chr_name = chr_name, 
                                                                       symbol = None, 
                                                                       transcript_id = None, 
                                                                       orf_start = orf_start, 
                                                                       orf_stop = orf_stop, 
                                                                       orf_strand = orf_strand, 
                                                                       index = index,
                                                                       log_symb_from_tr = False,
                                                                       log_single_symb_from_pos = False )
            
            
            ## DSORF
            #  -----
            dsorf = DSORF( id = autoincrement,
                           data_source = datasource.name,
                           chromosome = chr_name,
                           raw_strand = orf_strand,
                           raw_start_pos = orf_start,
                           raw_stop_pos = orf_stop,
                           spliced = orf_spliced,
                           raw_splice_starts = orf_splice_starts,
                           raw_splice_ends = orf_splice_ends,
                           spliced_parts_count = orf_spliced_parts_count )
            
            # If this ORF already exists, get the existing one
            existing_dsorf = all_dsorfs.get( dsorf )
            if existing_dsorf:
                dsorf = existing_dsorf
                
            # Otherwise, add the newly created ORF to the list of objects to insert and keep track of it
            else:
                all_dsorfs[ dsorf ] = dsorf
                objects_to_insert.append( dsorf )
                
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
                
            
            ## Gene
            #  ----
            # Try to get the gene object from its symbol and its chromosome name
            ( gene, new_obj_to_insert ) = self.get_gene_from_symbol( orf_id = orf_id,
                                                                     symbol = symbol,
                                                                     chr_name = chr_name )
            objects_to_insert += new_obj_to_insert
            
            
            ## DSTranscript
            #  ------------
            dstranscript = DSTranscript( id = autoincrement,
                                         transcript_id = transcript_id,
                                         data_source = datasource.name,
                                         gene_id = gene.gene_id,
                                         strand = None,
                                         raw_start_pos = None,
                                         raw_end_pos = None,
                                         raw_cds_start_pos = None,
                                         raw_cds_stop_pos = None)
    
            # Add the newly created transcript to the list of objects to insert and keep track of it
            all_dstranscripts[ dstranscript ] = dstranscript
            objects_to_insert.append( dstranscript )
                
            # Increase the autoincrement value for ID of 1
            autoincrement += 1
            
            
            ## DSORFTranscriptAsso
            #  -------------------
            # Get the mass spectrometry information about this ORF
            orf_len = row[ Erhard2018.HEADER_ORF_LENGTH ]
            if ParserStrategy.is_empty( orf_len ):
                orf_len = None
                orf_len_nt = None
            else:
                orf_len = int( orf_len )
                orf_len_nt = ( orf_len + 1 ) * 3
            
            if ( row[ Erhard2018.HEADER_ORF_MHCI_PEPTIDOME ] 
                 or row[ Erhard2018.HEADER_ORF_WHOLE_PROTEOME ]
                 or row[ Erhard2018.HEADER_ORF_NOVEL_MHCI_PEPTIDOME ] ):
                ms_info = True
            else:
                ms_info = False
            
            dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                       data_source = datasource.name,
                                                       transcript_id = dstranscript.id,
                                                       uniq_orf_id = dsorf.id,
                                                       predicted = Erhard2018.PREDICTED,
                                                       ribo_seq = Erhard2018.RIBO_SEQ,
                                                       cell_context = Erhard2018.CELL_CONTEXT,
                                                       orf_id = orf_id,
                                                       raw_sequence = None,
                                                       raw_sequence_aa = None,
                                                       start_codon_seq = None,
                                                       kozak_context = None,
                                                       orf_length_nt = orf_len_nt,
                                                       orf_length = orf_len,
                                                       provided_category = row[ Erhard2018.HEADER_ORF_CATEGORY ],
                                                       ms_info = None,
                                                       orf_score = None,
                                                       phylocsf = None,
                                                       phastcons = None,
                                                       floss = None,
                                                       floss_class = None )
                
            # Add the newly created DSORFTranscriptAsso to the list of objects to insert and keep track of it
            all_dsota[ dsorftranscriptasso ] = dsorftranscriptasso

            # Add it to the list of objects to insert in the database
            objects_to_insert.append( dsorftranscriptasso )
                
            # Increase the autoincrement value for ID of 1
            autoincrement += 1
            
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'Erhard2018.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
                    
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
    
        return objects_to_insert
    