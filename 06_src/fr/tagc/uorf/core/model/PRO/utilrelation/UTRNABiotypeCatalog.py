# -*- coding: utf-8 -*-

from sqlalchemy import Column, String


from fr.tagc.uorf.core.util.sql.Base import BasePRO

from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## UTRNABiotypeCatalog
#  ===================
#
# Each UTRNABiotypeCatalog contains:
#     - biotype: String - The name of the biotype.
#
class UTRNABiotypeCatalog( BasePRO ):
    
    # =============================================================================
    # /!\ This table is filled during the ComputeMissingInfo step.
    # =============================================================================
    
    __tablename__ = 'UTRNABiotypeCatalog'
    
    biotype = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                      primary_key = True )
    


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: UTRNABiotypeCatalog - Another UTRNABiotypeCatalog object 
    #                                     to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.biotype == other.biotype ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a UTRNABiotypeCatalog object.
    # The hash value of an instance is computed using its primary key attribute.
    #
    # @return the hash value of the UTRNABiotypeCatalog object.
    #
    def __hash__( self ):
        
        return hash( self.biotype )
        