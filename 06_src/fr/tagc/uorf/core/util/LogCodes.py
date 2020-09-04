# -*- coding: utf-8 -*-


# This file contains codes that may be add to the message logged in order to facilitate
# the extraction of all the messages related to a particular issue in one single 
# command (e.g. using grep). See the documentation for the list of available log codes.

# ===============================================================================
# Codes related to warnings
# ===============================================================================

# Prefix to add prior all warning codes
WARN_PREFIX = 'W'

# Warnings related to file headers
WARN_HEADER = WARN_PREFIX + 'Header'
  ## Warnings related to duplicated headers
WARN_HEADER_DUPL = WARN_HEADER + 'Dupl'


# Warnings related to gene lists
WARN_GENELIST = WARN_PREFIX + 'GeneList'
  ## Warnings related to IDs in the gene lists
WARN_GENELIST_ID = WARN_GENELIST + 'ID'
    ### Warnings related to missing IDs in the gene lists
WARN_GENELIST_ID_MISS = WARN_GENELIST_ID + 'Miss'


# Warning related to ORF splicing information
WARN_SPLIC = WARN_PREFIX + 'Splic'
  ## Warning related to missing splicing information
WARN_SPLIC_MISS = WARN_SPLIC + 'Miss'
  ## Warning related to too long splicing information
WARN_SPLIC_TOOLONG = WARN_SPLIC + 'TooLong'


# Warning related to the association of new genes or transcripts to ORFs
WARN_ORFASSO = WARN_PREFIX + 'ORFAsso'

  ## Warning related to association of ORF with new gene entries
WARN_ORFASSO_GENE = WARN_ORFASSO + 'Gene'
    ### Warning related to association of ORF with a single gene using the transcript ID
WARN_ORFASSO_GENE_FROM_TR_ID = WARN_ORFASSO_GENE + 'FromTrID'
    ### Warning related to association of ORF with a single gene
WARN_ORFASSO_GENE_SING = WARN_ORFASSO_GENE + 'Sing'
    ### Warning related to association of ORF with several genes
WARN_ORFASSO_GENE_SEV = WARN_ORFASSO_GENE + 'Sev'
    ### Warning related to association of ORF with lncRNAs
WARN_ORFASSO_GENE_LNCR = WARN_ORFASSO_GENE + 'LncR'
      #### Warning related to association of ORF with a single lncRNA
WARN_ORFASSO_GENE_LNCR_SING = WARN_ORFASSO_GENE_LNCR + 'Sing'
      #### Warning related to association of ORF with several lncRNAs
WARN_ORFASSO_GENE_LNCR_SEV = WARN_ORFASSO_GENE_LNCR + 'Sev'
    ### Warning related to association of ORF with intergenic regions
WARN_ORFASSO_GENE_INTERG = WARN_ORFASSO_GENE + 'Integ'
    ### Warning related to association of ORF with unknown gene
WARN_ORFASSO_GENE_UNKN = WARN_ORFASSO_GENE + 'Unkn'
      #### Warning related to association of ORF with unknown gene due to missing strand
WARN_ORFASSO_GENE_UNKN_MISSTRAND = WARN_ORFASSO_GENE_UNKN + 'Misstrand'
      #### Warning related to association of ORF with unknown gene due to missing chromosome
WARN_ORFASSO_GENE_UNKN_MISCHR = WARN_ORFASSO_GENE_UNKN + 'Mischr'

  ## Warning related to association of ORF with new transcript entries
WARN_ORFASSO_TR = WARN_ORFASSO + 'Tr'


# Warnings related to discarded information
WARN_DISCARD = WARN_PREFIX + 'Discard'
  ## Warnings related to discarded ORF
WARN_DISCARD_ORF = WARN_DISCARD + 'ORF'


# Warnings related to insertion itself
WARN_INSERT = WARN_PREFIX + 'Insert'
  ## Warnings related to missing data / no data to be inserted
WARN_INSERT_NODATA = WARN_INSERT + 'Nodata'


# Warnings related to the comparison of objects
WARN_COMP = WARN_PREFIX + 'Comp'
  ## Warnings related to the comparison of DenCellORF objects (i.e. entries of the database)
WARN_COMP_DCORF = WARN_COMP + 'DCORF'


# Warnings related to programming issue
WARN_PROG = WARN_PREFIX + 'Prog'
  ## Warnings related to None values passed whilst this should not happen
WARN_PROG_NONE = WARN_PROG + 'None'
    

