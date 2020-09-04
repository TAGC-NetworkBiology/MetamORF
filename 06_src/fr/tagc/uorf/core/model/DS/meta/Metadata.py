# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text
from sqlalchemy import PrimaryKeyConstraint


from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## Metadata
#  ========
#
# Each Metadata contains:
#     - parameter: String - The name of the parameter.
#     - value: String - The value set for this parameter.
#     - description: Text - A brief description of the parameter.
#
class Metadata( BaseDS ):
    
    __tablename__ = 'Metadata'
    
    parameter = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    value = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    description = Column( Text( collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'parameter' ),
                    )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are equal.
    #
    # @param other: Metadata - Another Metadata object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.parameter == other.parameter ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a Metadata object.
    # The hash value of an instance is computed using its primary key.
    #
    # @return the hash value of the Metadata object.
    #
    def __hash__( self ):
        
        return hash( self.parameter )
    