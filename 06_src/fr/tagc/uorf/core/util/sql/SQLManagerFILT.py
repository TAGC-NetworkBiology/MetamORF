# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.model import *
from fr.tagc.uorf.core.util.sql.Base import BasePRO
from fr.tagc.uorf.core.util.sql.SQLManager import SQLManager


## SQLManagerFILT
#  ==============
#
# This class is a singleton inheriting from SQLManager and aiming to manage SQL 
# connection to the FILT (filtered) database. This database uses the same model as the
# PRO (processed and merged) database, hence this SQLManager use the "PRO model".
# The singleton is able to manage the creation of a SQLAlchemy Session to the database
# it has been initiated with. The singleton keeps the same session open until it is
# asked to close it.
#
class SQLManagerFILT( SQLManager ):

    __instance = None
    
    BASE = BasePRO
    
    ## Constructor of SQLManagerFILT
    #  -----------------------------
    #
    def __init__( self ):
        
        SQLManager.__init__( self )
            
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of SQLManagerFILT, 
    # then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        
        if ( SQLManagerFILT.__instance == None ):
            SQLManagerFILT.__instance = SQLManagerFILT()

        return SQLManagerFILT.__instance
