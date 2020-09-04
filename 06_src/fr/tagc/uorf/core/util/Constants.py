# -*- coding: utf-8 -*-

import os
import logging


from fr.tagc.uorf.core.util import DefaultOutputFolder
from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util.sql import SQLConstants


# ===============================================================================
# Project informations
# ===============================================================================

PROJECT_NAME = 'MetamORF'
PROJECT_ALIAS = 'mORF'

WEBSITE_URL = 'http://metamorf.hb.univ-amu.fr'


# ===============================================================================
# Config file constants
# ===============================================================================

# Database
CONFIG_SECTION_DATABASE = 'DATABASE'

CONFIG_SECTION_DATABASE_ITEM_SPECIES = 'DATABASE_SPECIES'

  # DS database
CONFIG_SECTION_DATABASE_ITEM_DS_DB_NAME = 'DS_DATABASE_NAME'

  # PRO database
CONFIG_SECTION_DATABASE_ITEM_PRO_DB_NAME = 'PRO_DATABASE_NAME'

  # FILT database
CONFIG_SECTION_DATABASE_ITEM_FILT_DB_NAME = 'FILT_DATABASE_NAME'

  # Options for MySQL databases
CONFIG_SECTION_DATABASE_ITEM_USER_NAME = 'DATABASE_USER_NAME'
CONFIG_SECTION_DATABASE_ITEM_USER_PASSWD = 'DATABASE_USER_PASSWD'
CONFIG_SECTION_DATABASE_ITEM_HOST_IP = 'DATABASE_HOST_IP'
CONFIG_SECTION_DATABASE_ITEM_PORT = 'DATABASE_PORT'

  # Options for SQLite databases
CONFIG_SECTION_DATABASE_ITEM_DB_FOLDER = 'DATABASE_FOLDER'


# Gene list
CONFIG_SECTION_GENE_LIST = 'GENE_LISTS'
  # Insertion order
CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION = 'GENE_LIST_ORDER_OF_INSERTION'
CONFIG_SECTION_GENE_LIST_ORDER_OF_INSERTION_ITEM_ORDER = 'GL_ORDER_OF_INSERTION' 


# Datasource
CONFIG_SECTION_DATASOURCE = 'DATASOURCE'

  # Insertion order
CONFIG_SECTION_DATA_ORDER_OF_INSERTION = 'DATA_ORDER_OF_INSERTION'
CONFIG_SECTION_ORDER_OF_INSERTION_ITEM_ORDER = 'DATA_INSERTION_ORDER'


# Merge strategy
CONFIG_SECTION_MERGE_PARAMETERS = 'MERGE_PARAMETERS'

  # Threshold for absolute difference in genomic lengths
CONFIG_SECTION_MERGE_PARAMETERS_ITEM_GEN_LEN_DIFF_THRESHOLD = 'GENOMIC_LENGTH_DIFF_THRESHOLD'
  
  # Threshold for consensus sequences
CONFIG_SECTION_MERGE_PARAMETERS_ITEM_SQCE_CONSENSUS_AMBIG_THRESHOLD = 'SEQUENCE_CONSENSUS_AMBIGUOUS_THRESHOLD'

  # Maximal difference between the max. and min. lengths of 
  # DSORFTranscriptAsso to make them belong to the same group
CONFIG_SECTION_MERGE_PARAMETERS_ITEM_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS = 'MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS'


# Compute missing information strategy
CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS = 'COMPUTE_MISSING_INFO_PARAMETERS'

  # Dictionary to merge the cell contexts
CONFIG_SECTION_COMPUTE_MISSING_INFO_PARAMETERS_ITEM_CELLCONTEXT_DICT = 'CELL_CONTEXTS_DICTIONARY'


# ORF Annotation / Category strategy
CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS = 'ANNOTATE_ORF_PARAMETERS'

  # Dictionary to compute the ORF categories
CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_CATEGORY_DICT = 'CATEGORY_ASSOCIATION_DICTIONARY'

  # Maximal size for the ORF to be considered as a short ORF
CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_SHORT_ORF_SIZE_THRESHOLD = 'SHORT_ORF_ANNOTATION_SIZE_THRESHOLD'

# Filtering strategies
CONFIG_SECTION_FILTER = 'FILTERING'

  # Type of filtering (either intersection or union)
CONFIG_SECTION_FILTER_ITEM_TYPE = 'FILTERING_TYPE'

  # List of gene symbols to use for filtering
CONFIG_SECTION_FILTER_ITEM_GENE_LIST = 'GENE_LIST_FILTER'

  # List of cellular contexts to use for filtering
