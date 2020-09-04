# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## DataSource
#  ==========
#
# Each DataSource contains:
#     - name: String - The name of the source.
#     - doi: String - The DOI of the source.
#     - description: Text - The description of the source.
#     - url: String - The link to the raw data or the publication related to the data source.
#     - annotation_version: String - The genome version used by the source.
#     - ensembl_release: String - The Ensembl release number corresponding to the genome version.
#     - annotation_description: Text - The description of the annotation version as provided 
#                                      in the data source.
#
class DataSource( BaseDS ):
    
    __tablename__ = 'DataSource'
    
    name = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    doi = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    description = Column( Text( collation = SQLCollationManager.get_instance().get_db_collation() ) )
    url = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    annotation_version = Column( String( 10, collation = SQLCollationManager.get_instance().get_db_collation() ) )   
    ensembl_release = Column( String( 3, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    annotation_description = Column( Text )
    
    # Define the primary key attribute
    __table_args__ = (
                        PrimaryKeyConstraint( 'name' ),
                    )


    # Define the one-to-many relationships
    DSORF_list = relationship( 'DSORF', cascade = 'all', backref = 'DataSource' )
    DSTranscript_list = relationship( 'DSTranscript', cascade = 'all', backref = 'DataSource' )
    DSORFTranscriptAsso_list = relationship( 'DSORFTranscriptAsso', cascade = 'all', backref = 'DataSource' )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: DataSource - Another DataSource object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( self.name == other.name ):
            return True
        
        else:
            return False
   


    ## __hash__
    #  --------
    #
    # Returns the hash value of a DataSource object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the DataSource object.
    #
    def __hash__( self ):
        
        return hash( self.name )
    