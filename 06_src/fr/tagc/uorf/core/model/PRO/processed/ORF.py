# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORF
#  ===
#
# Each ORF contains:
#     - id: Integer - Unique ORF ID.
#     - chromosome: String - The chromosome name harboring the ORF.
#     - strand: String - The strand (+/-) in which the ORF is encoded (in the current genome version).
#     - start_pos: Integer - The genomic coordinates of the start codon (in the current genome version).
#     - stop_pos: Integer - The genomic coordinates of the stop codon (in the current genome version).
#     - spliced: Boolean - Is the ORF spliced?
#     - spliced_parts_count: Integer - The number of "exons" in the ORF.
#     - splice_starts: String - The genomic coordinates of the starts of the several "exons" of the ORF 
#                               (in the current genome version).
#     - splice_ends: String - The genomic coordinates of the ends of the several "exons" of the ORF
#                             (in the current genome version).
#     - sequence: Test - The sequence get using the genomic coordinates (in the current genome version).
#     - sequence_aa: Text - The sequence get by translated the nucleic sequence.
#     - genomic_length: Integer - The ORF length, computed using genomic coordinates.
#     - count_ds: Integer - The number of times this ORF has originally been reported.
#     - count_ds_ambiguous: Integer - The number of times this ORF may have been reported by the datasource.
#
class ORF( BasePRO ):

    __tablename__ = 'ORF'
    
    id = Column( Integer )
    chromosome = Column( String( 15, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_pos = Column( Integer )
    stop_pos = Column( Integer )
    spliced = Column( Boolean )
    spliced_parts_count = Column( Integer )
    splice_starts = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    splice_ends = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    sequence = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    sequence_aa = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    genomic_length = Column( Integer )
    count_ds = Column( Integer )
    count_ds_ambiguous = Column( Integer )
    
    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'chromosome', 'strand', 'start_pos', 'stop_pos', 
                                          'spliced', 'splice_starts', 'splice_ends', 
                                          'spliced_parts_count' ),
                    )

    # Define one-to-many relationship
    ORFDSAsso_list = relationship( 'ORFDSAsso', cascade = 'all', backref = 'ORF' )
    ORFTranscriptAsso_list = relationship( 'ORFTranscriptAsso', cascade = 'all', backref = 'ORF' )
    UTBEDContent = relationship( 'UTBEDContent', cascade = 'all', backref = 'ORF', uselist = False )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: ORF - Another ORF object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.id == other.id )
               or ( ( self.chromosome == other.chromosome ) 
                    and ( self.strand == other.strand ) 
                    and ( self.start_pos == other.start_pos )
                    and ( self.stop_pos == other.stop_pos )
                    and ( self.spliced == other.spliced )
                    and ( self.spliced_parts_count == other.spliced_parts_count )
                    and ( self.splice_starts == other.splice_starts )
                    and ( self.splice_ends == other.splice_ends ) ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a ORF object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the ORF object.
    #
    def __hash__( self ):
        
        return hash( ( self.chromosome, self.strand, self.start_pos, self.stop_pos,
                       self.spliced, self.spliced_parts_count, self.splice_starts, 
                       self.splice_ends ) )
            