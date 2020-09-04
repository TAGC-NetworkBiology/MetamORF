# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO

from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *


## ORFTranscriptAsso
#  =================
#
# Each ORFTranscriptAsso contains:
#     - id: Integer - A unique ORF-transcript association ID (Autoincremented).
#     - orf_id: Integer - The ORF ID.
#     - transcript_id: Integer - The transcript ID.
#     - rel_start_pos: Integer - The ORF start position in coordinates relative to the transcript.
#     - rel_stop_pos: Integer - The ORF stop position in coordinates relative to the transcript.
#     - predicted: Boolean - Has the ORF already been predicted by computational biology?
#     - ribo_seq: Boolean - Has the ORF already been detected or predicted from Ribo-seq data?
#     - ms_info: Boolean - Has the ORF already been detected by mass spectrometry?
#     - start_codon_seq: String - The nucleotidic sequence consensus of the start codon.
#     - start_flanking_seq: String(20) - The sequences flanking the start codon and used to compute
#                                        the Kozak context.
#     - sequence_nt: Text - The nucleotidic sequence consensus of the ORF.
#     - sequence_aa: Text - The amino acid sequence consensus of the ORF.
#     - kozak_context: Boolean - Has a Kozak context already been reported for the start codon?
#     - kozak_context_comp: String(30) - The Kozak context computed from the relative start position
#                                    and the flanking sequence.
#     - length_nt_min: Integer - The minimal length (in nucleotides) reported for this ORF.
#     - length_nt_max: Integer - The maximal length (in nucleotides) reported for this ORF.
#     - length_nt_median: Float - The median length (in nucleotides) reported for this ORF.
#     - length_nt_values: Integer - The list of lengths (in nucleotides) reported for this ORF.
#     - length_aa_min: Integer - The minimal length (in amino acids) reported for this ORF.
#     - length_aa_max: Integer - The maximal length (in amino acids) reported for this ORF.
#     - length_aa_median: Float - The median length (in amino acids) reported for this ORF.
#     - length_aa_values: String - The list of lengths (in amino acids) reported for this ORF.
#     - orf_score_min: Float - The minimal ORF score reported for this ORF.
#     - orf_score_max: Float - The maximal ORF score reported for this ORF.
#     - orf_score_median: Float - The median ORF score reported for this ORF.
#     - orf_score_values: String - The list of ORF score reported for this ORF.
#     - phylocsf_min: Float - The minimal PhyloCSF score reported for this ORF.
#     - phylocsf_max: Float - The maximal PhyloCSF score reported for this ORF.
#     - phylocsf_median: Float - The maximal PhyloCSF score reported for this ORF.
#     - phylocsf_values: String - The list of PhyloCSF scores reported for this ORF.
#     - phastcons_min: Float - The minimal PhastCons score reported for this ORF.
#     - phastcons_max: Float - The maximal PhastCons score reported for this ORF.
#     - phastcons_median: Float - The median PhastCons score reported for this ORF.
#     - phastcons_values: Float - The list of PhastCons scores reported for this ORF.
#     - floss_min: Float - The minimal FLOSS score reported for this ORF.
#     - floss_max: Float - The maximal FLOSS score reported for this ORF.
#     - floss_median: Float - The median FLOSS score reported for this ORF.
#     - floss_values: String - The list of FLOSS scores reported for this ORF.
#     - count_ds: Integer - The number of DSORFTranscriptAsso that have been merged to create 
#                           the current entry.
#     - count_computed_clusters: Integer - The number of "clusters" computed based upon the amino 
#                                          acid ORF length reported in the DSORFTranscript entries 
#                                          from which the ORFTranscriptAsso has been created.
#     - count_prov_lengths: Integer - The number of amino acid lengths that have been used in order
#                                     to compute the "clusters".
#     - computed_clusters: Text - The description of the "clusters" computed based upon the amino
#                                 acid ORF length reported in the DSORFTranscript entries from which 
#                                 the ORFTranscriptAsso has been created.
#     - gen_len_eq_orf_len: Boolean - Does the genomic length (computed using genomic coordinates)
#                                     equal the provided ORF length?
#
class ORFTranscriptAsso( BasePRO ):
    
    __tablename__ = 'ORFTranscriptAsso'
    
    id = Column( Integer, 
                 autoincrement=True )
    orf_id = Column( Integer, 
                     ForeignKey( 'ORF.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    transcript_id = Column( Integer, 
                            ForeignKey( 'Transcript.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    
    rel_start_pos = Column( Integer )
    rel_stop_pos = Column( Integer )
    
    predicted = Column( Boolean )
    ribo_seq = Column( Boolean )
    ms_info = Column( Boolean )
    
    start_codon_seq = Column( String( 3, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_flanking_seq = Column( String( 20, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    sequence_nt = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    sequence_aa = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    kozak_context = Column( Boolean )
    kozak_context_comp = Column( String( 30, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    length_nt_min = Column( Integer )
    length_nt_max = Column( Integer )
    length_nt_median = Column( Float )
    length_nt_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    length_aa_min = Column( Integer )
    length_aa_max = Column( Integer )
    length_aa_median = Column( Float )
    length_aa_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    orf_score_min = Column( Float )
    orf_score_max = Column( Float )
    orf_score_median = Column( Float )
    orf_score_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    phylocsf_min = Column( Float )
    phylocsf_max = Column( Float )
    phylocsf_median = Column( Float )
    phylocsf_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    phastcons_min = Column( Float )
    phastcons_max = Column( Float )
    phastcons_median = Column( Float )
    phastcons_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    floss_min = Column( Float )
    floss_max = Column( Float )
    floss_median = Column( Float )
    floss_values = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    count_ds = Column( Integer )
    count_computed_clusters = Column( Integer )
    count_prov_lengths = Column( Integer )
    computed_clusters = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    gen_len_eq_orf_len = Column( Boolean )
    

    # Define the unique constraint on "primary key-like attributes"
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'orf_id', 'transcript_id' ),
                    )

    # Define the one-to-many relationships
    ORFTranscriptAssoDSAsso_list = relationship( 'ORFTranscriptAssoDSAsso', cascade = 'all', backref = 'ORFTranscriptAssoDSAsso' )
    CellContext_list = relationship( 'CellContext', cascade = 'all', backref = 'ORFTranscriptAssoDSAsso' )
    ProvidedCategory_list = relationship( 'ProvidedCategory', cascade = 'all', backref = 'ORFTranscriptAssoDSAsso' )
    FLOSSClass_list = relationship( 'FLOSSClass', cascade = 'all', backref = 'ORFTranscriptAssoDSAsso' )
    ORFCategory_list = relationship( 'ORFCategory', cascade = 'all', backref = 'ORFTranscriptAsso' )
    ORFAnnotation_list = relationship( 'ORFAnnotation', cascade = 'all', backref = 'ORFTranscriptAsso' )
