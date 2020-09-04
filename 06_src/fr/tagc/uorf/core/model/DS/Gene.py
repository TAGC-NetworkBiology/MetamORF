# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## Gene
#  ====
#
# Each Gene contains:
#     - gene_id: String - The gene symbol.
#     - chromosome: String - The chromosome name. 
#
class Gene( BaseDS ):
    
    __tablename__ = 'Gene'
    
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    chromosome = Column( String( 15, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'gene_id' ),
                    )

    # Define the one-to-many relationships
    DSTranscript_list = relationship( 'DSTranscript', cascade = 'all', backref = 'Gene' )
    GeneAlias_list = relationship( 'GeneAlias', cascade = 'all', backref = 'Gene' )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: Gene - Another Gene object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.gene_id == other.gene_id ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a Gene object.
    # The hash value of an instance is computed using its primary key.
    #
    # @return the hash value of the Gene object.
    #
    def __hash__( self ):
        
        return hash( self.gene_id )
