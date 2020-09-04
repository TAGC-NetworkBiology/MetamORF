# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, Text
from sqlalchemy import PrimaryKeyConstraint


from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## UTDSTranscriptGeneConflict
#  ==========================
#
# Each UTDSTranscriptGeneConflict contains:
#     - transcript_id: String - The transcript ID (as provided by the source) 
#                               for which a conflict has been found.
#     - data_source: String - The data source to which the transcript is related.
#     - gene_ids: Test - The list of gene IDs
#
class UTDSTranscriptGeneConflict( BaseDS ):
    
    # =============================================================================
    # /!\ This table is build during the insertion of data. It associates to each
    #     (transcript_id, data_source) unique pair for which a conflict about the 
    #     Gene entry to which it is related, the list of gene IDs. This allows to 
    #     manage the cases where conflicts about the gene are found several times 
    #     for a particular DSTranscript entry.
    # =============================================================================
    
    __tablename__ = 'UTDSTranscriptGeneConflict'
    
    transcript_id = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    gene_ids = Column( Text( collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the primary key attribute
    __table_args__ = (
                        PrimaryKeyConstraint( 'transcript_id', 'data_source' ),
                    )
    


    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their primary keys are all equals.
    #
    # @param other: UTDSTranscriptGeneConflict - Another UTDSTranscriptGeneConflict 
    #                                            object to compare to this object.
    #
    # @return Boolean - Are this object and 'other' equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the two instances may be considered equal
        elif ( ( self.transcript_id == other.transcript_id )
               and ( self.data_source == other.data_source )):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a UTDSTranscriptGeneConflict object.
    # The hash value of an instance is computed using its primary key attributes.
    #
    # @return the hash value of the UTDSTranscriptGeneConflict object.
    #
    def __hash__( self ):
        
        return hash( ( self.transcript_id, self.data_source ) )
        