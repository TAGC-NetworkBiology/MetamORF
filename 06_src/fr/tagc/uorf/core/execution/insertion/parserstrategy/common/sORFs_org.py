# -*- coding: utf-8 -*-

import pandas as pd
import datetime

from abc import abstractmethod


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

## Source: sORFs.org
#
# NB: This file contains a header.
#     This file is expected to be in a tab-delimited format.
#     More information about each column may be found at: http://sorfs.org/biomart_manual.
#
## Description of the columns of the raw data file:
#  Extensive information about each feature may be found at: http://sorfs.org/biomart_manual
#  NB: Columns described here are the one used for the M. musculus database. Column names
#      used in the other files are described in the child parsers.
#- [0]: Sorf ID: Unique ORF ID - String
#                ORF ID formatted as: Data source name + ":" + unique integer
#- [1]: Cell line: The name of the data source - String
#- [2]: Chromosome: The chromosome name - String
#- [3]: Strand: Strand - String
#- [4]: Sorf start: Genomic start coordinate of the ORF - Integer
#- [5]: Sorf end: Genomic end coordinate of the ORF - Integer
#- [6]: Spliced: Is the ORF derived from splice variation of a mRNA transcript? - String 
#                NO = Canonical mRNA transcripts
#                YES = Splice variation of these mRNAs transcript
#                NA = No mRNA transcript information available
#- [7]: Spliced start parts: Spliced start positions - String
#                When the ORF is annotated on spliced mRNA variants, its genomic positions 
#                contain multiple starts and stops. In such case, the coordinates are 
#                separated by an underscore ("_") and the values of start and stop positions
#                are provided in the same order.
#- [8]: Spliced stop parts: SPliced stop positions - String
#                See comment for "Spliced start parts"
#- [9]: Sorf length: ORF length (in amino acids, include the stop codon) - Integer
#- [10]: Start codon: Start codon sequence - String
#- [11]: Downstream gene distance: Genomic distance to the closest downstream located gene 
#                                  (only for intergenic genes) - Integer
#- [12]: Upstream gene distance: Genomic distance to the closest upstream located gene 
#                                (only for intergenic genes) - Integer
#- [13]: Transcript sequence: ORF nucleotide sequence - String
#- [14]: AA-sequence: ORF Amino acids sequence - String
#- [15]: Mass: Hypothetic mass for the resulting micropeptide translated from the ORF - Float 
#- [16]: Annotation: Annotation based on the location of the ORF relative to Ensembl mRNA annotation.
#                    NB: in the list: exonic, intronic, intergenic, ncRNA, 3UTR, 5UTR, 
#                                    sORF (correspond to Ensembl protein coding ORF <= 100 AA), 
#                                    NMD (Nonsense mediated decay),
#                                    NSD (Non stop decay)
#- [17]: Biotype: Based on Ensembl annotation system - String
#              NB: in the list: protein_coding, pseudogene, long_noncoding, short_noncoding
#- [18]: RPKM: RPKM, Represents the ribosomal density across the ORF - Float
#- [19]: RPF coverage: Percentage of nucleotides covered by RPFs - Float
#- [20]: RPF coverage uniformity: Expresses how uniform the ribosome footprints are distributed 
#                                 over the ORF sequence - Float
#- [21]: Exon overlap: Amount of overlap between the ORF and exon regions of annotated protein coding 
#                      sequence - Float
#                      NB: Ranges between 0 (completetly outside exonic regions) and 
#                          1 (completely overlapping with exonic regions)
#- [22]: In frame coverage: ORF score, percentagee of nucleotides covered by in-frame situated RPF - Float
#                          NB: RPF lengths as defined in the ORFscore
#- [23]: In frame: In-frame with annotated protein coding sequences? - Boolean (String Yes/No)
#                 NB: ORFs located on annotated mRNA transcripts can be in-frame with annotated protein 
#                     coding sequences on this mRNA (=Yes) or out-of-frame (=No). For ORFs located on mRNA 
#                     transcripts without annotated protein coding sequence or ORFs not located on annotated 
#                     mRNA transcripts the in-frame attribute cannot be computed (=NA).
#- [24]: overlap with PC exons: Does the ORF overlap exon regions of annotated protein coding 
#                               sequences - Boolean (String Yes/No)
#- [25]: Ensembl transcript ID: Ensembl transcript ID - String 
#- [26]: Rltm min Rchx: Difference between ribosome accumulation on TIS-candidates from LTM/HARR treated 
#                       and CHX/EM treated RIBO-seq data - Float
#                       NB: Acts as a criterium in the TIS-calling algorithm.
#- [27]: FLOSS score: FLOSS score - Float
#                    NB: the FLOSS algorithm provides a score based on the comparison between the 
#                        RPF-length distribution of the ORF and the RPF-length distribution of canonical 
#                        protein-coding sequences.
#- [28]: Floss-Classification: Classification based on the FLOSS score - String
#                             NB: This classification represents the tendency of the ORF to be conding.
#                                 In the list: Good, Extreme (extreme but still in cutoff range), 
#                                              Not in cutoff range.
#- [29]: Orfscore: ORF score - Float
#                 NB: The ORF score calculates the preference of RPFs to accumulate in the first frame of 
#                     coding sequences.
#- [30]: Peak shift: Peak shift - String
#                 NB: Ribosome profiles are combined into peaks. When ribosome occupancy is detected on the
#                     first position of an ATG, or a near-cognate start codon, it is defined as a peak. 
#                     However, if the +/- 1 position is an ATG near-cognate, this ribosome profile will also 
#                     be defined as a peak and the position will change. As such, different profiles can be 
#                     combined into a single peak. If this is the case, the ribosome profile hits are added up.
#                     This value represents the peak shifts. A peak shift value of 1/-1 indicates a near 
#                     cognate start codon at the +/- 1 position, a peak shift value of 10/-10 means a near 
#                     cognate start codon right before/after the annotated peak, a peak shift position of 0 
#                     indicates no ATG near cognate in the neighbourhood. The peak shift filter allow to 
#                     select sORFs with a specific peak shift.
#- [31]: PhastCon: PhastCon score - Float
#                  NB: PhastCon examines evolutionary signatures characteristic to alignments of conserved
#                      coding region in order to determine whether a multi-species nucleotide sequence 
#                      alignment is likely to represent a protein-coding region and provides a score based 
#                      on this alignment.
#- [32]: PhyloP: PhyloP score - Float
#                NB: PhyloP examines evolutionary signatures characteristic to alignments of conserved 
#                    coding regions in order to determine whether a multi-species nucleotide sequence 
#                    alignment is likely to represent a protein-coding region.
#- [33]: cutoff p-value: ??
#
# Supplementary information
# - The chromosome name is provided without 'chr' prefix.
# - The genomic coordinates are reported on GRCh38 (v90) or GRCm38 (v90) annotation.
# - For '+'-strand ORFs,
#     - the first nucleotide of the start codon is located at start position (Sorf start).
#     - the last nucleotide of the stop codon is located at stop position (Sorf end).
#   and, for each exon,
#    [ e.g. when Spliced start parts = start1_start2 and Spliced stop parts = stop1_stop2 ]
#     - the first nucleotide of the exon is located at the Spliced start parts position, in the same order 
#      (e.g. start1 for exon1, start2 for exon2)
#     - the last nucleotide of the exon is located at the Spliced stop parts position, in the same order 
#      (e.g. stop1 for exon1, stop2 for exon2)
# - For '-'-strand ORFs,
#     - the first nucleotide of the start codon is located at stop position (Sorf end).
#     - the last nucleotide of the stop codon is located at start position (Sorf start).
#   and, for each exon,
#    [ e.g. when Spliced start parts = start1_start2 and Spliced stop parts = stop1_stop2 ]
#     - the first nucleotide of the exon is located at the Spliced start parts position, in the same order 
#      (e.g. start1 for exon1, start2 for exon2)
#     - the last nucleotide of the exon is located at the Spliced stop parts position, in the same order 
#      (e.g. stop1 for exon1, stop2 for exon2)
#    /!\ NB: contrary to the stop and start position, the spliced positions are NOT reverted!
# - The nucleic sequence (Transcript sequence) includes both the start and the stop codons.
# - The amino acid sequence (AA-sequence) includes both the start and the stop codons.
# - The ORF length (Sorf length) is in amino acids and includes both the start and the stop codons.


