# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## CellContext
#  ===========
#
# Each CellContext contains:
#     - orftranscriptasso_id: Integer - The ORF-transcript association ID.
#     - cell_context: String - The cellular context.
#
class CellContext( BasePRO ):
    
    __tablename__ = 'CellContext'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    cell_context = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                           ForeignKey( 'CellContextCatalog.context', ondelete='CASCADE', onupdate='CASCADE' )  )

    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'cell_context' ),
                    )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: CellContext - Another CellContext object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.orftranscriptasso_id == other.orftranscriptasso_id )
               and ( self.cell_context == other.cell_context ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a CellContext object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the CellContext object.
    #
    def __hash__( self ):
        
        return hash( ( self.orftranscriptasso_id, self.cell_context ) )
    