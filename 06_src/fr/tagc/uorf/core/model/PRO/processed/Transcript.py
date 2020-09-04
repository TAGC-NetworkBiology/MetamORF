# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.Base import BasePRO

from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## Transcript
#  ==========
#
# Each Transcript contains:
#     - id: Integer - A unique transcript ID.
#     - transcript_id: String - The transcript ID.
#     - transcript_name: String - The transcript name.
#     - gene_id: String - The unique gene ID.
#     - strand: String - The strand of the transcript.
#     - start_pos: Integer - The genomic coordinates of the first nucleotide of the transcript 
#                            (in the current annotation version).
#     - end_pos: Integer - The genomic coordinates of the last nucleotide of the transcript
#                          (in the current annotation version).
#     - sequence: Text - The sequence of nucleotides get using the genomic coordinates 
#                        (in the current annotation version).
#     - cds_start_pos: Integer - The genomic coordinates of the start codon of the CDS 
#                                (in the current annotation version).
#     - cds_stop_pos: Integer - The genomic coordinates of the stop codon of the CDS 
#                               (in the current annotation version).
#     - rel_cds_start_pos: Integer - The CDS start position in coordinates relative to the transcript.
#     - rel_cds_stop_pos: Integer - The CDS stop position in coordinates relative to the transcript.
#     - cds_genomic_length: Integer - The CDS length in nucleotides (excludes the introns, includes stop codon).
#     - rna_biotype: String - The RNA biotype ('mRNA', 'lncRNA'...).
#     - count_ds: Integer - The number of times this transcript has originally been reported.
#     - count_ds_ambiguous: Integer - The number of times this transcript may have been reported 
#                                     by the datasource.
#
class Transcript( BasePRO ):

    __tablename__ = 'Transcript'
            
    id = Column( Integer )
    transcript_id = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    transcript_name = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation=SQLCollationManager.get_instance().get_db_collation() ), 
                      ForeignKey( 'PROGene.gene_id', ondelete='CASCADE', onupdate='CASCADE' ) )
    strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_pos = Column( Integer )
    end_pos = Column( Integer )
    sequence = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    cds_start_pos = Column( Integer )
    cds_stop_pos = Column( Integer )
    cds_genomic_length = Column( Integer )
    rel_cds_start_pos = Column( Integer )
    rel_cds_stop_pos = Column( Integer )
    rna_biotype = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    count_ds = Column( Integer )
    count_ds_ambiguous = Column( Integer )

    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'transcript_id', 'gene_id' ),
                    )

    # Define the one-to-many relationship
    TranscriptDSAsso_list = relationship( 'TranscriptDSAsso', cascade = 'all', backref = 'Transcript' )
    ORFTranscriptAsso_list = relationship( 'ORFTranscriptAsso', cascade = 'all', backref = 'Transcript' )
    