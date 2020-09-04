# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## PROGene
#  =======
#
# Each PROGene contains:
#     - gene_id: String - The gene symbol.
#     - chromosome: String - The chromosome name. 
#
class PROGene( BasePRO ):
    
    __tablename__ = 'PROGene'
    
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                      primary_key = True )
    chromosome = Column( String( 15, collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the one-to-many relationships
    Transcript_list = relationship( 'Transcript', cascade = 'all', backref = 'PROGene' )
    PROGeneAlias_list = relationship( 'PROGeneAlias', cascade = 'all', backref = 'PROGene' )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: PROGene - Another PROGene object to compare to this object.
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
    # Returns the hash value of a PROGene object.
    # The hash value of an instance is computed using its primary key.
    #
    # @return the hash value of the PROGene object.
    #
    def __hash__( self ):
        
        return hash( self.gene_id )
