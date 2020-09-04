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

## Source: Johnstone et al., 2016
#
# NB: This file contains a header.
#     This file is expected to be in a tab-delimited format.
#
## Description of the columns of the raw data file:
#- [0]: orfID: Unique ORF ID - String
#- [1]: geneID: Ensembl gene ID - String
#- [2]: transcriptID: Ensembl transcript ID - String
#- [3]: txID: Unique internal transcript ID, per species - Integer
#- [4]: startLoc: Start location of the ORF, in transcript coordinates - Integer
#- [5]: stopLoc: Stop location of the ORF, in transcript coordinates - Integer
#- [6]: genomic_chr: Chromosome name (with 'chr' prefix) - String
#- [7]: genomic_start: Genomic location of start codon - Integer
#- [8]: genomic_stop: Genomic location of stop codon - Integer
#- [9]: genomic_strand: Strand - String
#- [10]: txCDSStart: Start location of the transcript's CDS, in 1-based transcript coordinates - Integer
#- [11]: txCDSEnd: Stop location of the transcript's CDS, in 1-based transcript coordinates - Integer
#- [12]: color: ORF type: dark green=CDS, red=dORF, blue=oORF, purple=uORF, orange=CDS-overlapping ORF that 
#               does not overlap AUG - String
#- [13]: orfSize_effective: ORF length (in nucleotides) - Integer
#                           NB: exclude start, stop and stop-proximal codons
#- [14]: Source: Source of annotations (ens74, ens80, refDec9) - String
#
#- tx_Input_RPKM_[SAMPLE]: mRNA expression level for the whole transcript 
#                          (in reads per kilobase million, RPKM) - Float
#- [15]: tx_Input_RPKM_hela 
#- [16]: tx_Input_RPKM_hek 
#- [17]: tx_Input_RPKM_hbrainwt 
#- [18]: tx_Input_RPKM_hbraintumor 
#- [19]: tx_Input_RPKM_bjf1 
#- [20]: tx_Input_RPKM_bjf2 
#
#- rpf_RPKM_[SAMPLE]: RPF levels for the ORF (in reads per kilobase million, RPKM) - Float
#- [21]: rpf_RPKM_hela
#- [22]: rpf_RPKM_hek 
#- [23]: rpf_RPKM_hbrainwt 
#- [24]: rpf_RPKM_hbraintumor 
#- [25]: rpf_RPKM_bjf1 
#- [26]: rpf_RPKM_bjf2 
#
#- utr5_rpf_RPKM_[SAMPLE]: RPF levels for the whole TLS (in reads per kilobase million, RPKM) - Float
#- [27]: utr5_rpf_RPKM_hela 
#- [28]: utr5_rpf_RPKM_hek 
#- [29]: utr5_rpf_RPKM_hbrainwt 
#- [30]: utr5_rpf_RPKM_hbraintumor 
#- [31]: utr5_rpf_RPKM_bjf1 
#- [32]: utr5_rpf_RPKM_bjf2
#
#- [33]: maxRPKM: Maximum RNA expression level across all samples for that organism - Float
#- [34]: max_RPF_RPKM: Maximum RPF level across all samples for that organism - Float
#- [35]: orfSize_total: ORF Size in nucleotides, including start and stop codons - Integer
#
#- orfTE_[SAMPLE]: Translation efficiency of the ORF - Float
#- [36]: orfTE_hela
#- [37]: orfTE_hek
#- [38]: orfTE_hbrainwt
#- [39]: orfTE_hbraintumor
#- [40]: orfTE_bjf1
#- [41]: orfTE_bjf2
#
#- utr5TE_[SAMPLE]: Translation efficiency of the 5UTR - Float
#- [42]: utr5TE_hela
#- [43]: utr5TE_hek
#- [44]: utr5TE_hbrainwt
#- [45]: utr5TE_hbraintumor
#- [46]: utr5TE_bjf1
#- [47]: utr5TE_bjf2
#
#- [48]: numuORFs: Number of uORFs in the transcript - Integer
#- [49]: numoORFs: Number of oORFs in the transcript - Integer
#- [50]: numuoORFs: Number of uORFs and oORFs combined in the transcript - Integer
#
#- CDSTE_[SAMPLE]: Translation efficiency of the CDS - Float
#- [51]: CDSTE_hela
#- [52]: CDSTE_hek
#- [53]: CDSTE_hbrainwt
#- [54]: CDSTE_hbraintumor
#- [55]: CDSTE_bjf1
#- [56]: CDSTE_bjf2
#
#- CDS_rpf_RPKM_[SAMPLE]: RPF expression level of the CDS (in reads per kilobase million, RPKM) - Float
#- [57]: CDS_rpf_RPKM_hela
#- [58]: CDS_rpf_RPKM_hek
#- [59]: CDS_rpf_RPKM_hbrainwt
#- [60]: CDS_rpf_RPKM_hbraintumor
#- [61]: CDS_rpf_RPKM_bjf1
#- [62]: CDS_rpf_RPKM_bjf2
#
# Supplementary information
# - The chromosome name is provided with the 'chr' prefix.
# - The coordinates are reported on GRCh38 or GRCm38 annotation.
# - For '+'-strand ORFs, 
#     - the first nucleotide of the start codon is located at the start position +1 (genomic_start + 1).
#     - the last nucleotide of the stop codon is located at the stop position (genomic_stop).
# - For '-'-strand ORFs,
#     - the first nucleotide of the start codon is located at the stop position (genomic_stop).
#     - the last nucleotide of the stop codon is located at the start position +1 (genomic_start + 1).
# - The ORF sequences are not provided.
# - The ORF length "orfSize_total" is in nucleotides includes both the start and the stop codons.
# - The ORF length "orfSize_effective" is in nucleotides and excludes both the start, the stop and 
#   the proximal-stop codon (i.e. orfSize_total - 9 nucleotides = orfSize_effective).