CONFIG_SECTION_FILTER_ITEM_CELL_CONTEXT = 'CELL_CONTEXT_FILTER'

  # List of ORF categories to use for filtering
CONFIG_SECTION_FILTER_ITEM_ORF_CAT = 'ORF_CATEGORY_FILTER'

  # List of ORF annotations to use for filtering
CONFIG_SECTION_FILTER_ITEM_ORF_ANNOT = 'ORF_ANNOTATION_FILTER'


# ===============================================================================
# DataManager constants
# ===============================================================================

# The constants defined in this section are used to handle the objects saved in 
# the DataManager main dictionary
  # Generics DM objects
DM_ALL_DATASOURCES = 'all_datasources'
DM_DATASOURCE_ANNOT = 'datasource_annot'

DM_ALL_DSORFS_FOR_SOURCE = 'all_dsorfs_for_source'
DM_ALL_DSTRANSCRIPTS_FOR_SOURCE = 'all_dstranscripts_for_source'
DM_ALL_DSORFTRANSCRIPTASSO_FOR_SOURCE = 'all_dsorftranscriptasso_for_source'

DM_AUTOINCREMENT = 'autoincrement'

DM_ALL_UTDSTRANSCRIPTGENECONFLICT = 'all_utdstranscriptgeneconflict'
DM_ALL_UTRNABIOTYPECATALOG = 'all_utrnabiotypecatalog'

DM_ALL_GENES = 'all_genes'
DM_ALL_GENEALIASES = 'all_genealiases'
DM_ALL_GENESFROMALIASES = 'all_genesfromaliases'
DM_ALL_GENE_ID_ASSO = 'all_gene_id_asso'
DM_ALL_GENE_SYMBOL_ASSO = 'all_gene_symbol_asso'

DM_ALL_EXISTING_ORF_TR_ASSO_DICT = 'all_existing_orf_tr_asso_dict'

DM_ALL_CELL_CONTEXT = 'all_cellcontext'
DM_ALL_CELL_CTXT_CAT = 'all_cell_ctxt_cat'
DM_ALL_PROVIDED_CAT_CAT = 'all_provided_cat_cat'
DM_ALL_FLOSS_CLASS_CAT = 'all_floss_class_cat'

DM_OBJECTS_TO_INSERT = 'objects_to_insert'

  # DM objects related to merge strategy
DM_ORF_TR_COUNT_FOR_DSOTA = 'orf_tr_count_for_dsota'



# ===============================================================================
# General constants
# ===============================================================================

# Species short and full descriptors
SPECIES_SHORT = 'species_short'
SPECIES_FULL = 'species_full'

# List of species
HSAPIENS = 'Hsapiens'
MMUSCULUS = 'Mmusculus'

# List of accepted species
SPECIES_CATALOG = { HSAPIENS : 'Hsapiens',
                    MMUSCULUS : 'Mmusculus' }

SPECIES_LIST = SPECIES_CATALOG.values()

# List of full names corresponding to the short name species (used by Ensembl databases)
SPECIES_CATALOG_FULL_NAMES = { SPECIES_CATALOG[ HSAPIENS ] : 'homo_sapiens',
                               SPECIES_CATALOG[ MMUSCULUS ] : 'mus_musculus' }

SPECIES_CATALOG_FULL_NAMES_WITH_CAPS = { SPECIES_CATALOG[ HSAPIENS ] : 'Homo sapiens',
                                         SPECIES_CATALOG[ MMUSCULUS ] : 'Mus musculus' }
    
# Dictionary of common names corresponding to the short name species
SPECIES_CATALOG_COMMON_NAMES = { SPECIES_CATALOG[ HSAPIENS ] : 'human',
                                 SPECIES_CATALOG[ MMUSCULUS ] : 'mouse' }

# Official taxonomic codes
# More information could be find at: https://www.uniprot.org/docs/speclist.txt'
SPECIES_CATALOG_CODE = { SPECIES_CATALOG[ HSAPIENS ] : 'HUMAN',
                         SPECIES_CATALOG[ MMUSCULUS ] : 'MOUSE' }
SPECIES_CATALOG_TAXON_ID = { SPECIES_CATALOG[ HSAPIENS ] : 9606,
                             SPECIES_CATALOG[ MMUSCULUS ] : 10090 }

# Values considered as empty / missing
EMPTY_VALUES_WO_DASH = [ None, '', ' ', 'NA', 'NaN', 'nan', 'NAN', 'null', 'NULL', 'none', 'None' ]
EMPTY_VALUES = EMPTY_VALUES_WO_DASH + [ '-' ]


