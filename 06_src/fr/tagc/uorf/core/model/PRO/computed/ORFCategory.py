# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFCategory
#  ===========
#
# Each ORFCategory contains:
#     - orftranscriptasso_id: Integer - The ORF-transcript association ID.
#     - orf_category: String - The computed ORF category.
#
class ORFCategory( BasePRO ):
    
    __tablename__ = 'ORFCategory'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    orf_category = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                           ForeignKey( 'ORFCategoryCatalog.category', ondelete='CASCADE', onupdate='CASCADE' ) )

    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'orf_category' ),
                    )    
    