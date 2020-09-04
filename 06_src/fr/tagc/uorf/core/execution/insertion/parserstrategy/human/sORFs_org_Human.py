# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.execution.insertion.parserstrategy.common.sORFs_org import sORFs_org

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log import *


# ===============================================================================
# Description of the file parsed using this class
# ===============================================================================

## Source: sORFs.org
#
# NB: This file contains a header.
#     This file is expected to be in a tab-delimited format.
#
## Description of the columns of the raw data file:
#  A complete description of each attribute is provided with the "sORFs_org" parser 
#  (metaclass of the current parser).
#- [0]: Sorf ID: See description of "Sorf ID"
#- [1]: Chromosome
#- [2]: Strand
#- [3]: Sorf start
#- [4]: Sorf end
#- [5]: Sorf length
#- [6]: Cell line
#- [7]: Spliced
#- [8]: Spliced start sites: See description of "Spliced start parts"
#- [9]: Spliced stop parts
#- [10]: Start codon
#- [11]: Ensembl Transcript ID: See description of "Ensembl transcript ID"
#- [12]: Transcript Sequence: See description of "Transcript sequence"
#- [13]: AA sequence: See description of "AA-sequence"
#- [14]: Annotation
#- [15]: Biotype
#- [16]: FLOSS classification: See description of "Floss-Classification"
#- [17]: RPF coverage
#- [18]: RPF coverage uniformity
#- [19]: RPKM
#- [20]: Rltm min Rchx
#- [21]: Peak shift
#- [22]: In frame coverage
#- [23]: Exon overlap
#- [24]: FLOSS: See description of "FLOSS score"
#- [25]: In frame
#- [26]: Mass
#- [27]: ORFscore: See description of "Orfscore"
#- [28]: Cutoff p-value: See description of "cutoff p-value"
#- [29]: Pc exon overlap: See description of "overlap with PC exons"
#- [30]: PhastCon
#- [31]: PhyloP
#- [32]: Downstream gene distance
#- [33]: Upstream gene distance


# ===============================================================================
# File parser
# ===============================================================================


## sORFs_org_Human
#  ===============
#
# This class inherits from sORFs_org and allows to parse data 
# from the sORFs.org Human database.
#
class sORFs_org_Human( sORFs_org ):
        
        
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.HSAPIENS ] ]
                                                
    # Headers
    HEADER_ORF_ID = 'Sorf ID'
    HEADER_CHROMOSOME = 'Chromosome'
    HEADER_TRANSCRIPT_ID = 'Ensembl transcript ID'
    
    HEADER_STRAND = 'Strand'
    HEADER_START_POS = 'Sorf start'
    HEADER_STOP_POS = 'Sorf end'
    HEADER_SPLICED = 'Spliced'
    HEADER_SPLICE_STARTS = 'Spliced start parts'
    HEADER_SPLICE_ENDS = 'Spliced stop parts'
    
    HEADER_CELL_CONTEXT = 'Cell line'
    HEADER_ORF_SEQUENCE = 'Transcript sequence'
    HEADER_ORF_SEQUENCE_AA = 'AA-sequence'
    HEADER_ORF_ANNOTATION = 'Annotation'
    HEADER_ORF_BIOTYPE = 'Biotype'
    HEADER_ORF_LENGTH = 'Sorf length'
    HEADER_ORF_SCORE = 'Orfscore'
    HEADER_PHASTCONS = 'PhastCon'
    HEADER_FLOSS_SCORE = 'FLOSS score'
    HEADER_FLOSS_CLASS = 'Floss-Classification'
    
    HEADER_LIST = [ HEADER_ORF_ID, HEADER_CHROMOSOME, HEADER_TRANSCRIPT_ID, HEADER_STRAND, 
                    HEADER_START_POS, HEADER_STOP_POS, HEADER_SPLICED, HEADER_SPLICE_STARTS, 
                    HEADER_SPLICE_ENDS, HEADER_CELL_CONTEXT, HEADER_ORF_SEQUENCE, 
                    HEADER_ORF_SEQUENCE_AA, HEADER_ORF_ANNOTATION, HEADER_ORF_BIOTYPE, 
                    HEADER_ORF_LENGTH, HEADER_ORF_SCORE, HEADER_PHASTCONS, HEADER_FLOSS_SCORE, 
                    HEADER_FLOSS_CLASS ]
    
    # Constants
    DATA_SOURCE = 'sORFs_org_Human'
    SOURCE_DESCRIPTION = 'Olexiouk et al., Nucl. Ac. Res., 2018. H. sapiens database downloaded from sORFs.org using the Biomart Graphic User Interface. The following parameters were used to query the database: "Homo sapiens" > "no filters" > "select all MAIN_ATTRIBUTES" > "results" > "download data".'
    
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = Constants.ANNOTATION_VERSION_GRCH38
    
    # Annotation version as described in the data source
    ANNOTATION_DESCRIPTION = 'Ensembl versions 81 to 90.'
    
    # Ensembl release corresponding to the annotation version
    ENSEMBL_RELEASE = '90'
    

    ## Constructor of sORFs_org
    #  ------------------------
    #
    def __init__( self, data_path ):
        sORFs_org.__init__( self, data_path )        



    ## execute
    #  -------
    #
    # Execute the parsing strategy.
    # See the execute() method documentation of the ParserStrategy metaclass 
    # and parse_file_content() method documentation of the sORFs_org metaclass for 
    # more information about the main steps of the algorithm run in this method.
    #
    # @return objects_to_insert: List - List of objects to insert in the database.
    #
    # @throw DenCellORFException: When this parser cannot be used for the species of the database.
    #
    def execute( self ):
        
        # Check this parser may be used for the species in the database
        sp = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        if ( sp not in self.AUTHORIZED_SPECIES ):
            raise DenCellORFException( 'The parser ' + self.data_source + 
                                       ' has been build to parse data from ' + 
                                       ', '.join( self.AUTHORIZED_SPECIES ) + 
                                       ' whilst data stored in this database is related to ' + sp + '.' )
                
        # Parse the content of the file and return the list of objects to insert in the database
        return self.parse_file_content()
        