# -*- coding: utf-8 -*-


## DenCellORFException
#  ===================
#
# This class allows to raise specific exceptions anywhere in the program.
# It inherits from Exception and is also the metaclass of numerous custom 
# exceptions allowing to raise and catch information about some specific
# problems anywhere in the program.
#
class DenCellORFException( Exception ):

    ## Constructor of DenCellORFException
    #  ----------------------------------
    #
    # Instance variable:
    #     - message: String - The message to log about the error.
    #     - exception: Exception - The exception caught. 
    #
    # @param message: String - The message to log about the error.
    # @param exception: Exception - The exception caught. None by default.
    #
    def __init__( self, message, exception=None ):
        
        Exception.__init__( self )
        
        self.message = message
        self.exception = exception
        
        
    ## get_message
    #  -----------
    #
    # This method returns the message of the exception.
    #
    # @return self.message: String - The message to log.
    #
    def get_message( self ):
        
        if self.exception:
            try:
                message_from_exception = self.exception.get_message()
            except:
                message_from_exception = str( self.exception )
            
            message_out = ( self.message +
                            '\n   ... comes from' +
                            ' (Exception class: ' + str( self.exception.__class__.__name__ ) + 
                            '): \n' + '       ' + message_from_exception )
        else:
            message_out = self.message
        
        return message_out
        
        
    ## __str__
    #  -------
    #
    # Returns the same result as the get_message() method.
    #
    # @return self.message: String - The message to log.
    #
    def __str__( self ):
        
        return self.get_message()
