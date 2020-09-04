# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text
from sqlalchemy import PrimaryKeyConstraint


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## UTGeneFromAlias
#  ===============
#
# Each UTGeneFromAlias contains:
#     - alias: String - The alias for this gene.
#     - gene_ids: String - The gene IDs matching this alias (comma separated if several).
#
class UTGeneFromAlias( BaseDS ):
    
    # =============================================================================
    # /!\ This table is build from data in Gene and GeneAlias tables. It associates
    #     to each alias a list of genes that may correspond to it.
    # =============================================================================
    
    __tablename__ = 'UTGeneFromAlias'
    
    alias = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    gene_ids = Column( Text( collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the primary key attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'alias' ),
                    )
    


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: UTGeneFromAlias - Another UTGeneFromAlias object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.alias == other.alias ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a UTGeneFromAlias object.
    # The hash value of an instance is computed using its primary key attribute.
    #
    # @return the hash value of the UTGeneFromAlias object.
    #
    def __hash__( self ):
        
        return hash( self.alias )
        