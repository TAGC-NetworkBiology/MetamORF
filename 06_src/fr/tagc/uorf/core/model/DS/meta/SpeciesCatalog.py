# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## SpeciesCatalog
#  ==============
#
# Each SpeciesCatalog contains:
#     - name: String - The species name.
#
class SpeciesCatalog( BaseDS ):
    
    __tablename__ = 'SpeciesCatalog'
    
    name = Column( String(50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                   primary_key = True )