# ===============================================================================
# Constants relative to the annotation versions
# ===============================================================================

# Accepted annotation versions
ANNOTATION_VERSION_GRCH38 = 'GRCh38'
ANNOTATION_VERSION_HG38 = 'hg38'

ANNOTATION_VERSION_GRCH37 = 'GRCh37'
ANNOTATION_VERSION_HG19 = 'hg19'

ANNOTATION_VERSION_GRCM38 = 'GRCm38'
ANNOTATION_VERSION_MM10 = 'mm10'

# Annotation versions by species
HUMAN_ANNOTATION_VERSIONS = [ ANNOTATION_VERSION_GRCH38, ANNOTATION_VERSION_HG38, 
                              ANNOTATION_VERSION_GRCH37, ANNOTATION_VERSION_HG19 ]

MOUSE_ANNOTATION_VERSIONS = [ ANNOTATION_VERSION_GRCM38, ANNOTATION_VERSION_MM10 ]

# All annotation versions
ALL_SPECIES_ANNOTATIONS = HUMAN_ANNOTATION_VERSIONS + MOUSE_ANNOTATION_VERSIONS

# Annotation versions by source (NCBI, UCSC)
ALL_NCBI_ANNOTATIONS = [ ANNOTATION_VERSION_GRCH37, ANNOTATION_VERSION_GRCH38, ANNOTATION_VERSION_GRCM38 ]

ALL_UCSC_ANNOTATIONS = [ ANNOTATION_VERSION_HG19, ANNOTATION_VERSION_HG38, ANNOTATION_VERSION_MM10 ]

  # Correspondance of annotation versions between NCBI and UCSC
CORRESPONDING_NCBI_FROM_UCSC = { ANNOTATION_VERSION_HG19 : ANNOTATION_VERSION_GRCH37,
                                 ANNOTATION_VERSION_HG38 : ANNOTATION_VERSION_GRCH38,
                                 ANNOTATION_VERSION_MM10 : ANNOTATION_VERSION_GRCM38 }
CORRESPONDING_UCSC_FROM_NCBI = { ncbi_annot: ucsc_annot 
                                for ( ucsc_annot, ncbi_annot ) in CORRESPONDING_NCBI_FROM_UCSC.items() }


# Current annotation versions
CURRENT_NCBI_ANNOTATION = { HSAPIENS : ANNOTATION_VERSION_GRCH38,
                            MMUSCULUS : ANNOTATION_VERSION_GRCM38 }

CURRENT_UCSC_ANNOTATION = { HSAPIENS : ANNOTATION_VERSION_HG38,
                            MMUSCULUS : ANNOTATION_VERSION_MM10 }

# Ensembl release corresponding to the current annotation
CURRENT_ENSEMBL_RELEASE = 90


# ===============================================================================
# Constants relative to the Gene / GeneAlias / util tables of the database
# ===============================================================================

# GeneAlias: prefix used for official / approved symbols
ALIAS_OFF_PREFIX = 'OFF:'

# UTGeneFromAlias: character used to separated the gene IDs
GENEFROMALIAS_SEPARATOR_IDS = ','

# UTDSTranscriptGeneConflict: character used to separated the gene IDs
UTDSTRANSCRIPTGENECONFLICT_SEPARATOR_IDS = ','


# ===============================================================================
# Constants relative to the connection to the database
# ===============================================================================

DB_SETTINGS_DB_NAME = 'db_name'
DB_SETTINGS_DB_TYPE = 'db_type'
DB_SETTINGS_MYSQL_USER = 'mysql_user'
DB_SETTINGS_MYSQL_PASSWD = 'mysql_passwd'
DB_SETTINGS_MYSQL_HOST = 'mysql_host'
DB_SETTINGS_MYSQL_PORT = 'mysql_port'
DB_SETTINGS_DB_FOLDER = 'db_folder'


# ===============================================================================
# Constants relative to logs
# ===============================================================================

PATH_LOG = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER, 'execution.log' )

LOG_APPEND = 'a'
LOG_NO_APPEND = 'w'
LOG_DEFAULT = LOG_APPEND

LOG_SIZE_MAX = 1000000
LOG_MAX_FILES_NB = 1000

MODE_DEBUG = logging.DEBUG
MODE_INFO = logging.INFO
MODE_WARNING = logging.WARNING
MODE_ERROR = logging.ERROR
MODE_CRITICAL = logging.CRITICAL

