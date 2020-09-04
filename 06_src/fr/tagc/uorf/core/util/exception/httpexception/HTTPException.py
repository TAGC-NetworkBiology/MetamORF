# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException


## HTTPException
#  =============
#
# This class allows to raise exceptions related to exceptions or errors raised during 
# HTTP requests anywhere in the program. It inherits from the DenCellORFException.
#
class HTTPException( DenCellORFException ):

    ## Constructor of HTTPException
    #  ----------------------------
    #
    # Instance variable:
    #     - message: String - The message to log about the error.
    #     - exception: Exception - The exception caught. 
    #     - code: String - The HTTP error code.
    # 
    # @param message: String - The message to log.
    # @param exception: Exception - The exception caught. None by default.
    # @param code: String - The HTTP error code. None by default.
    #
    def __init__( self, message, exception=None, code=None ):
        
        DenCellORFException.__init__( self,  
                                      message = message, 
                                      exception = exception )
        
        if code:
            self.code = code
        else:
            try: 
                self.code = exception.code
            except:
                self.code = None
        
        
    ## get_code
    #  --------
    #
    # This method returns the code related to the exception.
    #
    # @return self.code
    #
    def get_code( self ):
        
        return self.code
