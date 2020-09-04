# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ProvidedCategory
#  ================
#
# Each ProvidedCategory contains:
#     - orftranscriptasso_id: Integer - The ORF-transcript association ID.
#     - provided_category: String - The ORF category provided by the data sources.
#
class ProvidedCategory( BasePRO ):
    
    __tablename__ = 'ProvidedCategory'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    provided_category = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                                ForeignKey( 'ProvidedCategoryCatalog.category', ondelete='CASCADE', onupdate='CASCADE' ) )

    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'provided_category' ),
                    )    
    