# Verbosity levels
LOG_MODE_DEBUG = 'debug'
LOG_MODE_INFO = 'info'
LOG_MODE_WARNING = 'warning'
LOG_MODE_ERROR = 'error'
LOG_MODE_CRITICAL = 'critical'

LOG_MODES = { LOG_MODE_DEBUG : MODE_DEBUG, 
              LOG_MODE_INFO : MODE_INFO,
              LOG_MODE_WARNING : MODE_WARNING,
              LOG_MODE_ERROR : MODE_ERROR,
              LOG_MODE_CRITICAL : MODE_CRITICAL }


# ===============================================================================
# Constants relative to gene reference logs
# ===============================================================================

PATH_GENEREF_LOG = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                 'generefwarnings.log' )

GENEREF_LOG_APPEND = 'a'
GENEREF_LOG_NO_APPEND = 'w'
GENEREF_LOG_DEFAULT = GENEREF_LOG_APPEND

GENEREF_LOG_SIZE_MAX = 1000000
GENEREF_LOG_MAX_FILES_NB = 1000


# ===============================================================================
# Constants relative to the files created by the program
# ===============================================================================

# Folder where to save libraries installed by R
CUSTOM_R_LIBRARY_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER, 
                                        '.Rlibrary' )

# Folder where to save files generated by the program
# and that may be read by the program
PARSED_DATA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER, 
                                   '.parsed_data' )

LIFTOVER_DATA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                     '.liftover_data' )

MERGED_DATA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                   '.merged_data' )

ANNOTATE_DATA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                     '.orf_annotations' )

BACKUP_DATA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                   '.backup' )

# Extension to use for the file generated by the program
# and that may be read by the program
DENCELLORF_FILES_EXTENSION = '.dcorf'

# Folder where to save files generated by the program
# and that may be used for analysis
DB_CONTENT_CONSISTENCY_ASSESSMENT_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                                         'content_consistency_assessment' )

MERGE_DATA_ANALYSIS_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                                           'merged_data_analysis' )

BED_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                           'bed_files' )

TRACK_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                             'track_files' )

GFF_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                           'gff_files' )

FASTA_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                            'fasta_files' )

STAT_FOLDER = os.path.join( DefaultOutputFolder.OUTPUT_FOLDER,
                           'stat_files' )

# Default file names (without extensions)
DEFAULT_BED_FILENAME = PROJECT_NAME
DEFAULT_TRACK_FILENAME = 'trackDb'
DEFAULT_GFF_FILENAME = PROJECT_NAME
DEFAULT_FASTA_FILENAME = PROJECT_NAME

  # Default filename related to Merge strategy
ALL_EXISTING_ORF_TR_ASSO_IDS_FILENAME = 'all_existing_orf_tr_asso_ids'


# ===============================================================================
# Constants relative to the insertion of data in the database
# ===============================================================================

# Maximum number of objects to insert at one time
MAX_COUNT_TO_INSERT = 50000

# Maximum number of objects that can be updated in a same commit
MAX_COMMIT_BATCH_SIZE = 10000

# Maximum number of characters that may be stored in a string
# NB: Please, note that this number should never exceed 300. By default, use 250.
MAX_LEN_STRING = 300

# Replacing value for strings longer than the MAX_LEN_STRING value
REPLACE_TOO_LONG_STRINGS = 'TOO_LONG'

# Maximum number of characters that may be stored in a text
# NB: Please, note that this number should never exceed 65535. By default, use 250.
MAX_LEN_TEXT = SQLConstants.MAX_LEN_TEXT

# Replacing value for text longer than the MAX_LEN_TEXT value
REPLACE_TOO_LONG_TEXT = 'TOO_LONG'


# ===============================================================================
# Constants relative to the built of the PRO database
# ===============================================================================

## Merge strategy
# Maximum number of process that can be run in the same pool
MAX_POOL_SIZE = 20000
# Default threshold for absolute difference in genomic lengths
DEFAULT_MERGE_GEN_LEN_DIFF_THRESHOLD = 1

# Value to ignore the use of a minimal absolute difference in genomic 
# lengths threshold
GEN_LEN_DIFF_THRESHOLD_IGNORE = -1


# ===============================================================================
# Constants relative to the DenCellORFObjects
# ===============================================================================

## Chromosomes
# Chromosome name to use when a feature is located on both X and Y chromosomes 
CHROMOSOME_NAME_XY = 'X|Y'
CHROMOSOME_X = 'X'
CHROMOSOME_Y = 'Y'

