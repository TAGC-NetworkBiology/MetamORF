# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager

from fr.tagc.uorf.core.util.log.Logger import Logger


## DSORF
#  =====
#
# Each DSORF contains:
#     - id: Integer - Unique ORF ID.
#     - data_source: String - The name of the source.
#     - chromosome: String - The chromosome name harboring the ORF.
#     - raw_strand: String - The strand (+/-) in which the ORF is encoded (in the original genome version).
#     - raw_start_pos: Integer - The genomic coordinates of the start codon (in the original genome version).
#     - raw_stop_pos: Integer - The genomic coordinates of the stop codon (in the original genome version).
#     - spliced: Boolean - Is the ORF spliced?
#     - raw_splice_starts: String - The genomic coordinates of the starts of the several "exons" 
#                                   of the ORF (in the original genome version).
#     - raw_splice_ends: String - The genomic coordinates of the ends of the several "exons" 
#                                 of the ORF (in the original genome version).
#     - spliced_parts_count: Integer - The number of "exons" constituting the ORF.
#     - strand: String - The strand (+/-) in which the ORF is encoded (in the current genome version).
#     - start_pos: Integer - The genomic coordinates of the start codon (in the current genome version).
#     - stop_pos: Integer - The genomic coordinates of the stop codon (in the current genome version).
#     - splice_starts: String - The genomic coordinates of the starts of the several "exons" 
#                               of the ORF (in the current genome version).
#     - splice_ends: String - The genomic coordinates of the ends of the several "exons" 
#                             of the ORF (in the current genome version).
#     - raw_genomic_length: Integer -The ORF length, computed using the genomic coordinates 
#                                    (in the original genome version).
#     - genomic_length: Integer - The ORF length, computed using the genomic coordinates
#                                    (in the current genome version).
#     - genomic_length_diff: Integer - The absolute difference between the length computed using the 
#                                      genomic coordinates in the original genome version and the one
#                                      computed using the genomic coordinates in the current version.
#     - liftover_succeed: Integer - Did the lifotver succeed?
#
class DSORF( BaseDS ):

    __tablename__ = 'DSORF'
    
    id = Column( Integer )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                          ForeignKey( 'DataSource.name', ondelete='CASCADE', onupdate='CASCADE' ) )
    chromosome = Column( String( 15, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    raw_strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    raw_start_pos = Column( Integer )
    raw_stop_pos = Column( Integer )
    spliced = Column( Boolean )
    raw_splice_starts = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    raw_splice_ends = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    spliced_parts_count = Column( Integer )
    strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_pos = Column( Integer )
    stop_pos = Column( Integer )
    splice_starts = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    splice_ends = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()  ) )
    raw_genomic_length = Column( Integer )
    genomic_length = Column( Integer )
    genomic_length_diff = Column( Integer )
    liftover_succeed = Column( Boolean )
    
    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'data_source', 'chromosome', 'raw_strand', 
                                          'raw_start_pos', 'raw_stop_pos', 'spliced', 'raw_splice_starts', 
                                          'raw_splice_ends', 'spliced_parts_count' ),
                    )

    # Define the one-to-many relationship
    DSORFTranscriptAsso_list = relationship( 'DSORFTranscriptAsso', cascade = 'all', backref = 'DSORF' )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: DSORF - Another DSORF object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.raw_start_pos == other.raw_start_pos ) 
               and ( self.raw_stop_pos == other.raw_stop_pos )
               and ( self.raw_strand == other.raw_strand )
               and ( self.chromosome == other.chromosome )
               and ( self.spliced == other.spliced )
               and ( self.raw_splice_starts == other.raw_splice_starts )
               and ( self.raw_splice_ends == other.raw_splice_ends )
               and ( self.spliced_parts_count == other.spliced_parts_count )
               and ( self.data_source == other.data_source ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a DSORF object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the DSORF object.
    #
    def __hash__( self ):
        
        return hash( ( self.data_source, self.chromosome, self.raw_strand, 
                       self.raw_start_pos, self.raw_stop_pos, self.spliced, 
                       self.raw_splice_starts, self.raw_splice_ends, 
                       self.spliced_parts_count ) )
    