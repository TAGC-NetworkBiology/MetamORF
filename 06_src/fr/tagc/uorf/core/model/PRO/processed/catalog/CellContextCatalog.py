# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## CellContextCatalog
#  ==================
#
# Each CellContextCatalog contains:
#     - cell_context: String - The cellular context.
#
class CellContextCatalog( BasePRO ):
    
    __tablename__ = 'CellContextCatalog'
    
    context = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                      primary_key = True )

    # Define the one-to-many relationship
    CellContext_list = relationship( 'CellContext', cascade = 'all', backref = 'CellContextCatalog' )


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: CellContextCatalog - Another CellContextCatalog object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.context == other.context ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a CellContextCatalog object.
    # The hash value of an instance is computed using its primary key attribute.
    #
    # @return the hash value of the CellContextCatalog object.
    #
    def __hash__( self ):
        
        return hash( self.context )
    