# Warnings related to problems during lift over (conversion of genomic coordinates)
WARN_LIFTOV = WARN_PREFIX + 'LiftOver'
  ## The value of the annotation version registered in the meta table was not the one expected and has been changed
WARN_LIFTOV_META_ANNOT_UP = WARN_LIFTOV + 'MetaAnnotUpdate'
  ## Warnings related to impossible conversion of a coordinate
WARN_LIFTOV_FAIL = WARN_LIFTOV + 'Fail'
  ## Warnings related to a chromosome returned after LiftOver different than expected
WARN_LIFTOV_DIFFCHR = WARN_LIFTOV + 'DiffChr'
    

# Warnings related to problems during the translation of a nucleic sequence
WARN_TRANSL = WARN_PREFIX + 'Transl'
  ## Warnings related to a wrong sequence size
WARN_TRANSL_SEQSIZE = WARN_TRANSL + 'SeqSize'
    ### Warnings logged when the size is not a multiple of 3
WARN_TRANSL_SEQSIZE_NOT3 = WARN_TRANSL_SEQSIZE + 'Not3'
    

# Warnings related to DenCellORF objects
WARN_DCORF = WARN_PREFIX + 'DCORF'
  ## Warnings related to DSORFTranscriptAsso objects
WARN_DCORF_DSOTA = WARN_DCORF + 'DSOTA'
    ### Warnings related to conflicting information contained in a DSORFTranscriptAsso object
WARN_DCORF_DSOTA_CONFL = WARN_DCORF_DSOTA + 'Confl'
      #### Conflict in sequence information
WARN_DCORF_DSOTA_CONFL_SEQ = WARN_DCORF_DSOTA_CONFL + 'Seq'
      #### Conflict in length in nucleotids
WARN_DCORF_DSOTA_CONFL_NTLEN = WARN_DCORF_DSOTA_CONFL + 'NtLen'
      #### Conflict in length in amino acids
WARN_DCORF_DSOTA_CONFL_AALEN = WARN_DCORF_DSOTA_CONFL + 'AALen'
      #### Conflict in length in amino acids and nucleotids
WARN_DCORF_DSOTA_CONFL_AANTLEN = WARN_DCORF_DSOTA_CONFL + 'AANtLen'
  ## Warnings related to Transcript objects
WARN_DCORF_TR = WARN_DCORF + 'TR'
    ### Conflict information about one of the attributes
WARN_DCORF_TR_CONFL = WARN_DCORF_TR + 'Confl'
    

# Warnings related to the merging step
WARN_MERG = WARN_PREFIX + 'Merg'
  ## Warnings related to conflict during the merging step
WARN_MERG_CONFL = WARN_MERG + 'Confl'
    ## Warnings related to conflicting information between the DSTranscript merged
WARN_MERG_CONFL_TR =WARN_MERG_CONFL + 'Tr'
    ## Warnings related to conflicting information between the Genes associated to the
    #  DSTranscript merged
WARN_MERG_CONFL_GENE_ASSO_TR =WARN_MERG_CONFL + 'GeneAssoTr'
    

# Warnings related to the relative coordinates
WARN_RELCOORD = WARN_PREFIX + 'RelCoord'
  ## Warnings related to conflicts during the computation of relative coordinates
WARN_RELCOORD_CONFL = WARN_RELCOORD + 'Confl'
    ### Warnings related to conflicting information about the OTA start codon
WARN_RELCOORD_CONFL_STARTCODON = WARN_RELCOORD_CONFL + 'StartCodon' 


# Warnings related to the ORF categories
WARN_ORFCAT = WARN_PREFIX + 'ORFCat'
  ## Warnings related to missing information in the association dictionary regarding a provided category
WARN_ORFCAT_PROV_NOTIN_DICT = WARN_ORFCAT + 'ProvNotInDict'


# Warnings related to the ORF annotations
WARN_ORFANNOT = WARN_PREFIX + 'ORFAnnot'
  ## Warnings related to conflicting information regarding an ORF annotation
WARN_ORFANNOT_CONFL = WARN_ORFANNOT + 'Confl'
    ### Warnings related to conflicting information about the strand of an ORF 
    ### and its associated transcript
WARN_ORFANNOT_CONFL_STRD = WARN_ORFANNOT_CONFL + 'Strd'


# Warnings related to the metadata
WARN_META = WARN_PREFIX + 'Meta'
  ## Warning related to the Ensembl Release
WARN_META_ENSEMBL_RELEASE = WARN_META + 'EnsemblRelease'
    ### Warning related to conflicting information about the Ensembl release
WARN_META_ENSEMBL_RELEASE_CONFL = WARN_META_ENSEMBL_RELEASE + 'Confl'


