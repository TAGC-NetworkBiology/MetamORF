# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException


## RefException
#  ============
#
# This class allows to raise exceptions related to problems about gene references 
# anywhere in the program. It inherits from the DenCellORFException.
#
class RefException( DenCellORFException ):

    ## Constructor of RefException
    #  ---------------------------
    #
    # Instance variable:
    #     - message: String - The message to log about the error.
    #     - exception: Exception - The exception caught.
    #     - gene: Gene - A Gene object.
    #
    # The gene object registered as attribute of the exception may be either the updated 
    # gene (in the case of the RefGeneUpdateException class) or a gene that is related to 
    # the exception, such as a "fake" gene that has been created to respect the relational 
    # integrity of the database when one was not able to find an unique gene for a unique
    # (symbol, chromosome) pair.
    #
    # @param message: String - The message to log about the error.
    # @param exception: Exception - The exception caught. None by default.
    # @param gene: Gene - The Gene object related to the exception.
    #
    def __init__( self, message, exception=None, gene=None ):
        
        DenCellORFException.__init__( self,  
                                      message = message, 
                                      exception = exception )
        
        self.gene = gene
        
        
    ## get_gene
    #  --------
    #
    # This method returns the Gene object of this exception.
    #
    # @return self.gene
    #
    def get_gene( self ):
        
        return self.gene
        
                
    ## set_gene
    #  --------
    #
    # Set the Gene object of this exception.
    #
    # @param g: Gene - The gene object associated with the exception.
    #
    # @return self.gene
    #
    def set_gene( self, g ):
        
        self.gene = g
