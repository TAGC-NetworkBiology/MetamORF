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

## Source: Samandi et al., 2017
#
# NB: This file contains a header.
#     This file is expected to be in a tab separated values (TSV) format.
#
## Description of the columns of the raw data file:
#- [0]: Protein accession: ORF ID - String
#- [1]: Frame: Reading frame - String
#- [2]: Kozak: Kozak context - Integer
#- [3]: Gene: Gene symbol - String
#- [4]: Chromosome: Chromosome name - String
#- [5]: Start genomic coordinate - Genomic coordinates of the start codon 
#                                  (coordinates of the 1st nucleotide) - Integer
#- [6]: End genomic coordinate - Genomic coordinates of the stop codon 
#                                (coordinates of the last nucleotide) - Integer
#- [7]: Protein sequence: Protein sequence - String
#
# Supplementary information
# - The chromosome name is provided without 'chr' prefix.
# - The genomic coordinates are reported on GRCh38 or GRCm38 annotation.
#   (NCBI GCF_000001405.26, correspond to Ensembl v76 for H. sapiens,
#    NCBI GCF_000001635.22, correspond to Ensembl v75 for M. musculus).
# - For '+'-strand ORFs,
#     - the first nucleotide of the start codon is located at the start position (Start genomic coordinate).
#     - the last nucleotide of the stop codon is located at the stop position (End genomic coordinate).
# - For '-'-strand ORFs,
#     - the first nucleotide of the start codon is located at the stop position (End genomic coordinate).
#     - the last nucleotide of the stop codon is located at the start position (Start genomic coordinate).
# - The nucleic sequence is not provided.
# - NB: There is no information about the strand provided in the file.
# - The amino acid sequence includes the start codon and excludes the stop codon.
# - The ORF length is not provided.


# ===============================================================================
# File parser
# ===============================================================================