# Sexual chromosomes to change for CHROMOSOME_NAME_XY
SEX_CHROMOSOME = { HSAPIENS : '23',
                   MMUSCULUS : '20' }

# Chromosome name to use for mitochondrial chromosomes
MITOCHONDRIAL_CHR = 'MT'

# List of chromosome names considered equal as MT (i.e. mitochondrial)
MITOCHONDRIAL_CHR_LIST = [ 'mitochondrial', 'mitochondria', 'MT', 'M' ]

## Transcripts
# Prefix to add for "fake" transcripts
PREFIX_FAKE_TRANSCRIPT = 'UNKNOWN_TRANSCRIPT_'

# Value for Unknown transcripts (PRO database)
UNKNOWN_TRANSCRIPT = 'UNKNOWN_TRANSCRIPT'

## Genes
# Prefix to add for "unknown" genes
PREFIX_UNKNOWN_GENE = 'UNKNOWN_GENE_'

# Prefix to add for "overlapping" genes
PREFIX_OVERLAPPING_GENES = 'OVERLAPPING_GENES_'
PREFIX_OVERLAPPING_LNCRNAS = 'OVERLAPPING_LNCRNAS_'

# Prefix to add for "genes" located in intergenic regions
PREFIX_INTERGENIC_GENE = 'INTERGENIC_GENE_'

# Prefix to add for "conflicting" genes. These are gene IDs generated when the same transcript ID
# has been found associated with several gene IDs.
PREFIX_CONFLICT_GENE_TRANSCRIPT = 'CONFLICT_GENE_'

# Cross-reference value to use when creating "fake" genes
FAKE_CROSSREF = 'FAKE_GENE'

## ORFs
# Separator to use between each splicing genomic coordinates
    # NB: This constant should not be changed unless sORFs.org parser is updated 
    #     as this last import splicing coordinates directly in the original format
    #     (i.e. using '_' as separator)
ORF_SPLICING_COORD_SEPARATOR = '_'

## ORFTranscriptAsso
# Separator to use between each values provided in lists (e.g. length_nt, orf_score)
OTA_LIST_VALUES_SEPARATOR = '_'

## Common to several DenCellORFObjects
# Value to use for ambiguous attributes (i.e. attributes found different 
# for a same object)
DENCELLORFOBJ_AMBIGUOUS_ATT = 'AMBIGUOUS_FLAG'


# ===============================================================================
# Constants relative to the Metadata table
# ===============================================================================

METATABLE_CURRENT_ANNOTATION = 'current_annotation'
METATABLE_CURRENT_ANNOTATION_DESCRIPTION = 'Version of the annotation used in the database'

METATABLE_CURRENT_ENSEMBL_RELEASE = 'current_ensembl_release'
METATABLE_CURRENT_ENSEMBL_RELEASE_DESCRIPTION = 'Version of the ensembl release used'

METATABLE_DATABASE_VERSION_NUMBER = 'db_version_number'

METATABLE_DS_ORIGIN = 'ds_db_origin'
METATABLE_DS_ORIGIN_DESCRIPTION = 'Name of the DS database used'


# ===============================================================================
# Constants relative to the sequences
# ===============================================================================

# Sequence types
SEQUENCE_TYPE_DNA = 'DNA'
SEQUENCE_TYPE_PROT = 'PROT'

# Letters to use as ambiguous base / amino acid in consensus
SEQUENCE_AMBIGUOUS_DNA_BASE = 'N'
SEQUENCE_AMBIGUOUS_PROT_AA = 'X'

# Default value for the threshold to use when computing the consensus sequence
DEFAULT_SQCE_CONSENSUS_AMBIG_THRESHOLD = float( 2 ) / float( 3 )

# Default value for the maximal difference between the max. and min. lengths of
# DSORFTranscriptAsso to make them belong to the same group (cf. MergeStrategy
# split_dsota_using_length() method for more information)
DEFAULT_MAX_LEN_DIFF_FOR_DSOTA_CLUSTERS = 3


# ===============================================================================
# Constants relative to the computation of relative coordinates 
# from absolute coordinates relative 
# ===============================================================================

# Maximum number of entries (DSORFTranscriptAsso or Transcript table)
# for which to compute the relative coordinates in the same R subprocess
MAX_ENTRIES_PER_DATAFRAME = 500


# ===============================================================================
# Constants relative to the merging of CellContext entries
# ===============================================================================

