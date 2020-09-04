# -*- coding: utf-8 -*-

from os.path import sys
from optparse import OptionParser


from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger


## OptionManager
#  =============
#
# This class is a singleton and a wrapper aiming to parse and handle the options 
# provided by the user in the command line. 
#
class OptionManager( object ):

    __instance = None
    

    ## Constructor of OptionManager
    #  ----------------------------
    #
    # Instance variables:
    #    - strategy: String - The strategy selected.
    #    - optionDict: Dict - A dictionary of options provided by the user.
    #    - optionParser: OptionParser - The option parser object.
    #    - args: args - The arguments of the option parser.
    #
    def __init__( self ):
        
        self.strategy = None
        self.optionDict = None
        self.optionParser = None
        self.args = None
        

    ## initialize
    #  ----------
    #
    # This method allows to initialize the manager with by parsing the options 
    # provided in the command line.
    # 
    # @throw DenCellORFException: When the strategy selected is not an existing one.
    #
    def initialize( self ):
        
        # Get the main keyword that defines the strategy
        self.strategy = sys.argv[1]
        
        # If the strategy is not known, check if the user asked the help.
        # Otherwise, raise a DenCellORFException.
        if ( self.strategy not in OptionConstants.STRATEGIES_LIST ):

            # Display help on the console if necessary and exit the program
            if ( self.strategy in [ '-h', '--help' ] ):
                print( 'To run a strategy, you need to type the command such as: \n' +
                       'python $PYTHONPATH/fr/tagc/uorf/uorf.py [StrategyKeyword] [Options] \n' +
                       'or DenCellORF [StrategyKeyword] [Options]. \n'
                       'The following strategies are available: ' + 
                       ', '.join( OptionConstants.STRATEGIES_LIST ) + '.\n'
                       ' You may find more information about the options available for each strategy' +
                       ' using the command DenCellORF [StrategyKeyword] -h' +
                       ' or DenCellORF [StrategyKeyword] --help. \n' +
                       ' For extensive information, please read the user manual (PDF file).' )
                exit()

            else:
                raise DenCellORFException( 'The strategy selected (' + self.strategy + ') is not correct.' +
                                           ' It must be one of ' + ', ' .join( OptionConstants.STRATEGIES_LIST ) + 
                                           '. Please see the documentation for more information.' )
        
        Logger.get_instance().info( '---' ) 
        Logger.get_instance().info( 'Selected strategy: ' + self.strategy )
        
        # Build an option parser to collect the option values
        self.optionParser = OptionParser()
        for current_prop_list in OptionConstants.OPTION_LIST[ self.strategy ]:
            self.optionParser.add_option( current_prop_list[0],
                                          current_prop_list[1],
                                          action = current_prop_list[2],
                                          type = current_prop_list[3],
                                          dest = current_prop_list[4],
                                          default = current_prop_list[5],
                                          help = current_prop_list[6] )
                
        # Get the various option values into a dictionary
        (opts, args) = self.optionParser.parse_args()
        self.optionDict = vars( opts )
        self.args = args
        
        # Log the settings
        Logger.get_instance().info( 'Settings:' )
        for opt in self.optionDict.items():
            Logger.get_instance().info( "-" + str( opt[0] ) + ": '" + str(opt[1]) + "'" )
        Logger.get_instance().info( '---' )
        

    ## get_strategy
    #  ------------
    #
    # This method returns the value of the strategy selected.
    #
    # @return self.strategy
    #
    def get_strategy( self ):

        return self.strategy


    ## get_option
    #  ----------
    #
    # This method returns the value of the option with the provided option_name.
    # If the option is not available, return None or raise a DenCellORFException.
    #
    # @param option_name: String - The name of the option to get.
    # @param not_none: Boolean - If True, None cannot be returned when the option is 
    #                            is missing (i.e. has not be provided by the user).
    #                            False by default.
    #
    # @return The value of option if available. None otherwise.
    #
    # @throw DenCellORFException: When the option dictionary is empty (i.e. no option has 
    #                             been provided in the command line) whilst a particular
    #                             option is expected.
    # @throw DenCellORFException: When a particular option expected to be provided by the 
    #                             user is missing.
    #
    def get_option( self, option_name, not_none=False ):
        
        if not self.optionDict:
            if not_none:
                raise DenCellORFException( 'No option has been provided in the command line, while the option: "' + 
                                           option_name + '" is expected.' +
                                           ' Please see the documentation for more information about the' +
                                           ' options available.' )
            else:
                return None
            
        if ( option_name in self.optionDict.keys() ):
            return self.optionDict[ option_name ]
        
        else:
            if not_none:
                raise DenCellORFException( 'The option: "' + option_name + 
                                           '" has to be provided in the command line.' +
                                           ' Please see the documentation for more information.' )
            else:
                return None


    ## set_option
    #  ----------
    #
    # This method allows to set the value of a particular parameter in 
    # the option dictionary.
    #
    # @param option_name: String - The name of the option.
    # @param option_value: String - The value of the option.
    #
    # @throw DenCellORFException: When the option name provided is None.
    #
    def set_option( self, option_name, option_value ):

        if ( self.optionDict == None ):
            self.optionDict = {}
            
        if ( option_name != None ) and ( len( option_name ) > 0 ):
            self.optionDict[ option_name ] = option_value
            
        else:
            raise DenCellORFException( 'OptionManager.set_option(): Trying to pass None as a key' +
                                       ' of the option dictionary.' +
                                       '\n Warning code: ' + LogCodes.WARN_PROG_NONE + '.' )


    ## get_instance
    #  ------------
    #
    # First time create an instance of OptionManager, 
    # then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        
        if ( OptionManager.__instance == None ):
            OptionManager.__instance = OptionManager()
            
        return OptionManager.__instance
