# -*- coding: utf-8 -*-

import sys
import time


## ProgressionBar
#  ==============
#
# This class is a singleton allowing to display a progression bar on the console.
#
class ProgressionBar( object ):
        
    __instance = None
    
    ## Constructor of ProgressionBar
    #  -----------------------------
    #
    # Instance variable:
    #     - progression_count: Integer - The value at which the process is considered completed.
    #     - total: Integer - The current value of the process.
    #
    # @param progress: Integer - The current value of the process. Equals 0 by default.
    # @param total: Integer - The value at which the process is considered finished. 
    #                         Equals 1 by default.
    #
    def __init__( self, progress=0, total=1 ):
        
        self.progression_count = progress
        self.total_row_count = total
            

    ## increase_and_display
    #  --------------------
    #
    # This method allows to increase the progression count of the provided value 
    # (or one by default) and to display the progression bar on the console.
    #
    # @param add_val: Integer - The value to add to the progression count.
    #                           Equals 1 by default.
    #
    def increase_and_display( self, add_val=1 ): 
        
        self.increase( add_val = add_val )
        self.display()
            

    ## increase
    #  --------
    #
    # This method allows to increase the progression count of 
    # the provided value (or one if no value if provided).
    #
    # @param add_val: Integer - The value to add to the progression count. 
    #                           Equals 1 by default.
    #
    def increase( self, add_val=1 ):
        
        self.progression_count += add_val
        
        
    ## display
    #  -------
    #
    # This method allows to display a progression bar on the console.
    #
    def display( self ):
        
        # Set the bar length
        bar_length = 50
        status = ''
        
        if ( self.total_row_count > 0 ):
            progress = float( self.progression_count ) / float( self.total_row_count )
        else:
            progress = 1
        
        # If the process is finished, set the progress variable to 1
        if ( progress >= 1 ):
            progress = 1
        
        # Get the size of the block corresponding to the accomplished process
        block = int( round( bar_length * progress ) )
        
        # Create the progression bar
        # This will display the bar on a new line and add '=' 
        # for the part of the process which is completed.
        # Return to the line if the process is finished.
        text = "\r[{}] {:.0f} % ".format( '=' * block + ' ' * ( bar_length - block ),
                                           round( progress * 100, 0 ) )
        
        # Display the bar on the console and flush it
        sys.stdout.write( text )
        sys.stdout.flush()
        
        # If the process has finished, let the progression bar at 100% 
        # and go to the next line
        if ( progress == 1 ):
            sys.stdout.write( '\n' )
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of ProgressionBar, 
    # then return this instance.
    #
    # @return the singleton instance.
    #
    @staticmethod
    def get_instance():
        
        if ( ProgressionBar.__instance == None ):
            ProgressionBar.__instance = ProgressionBar()

        return ProgressionBar.__instance
            

    ## reset_instance
    #  --------------
    #
    # This method allows to reset the attributes of the ProgressionBar instance.
    #
    # @param progress: Integer - The current value of the process. 
    #                            Equals 0 by default.
    # @param total: Integer - The value at which the process is considered completed. 
    #                         Equals 1 by default.
    #
    def reset_instance( self, progress=0, total=1): 
         
        self.progression_count = progress
        self.total_row_count = total
        