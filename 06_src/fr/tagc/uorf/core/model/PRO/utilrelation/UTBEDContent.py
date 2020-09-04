# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, Text
from sqlalchemy import ForeignKey


from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager


## UTBEDContent
#  ============
#
# Each UTBEDContent contains:
#     - orf_id: Integer - The ID of the ORF entry.
#     - bed_index: Integer - The index of the line when building the full BED file. First index is 0.
#     - bed_col: Text - The line to use in the BED file (as a single string of 12 tab-separated columns).
#     - bed_add_col: Text - The additional columns of the BED file (as a single string of 5 tab-separated columns).
#
class UTBEDContent( BasePRO ):
        
    __tablename__ = 'UTBEDContent'
    
    orf_id = Column( Integer, 
                     ForeignKey( 'ORF.id', ondelete='CASCADE', onupdate='CASCADE' ),
                     primary_key = True )
    bed_index = Column( Integer )
    bed_col = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    bed_add_col = Column( Text( SQLConstants.MAX_LEN_TEXT, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    