DEFAULT_CELL_CONTEXT_DICT = {   HSAPIENS:   { 
                                                'BJ':               [ 'loayza_puch_2013', 'rooijers_2013', 'ji_BJ_2015' ],
                                                'B_cell':           [ 'B cells' ],
                                                'Blood':            [ 'mills_2016' ],
                                                'Brain':            [ 'gonzalez_2014' ],
                                                'Brain_tumor':      [ 'Human brain tumor' ],
                                                'Breast':           [ 'ji_breast_2015' ],
                                                'Breast_tumor':     [ 'loayza_puch_2016' ],
                                                'HAP1':             [ 'jakobsson_2017' ],
                                                'HCT116':           [ 'crappe_2014' ],
                                                'HEK293':           [ 'lee_2012', 'andreev_2015', 'sidrauski_2015', 'liu_2013_HEK',
                                                                      'liu_HEK_2013', 'ingolia_2012', 'ingolia_2014', 'calviello_2016', 
                                                                      'iwasaki_2016', 'park_2017', 'zhang_2017' ],
                                                'HEK293T':          [ 'eichorn_2014', 'jan_2014' ],
                                                'HFF':              [ 'Primary human foreskin fibroblasts (HFFs)', 
                                                                      'Primary human fibroblast (HFF)', 'rutkowski_2015' ],
                                                'HeLa':             [ 'wang_2015', 'niu_2014', 'yoon_2014', 'liu_2013_HeLa', 'liu_Hela_2013',
                                                                      'stumpf_2013', 'park_2016', 'zur_2016', 'shi_2017' ],
                                                'hES':              [ 'werner_2015', 'xu_2016' ],
                                                'Jurkat':           [ 'gawron_2016' ],
                                                'LCL':              [ 'cenik_2015' ],
                                                'MCF7':             [ 'Loayza_Puch_2016' ],
                                                'MDA-MB-231':       [ 'rubio_2014' ],
                                                'MM1S':             [ 'wiita_2013' ],
                                                'Monocyte':         [ 'su_2015' ],
                                                'NCCIT':            [ 'grow_2015' ],
                                                'RPE-1':            [ 'tanenbaum_2015', 'tirosh_2015' ],
                                                'Skeletal_muscle':  [ 'wein_2014' ],
                                                'THP-1':            [ 'fritsch_2012', 'stern_ginossar_2012' ],
                                                'U2OS':             [ 'elkon_2015' ],
                                                'Flp-In_T-REx-293': [ 'malecki_2017' ]
                                            },
                                MMUSCULUS:  { 
                                                '3T3':              [ 'eichorn_3t3_2014' ],
                                                'BMDC':             [ 'jovanovic_2015', 'fields_2015' ],
                                                'B_cell':           [ 'eichorn_bcell_2014' ],
                                                'Brain':            [ 'gonzalez_2014_mmu', 'cho_2015', 'laguesse_2015' ],
                                                'C2C12':            [ 'deklerck_2015' ],
                                                'E14':              [ 'ingolia_2014_mmu', 'Ingolia_2011', 'ingolia_2011' ],
                                                'Glioma':           [ 'Mouse gliomal cells', ' Mouse gliomal cells' ],
                                                'Liver':            [ 'Mouse liver cell', 'eichorn_liver_2014', 'gao_liver_2014', 
                                                                      'gerashchenko_2016', 'janich_2015' ],
                                                'MEF':              [ ' Mouse Embryonic Fibroblast (MEFs)', 'Mouse Embryonic Fibroblast (MEFs)', 
                                                                      'thoreen_2012', 'lee_2012_mmu', 'gao_mef_2014', 
                                                                      'reid_er_2016', 'reid_cytosol_2016', 'reid_2014' ],
                                                'MESC':             [ 'Mouse Embryonic Stem Cells' ],
                                                'NSC':              [ 'katz_2014' ],
                                                'Neutrophil':       [ 'guo_2010_mmu' ],
                                                'R1E':              [ 'you_2015' ],
                                                'Skin_tumor':       [ 'blanco_2016' ],
                                                'Spleen_B_cell':    [ 'diaz_munoz_2015' ],
                                                'Testis':           [ 'castaneda_2014' ],
                                                'v6-5':             [ 'hurt_2013' ]
                                            } 
                            }


# ===============================================================================
# Constants relative to the ORF annotations
# ===============================================================================

# Maximal size for the ORF to be considered as a short ORF
# (the value is included)
DEFAULT_SHORT_ORF_ANNOTATION_SIZE_THRESHOLD = 100

# Annotations to ignore
ORF_ANNOTATION_TO_IGNORE = 'None'

# Short ORF
ORF_ANNOTATION_SHORT_ORF = 'sORF'

