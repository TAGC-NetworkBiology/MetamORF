# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## TranscriptDSAsso
#  ================
#
# Each TranscriptDSAsso contains:
#     - transcript_id: Integer - The Transcript ID (PRO database).
#     - dstranscript_id: Integer - The DSTranscript ID (DS database) from which 
#                                  the Transcript has been merged.
#     - data_source: String - The name of the data source.
#     - ambiguous: Boolean - Was the DSTranscript merged in this Transcript ambiguous?
#
class TranscriptDSAsso( BasePRO ):

    __tablename__ = 'TranscriptDSAsso'
    
    transcript_id = Column( Integer, 
                            ForeignKey( 'Transcript.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    dstranscript_id = Column( Integer )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    ambiguous = Column( Boolean )
    
    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'transcript_id', 'dstranscript_id' ),
                    )
    