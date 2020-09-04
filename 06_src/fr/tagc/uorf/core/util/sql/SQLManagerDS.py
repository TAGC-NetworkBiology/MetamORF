# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *
from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLManager import SQLManager


## SQLManagerDS
#  ============
#
# This class is a singleton inheriting from SQLManager and aiming to manage SQL 
# connection to the DS (data source) database. This SQLManager use the "DS model".
# The singleton is able to manage the creation of a SQLAlchemy Session to the database
# it has been initiated with. The singleton keeps the same session open until it is
# asked to close it.
#
class SQLManagerDS( SQLManager ):

    __instance = None
    
    BASE = BaseDS
    
    ## Constructor of SQLManagerDS
    #  ---------------------------
    #
    def __init__( self ):
        
        SQLManager.__init__( self )
            
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of SQLManagerDS, 
    # then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        
        if ( SQLManagerDS.__instance == None ):
            SQLManagerDS.__instance = SQLManagerDS()

        return SQLManagerDS.__instance
