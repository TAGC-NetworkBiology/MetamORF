# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFAnnotationCatalog
#  ====================
#
# Each ORFAnnotationCatalog contains:
#     - annotation: String - The ORF annotation.
#     - family: String - The family of the annotation (length, biotype, relative position or alternative frame).
#
class ORFAnnotationCatalog( BasePRO ):
    
    __tablename__ = 'ORFAnnotationCatalog'
    
    annotation = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                         primary_key = True )
    family = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )

    # Define one-to-many relationship
    ORFAnnotation_list = relationship( 'ORFAnnotation', cascade = 'all', backref = 'ORFAnnotationCatalog' )
    