# Warnings related Ensembl queries
WARN_ENSEMBL = WARN_PREFIX + 'Ensembl'
  ## Warnings related to transcripts
WARN_ENSEMBL_TR = WARN_ENSEMBL + 'Tr'
    ### Warnings related to not found transcripts
WARN_ENSEMBL_TR_NOT_FOUND = WARN_ENSEMBL_TR + 'NotFound'




# ===============================================================================
# Codes related to errors
# ===============================================================================

# Prefix to add prior all error codes
ERR_PREFIX = 'E'

# Errors related to data source parsing
ERR_PARS = ERR_PREFIX + 'Pars'
  ## Errors related to parsing issues
ERR_PARS_PARSING = ERR_PARS + 'Parsing'
  ## Errors related to the initialization or execution of the parser
ERR_PARS_PARSER = ERR_PARS + 'Parser'


# Errors related to DenCellORF objects
ERR_DCORF = ERR_PREFIX + 'DCORF'
  ## Errors related to conflicting information about DenCellORF object attributes
ERR_DCORF_CONFL = ERR_DCORF + 'Confl'
    ### Errors related to conflicting information about DSTranscript attributes
ERR_DCORF_CONFL_DSTR = ERR_DCORF_CONFL + 'DSTr'
    ### Errors related to conflicting information about DSORF attributes
ERR_DCORF_CONFL_DSORF = ERR_DCORF_CONFL + 'DSORF'


# Errors related to gene lists
ERR_GENELIST = ERR_PREFIX + 'GeneList'
  ## Errors related to the format of the entries in the gene lists
ERR_GENELIST_FORM = ERR_GENELIST + 'Form'


# Errors related to SQL
ERR_SQL = ERR_PREFIX + 'SQL'
  ## Errors related to SQL sessions
ERR_SQL_SESSION = ERR_SQL + 'Session'
  ## Errors related to SQLite files
ERR_SQL_FILE = ERR_SQL + 'File'

# Errors related to DatabaseCheck
ERR_DBCHECK = ERR_PREFIX + 'DBCheck'

# Errors related to file handling
ERR_FILEHAND = ERR_PREFIX + 'FileHand'


# Errors related to lift over (conversion of genomic coordinates from a version to another)
ERR_LIFTOV = ERR_PREFIX + 'LiftOver'
  ## Errors related to conflicting information found during lift over
ERR_LIFTOV_CONFL = ERR_LIFTOV + 'Confl'
    ### Errors related to conflict on the strand information
ERR_LIFTOV_CONFL_STRAND = ERR_LIFTOV_CONFL + 'Strand'
    ### Errors related to conflict on the chromosome information
ERR_LIFTOV_CONFL_CHR = ERR_LIFTOV_CONFL + 'Chr'
    ### Errors related to conflict on the coordinates
ERR_LIFTOV_CONFL_POS = ERR_LIFTOV_CONFL + 'Pos'
    ### Errors related to conflict on the splicing coordinates
ERR_LIFTOV_CONFL_SPLCOORD = ERR_LIFTOV_CONFL + 'SplCoord'


# Errors related to downloads
ERR_DOWNLOAD = ERR_PREFIX + 'Download'
  ## Errors related to sequence downloads
ERR_DOWNLOAD_SEQ = ERR_DOWNLOAD + 'Seq'


# Errors related to deletions
ERR_DELETE = ERR_PREFIX + 'Delete'
  ## Errors related to sequence downloads
ERR_DELETE_DS = ERR_DELETE + 'Datasource'


# Errors related to ORF annotations
ERR_ORF_ANNOT_CONFL = ERR_PREFIX + 'ORFAnnotConfl'
  ## Errors related to positions
ERR_ORF_ANNOT_CONFL_POS = ERR_ORF_ANNOT_CONFL + 'Pos'
    ### ORF located out of the transcript bounds
ERR_ORF_ANNOT_CONFL_POS_OUT = ERR_ORF_ANNOT_CONFL_POS + 'Out'


# Errors related to the execution of sub-processes
ERR_SUBPROC = ERR_PREFIX + 'Subproc'
  ## Errors related to the execution of sub-processes in bash
ERR_SUBPROC_BASH = ERR_SUBPROC + 'Bash'
    ### Errors related to execution of grep command
ERR_SUBPROC_BASH_GREP = ERR_SUBPROC_BASH + 'Grep'
    ### The execution of bash command returned nothing
ERR_SUBPROC_BASH_EMPTY = ERR_SUBPROC_BASH + 'Empty'
