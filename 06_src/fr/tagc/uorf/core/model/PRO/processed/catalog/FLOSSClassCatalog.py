# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## FLOSSClassCatalog
#  =================
#
# Each FLOSSClassCatalog contains:
#     - floss_class: String - The FLOSS classification.
#
class FLOSSClassCatalog( BasePRO ):
    
    __tablename__ = 'FLOSSClassCatalog'
    
    floss_class = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                          primary_key = True )

    # Define one-to-many relationship
    FLOSSClass_list = relationship( 'FLOSSClass', cascade = 'all', backref = 'FLOSSClassCatalog' )


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: FLOSSClassCatalog - Another FLOSSClassCatalog object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.floss_class == other.floss_class ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a FLOSSClassCatalog object.
    # The hash value of an instance is computed using its primary key attribute.
    #
    # @return the hash value of the FLOSSClassCatalog object.
    #
    def __hash__( self ):
        
        return hash( self.floss_class )
    