# Upstream ORFs
ORF_ANNOTATION_UPSTREAM = 'Upstream'

# Overlapping ORFs
ORF_ANNOTATION_OVERLAP = 'Overlapping'
ORF_ANNOTATION_EXONIC = 'Exonic'
ORF_ANNOTATION_INTRONIC = 'Intronic'
ORF_ANNOTATION_IN_CDS = 'InCDS'

# Downstream ORFs
ORF_ANNOTATION_DOWNSTREAM = 'Downstream'

# Intergenic ORFs 
ORF_ANNOTATION_INTERGENIC = 'Intergenic'

# ORFs located on non-coding regions
ORF_ANNOTATION_NON_CODING_LOCUS = 'ncRNA'

# ORFs located on pseudogenes
ORF_ANNOTATION_PSEUDOGENE = 'Pseudogene'

# Coding DNA Sequence
ORF_ANNOTATION_CDS = 'CDS'

# Non sense mediated decay
ORF_ANNOTATION_NMD = 'NMD'

# Non-stop decay
ORF_ANNOTATION_NSD = 'NSD'

# Alternative ORF
ORF_ANNOTATION_ALT = 'Alternative'

# ORF on readthrough sequences
ORF_ANNOTATION_READTHROUGH = 'Readthrough'

# ORF overlapping more than the whole CDS
ORF_ANNOTATION_NEW_CDS = 'NewCDS'

# ORF located on the opposite strand of the transcript
ORF_ANNOTATION_OPPOSITE = 'Opposite'

# Dictionary associating all the provided categories
# to the one to use in the database
ORF_CATEGORY_CORRESP = { 
                            ORF_ANNOTATION_TO_IGNORE:        [ 'NO_FRAME', 'other', 'TEC', 'In' ],
                            ORF_ANNOTATION_SHORT_ORF:        [ 'sORF' ],
                            ORF_ANNOTATION_OVERLAP:          [ 'CDS_overlap', 'uoORF', 'ANTISENSE' ],
                            ORF_ANNOTATION_CDS:              [ 'annotated', 'Annotated', 'Isoform' ],
                            ORF_ANNOTATION_INTRONIC:         [ 'INTRON', 'iORF', 'intronic', 'RETAINED_INTRON' ],
                            ORF_ANNOTATION_EXONIC:           [ 'EXON', 'exonic' ],
                            ORF_ANNOTATION_UPSTREAM:         [ '5UTR', '5_UTR', 'uoORF', 'uORF', 'utr5' ],
                            ORF_ANNOTATION_DOWNSTREAM:       [ '3UTR', '3_UTR', 'dORF', 'utr3' ],
                            ORF_ANNOTATION_INTERGENIC:       [ 'lincRNA', 'INTERGENIC', 'intergenic' ],
                            ORF_ANNOTATION_NON_CODING_LOCUS: [ 'lincRNA', 'lncrna', 'ncRNA' ],
                            ORF_ANNOTATION_PSEUDOGENE:       [ 'pseudogene' ],
                            ORF_ANNOTATION_NMD:              [ 'NMD' ],
                            ORF_ANNOTATION_NSD:              [ 'NSD' ],
                            ORF_ANNOTATION_ALT:              [ 'Out', 'alternative_frame' ]
                        }

