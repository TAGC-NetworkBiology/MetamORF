# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFTranscriptAssoDSAsso
#  =======================
#
# Each ORFTranscriptAssoDSAsso contains:
#     - orftranscriptasso_id: Integer - The ORFTranscriptAsso ID (PRO database).
#     - dsorftranscriptasso_id: Integer - The DSORFTranscriptAsso ID (DS database) 
#                                         from which the ORFTranscriptAsso has been created.
#     - data_source: String - The name of the data source.
#
class ORFTranscriptAssoDSAsso( BasePRO ):

    __tablename__ = 'ORFTranscriptAssoDSAsso'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    dsorftranscriptasso_id = Column( Integer )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    
    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'dsorftranscriptasso_id' ),
                    )
    