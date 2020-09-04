# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException


## TranslateDNAException
#  =====================
#
# This class allows to raise exceptions related to problems during the translation
# of a DNA sequence into amino acid sequence anywhere in the program. 
# It inherits from the DenCellORFException.
#
class TranslateDNAException( DenCellORFException ):

    ## Constructor of TranslateDNAException
    #  ------------------------------------
    #
    # Instance variable:
    #     - message: String - The message to log about the error.
    #     - exception: Exception - The exception caught.
    #     - dna_seq: String - The sequence being translated.
    #     - aa_seq: String - The amino acid sequence get by translation 
    #                        of the DNA sequence.
    #     - remainder: Integer - The value of the remainder when dividing 
    #                            the DNA sequence length by 3.
    #
    # The DNA and amino acid sequences are registered as attributes of the exception in 
    # order to be logged if necessary.
    #
    # @param message: String - The message to log about the error.
    # @param exception: Exception - The exception caught. None by default.
    # @param dna_seq: String - The sequence being translated. None by default.
    # @param aa_seq: String - The amino acid sequence get by translation of the DNA 
    #                         sequence. None by default.
    # @param remainder: Integer - The value of the remainder when dividing 
    #                             the DNA sequence length by 3. None by default.
    #
    def __init__( self, message, exception=None, dna_seq=None, aa_seq=None, remainder=None ):
        
        DenCellORFException.__init__( self,  
                                      message = message, 
                                      exception = exception )
        
        self.dna_seq = dna_seq
        self.aa_seq = aa_seq
        self.remainder = remainder
        
        
    ## get_dna_seq
    #  -----------
    #
    # This method returns the dna_seq attribute of this exception.
    #
    # @return self.dna_seq
    #
    def get_dna_seq( self ):
        
        return self.dna_seq
        
        
    ## get_aa_seq
    #  ----------
    #
    # This method returns the aa_seq attribute of this exception.
    #
    # @return self.aa_seq
    #
    def get_aa_seq( self ):
        
        return self.aa_seq
        
        
    ## get_remainder
    #  -------------
    #
    # This method returns the remainder attribute of this exception.
    #
    # @return self.remainder
    #
    def get_remainder( self ):
        
        return self.remainder
    