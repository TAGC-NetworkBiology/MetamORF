# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *
from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLManager import SQLManager


## SQLManagerPRO
#  =============
#
# This class is a singleton inheriting from SQLManager and aiming to manage SQL 
# connection to the PRO (processed and merged) database. This SQLManager use the "PRO model".
# The singleton is able to manage the creation of a SQLAlchemy Session to the database
# it has been initiated with. The singleton keeps the same session open until it is
# asked to close it.
#
class SQLManagerPRO( SQLManager ):

    __instance = None
    
    BASE = BasePRO
    
    ## Constructor of SQLManagerPRO
    #  ----------------------------
    #
    def __init__( self ):
        
        SQLManager.__init__( self )
            
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of SQLManagerPRO,
    # then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        
        if ( SQLManagerPRO.__instance == None ):
            SQLManagerPRO.__instance = SQLManagerPRO()

        return SQLManagerPRO.__instance
