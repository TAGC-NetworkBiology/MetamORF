# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## FLOSSClass
#  ==========
#
# Each FLOSSClass contains:
#     - orftranscriptasso_id: Integer - The ORF-transcript association ID.
#     - floss_class: String - The FLOSS classification of the ORF.
#
class FLOSSClass( BasePRO ):
    
    __tablename__ = 'FLOSSClass'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    floss_class = Column( String( 100, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                          ForeignKey( 'FLOSSClassCatalog.floss_class', ondelete='CASCADE', onupdate='CASCADE' ) )

    # Define composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'floss_class' ),
                    )    
    