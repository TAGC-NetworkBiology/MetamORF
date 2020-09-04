# -*- coding: utf-8 -*-

from sqlalchemy import Column, String
from sqlalchemy import PrimaryKeyConstraint, ForeignKey


from fr.tagc.uorf.core.util import Constants

from fr.tagc.uorf.core.util.sql.Base import BasePRO

from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## PROGeneAlias
#  ============
#
# Each PROGeneAlias contains:
#     - gene_id: String - The unique gene ID.
#     - alias: String - The alias for this gene.
#
class PROGeneAlias( BasePRO ):

    __tablename__ = 'PROGeneAlias'
     
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()), 
                      ForeignKey( 'PROGene.gene_id', ondelete='CASCADE', onupdate='CASCADE' ) )
    alias = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation()) )
    
    # Define composite primary key
    __table_args__ = (
                        PrimaryKeyConstraint( 'gene_id', 'alias' ),
                    )