## Samandi2017
#  ===========
#
# This class inherits from ParserStrategy and allows to parse data 
# from Samandi et al., 2017.
#
class Samandi2017(ParserStrategy):
                
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ],
                          Constants.SPECIES_CATALOG[ Constants.MMUSCULUS ] ]
    
    # Headers (TSV file)
    HEADER_ORF_ID = 'Protein accession'
    HEADER_CHROMOSOME = 'Chromosome'
    HEADER_GENE_SYMBOL = 'Gene'
    
    HEADER_START_POS = 'Start genomic coordinate'
    HEADER_STOP_POS = 'End genomic coordinate'
    
    HEADER_ORF_AA_SEQUENCE = 'Protein sequence'
    HEADER_KOZAK_CONTEXT = 'Kozak'
    
    HEADER_FRAME = 'Frame'
    
    HEADER_LIST = [ HEADER_ORF_ID, HEADER_CHROMOSOME, HEADER_GENE_SYMBOL, HEADER_START_POS, HEADER_STOP_POS,
                    HEADER_ORF_AA_SEQUENCE, HEADER_KOZAK_CONTEXT, HEADER_FRAME ]
    
    # Constants
    DATA_SOURCE = 'Samandi2017'
    
    DOI = '10.7554/eLife.27860'
    SOURCE_DESCRIPTION = { Constants.HSAPIENS : 'Samandi et al., eLIFE, 2017. "Homo sapiens alternative protein predictions based on RefSeq GRCh38 (hg38) based on assembly GCF_000001405.26. Release date 01/01/2016.". The TSV file has been used.',
                           Constants.MMUSCULUS : 'Samandi et al., eLIFE, 2017. "Mus musculus alternative protein predictions based on annotation version GRCm38. Release date 01/01/2016". The TSV file has been used.' }
    URL = 'https://elifesciences.org/articles/27860'
        
    PREDICTED = True
    RIBO_SEQ = False
    CELL_CONTEXT = None
    
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = { Constants.HSAPIENS : Constants.ANNOTATION_VERSION_GRCH38,
                           Constants.MMUSCULUS : Constants.ANNOTATION_VERSION_GRCM38 }
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = { Constants.HSAPIENS : 'GRCh38 (hg38), RefSeq assembly GCF_000001405.26.',
                               Constants.MMUSCULUS : 'GRCm38.p2, RefSeq assembly GCF_000001635.22.' }
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = { Constants.HSAPIENS : '76',
                        Constants.MMUSCULUS : '75' }
    


    ## Constructor of Samandi2017
    #  --------------------------
    #
    def __init__( self, data_path ):
        
        ParserStrategy.__init__( self, data_path )

    
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
                                       ' whilst data store in this database is related to ' + sp )
        
        # Get the appropriate annotation version and description
        else:
            annotation_version = self.ANNOTATION_VERSION[ sp ]
            annotation_description = self.ANNOTATION_DESCRIPTION[ sp ]
            ensembl_release = self.ENSEMBL_RELEASE[ sp ]
        
        # Get the content of the file
        self.import_file_content( file_sep = '\t' )
        
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
        ensembl_db = ParserStrategy.get_ensembl_db( ensembl_release )
        
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
        # Initialize the list of objects to insert
        objects_to_insert = []
        
        # All ORFs associated with multiple chromosomes are discarded from insertion. Keep the count of these ORFs.
        discarded_orfs = 0 
        

        ## DataSource
        #  ----------
        datasource = DataSource( name = Samandi2017.DATA_SOURCE,
                                 doi = Samandi2017.DOI,
                                 description = Samandi2017.SOURCE_DESCRIPTION[ sp ],
                                 url = Samandi2017.URL, 
                                 annotation_version = annotation_version,
                                 ensembl_release = ensembl_release,
                                 annotation_description = annotation_description )
        objects_to_insert.append( datasource )
        
        
        # Parse the content of the file and save it in appropriate objects
        start_time = datetime.datetime.now()
        for ( index, row ) in self.file_content.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Assign useful information to new variables
            chr_name = row[ Samandi2017.HEADER_CHROMOSOME ]
            
            # Skip the ORFs reported as being on multiple chromosomes
            if ( len( chr_name.split( ',' ) ) > 1 ):
                discarded_orfs += 1
            
            elif ( len( chr_name.split( '.' ) ) > 1 ):
                discarded_orfs += 1
            
            else:
                # Assign other useful information to new variables
                orf_id = row[ Samandi2017.HEADER_ORF_ID ]
                symbol = row[ Samandi2017.HEADER_GENE_SYMBOL ]
                # If the gene is associated with several gene symbols, concatenate them
                symbol = '_'.join( sorted( str( symbol ).split(' ') ) )
                # If the symbol get by concatenation is too long, use the unknown gene prefix
                if ( len( symbol ) > Constants.MAX_LEN_STRING ):
                    symbol = Constants.PREFIX_UNKNOWN_GENE + chr_name
                
                transcript_id = None
    
                orf_start = row[ Samandi2017.HEADER_START_POS ]
                orf_stop = row[ Samandi2017.HEADER_STOP_POS ]
                orf_strand = None
                
                # Reset the chr_name, symbol and transcript_id if necessary
                ( chr_name, symbol, transcript_id ) = self.initialize_ids( ensembl_db = ensembl_db,
                                                                           orf_id = orf_id,
                                                                           chr_name = chr_name, 
                                                                           symbol = symbol, 
                                                                           transcript_id = None, 
                                                                           orf_start = orf_start, 
                                                                           orf_stop = orf_stop, 
                                                                           orf_strand = orf_strand, 
                                                                           index = index )
                
                ## DSORF
                #  -----
                dsorf = DSORF( id = autoincrement,
                               data_source = datasource.name,
                               chromosome = chr_name,
                               raw_strand = orf_strand,
                               raw_start_pos = orf_start,
                               raw_stop_pos = orf_stop,
                               spliced = None,
                               raw_splice_starts = None,
                               raw_splice_ends = None,
                               spliced_parts_count = None )
                
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
                                             raw_cds_stop_pos = None )
                
                # Add the newly created transcript to the list of objects to insert and keep track of it
                all_dstranscripts[ dstranscript ] = dstranscript
                objects_to_insert.append( dstranscript )
                
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
                
                
                ## DSORFTranscriptAsso
                #  -------------------                
                orf_seq_aa = row[ Samandi2017.HEADER_ORF_AA_SEQUENCE ]
                if ParserStrategy.is_empty( orf_seq_aa ):
                    orf_len_aa = None
                    orf_len_nt = None
                else:
                    orf_len_aa = len( orf_seq_aa )
                    orf_len_nt = ( orf_len_aa + 1 ) * 3
                
                
                if ( row[ Samandi2017.HEADER_FRAME ] != '1' ):
                    orf_annot = 'alternative frame' 
                else:
                    orf_annot = None
                
                dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                           data_source = datasource.name,
                                                           transcript_id = dstranscript.id,
                                                           uniq_orf_id = dsorf.id,
                                                           predicted = Samandi2017.PREDICTED,
                                                           ribo_seq = Samandi2017.RIBO_SEQ,
                                                           cell_context = Samandi2017.CELL_CONTEXT,
                                                           orf_id = orf_id,
                                                           raw_sequence = None,
                                                           raw_sequence_aa = orf_seq_aa,
                                                           start_codon_seq = None,
                                                           kozak_context = row[ Samandi2017.HEADER_KOZAK_CONTEXT ],
                                                           orf_length_nt = orf_len_nt,
                                                           orf_length = orf_len_aa,
                                                           provided_category = orf_annot,
                                                           ms_info = None,
                                                           orf_score = None,
                                                           phylocsf = None,
                                                           phastcons = None,
                                                           floss = None,
                                                           floss_class = None )
            
                # Otherwise, add the newly created DSORFTranscriptAsso to the list of objects to insert and keep track of it
                all_dsota[ dsorftranscriptasso ] = dsorftranscriptasso
    
                # Add it to the list of objects to insert in the database
                objects_to_insert.append( dsorftranscriptasso )
                    
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
                
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'Samandi2017.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
                    
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
                    

        if discarded_orfs > 0:              
            Logger.get_instance().warning( str( discarded_orfs ) + ' ORFs from ' + self.data_source + 
                                           ' have been discarded as they were reported as being' +
                                           ' located on several chromosomes.' +
                                           ' Warning code: ' + LogCodes.WARN_DISCARD_ORF + '.' )
                    
        return objects_to_insert
            