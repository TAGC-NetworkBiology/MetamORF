# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFAnnotation
#  =============
#
# Each ORFAnnotation contains:
#     - orftranscriptasso_id: Integer - The ORF-transcript association ID.
#     - orf_annotation: String - The computed ORF annotation.
#     - criteria: String - The criteria used to perform the annotation.
#
class ORFAnnotation( BasePRO ):
    
    __tablename__ = 'ORFAnnotation'
    
    orftranscriptasso_id = Column( Integer, 
                                   ForeignKey( 'ORFTranscriptAsso.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    orf_annotation = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                           ForeignKey( 'ORFAnnotationCatalog.annotation', ondelete='CASCADE', onupdate='CASCADE' ) )
    criteria = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'orftranscriptasso_id', 'orf_annotation', 'criteria' ),
                    )
    