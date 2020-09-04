# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.Base import BaseDS

from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## GeneAlias
#  =========
#
# Each GeneAlias contains:
#     - gene_id: String - The unique gene ID.
#     - alias: String - The alias for this gene.
#     - crossref: String - The source in which the alias has been found for the first time.
#
class GeneAlias( BaseDS ):

    __tablename__ = 'GeneAlias'
     
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()), 
                      ForeignKey( 'Gene.gene_id', ondelete='CASCADE', onupdate='CASCADE' ) )
    alias = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()) )
    crossref = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation()) )
    
    # Define composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'gene_id', 'alias' ),
                    )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: GeneAlias - Another GeneAlias object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.gene_id == other.gene_id )
               and ( self.alias == other.alias ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a GeneAlias object.
    # The hash value of an instance is computed using its primary key.
    #
    # @return the hash value of the GeneAlias object.
    #
    def __hash__( self ):
        
        return hash( ( self.gene_id, self.alias ) )
    