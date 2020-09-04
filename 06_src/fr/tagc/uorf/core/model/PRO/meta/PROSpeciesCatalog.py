# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## PROSpeciesCatalog
#  =================
#
# Each PROSpeciesCatalog contains:
#     - name: String - The species name.
#
class PROSpeciesCatalog( BasePRO ):
    
    __tablename__ = 'PROSpeciesCatalog'
    
    name = Column( String(50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                   primary_key = True )
