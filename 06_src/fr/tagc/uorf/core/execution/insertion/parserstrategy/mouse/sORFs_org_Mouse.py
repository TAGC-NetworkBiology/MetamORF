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
# NB: This file contains a header
#     This file is expected to be in a tab-delimited format
#
## Description of the columns of the raw data file:
#  A complete description of each attribute is provided with the "sORFs_org" parser 
#  (metaclass of the current parser).
#- [0]: Sorf ID
#- [1]: Cell line
#- [2]: Chromosome
#- [3]: Strand
#- [4]: Sorf start
#- [5]: Sorf end
#- [6]: Spliced
#- [7]: Spliced start parts
#- [8]: Spliced stop parts
#- [9]: Sorf length
#- [10]: Start codon
#- [11]: Downstream gene distance
#- [12]: Upstream gene distance
#- [13]: Transcript sequence
#- [14]: AA-sequence
#- [15]: Mass
#- [16]: Annotation
#- [17]: Biotype
#- [18]: RPKM
#- [19]: RPF coverage
#- [20]: RPF coverage uniformity
#- [21]: Exon overlap
#- [22]: In frame coverage
#- [23]: In frame
#- [24]: overlap with PC exons
#- [25]: Ensembl transcript ID
#- [26]: Rltm min Rchx
#- [27]: FLOSS score
#- [28]: Floss-Classification
#- [29]: Orfscore
#- [30]: Peak shift
#- [31]: PhastCon
#- [32]: PhyloP
#- [33]: cutoff p-value



# ===============================================================================
# File parser
# ===============================================================================


## sORFs_org_Mouse
#  ===============
#
# This class inherits from sORFs_org and allows to parse data 
# from the sORFs.org Murine database.
#
class sORFs_org_Mouse( sORFs_org ):
        
        
    ## Class variables
    #  ---------------
    #
    # General constants
    AUTHORIZED_SPECIES = [ Constants.SPECIES_CATALOG[ Constants.MMUSCULUS ] ]
    
    # Headers
    HEADER_ORF_ID = 'sORF ID'
    HEADER_CHROMOSOME = 'Chromosome'
    HEADER_TRANSCRIPT_ID = 'Ensembl Transcript ID'
    
    HEADER_STRAND = 'Strand'
    HEADER_START_POS = 'Sorf start'
    HEADER_STOP_POS = 'Sorf end'
    HEADER_SPLICED = 'Spliced'
    HEADER_SPLICE_STARTS = 'Spliced start sites'
    HEADER_SPLICE_ENDS = 'Spliced stop parts'
        
    HEADER_CELL_CONTEXT = 'Cell line'
    HEADER_ORF_SEQUENCE = 'Transcript Sequence'
    HEADER_ORF_SEQUENCE_AA = 'AA sequence'
    HEADER_ORF_ANNOTATION = 'Annotation'
    HEADER_ORF_BIOTYPE = 'Biotype'
    HEADER_ORF_LENGTH = 'Sorf length'
    HEADER_ORF_SCORE = 'ORFscore'
    HEADER_PHASTCONS = 'PhastCon'    
    HEADER_FLOSS_SCORE = 'FLOSS'
    HEADER_FLOSS_CLASS = 'FLOSS classification'
    
    HEADER_LIST = [ HEADER_ORF_ID, HEADER_CHROMOSOME, HEADER_TRANSCRIPT_ID, HEADER_STRAND, 
                    HEADER_START_POS, HEADER_STOP_POS, HEADER_SPLICED, HEADER_SPLICE_STARTS, 
                    HEADER_SPLICE_ENDS, HEADER_CELL_CONTEXT, HEADER_ORF_SEQUENCE,
                    HEADER_ORF_SEQUENCE_AA, HEADER_ORF_ANNOTATION, HEADER_ORF_BIOTYPE, 
                    HEADER_ORF_LENGTH, HEADER_ORF_SCORE, HEADER_PHASTCONS, HEADER_FLOSS_SCORE, 
                    HEADER_FLOSS_CLASS ]
    
    # Constants
    DATA_SOURCE = 'sORFs_org_Mouse'
    SOURCE_DESCRIPTION = 'Olexiouk et al., Nucl. Ac. Res., 2018. M. musculus database downloaded from sORFs.org using the Biomart Graphic User Interface. The following parameters were used to query the database: "Mus musculus" > "no filters" > "select all MAIN_ATTRIBUTES" > "results" > "download data".'
        
    # Information about the annotation version of the genome used by the source
    # Annotation version
    ANNOTATION_VERSION = Constants.ANNOTATION_VERSION_GRCM38
    
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
            raise DenCellORFException( 'The parser ' + self.data_source + ' has been build to parse data from ' + 
                                       ', '.join( self.AUTHORIZED_SPECIES ) + 
                                       ' whilst data stored in this database is related to ' + sp + '.' )
                
        # Parse the content of the file and return the list of objects to insert in the database
        return self.parse_file_content()
                