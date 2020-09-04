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

## Source: Mackowiak et al., 2015
#
# NB: This file contains a header.
#     This file is expected to be in a tab-delimited format.
#
## Description of the columns of the raw data file:
#- [0]: \#chrom: Chromosome name - String
#- [1]: transcript_start: Genomic coordinates of the transcript start - Integer
#- [2]: transcript_end: Genomic coordinates of the transcript stop - Integer
#- [3]: orfID: ORF ID - String
#       ORF ID formatted as: Ensembl transcript ID + "_chr" + chromosome name + 
#                          ":" +  start + "-" + stop + ":" + strand
#- [4]: phyloCSF_score: PhyloCSF score (omega mode) - Float
#- [5]: strand: Strand - String
#- [6]: CDS_start: Genomic start of the ORF - String
#- [7]: CDS_end: Genomic end of the ORF - Stop
#- [8]: color: Unused (no information) - Integer (0)
#- [9]: nexons: Number of exons in the transcript - Integer
#- [10]: exon_sizes: Exon sizes (comma separated values) - String
#- [11]: exon_starts: Transcript coordinates of exon starts (csv) - String
#- [12]: transcriptID: Ensembl transcript ID or lncRNA name - String
#- [13]: other_transcriptIDs: Other transcripts harboring this ORF (csv) - String
#- [14]: gene_name: Gene symbol - String
#- [15]: sORF_type: ORF classification - String
#- [16]: length: ORF length in amino acids (excluding stop) - Integer
#- [17]: rfc_species: Number of species with conserved ORF - Integer
#- [18]: adjusted_phyloCSF_score: Length-adjusted phyloCSF score - Float
#- [19]: predicted: SVM predicted? - Boolean
#- [20]: nonoverlapping: Passing overlap filter? - Boolean
#- [21]: CSV_overlap: Overlap with annotated CDS? - Boolean
#- [22]: conserved_exon_overlap: Overlap with conserved coding exons? - Boolean
#- [23]: phastcons_conserved_elements_overlap: Fractional overlap with PhastCOns conserved elements - Float
#- [24]: blast_homology: BLAST homology to known RefSeq protein? - Boolean
#- [25]: average_disorder: IUpred average disorder - Float
#- [26]: num_ELM_matches: Number of matches to ELM motifs (only in disordered regions) - Integer
#- [27]: signal_peptide: Signalp prediction - Boolean
#- [28]: homology_graph_neighbors: Neighbors in the homology graph 
#                                  (only for predicted and nonoverlapping ORFs) - String
#- [29]: alignment_conservation: Species with conserved start/stop/splice sites, no frameshift, 
#                                no nonsense mutations (csv) - String
#- [30]: num_synonymous_SNPs: Number of synonymous SNPs - Integer
#- [31]: num_synonymous_sites: Number of synonymous sites - Integer
#- [32]: num_nonsynonymous_SNPss: Number of non-synonymous SNPs - Integer
#- [33]: num_nonsynonymous_sites: Number of non-synonymous sites - Integer
#- [34]: UniProt_IDs: UniProt IDs (Swiss-Prot and TrEMBL) (separated with "|") - String
#- [35]: sequence: Sequence - Amino acid sequence
#
# Supplementary information
# - The chromosome name is provided with the 'chr' prefix
# - The genomic coordinates are reported on GRCh37 (v74) or GRCm38 (v74) annotation.
# - For '+'-strand ORFs,
#     - the first nucleotide of the start codon is located at the start position +1 (CDS_start + 1).
#     - the last nucleotide of the stop codon is located at the stop position (CDS_end).
# - For '-'-strand ORFs,
#     - the first nucleotide of the start codon is located at the stop position (CDS_end).
#     - the last nucleotide of the stop codon is located at the start position +1 (CDS_start + 1).
# - The nucleic sequence is not provided.
# - The amino acid sequence (sequence) includes the start codon and excludes the stop codon.
# - The ORF length (length) is in amino acids and includes the start codon but excludes the stop codon.


