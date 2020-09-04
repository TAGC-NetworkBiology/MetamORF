# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Text, Boolean, Float
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BaseDS

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager
from fr.tagc.uorf.core.util.genetics.GeneticsUtil import GeneticsUtil 
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *


## DSORFTranscriptAsso
#  ===================
#
# Each ORFTranscriptAsso contains:
#     - id: Integer - A unique ORF-transcript association ID.
#     - data_source: String - The name of the source.
#     - transcript_id: String - The unique transcript ID (id of related DSTranscript entry).
#     - uniq_orf_id: Integer - The unique ORF ID (id of related DSORF entry).
#     - predicted: Boolean - Was the ORF predicted by computational biology?
#     - ribo_seq: Boolean - Was the ORF detected or predicted from Ribo-seq data?
#     - cell_context: String - The cell line or context in which the ORF was described.
#     - orf_id: String - The ORF ID as defined in the publication where it was described (cf. data_source).
#     - start_codon_seq: String - The nucleic sequence of the start codon (as provided in the dataset).
#     - raw_sequence: Text - The nucleotidic sequence of the ORF (as provided in the dataset 
#                            in which it has been reported).
#     - raw_sequence_aa: Text - The amino acid sequence of the ORF (as provided in the dataset 
#                               in which it has been reported).
#     - kozak_context: String - The Kozak context of the start codon.
#     - orf_length_nt: Integer - The ORF length as provided by the source (in nucleotides).
#     - orf_length: Integer - The ORF length as provided by the source (in amino acids).
#     - provided_category: String - The ORF category provided in the original dataset.
#     - ms_info: Boolean - Is there any mass spectrometry evidence about the ORF-encoded peptide?
#     - orf_score: Float - The ORF score (provided by the source).
#     - phylocsf: Float - The PhyloCSF score of the ORF (provided).
#     - phastcons: Float - The PhastCons score of the ORF (provided).
#     - floss: Float - The FLOSS score of the ORF (provided).
#     - floss_class: String - The FLOSS class of the ORF (provided).
#     - gen_len_eq_orf_len: Boolean - Does the genomic length (computed using genomic coordinates) 
#                                     equal the provided ORF length?
#
class DSORFTranscriptAsso( BaseDS ):
    
    __tablename__ = 'DSORFTranscriptAsso'
    
    id = Column( Integer )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                          ForeignKey( 'DataSource.name', ondelete='CASCADE', onupdate='CASCADE' ) )
    transcript_id = Column( Integer, 
                            ForeignKey( 'DSTranscript.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    uniq_orf_id = Column( Integer, 
                          ForeignKey( 'DSORF.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    predicted = Column( Boolean )
    ribo_seq = Column( Boolean )
    cell_context = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    orf_id = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_codon_seq = Column( String( 3, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    raw_sequence = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    raw_sequence_aa = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    kozak_context = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    orf_length_nt = Column( Integer )    
    orf_length = Column( Integer )
    provided_category = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    ms_info = Column( Boolean )
    orf_score = Column( Float )
    phylocsf = Column( Float )
    phastcons = Column( Float )
    floss = Column( Float )
    floss_class = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    gen_len_eq_orf_len = Column( Boolean )

    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'data_source', 'transcript_id', 'uniq_orf_id', 
                                          'predicted', 'ribo_seq', 'cell_context' ),
                    )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: DSORFTranscriptAsso - Another DSORFTranscriptAsso object to
    #                                     compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.uniq_orf_id == other.uniq_orf_id )
               and ( self.transcript_id == other.transcript_id )
               and ( self.data_source == other.data_source )
               and ( self.cell_context == other.cell_context )
               and ( self.predicted == other.predicted ) 
               and ( self.ribo_seq == other.ribo_seq ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a DSORFTranscriptAsso object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the DSTranscript object.
    #
    def __hash__( self ):
        
        return hash( ( self.data_source, self.transcript_id, self.uniq_orf_id, 
                       self.predicted, self.ribo_seq, self.cell_context ) )


    ## update
    #  ------
    #
    # This method try to combine two instances of this class when they are "equals"
    # (i.e. share the same values for "primary key-like attributes") by getting the 
    # missing attributes. It tests the equality between non-primary-key attributes 
    # of two equal instances of this class, and raise an DenCellORFObjUpdateException 
    # if DSORFTranscriptAsso compared have different values for their non-primary key 
    # attributes.
    # If:
    #     - The self object is missing some values the other object has, then it updates
    #       the current object. 
    #     - The information provided by both objects are contradictory, it logs a warning.
    #
    # @param other: DSORFTranscriptAsso - Another DSORFTranscriptAsso object "equal" to the
    #                                     current one.
    #
    # @throw DenCellORFObjUpdateException: When different values are found for the same attributes
    #                                      of two objects assumed to be the same.
    #
    def update( self, other):
        
        # For each non-primary-key attribute, check if it is provided, 
        # try to update the current object by completing missing information 
        # using information provided by the other one and if there are attributes 
        # which have different values, raise an excpetion
        attributes_to_check = [ 'orf_id', 'raw_sequence', 'raw_sequence_aa', 'start_codon_seq', 
                                'kozak_context', 'orf_length_nt', 'orf_length', 'provided_category', 
                                'ms_info', 'orf_score', 'phylocsf', 'phastcons', 'floss', 
                                'floss_class', 'gen_len_eq_orf_len' ]
        
        # List of the attributes for which the value should be set to 
        # None if they are found different
        att_to_none_if_conflict = [ 'start_codon_seq', 'kozak_context', 'orf_length', 'orf_length_nt',
                                    'ms_info', 'orf_score', 'phylocsf', 'phastcons', 'floss' ]
        
        # List of the attributes for which the value should be set to 
        # 'AMBIGUOUS' if they are found different
        att_to_flag_if_conflict = [ 'provided_category', 'floss_class' ]
        
        # List of the attributes storing sequences
        att_sequences = [ 'raw_sequence', 'raw_sequence_aa' ]

        # Initialize a dictionary attributes for which there is a conflict
        conflicting_att = {}
        
        for att in attributes_to_check:
            
            self_att = getattr( self, att )
            other_att = getattr( other, att )
            
            self_att_is_empty = GeneralUtil.is_empty( self_att )
            other_att_is_empty = GeneralUtil.is_empty( other_att )
        
            # If the other attribute is provided
            if ( not other_att_is_empty ):
                
                # and if the self attribute is empty, fill it using the information of the other object
                if self_att_is_empty:
                    setattr( self, att, other_att )
                
                # and if the self attribute is filled and the two values of the attribute
                # are different, reset the value to 'AMBIGUOUS' or None or compute a consensus
                # for the sequences and keep track of this update
                # attribute and its values
                elif ( ( not self_att_is_empty ) and ( other_att != self_att ) ):
                    
                    if ( att in att_to_flag_if_conflict ):
                        setattr( self, att, Constants.DENCELLORFOBJ_AMBIGUOUS_ATT )
                        conflicting_att[ att ] = ( self_att, other_att, getattr( self, att ) )
                    
                    elif ( att in att_sequences ):
                        if ( att == 'raw_sequence' ):
                            sqce_type = Constants.SEQUENCE_TYPE_DNA
                        else:
                            sqce_type = Constants.SEQUENCE_TYPE_PROT
                        sqce_list = [ self_att, other_att ]
                        # Compute the consensus (the threshold is set to 1 as the same 
                        # DSORFTranscriptAsso may be updated several time but sequentially.
                        # Setting this threshold to 1 allow to always get a N/X as soon as
                        # there is an ambiguity for one of the nucleotide / amino acid.
                        sqce_consensus = GeneticsUtil.find_sqce_consensus( list_of_sequences = sqce_list, 
                                                                           sqce_type = sqce_type,
                                                                           threshold = 1 )
                        setattr( self, att, sqce_consensus )
                        conflicting_att[ att ] = ( self_att, other_att, getattr( self, att ) )
                        
                    elif ( att in att_to_none_if_conflict ):
                        setattr( self, att, None )
                        conflicting_att[ att ] = ( self_att, other_att, getattr( self, att ) )
        
        
        # If there are attributes for which there is a conflict, raise a DenCellORFObjUpdateException
        if ( conflicting_att != {} ):
            except_message = []
            for ( att, val ) in conflicting_att.items():
                except_message.append( 'the attribute ' + att + ' has been found with the values "' + 
                                       str( val[0] ) + '" and "' + str( val[1] ) + '",' +
                                       ' hence its value has been set to "' + str( val[2] ) + '"' )
            except_message = ', '.join( except_message ) + '.'
            
            raise DenCellORFObjUpdateException( except_message )
        