# ===============================================================================
# File parser
# ===============================================================================


## sORFs_org
#  =========
#
# This class inherits from ParserStrategy and is a metaclass aiming to parse 
# data from the sORFs.org databases.
#
class sORFs_org( ParserStrategy ):
                
    ## Class variables
    #  ---------------
    #
    # Constants    
    DOI = '10.1093/nar/gkx1130'
    URL = 'https://academic.oup.com/nar/article/46/D1/D497/4621340'
    
    PREDICTED = False
    RIBO_SEQ = True
    
    # ORF annotations
    ORF_INTERGENIC_ANNOTATION = 'intergenic'


    ## Constructor of sORFs_org
    #  ------------------------
    #
    def __init__( self, data_path ):
        
        ParserStrategy.__init__( self, data_path )



    ## rm_stop_from_seq
    #  ----------------
    #
    # This is a static method that allows to return an amino acid sequence without its stop.
    #
    # @param aa_sequence: String - The sequence (in amino acid).
    #
    # @return String - The amino acid sequence without 
    #
    @staticmethod
    def rm_stop_from_seq( aa_sequence ):
        
        if ( isinstance( aa_sequence, basestring )
             and len( aa_sequence ) > 0 ):
            if aa_sequence[-1] == '*':
                return aa_sequence[:-1]
            else:
                return aa_sequence
        else:
            return None



    ## parse_file_content
    #  ------------------
    #
    # Parse the content of the file and return the list of object that have to be inserted
    # in the database.
    # See the execute() method documentation of the ParserStrategy metaclass for 
    # more information about the main steps of the algorithm run in this method.
    #
    # @return objects_to_insert: List - List of objects to insert in the database.
    #
    # @throw DenCellORFException: When this parser cannot be used for the species of the database.
    # @throw DenCellORFException: When an exception has been raised checking the headers of the file.
    #
    @abstractmethod
    def parse_file_content( self ):
        
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
        datasource = DataSource( name = self.DATA_SOURCE,
                                 doi = sORFs_org.DOI,
                                 description = self.SOURCE_DESCRIPTION,
                                 url = self.URL, 
                                 annotation_version = self.ANNOTATION_VERSION,
                                 ensembl_release = self.ENSEMBL_RELEASE,
                                 annotation_description = self.ANNOTATION_DESCRIPTION )
        objects_to_insert.append( datasource )
        
        
        # Parse the content of the file and save it in appropriate objects
        start_time = datetime.datetime.now()
        for ( index, row ) in self.file_content.iterrows():
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Assign useful information to new variables
            chr_name = row[ self.HEADER_CHROMOSOME ]
            orf_id = row[ self.HEADER_ORF_ID ]
            transcript_id = row[ self.HEADER_TRANSCRIPT_ID ]
            orf_annotation = row[ self.HEADER_ORF_ANNOTATION ]
            
            if int(row[self.HEADER_STRAND]) == 1:
                orf_strand = "+"
            else:
                orf_strand = "-"
                
            orf_start = row[ self.HEADER_START_POS ]
            orf_stop = row[ self.HEADER_STOP_POS ]
            
            if ( row[ self.HEADER_SPLICED ] == 'Yes' ):
                orf_spliced = True
            elif ( row[ self.HEADER_SPLICED ] == 'No' ):
                orf_spliced = False
            else:
                orf_spliced = None
                
            orf_splice_starts = row[ self.HEADER_SPLICE_STARTS ]
            orf_splice_ends = row[ self.HEADER_SPLICE_ENDS ]
            # Get the number of "exonic" parts of the ORF
            if orf_spliced:
                
                if ( ( orf_splice_starts != None ) and ( orf_splice_ends != None ) ):
                    splice_starts_count = len( orf_splice_starts.split( '_' ) )
                    splice_ends_count = len( orf_splice_ends.split( '_' ) )
                    
                    # If the number of starts is different from the number of ends, raise an exception
                    if ( splice_starts_count != splice_ends_count ):
                        raise DenCellORFException( self.data_source + '.execute():' +
                                                   ' The number of starts for exonic parts (' + 
                                                   str( splice_starts_count ) + 
                                                   ') does not equal the number of ends for exonic parts (' +
                                                   str( splice_ends_count ) + 
                                                   ') for the ORF with original ID "' + orf_id + '".' )
                        spliced_parts_count = None
                        
                    else:
                        spliced_parts_count = splice_starts_count
                    
                else:
                    Logger.get_instance().warning( 'The ORF with original ID "' + orf_id + 
                                                   '" is reported to be spliced in ' + self.data_source +
                                                   ' but no location of start and ends of "exonic" parts are provided.' +
                                                   ' Warning code: ' + LogCodes.WARN_SPLIC_MISS + '.' )
                    spliced_parts_count = None
                
                # Replace too long strings of coordinates by "TOO_LONG"
                if ( len( str( orf_splice_starts ) ) > Constants.MAX_LEN_STRING ):
                    Logger.get_instance().warning( 'The splicing information for the ORF with original ID"' + 
                                                   orf_id + '" in ' + self.data_source +
                                                   ' was too long to be stored in the database' +
                                                   ' (raw splice starts: ' + orf_splice_starts + 
                                                   ', raw splice ends: ' + orf_splice_ends + ').'
                                                   ' Hence these values will be changed for "' + 
                                                   Constants.REPLACE_TOO_LONG_STRINGS + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_SPLIC_TOOLONG + '.' )
                    orf_splice_starts = Constants.REPLACE_TOO_LONG_STRINGS
                    orf_splice_ends = Constants.REPLACE_TOO_LONG_STRINGS
                    
            else:
                spliced_parts_count = 1
            
            # Reset the chr_name, symbol and transcript_id if necessary
            ( chr_name, symbol, transcript_id ) = self.initialize_ids( ensembl_db = ensembl_db,
                                                                       orf_id = orf_id,
                                                                       chr_name = chr_name,
                                                                       symbol = None,
                                                                       transcript_id = transcript_id, 
                                                                       orf_start = orf_start,
                                                                       orf_stop = orf_stop,
                                                                       orf_strand = orf_strand,
                                                                       index = index,
                                                                       log_symb_from_tr = False )


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
                           spliced_parts_count = spliced_parts_count )
            
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
                                         raw_cds_stop_pos = None,
                                         rna_biotype = row[ self.HEADER_ORF_BIOTYPE ] )
            
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
                    
                    # If a conflict has been found on the gene ID, associate this transcript to its new "conflict" gene ID
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
                            raise DenCellORFException( 'sORFs_org.parse_file_content(): The gene ID associated with the DSTranscript with ID "' +
                                                       existing_dstranscript.id + '" has been updated whilst the list of genes related to the' +
                                                       ' DSTranscript cannot be get. Please contact the developer if you see this message.' )
                    
                        # Get the appropriate gene object from this new gene ID
                        ( gene, new_obj_to_insert ) = self.get_gene_from_conflict_id( conflict_symbol = new_gene_id,
                                                                                      chr_name = chr_name )
                        
                        # Add the newly created object to the list
                        # NB: The DSTranscript entry has been created before the Gene, GeneAlias and UTGeneFromAlias 
                        #     entries but the gene_id attribute of the DSTranscript is a foreign key from the Gene
                        #     table. Hence, this is necessary to add these new objects to the session prior than the
                        #     existing DSTranscript.
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
            raw_sequence = row[ self.HEADER_ORF_SEQUENCE ]
            if ParserStrategy.is_empty( raw_sequence ):
                raw_sequence = None
                start_codon_seq = None
                orf_len_nt = None
            else:
                start_codon_seq = raw_sequence[:3]
                orf_len_nt = len( raw_sequence )
            
            if ParserStrategy.is_empty( row[ self.HEADER_ORF_LENGTH ] ):
                orf_len = None
            else:
                orf_len = int( row[ self.HEADER_ORF_LENGTH ] ) - 1
                
            dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                       data_source = datasource.name,
                                                       transcript_id = dstranscript.id,
                                                       uniq_orf_id = dsorf.id,
                                                       predicted = self.PREDICTED,
                                                       ribo_seq = self.RIBO_SEQ,
                                                       cell_context = row[ self.HEADER_CELL_CONTEXT ],
                                                       orf_id = orf_id,
                                                       raw_sequence = raw_sequence,
                                                       raw_sequence_aa = self.rm_stop_from_seq( row[ self.HEADER_ORF_SEQUENCE_AA ] ),
                                                       start_codon_seq = start_codon_seq,
                                                       kozak_context = None,
                                                       orf_length_nt = orf_len_nt,
                                                       orf_length = orf_len,
                                                       provided_category = orf_annotation,
                                                       ms_info = None,
                                                       orf_score = row[ self.HEADER_ORF_SCORE ],
                                                       phylocsf = None,
                                                       phastcons = row[ self.HEADER_PHASTCONS ],
                                                       floss = row[ self.HEADER_FLOSS_SCORE ],
                                                       floss_class = row[ self.HEADER_FLOSS_CLASS ] )
            
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
                
                dsorftranscriptasso = existing_dsota

                
            # Otherwise, add the newly created DSORFTranscriptAsso to the list of objects to insert and keep track of it
            else:
                all_dsota[ dsorftranscriptasso ] = dsorftranscriptasso

                # Add it to the list of objects to insert in the database
                objects_to_insert.append( dsorftranscriptasso )
                
                # Increase the autoincrement value for ID of 1
                autoincrement += 1
            
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'sORFs_org.parse_file_content(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
                
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
        
        return objects_to_insert
    


    ## execute
    #  -------
    #
    # Log an error to inform the user that he/she has to used one of the child class
    # to parse the data from sORF.org. The data will not be parsed using the current metaclass.
    #
    # @return None
    #
    @abstractmethod
    def execute(self):
    
        Logger.get_instance().error( 'Several parsers inheriting from sORF_org are existing to parse data' +
                                     ' from this source (one for each species). Please select the' +
                                     ' appropriate one (in the config file) to insert data in the database.',
                                     ex = False )
        
        return None
    