# Dictionary associating all the existing RNA biotypes
# to ORF annotations
# NB: Some biotypes (e.g. 'Protein coding') have not been 
#     associated to any ORF annotation in this dictionary
#     as they are not sufficient to perform a valuable
#     annotation of the ORF (i.e. the comparison of the ORF
#     coordinates to the CDS ones is necessary to annotated it)
#     Cf. documentation and Ensembl website for list of biotypes.
ORF_BIOTYPE_ANNOT_CORRESP = {
                                ORF_ANNOTATION_OVERLAP:             [ 'Antisense', 'antisense', 'antisense_RNA', 'Antisense_RNA' ],
                                ORF_ANNOTATION_INTRONIC:            [ 'retained_intron',
                                                                      'sense_intronic',
                                                                      'sense_overlapping' ],
                                ORF_ANNOTATION_DOWNSTREAM:          [ "3' overlapping ncRNA" ],
                                ORF_ANNOTATION_INTERGENIC:          [ 'Long intergenic ncRNA', 'lincRNA' ],
                                ORF_ANNOTATION_NON_CODING_LOCUS:    [ 'Non coding', 'ncRNA',
                                                                      'Processed transcript', 'processed_transcript', 
                                                                      'Long non-coding RNA', 'lncRNA', 
                                                                      "3' overlapping ncRNA",
                                                                      'Macro lncRNA',
                                                                      'Long intergenic ncRNA', 'lincRNA',
                                                                      'miRNA', 
                                                                      'miscRNA', 
                                                                      'piRNA', 
                                                                      'rRNA', 
                                                                      'siRNA', 
                                                                      'snRNA', 
                                                                      'snoRNA', 
                                                                      'tRNA', 
                                                                      'vaultRNA' ],
                                ORF_ANNOTATION_PSEUDOGENE:          [ 'Pseudogene',
                                                                      'IG pseudogene', 
                                                                      'Polymorphic pseudogene', 
                                                                      'Processed pseudogene', 'processed_pseudogene',
                                                                      'Transcribed pseudogene', 'transcribed_processed_pseudogene', 
                                                                      'transcribed_unprocessed_pseudogene', 'unprocessed_pseudogene',
                                                                      'transcribed_unitary_pseudogene',
                                                                      'Translated pseudogene',  
                                                                      'Unitary pseudogene', 'unitary_pseudogene',
                                                                      'Unprocessed pseudogene' ],
                                ORF_ANNOTATION_NMD:                 [ 'Non sense mediated decay',
                                                                      'NMD', 'nonsense_mediated_decay' ],
                                ORF_ANNOTATION_NSD:                 [ 'non_stop_decay' ],
                                ORF_ANNOTATION_READTHROUGH:         [ 'Readthrough',
                                                                      'Stop codon readthrough' ]
                            }

# Constants relative to the criteria used to perform the annotation
  # Criteria based upon the maximal amino acid length (ORFTranscriptAsso table)
ANNOTATE_CRITERIA_MAX_AA_LEN = 'max_aa_len'

  # Criteria based upon the cumulative exonic length (ORF table)
ANNOTATE_CRITERIA_EXONIC_LEN = 'exonic_len'

  # Criteria based upon the biotype of the related transcript
ANNOTATE_CRITERIA_BIOTYPE = 'biotype'

  # Criteria based upon the ORF and CDS coordinates
ANNOTATE_CRITERIA_COORD = 'coordinates'

# Dictionary associating all the existing ORF annotations with
# the family of criteria used to perform the annotation
  # Family of criteria based on the ORF length
ANNOTATION_FAMILY_LEN = 'Length'

  # Family of criteria based on the biotype of the related transcript
ANNOTATION_FAMILY_BIOTYPE = 'Biotype'

  # Family of criteria based on the relative position
ANNOTATION_FAMILY_REL_POS = 'Relative position'

  # Family of criteria based on the reading frame
ANNOTATION_FAMILY_READING_FRAME = 'Reading frame'

  # Family of criteria based on the strand
ANNOTATION_FAMILY_STRAND = 'Strand'

  # Dictionary that associate each existing annotation
  # with its family
ORF_ANNOTATION_CATALOG_FAMILY_CORRESP = { ANNOTATION_FAMILY_LEN: [ ORF_ANNOTATION_SHORT_ORF ],
                                          ANNOTATION_FAMILY_BIOTYPE:[ ORF_ANNOTATION_INTERGENIC,
                                                                      ORF_ANNOTATION_NON_CODING_LOCUS,
                                                                      ORF_ANNOTATION_PSEUDOGENE,
                                                                      ORF_ANNOTATION_NMD,
                                                                      ORF_ANNOTATION_NSD,
                                                                      ORF_ANNOTATION_READTHROUGH ],
                                          ANNOTATION_FAMILY_REL_POS: [ ORF_ANNOTATION_UPSTREAM, 
                                                                       ORF_ANNOTATION_OVERLAP,
                                                                       ORF_ANNOTATION_EXONIC,
                                                                       ORF_ANNOTATION_INTRONIC,
                                                                       ORF_ANNOTATION_IN_CDS,
                                                                       ORF_ANNOTATION_DOWNSTREAM,
                                                                       ORF_ANNOTATION_CDS,
                                                                       ORF_ANNOTATION_NEW_CDS, ],
                                        ANNOTATION_FAMILY_READING_FRAME: [ ORF_ANNOTATION_ALT ],
                                        ANNOTATION_FAMILY_STRAND: [ ORF_ANNOTATION_OPPOSITE ] }
                                       


# ===============================================================================
# Constants relative to the filtering
# ===============================================================================

# Filter types
  # Intersection
FILTER_INTERSECTION = 'intersection'

  # Union
FILTER_UNION = 'union'
  