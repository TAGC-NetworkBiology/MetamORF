# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.util.exception.dencellorfobject.DenCellORFObjUpdateException import DenCellORFObjUpdateException


## DenCellORFTrUpdateException
#  ===========================
#
# This class allows to raise exceptions related to problems of updates 
# of Transcript objects (such as DSTranscript) anywhere in the program. 
# It inherits from the DenCellORFObjUpdateException.
#
class DenCellORFTrUpdateException( DenCellORFObjUpdateException ):

    ## Constructor of DenCellORFTrUpdateException
    #  ------------------------------------------
    #
    # Instance variable:
    #     - message: String - The message to log about the error.
    #     - exception: Exception - The exception caught.
    #     - gene_id: String - The gene_id related to the exception.
    #     - gene_id_conflicts: List - The list of all gene IDs that have been found associated to
    #                                 the DSTranscript entry.
    #
    # The gene_id string registered as attribute of the exception aims to store the value of 
    # the new gene ID (created by concatenation of the two different gene IDs of the original
    # Transcript entries) associated with the updated Transcript if a conflict has been found 
    # on the gene IDs.
    #
    # @param message: String - The message to log about the error.
    # @param exception: Exception - The exception caught. None by default.
    # @param gene_id: String - The gene_id related to the exception.
    # @param gene_id_conflicts: List - The list of all gene IDs that have been found associated to
    #                                  the DSTranscript entry. None by default.
    #
    def __init__( self, message, exception=None, gene_id=None, gene_id_conflicts=None ):
        
        DenCellORFObjUpdateException.__init__( self,  
                                               message = message, 
                                               exception = exception )
        
        self.gene_id = gene_id
        self.gene_id_conflicts = gene_id_conflicts
        
        
    ## get_gene_id
    #  -----------
    #
    # This method returns the gene_id attribute of this exception.
    #
    # @return self.gene_id
    #
    def get_gene_id( self ):
        
        return self.gene_id
        
        
    ## get_conflict_list
    #  -----------------
    #
    # This method returns the gene_id_conflicts attribute of this exception.
    #
    # @return self.gene_id_conflicts
    #
    def get_conflict_list( self ):
        
        return self.gene_id_conflicts    
    