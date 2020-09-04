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

## Source: Laumont et al., 2016
#
# NB: This file contains a header.
#     This file is expected to be in a comma-separated values (CSV) format.
#
## Description of the columns of the raw data file:
#- [0]: Peptide: ORF sequence (in amino acids) - String
#- [1]: Chromosome: Chromosome name (without 'chr' prefix) - String
#- [2]: Start: Genomic position of the start codon - Integer
#- [3]: Stop: Genomic position of the stop codon - Integer
#- [4]: Peptide_length_(aa): Peptide length in amino acids - Integer
#- [5]: Peptide_strand: Peptide strand - String
#- [6]: Splicing_status: Is the ORF spliced? - Boolean
#- [7]: Cryptic_status: Category of the ORF - String
#- [8]: Peptide_reading_frame: Is the ORF in frame or out of frame? - String
#- [9]: Nterminal_extension: ? - Boolean
#- [10]: HLA_allele
#- [11]: IC50 (nM): Predicted binding affinity of the MAPs for the four HLA-A and -B allotypes 
#                   of subject 4 - Float
#- [12]: Ensembl_gene_id: Ensembl gene ID - String
#- [13]: Gene_strand: Gene strand - String
#- [14]: Gene_biotype: Gene biotype - String
#- [15]: Gene_expression_(FPKM): Expression level (FPKM) - Float
#- [16]: Ensembl_transcript_id: Ensembl transcript ID - String
#- [17]: Transcript_expression_(FPKM): Expression level (FPKM) - Float
#- [18]: Ensembl_protein_id: Ensembl protein ID - String
#- [19]: Mascot_score: Mascot score (represents the confidence level of a peptide assignation) - Float
#- [20]: Post_translational_modification: PTM - String
#- [21]: Number_of_replicates_with_positive_detection: Number of replicates with a 
#                                                      positive detection - Integer
#- [22]: Detection_intensity_replicate_1: ? - Float
#- [23]: Detection_intensity_replicate_2: ? - Float
#- [24]: Detection_intensity_replicate_3: ? - Float
#- [25]: Detection_intensity_replicate_4: ? - Float
#
# Supplementary information
# - The chromosome name is provided without 'chr' prefix.
# - The genomic coordinates are reported on GRCh37 (Ensembl v75) annotation.
# - For '+'-strand ORFs,
#     - the first nucleotide of the codon encoding the FIRST AMINO ACID is located at the start position +1 (Start + 1),
#       suggesting the first nucleotide of the start codon should be at the start position + 1 - 3 (i.e. Start - 2).
#     - the last nucleotide of the codon encoding the LAST AMINO ACID is located at the stop position (Stop),
#       suggesting the last nucleotide of the stop codon should be at the stop position + 3 (Stop + 3).
# - For '-'-strand ORFs,
#     - the first nucleotide of the codon encoding the FIRST AMINO ACID is located at the stop position (Stop),
#       suggesting the first nucleotide of the start codon should be at the stop position +3 (Stop +3).
#     - the last nucleotide of the codon encoding the LAST AMINO ACID is located at the start position + 1 (Start + 1),
#       suggesting the last nucleotie of the stop codon should be at the start position + 1 - 3 (i.e. Start - 2).
# - The nucleic sequence is not provided.
# - The amino acid sequence excludes both the start and the stop codons.
# - The ORF length (Peptide_length_(aa)) in amino acids excludes both the start and the stop codons.



# ===============================================================================
# File parser
# ===============================================================================


