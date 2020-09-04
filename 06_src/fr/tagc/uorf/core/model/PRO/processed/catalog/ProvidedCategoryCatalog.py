# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ProvidedCategoryCatalog
#  =======================
#
# Each ProvidedCategoryCatalog contains:
#     - provided_category: String - The ORF category provided by the data sources.
#
class ProvidedCategoryCatalog( BasePRO ):
    
    __tablename__ = 'ProvidedCategoryCatalog'
    
    category = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                       primary_key = True )

    # Define one-to-many relationship
    ProvidedCategory_list = relationship( 'ProvidedCategory', cascade = 'all', backref = 'ProvidedCategoryCatalog' )


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: ProvidedCategoryCatalog - Another ProvidedCategoryCatalog object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.category == other.category ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a ProvidedCategoryCatalog object.
    # The hash value of an instance is computed using its primary key attributes.
    #
    # @return the hash value of the ProvidedCategoryCatalog object.
    #
    def __hash__( self ):
        return hash( self.category )
    