# ===============================================================================
# File parser
# ===============================================================================


## Johnstone2016
#  =============
#
# This class inherits from ParserStrategy and allows to parse data 
# from Johnstone et al., 2016.
#
class Johnstone2016( ParserStrategy ):
    
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ],
                            Constants.SPECIES_CATALOG[ Constants.MMUSCULUS ] ]
    
    # Headers
    HEADER_ORF_ID = 'orfID'
    HEADER_CHROMOSOME = 'genomic_chr'
    HEADER_GENE_ID = 'geneID'
    HEADER_TRANSCRIPT_ID = 'transcriptID'    
    
    HEADER_STRAND = 'genomic_strand'
    HEADER_START_POS = 'genomic_start'
    HEADER_STOP_POS = 'genomic_stop'
    
    HEADER_ORF_LENGTH = 'orfSize_total'
    
    HEADER_ORF_CATEGORY = 'color'
    
    HEADER_LIST = [ HEADER_ORF_ID, HEADER_CHROMOSOME, HEADER_GENE_ID, HEADER_TRANSCRIPT_ID, HEADER_STRAND, 
                    HEADER_START_POS, HEADER_STOP_POS, HEADER_ORF_LENGTH, HEADER_ORF_CATEGORY ]
    
    # Constants
    DATA_SOURCE = 'Johnstone2016'
    
    DOI = '10.15252/embj.201592759'
    SOURCE_DESCRIPTION = { Constants.HSAPIENS : 'Johnstone et al., EMBO, 2016. "Dataset EV2: Location and translation data for all analyzed transcripts and ORFs in human".',
                           Constants.MMUSCULUS : 'Johnstone et al., EMBO, 2016. "Dataset EV3: Location and translation data for all analyzed transcripts and ORFs in mouse".' }
    URL = 'http://emboj.embopress.org/content/35/7/706.long'
        
    PREDICTED = False
    RIBO_SEQ = True
    CELL_CONTEXT = { Constants.HSAPIENS : 'HeLa,HEK293,Primary human foreskin fibroblasts (HFFs),Human brain tumor',
                     Constants.MMUSCULUS : 'Mouse Embryonic Stem Cells, Mouse Embryonic Fibroblast (MEFs),Mouse liver cell, Mouse gliomal cells' }
    
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = { Constants.HSAPIENS : Constants.ANNOTATION_VERSION_GRCH38,
                           Constants.MMUSCULUS : Constants.ANNOTATION_VERSION_GRCM38 }
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = { Constants.HSAPIENS : 'Ensembl transcript annotations release 80 ',
                               Constants.MMUSCULUS : 'Ensembl transcript annotations release 80 ' }
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = { Constants.HSAPIENS : '80',
                        Constants.MMUSCULUS : '80' }
    
    # Variable specific to the data source
    COLORS_TO_CATEGORY = { 'dark green' : 'CDS',
                           'red' : 'dORF',
                           'blue' : 'oORF',
                           'purple' : 'uORF',
                           'orange' : 'CDS-overlapping ORF' }


    ## Constructor of Johnstone2016
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
        datasource = DataSource( name = Johnstone2016.DATA_SOURCE,
                                 doi = Johnstone2016.DOI,
                                 description = Johnstone2016.SOURCE_DESCRIPTION[ sp ],
                                 url = Johnstone2016.URL, 
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
            chr_name = row[ Johnstone2016.HEADER_CHROMOSOME ][3:]
            orf_id = row[ Johnstone2016.HEADER_ORF_ID ]
            symbol = row[ Johnstone2016.HEADER_GENE_ID ]
            transcript_id = row[ Johnstone2016.HEADER_TRANSCRIPT_ID ]
                        
            orf_strand = row[ Johnstone2016.HEADER_STRAND ]
            orf_start = int( row[ Johnstone2016.HEADER_START_POS ] ) + 1
            orf_stop = row[ Johnstone2016.HEADER_STOP_POS ]
            
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
                            raise DenCellORFException( 'Johnstone2016.execute(): The gene ID associated with' +
                                                       ' the DSTranscript with ID "' + existing_dstranscript.id + 
                                                       '" has been updated whilst the list of genes related to the' +
                                                       ' DSTranscript cannot be get.' +
                                                       ' Please contact the developer if you see this message.' )
                    
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
            
            # Get the category of the ORF
            orf_category = row[ Johnstone2016.HEADER_ORF_CATEGORY ]
            if orf_category in Johnstone2016.COLORS_TO_CATEGORY.values():
                orf_category = Johnstone2016.COLORS_TO_CATEGORY[ orf_category ]
            else:
                orf_category = None
            
            # Convert the ORF length in amino acids
            if ParserStrategy.is_empty( row[ Johnstone2016.HEADER_ORF_LENGTH ] ):
                orf_len_nt = None
                orf_len = None
            else:
                orf_len_nt = int( row[ Johnstone2016.HEADER_ORF_LENGTH ] )
                orf_len = ( orf_len_nt - 3 ) / 3
            
            dsorftranscriptasso = DSORFTranscriptAsso( id = autoincrement,
                                                       data_source = datasource.name,
                                                       transcript_id = dstranscript.id,
                                                       uniq_orf_id = dsorf.id,
                                                       predicted = Johnstone2016.PREDICTED,
                                                       ribo_seq = Johnstone2016.RIBO_SEQ,
                                                       cell_context = Johnstone2016.CELL_CONTEXT[ sp ],
                                                       orf_id = orf_id,
                                                       raw_sequence = None,
                                                       raw_sequence_aa = None,
                                                       start_codon_seq = None,
                                                       kozak_context = None,
                                                       orf_length_nt = orf_len_nt,
                                                       orf_length = orf_len,
                                                       provided_category = orf_category,
                                                       ms_info = None,
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
        Logger.get_instance().debug( 'Johnstone2016.execute(): Duration of parsing: ' + 
                                     str( end_time - start_time ) + ' (' +
                                     str( ProgressionBar.get_instance().total_row_count ) + 
                                     ' rows processed).' )
                
        # Store the current value of the autoincrement in the DataManager
        DataManager.get_instance().store_data( Constants.DM_AUTOINCREMENT, autoincrement )
                
        return objects_to_insert
