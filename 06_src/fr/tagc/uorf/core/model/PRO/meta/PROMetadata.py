# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text


from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## PROMetadata
#  ===========
#
# Each PROMetadata contains:
#     - parameter: String - The name of the parameter.
#     - value: String - The value set for this parameter.
#     - description: String - A brief description of the parameter.
#
class PROMetadata( BasePRO ):
    
    __tablename__ = 'PROMetadata'
    
    parameter = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                        primary_key = True )
    value = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    description = Column( Text( collation = SQLCollationManager.get_instance().get_db_collation() ) )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: PROMetadata - Another PROMetadata object to compare to this object.
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
    # Returns the hash value of a PROMetadata object.
    # The hash value of an instance is computed using its primary key.
    #
    # @return the hash value of the PROMetadata object.
    #
    def __hash__( self ):
        
        return hash( self.parameter )
    