## Laumont2016
#  ===========
#
# This class inherits from ParserStrategy and allows to parse data 
# from Laumont et al., 2016.
#
class Laumont2016( ParserStrategy ):
                
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ] ]
    
    # Headers
    HEADER_CHROMOSOME = 'Chromosome'
    HEADER_GENE_ID = 'Ensembl_gene_id'
    HEADER_TRANSCRIPT_ID = 'Ensembl_transcript_id'
    
    HEADER_STRAND = 'Peptide_strand'
    HEADER_START_POS = 'Start'
    HEADER_STOP_POS = 'Stop'
    HEADER_SPLICED = 'Splicing_status'
        
    HEADER_ORF_AA_SEQUENCE = 'Peptide'
    HEADER_ORF_CATEGORY = 'Cryptic_status'
    HEADER_ORF_ALT_FRAME = 'Peptide_reading_frame'
    HEADER_MS_DETECTION = 'Number_of_replicates_with_positive_detection'
    HEADER_ORF_LENGTH = 'Peptide_length_(aa)'
    
    HEADER_HLA_ALLELE = 'HLA_allele'
    
    HEADER_LIST = [ HEADER_CHROMOSOME, HEADER_GENE_ID, HEADER_TRANSCRIPT_ID, HEADER_STRAND, 
                    HEADER_START_POS, HEADER_STOP_POS, HEADER_SPLICED, HEADER_ORF_AA_SEQUENCE, 
                    HEADER_ORF_CATEGORY, HEADER_ORF_ALT_FRAME, HEADER_MS_DETECTION, 
                    HEADER_ORF_LENGTH, HEADER_HLA_ALLELE ]
    
    # Constants
    DATA_SOURCE = 'Laumont2016'
    
    DOI = '10.1038/ncomms10238'
    SOURCE_DESCRIPTION = 'Laumont et al., Nat. Commun., 2016. "Supplementary Data 2:  List of all cryptic MAPs detected in subject 1. Table presenting the genomic and proteomic features of all cryptic MAPs". The two first rows have to be manually removed.'
    URL = 'https://www.nature.com/articles/ncomms10238'
        
    PREDICTED = False
    RIBO_SEQ = True
    CELL_CONTEXT = 'B cells'
        
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = Constants.ANNOTATION_VERSION_GRCH37
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = 'GRCh37.75'
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = '75'
    

    ## Constructor of Laumont2016
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
                                       ' whilst data store in this database is related to ' + sp + '.' )
        
        
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
        all_utdstranscriptgeneconflict = DataManager.get_instance().get_data( Constants.DM_ALL_UTDSTRANSCRIPTGENECONFLICT )
         
        autoincrement = DataManager.get_instance().get_data( Constants.DM_AUTOINCREMENT )
        
        # Get the appropriate Ensembl database to recover missing gene IDs
        ensembl_db = ParserStrategy.get_ensembl_db( self.ENSEMBL_RELEASE )
        
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
        # Initialize the list of objects to insert
        objects_to_insert = []


        ## DataSource
        #  ----------
        datasource = DataSource( name = Laumont2016.DATA_SOURCE,
                                 doi = Laumont2016.DOI,
                                 description = Laumont2016.SOURCE_DESCRIPTION,
                                 url = Laumont2016.URL,
                                 annotation_version = Laumont2016.ANNOTATION_VERSION,
                                 ensembl_release = Laumont2016.ENSEMBL_RELEASE,
                                 annotation_description = Laumont2016.ANNOTATION_DESCRIPTION )
        objects_to_insert.append( datasource )
        
        
        # Parse the content of the file and save it in appropriate objects
        start_time = datetime.datetime.now()
        for ( index, row ) in self.file_content.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Assign useful information to new variables
            chr_name = row[ Laumont2016.HEADER_CHROMOSOME ]
              # As there is no ORF ID in this file, an ORF ID is created in the following format:
              #    (index + 2) + '_' + Chromosome + ':' + start + '-' + stop + ':' + strand
            orf_id = ( str( index + 2 ) + '_' + 
                       'chr' + str( row[ Laumont2016.HEADER_CHROMOSOME ] ) + ':' +
                       str( row[ Laumont2016.HEADER_START_POS ] ) + '-' + 
                       str( row[ Laumont2016.HEADER_STOP_POS ] ) + ':' +
                       row[ Laumont2016.HEADER_STRAND ] )
            symbol = row[ Laumont2016.HEADER_GENE_ID ]
            transcript_id = row[ Laumont2016.HEADER_TRANSCRIPT_ID ]
            
            orf_strand = row[ Laumont2016.HEADER_STRAND ]
            orf_start = int( row[ Laumont2016.HEADER_START_POS ] ) - 2
            orf_stop = int( row[ Laumont2016.HEADER_STOP_POS ] ) + 3
            
            if ( row[ Laumont2016.HEADER_SPLICED ] == 'TRUE' ):
                orf_spliced = True
            elif ( row[ Laumont2016.HEADER_SPLICED ] == 'FALSE' ):
                orf_spliced = False
            else:
                orf_spliced = None
            
            # Reset the chr_name, symbol and transcript_id if necessary
            ( chr_name, symbol, transcript_id ) = self.initialize_ids( ensembl_db = ensembl_db,
                                                                       orf_id = orf_id,
                                                                       chr_name = chr_name, 
                                                                       symbol = symbol, 
                                                                       transcript_id = transcript_id, 
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
                           spliced = orf_spliced,
                           raw_splice_starts = None,
                           raw_splice_ends =  None,
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
            
            # If this transcript already exists, get the existing one
            existing_dstranscript = all_dstranscripts.get( dstranscript )
            if existing_dstranscript:
                
                # If a conflict about the genes associated with this transcript has already been found, 
                # get the UTDSTranscriptGeneConflict entry that keep record of it
                utdstranscriptgeneconflict = UTDSTranscriptGeneConflict( transcript_id = dstranscript.transcript_id,
                                                                         data_source = dstranscript.data_source )
                
                existing_utdstranscriptgeneconflict = all_utdstranscriptgeneconflict.get( utdstranscriptgeneconflict )
                if existing_utdstranscriptgeneconflict:
                    # Get the list of gene already reported as being associated with the transcript
                    gene_id_conflicts = existing_utdstranscriptgeneconflict.gene_ids.split( Constants.UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS )
                else:
                    gene_id_conflicts = None
                
                # Update the existing transcript using information from the current entry if necessary
                try:
                    existing_dstranscript.update( dstranscript, gene_id_conflicts )
                    
                except DenCellORFTrUpdateException as e:
                    Logger.get_instance().error( 'The transcript ' + transcript_id + ' (from ' + self.data_source +
                                                 ') has been found several time with different properties: ' + e.get_message() +
                                                 ' Error code: ' + LogCodes.ERR_DCORF_CONFL_DSTR + '.',
                                                 ex = False )
                    
                    # If a conflict has been found on the gene ID, associate this transcript
                    # to its new "conflict" gene ID
                    new_gene_id = e.get_gene_id()
                    
                    if new_gene_id:
                        # Get the lists of all the genes that have been found conflicting
                        if e.get_conflict_list():
                            # If an UTDSTranscriptGeneConflict entry was already existing, update the list of gene IDs,
                            # Otherwise, add the new entry to the list of objects to insert
                            if existing_utdstranscriptgeneconflict:
                                existing_utdstranscriptgeneconflict.gene_ids = Constants.UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS.join( e.get_conflict_list() )
                                utdstranscriptgeneconflict = existing_utdstranscriptgeneconflict
                            
                            else:
                                utdstranscriptgeneconflict.gene_ids = Constants.UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS.join( e.get_conflict_list() )
                                all_utdstranscriptgeneconflict[ utdstranscriptgeneconflict ] = utdstranscriptgeneconflict
                                objects_to_insert.append( utdstranscriptgeneconflict )
                            
                        else:
                            raise DenCellORFException( 'sORFs_org.execute(): The gene ID associated with the DSTranscript with ID "' +
                                                       existing_dstranscript.id + '" has been updated whilst the list of genes related to the' +
                                                       ' DSTranscript cannot be get. Please contact the developer if you see this message.' )
                    
                        # Get the appropriate gene object from this new gene ID
                        ( gene, new_obj_to_insert ) = self.get_gene_from_conflict_id( conflict_symbol = new_gene_id,
                                                                                      chr_name = chr_name )
                        
                        # Add the newly created object to the list
                        # NB: The DSTranscript entry has been created before the Gene, GeneAlias and 
                        #     UTGeneFromAlias entries but the gene_id attribute of the DSTranscript is 
                        #     a foreign key from the Gene table. Hence, this is necessary to add these 
                        #     new objects to the session prior than the existing DSTranscript.
                        objects_to_insert = new_obj_to_insert + objects_to_insert
                        existing_dstranscript.gene_id = gene.gene_id
                        
                dstranscript = existing_dstranscript

            # Otherwise, add the newly created transcript to the list of objects to insert and keep track of it
            else:
                all_dstranscripts[ dstranscript ] = dstranscript
                objects_to_insert.append( dstranscript )
            
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
            
            
            ## DSORFTranscriptAsso
            #  -------------------            
            # Get the ORF length
            if ParserStrategy.is_empty( row[ Laumont2016.HEADER_ORF_LENGTH ] ):
                orf_len = None
                orf_len_nt = None
            else:
                orf_len = int( row[ Laumont2016.HEADER_ORF_LENGTH ] ) + 1
                orf_len_nt = ( orf_len + 1 ) * 3
            
            # The provided category value is computed by concatenating the "cryptic status" and 
            # the "alternative property" of the peptide
            provided_category = ( str( row[ Laumont2016.HEADER_ORF_CATEGORY ] ) + ',' +
                                  str( row[ Laumont2016.HEADER_ORF_ALT_FRAME ] ) )
            
            # The MS info equals True if there is at least one MS experiment where it was detected
            if ( not ParserStrategy.is_empty( row[ Laumont2016.HEADER_MS_DETECTION ] ) 
                 and int( row[ Laumont2016.HEADER_MS_DETECTION ] ) >= 1 ):
                ms_info = True
            else:
                ms_info = False
            
            # Get the amino acid raw sequence
            if ParserStrategy.is_empty( row[ Laumont2016.HEADER_ORF_AA_SEQUENCE ] ):
                raw_sequence_aa = None
            else:
                raw_sequence_aa = 'X' + str( row[ Laumont2016.HEADER_ORF_AA_SEQUENCE ] )
            
            dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                       data_source = datasource.name,
                                                       transcript_id = dstranscript.id,
                                                       uniq_orf_id = dsorf.id,
                                                       predicted = Laumont2016.PREDICTED,
                                                       ribo_seq = Laumont2016.RIBO_SEQ,
                                                       cell_context = Laumont2016.CELL_CONTEXT,
                                                       orf_id = orf_id,
                                                       raw_sequence = None,
                                                       raw_sequence_aa = raw_sequence_aa,
                                                       start_codon_seq = None,
                                                       kozak_context = None,
                                                       orf_length_nt = orf_len_nt,
                                                       orf_length = orf_len,                                                  
                                                       provided_category = provided_category,
                                                       ms_info = ms_info,
                                                       orf_score = None,
                                                       phylocsf = None,
                                                       phastcons = None,
                                                       floss = None,
                                                       floss_class = None )
            
            # If this DSORFTranscriptAsso has already been reported (in the current source), get the existing one
            existing_dsota = all_dsota.get( dsorftranscriptasso )
            if existing_dsota:
                
                # Try to update the existing DSORFTranscriptAsso
                try:
                    existing_dsota.update( dsorftranscriptasso )
                except DenCellORFObjUpdateException as e:
                    Logger.get_instance().error( 'The same ORF has been found associated several time' +
                                                 ' with the same transcript ("' + dstranscript.transcript_id +
                                                 '") under original ORF IDs "' + orf_id + '" and "' + 
                                                 existing_dsota.orf_id + '" in ' + self.data_source + '.' +
                                                 ', with different properties: ' + e.get_message() +
                                                 ' Error code: ' + LogCodes.ERR_DCORF_CONFL_DSORF + '.',
                                                 ex = False )

                
            # Otherwise, add the newly created DSORFTranscriptAsso to the list of objects to insert and keep track of it
            else:
                all_dsota[ dsorftranscriptasso ] = dsorftranscriptasso

                # Add it to the list of objects to insert in the database
                objects_to_insert.append( dsorftranscriptasso )
                    
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
                    
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'Laumont2016.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
        
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
                
        return objects_to_insert
    