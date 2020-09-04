# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## ORFDSAsso
#  =========
#
# Each ORFDSAsso contains:
#     - orf_id: Integer - Unique ORF ID (PRO database).
#     - dsorf_id: Integer - Unique DSORF ID (DS database) from which the ORF has been merged.
#     - data_source: String - Name of the datasource.
#     - ambiguous: Boolean - Was the DSORF merged in this ORF as ambiguous?
#
class ORFDSAsso( BasePRO ):

    __tablename__ = 'ORFDSAsso'
    
    orf_id = Column( Integer, 
                     ForeignKey( 'ORF.id', ondelete='CASCADE', onupdate='CASCADE' ) )
    dsorf_id = Column( Integer )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    ambiguous = Column( Boolean )
    
    # Define unique constraint on "primary key-like attributes"
    __table_args__ = (
                        PrimaryKeyConstraint( 'orf_id', 'dsorf_id' ),
                    )
    