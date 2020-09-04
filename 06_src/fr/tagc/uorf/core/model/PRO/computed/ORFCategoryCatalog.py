# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFCategoryCatalog
#  ==================
#
# Each ORFCategoryCatalog contains:
#     - category: String - The ORF category.
#
class ORFCategoryCatalog( BasePRO ):
    
    __tablename__ = 'ORFCategoryCatalog'
    
    category = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                       primary_key = True )

    # Define one-to-many relationship
    ORFcategory_list = relationship( 'ORFCategory', cascade = 'all', backref = 'ORFCategoryCatalog' )
    