# ===============================================================================
# File parser
# ===============================================================================


## Mackowiak2015
#  =============
#
# This class inherits from ParserStrategy and allows to parse data 
# from Mackowiak et al., 2015.
#
class Mackowiak2015( ParserStrategy ):
        
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ], 
                           Constants.SPECIES_CATALOG[ Constants.MMUSCULUS ] ]
    
    # Headers
    HEADER_ORF_ID = 'orfID'
    HEADER_CHROMOSOME = '#chrom'
    HEADER_GENE_SYMBOL = 'gene_name'
    HEADER_TRANSCRIPT_ID = 'transcriptID'
    HEADER_OTHER_TRANSCRIPT_IDS = 'other_transcriptIDs'
    
    HEADER_STRAND = 'strand'
    HEADER_START_POS = 'CDS_start'
    HEADER_STOP_POS = 'CDS_end'
    
    HEADER_TRANSCRIPT_START = 'transcript_start'
    HEADER_TRANSCRIPT_END = 'transcript_end'
    
    HEADER_ORF_AA_SEQUENCE = 'sequence'
    HEADER_ORF_CATEGORY = 'sORF_type'
    HEADER_ORF_LENGTH = 'length'
    HEADER_PHYLOCSF = 'phyloCSF_score'
    HEADER_PHASTCONS = 'phastcons_conserved_elements_overlap'
    
    HEADER_LIST = [ HEADER_ORF_ID, HEADER_CHROMOSOME, HEADER_GENE_SYMBOL, HEADER_TRANSCRIPT_ID, 
                    HEADER_OTHER_TRANSCRIPT_IDS, HEADER_STRAND, HEADER_START_POS, HEADER_STOP_POS, 
                    HEADER_TRANSCRIPT_START, HEADER_TRANSCRIPT_END, HEADER_ORF_AA_SEQUENCE,
                    HEADER_ORF_CATEGORY, HEADER_ORF_LENGTH, HEADER_PHYLOCSF, HEADER_PHASTCONS ]
    
    # Constants
    DATA_SOURCE = 'Mackowiak2015'
    
    DOI = '10.1186/s13059-015-0742-x'
    SOURCE_DESCRIPTION = { Constants.HSAPIENS : 'Mackowiak et al., Genome Biol., 2015. "Additional file 2: Table S1. All sORF information for human". The file header has to be removed manually (45 first rows).',
                           Constants.MMUSCULUS : 'Mackowiak et al., Genome Biol., 2015. "Additional file 3: Table S2. All sORF information for mouse". The file header has to be removed manually (45 first rows).' }
    URL = 'https://genomebiology.biomedcentral.com/articles/10.1186/s13059-015-0742-x'
        
    PREDICTED = True
    RIBO_SEQ = False
    CELL_CONTEXT = None
        
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = { Constants.HSAPIENS : Constants.ANNOTATION_VERSION_GRCH37,
                           Constants.MMUSCULUS : Constants.ANNOTATION_VERSION_GRCM38 }
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = { Constants.HSAPIENS : 'Transcript annotation from Ensembl (v74). Additionally, use of published lincRNA catalogs for human (2011, Cabili et al., Genes Dev. and 2012, Derrien et al., Genome Res.).',
                               Constants.MMUSCULUS : 'Transcript annotation from Ensembl (v74). Additionally, use of published lincRNA catalog for mouse (2010, Guttman et al., Nat. Biotechnol.).' }
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = { Constants.HSAPIENS : '74',
                        Constants.MMUSCULUS : '74' }
    

    ## Constructor of Mackowiak2015
    #  ----------------------------
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
        all_utdstranscriptgeneconflict = DataManager.get_instance().get_data( Constants.DM_ALL_UTDSTRANSCRIPTGENECONFLICT )
        
        autoincrement = DataManager.get_instance().get_data( Constants.DM_AUTOINCREMENT )
        
        # Get the appropriate Ensembl database to recover missing gene IDs
        ensembl_db = ParserStrategy.get_ensembl_db( ensembl_release )
        
        # Get the number of rows expected to be treated and reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = self.file_content.shape[ 0 ] )
        
        # Initialize the list of objects to insert
        objects_to_insert = []


        ## DataSource
        #  ----------
        datasource = DataSource( name = Mackowiak2015.DATA_SOURCE,
                                 doi = Mackowiak2015.DOI,
                                 description = Mackowiak2015.SOURCE_DESCRIPTION[ sp ],
                                 url = Mackowiak2015.URL,
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
            chr_name = row[Mackowiak2015.HEADER_CHROMOSOME][3:]
            orf_id = row[ Mackowiak2015.HEADER_ORF_ID ]
            symbol = row[ Mackowiak2015.HEADER_GENE_SYMBOL ]
            main_transcript_id = row[ Mackowiak2015.HEADER_TRANSCRIPT_ID ]
            other_transcript_ids = row[ Mackowiak2015.HEADER_OTHER_TRANSCRIPT_IDS ]
 
            orf_strand = row[ Mackowiak2015.HEADER_STRAND ]
            orf_start = int( row[ Mackowiak2015.HEADER_START_POS ] ) +1
            orf_stop = row[ Mackowiak2015.HEADER_STOP_POS ]
            
            # Reset the chr_name if necessary
            chr_name = self.initialize_chromosome_name( chr_name = chr_name )
            
            # Reset the symbol if it is provided (otherwise, one will try to recover the symbol
            # from the transcript ID or the ORF coordinates later)
            if ( not ParserStrategy.is_empty( symbol ) ):
                symbol = str( symbol )
            else:
                symbol = None

            
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
            
            
            ## Gene and DSTranscript
            #  ---------------------
            # Get the complete list of transcripts associated with this ORF
            #   NB: In this file, the transcript start and transcript end genomic coordinates are only 
            #       provided for the "main" transcript (i.e. the one provided in the "transcriptID" column). 
            #       Then, this is not possible to get the genomic coordinates for the transcripts provided 
            #       in the column entitled "other_transcriptIDs".
            if ( not ParserStrategy.is_empty( main_transcript_id ) ):
                transcript_ids = [ main_transcript_id ]
                
                if ( not ParserStrategy.is_empty( other_transcript_ids ) ):
                    transcript_ids += other_transcript_ids.split( ',' )
            
            # If there is no transcript ID associated with this ORF, generate a "fake" transcript ID
            else:
                transcript_id = self.initialize_transcript_id( transcript_id = None, 
                                                               orf_id = orf_id, 
                                                               index = index )
                transcript_ids = [ transcript_id ]
            
            for tr in transcript_ids:
                # If a symbol is not provided, try to get it from the ORF coordinates or the transcript ID
                # and if this is not possible create a "unknown" symbol.
                if ( symbol == None ):
                    symbol = self.initialize_gene_symbol( ensembl_db = ensembl_db, 
                                                          orf_id = orf_id, 
                                                          chr_name = chr_name, 
                                                          symbol = symbol, 
                                                          transcript_id = tr, 
                                                          orf_start = orf_start, 
                                                          orf_stop = orf_stop,
                                                          orf_strand = orf_strand )
                
                ## Gene
                #  ----
                # Try to get the gene object from its symbol and its chromosome name
                ( gene, new_obj_to_insert ) = self.get_gene_from_symbol( orf_id = orf_id,
                                                                         symbol = symbol,
                                                                         chr_name = chr_name )
                objects_to_insert += new_obj_to_insert
                
                ## DSTranscript
                #  ------------
                
                # For the 1st transcript ID, get its start and end positions as they are provided.
                # If the transcript is provided with its version number, just get the transcript ID.
                if ( tr == transcript_ids[ 0 ] ):
                    dstranscript = DSTranscript( id = autoincrement,
                                                 transcript_id = tr.split( '.' )[ 0 ],
                                                 data_source = datasource.name,
                                                 gene_id = gene.gene_id,
                                                 strand = None,
                                                 raw_start_pos = row[ Mackowiak2015.HEADER_TRANSCRIPT_START ],
                                                 raw_end_pos = row[ Mackowiak2015.HEADER_TRANSCRIPT_END ],
                                                 raw_cds_start_pos = None,
                                                 raw_cds_stop_pos = None )
                else:
                    dstranscript = DSTranscript( id = autoincrement,
                                                 transcript_id = tr.split( '.' )[ 0 ],
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
                        Logger.get_instance().error( 'The transcript ' + tr.split( '.' )[ 0 ] + ' (from ' + self.data_source +
                                                     ') has been found several time with different properties: ' + e.get_message() +
                                                     ' Error code: ' + LogCodes.ERR_DCORF_CONFL_DSTR + '.',
                                                     ex = False )
                        
                            # If a conflict has been found on the gene ID, 
                            # associate this transcript to its new "conflict" gene ID
                        new_gene_id = e.get_gene_id()
                        
                        if new_gene_id:
                            # Get the lists of all the genes that have been found conflicting
                            if e.get_conflict_list():
                                # If an UTDSTranscriptGeneConflict entry was already existing, 
                                # update the list of gene IDs,
                                # Otherwise, add the new entry to the list of objects to insert
                                if existing_utdstranscriptgeneconflict:
                                    existing_utdstranscriptgeneconflict.gene_ids = Constants.UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS.join( e.get_conflict_list() )
                                    utdstranscriptgeneconflict = existing_utdstranscriptgeneconflict
                                
                                else:
                                    utdstranscriptgeneconflict.gene_ids = Constants.UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS.join( e.get_conflict_list() )
                                    all_utdstranscriptgeneconflict[ utdstranscriptgeneconflict ] = utdstranscriptgeneconflict
                                    objects_to_insert.append( utdstranscriptgeneconflict )
                                
                            else:
                                raise DenCellORFException( 'Mackowiak2015.execute(): The gene ID associated with the DSTranscript with ID "' +
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
                orf_len = row[ Mackowiak2015.HEADER_ORF_LENGTH ]
                if ParserStrategy.is_empty( orf_len ):
                    orf_len = None
                    orf_len_nt = None
                else:
                    orf_len = int( row[ Mackowiak2015.HEADER_ORF_LENGTH ] )
                    orf_len_nt = ( orf_len + 1 ) * 3
                
                dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                           data_source = datasource.name,
                                                           transcript_id = dstranscript.id,
                                                           uniq_orf_id = dsorf.id,
                                                           predicted = Mackowiak2015.PREDICTED,
                                                           ribo_seq = Mackowiak2015.RIBO_SEQ,
                                                           cell_context = Mackowiak2015.CELL_CONTEXT,
                                                           orf_id = orf_id,
                                                           raw_sequence = None,
                                                           raw_sequence_aa = row[ Mackowiak2015.HEADER_ORF_AA_SEQUENCE ],
                                                           start_codon_seq = None,
                                                           kozak_context = None,
                                                           orf_length_nt = orf_len_nt,
                                                           orf_length = orf_len,
                                                           provided_category = row[ Mackowiak2015.HEADER_ORF_CATEGORY ],
                                                           ms_info = None,
                                                           orf_score = None,
                                                           phylocsf = row[ Mackowiak2015.HEADER_PHYLOCSF ],
                                                           phastcons = row[ Mackowiak2015.HEADER_PHASTCONS ],
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
                    
                    dsorftranscriptasso = existing_dsota
    
                    
                # Otherwise, add the newly created DSORFTranscriptAsso to the list of
                # objects to insert and keep track of it
                else:
                    all_dsota[ dsorftranscriptasso ] = dsorftranscriptasso
    
                    # Add it to the list of objects to insert in the database
                    objects_to_insert.append( dsorftranscriptasso )
                    
                    # Increase the autoincrement value for ID of 1
                    autoincrement += 1
        
        # Log the duration of the process
        end_time = datetime.datetime.now()
        Logger.get_instance().debug( 'Mackowiak2015.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
        
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
                
        return objects_to_insert
    