# -*- coding: utf-8 -*-

import ConfigParser
import os
import re


from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## ComputeKozakContextStrategy
#  ===========================
#
# This class is a strategy aiming to compute the Kozak context
# for the ORF searching for regular expressions in the sequences
# flanking their start codon.
#
class ComputeKozakContextStrategy( object ):
                
    ## Class variables
    #  ---------------
    
    # Dictionary of Kozak context descriptions for eukaryotes
    # The regular expressions for the classification of Kozak 
    # context used are the one defined in Hernandez et al., 
    # Trends in Biochemical Sciences, 2019 
    # (doi: 10.1016/j.tibs.2019.07.001)
    #
    # Positions:  -6   -5   -4   -3   -2   -1  [+1   +2   +3]  +4
    # Optimal:     G    C    C  (A/G)  C    C    A    U    G    G
    # Strong:      N    N    N  (A/G)  N    N    A    U    G    G
    # Moderate:    N    N    N  (A/G)  N    N    A    U    G  (A/U/C)
    #       or     N    N    N  (C/U)  N    N    A    U    G    G
    # Weak:        N    N    N  (C/U)  N    N    A    U    G  (A/C/U) 
    #
    KOZAK_CONTEXT_REGEX = { 
                            'optimal': 'GCC[AG]CC.{3}G',
                            'strong': '.{3}[AG].{2}.{3}G',
                            'moderate': '(.{3}[AG].{2}.{3}[ATC]|.{3}[CT].{2}.{3}G)',
                            'weak': '.{3}[CT].{2}.{3}[ACT]',
                           }
    KOZAK_CONTEXT_PRIORITY_ORDER = [ 'optimal', 'strong', 'moderate', 'weak' ]
        
    
    
    ## Constructor of ComputeKozakContextStrategy
    #  ------------------------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - force_overwrite: Boolean - Does the computation needs to be performed again?
    #                                  If True:
    #                                      - The flanking regions will be computed again
    #                                      - The Kozak context will be computed again
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    #
    def __init__( self ):
        
        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none = True )
            
        if configfile:
            self.configfile = configfile
            if ( not os.path.exists( configfile ) ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' See the documentation for more information.' )

        # Check if the forceOverwrite option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
            self.force_overwrite = True
        else:
            self.force_overwrite = False
    
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to complete missing information.
    #
    # @throw DenCellORFException: When an exception has been raised whilst checking the PRO database.
    # @throw DenCellORFException: When the ORFTranscriptAsso table is empty.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check PRO database is reachable and use
        # the appropriate models prior to the merging of data.
        Logger.get_instance().info( 'Checking the PRO database prior to compute missing information...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( ' An error occurred whilst checking the database prior to' +
                                       ' compute missing information.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        
        Logger.get_instance().info( 'Starting the computation of Kozak contexts using the relative ORF' +
                                    ' start coordinates registered in the ORFTranscriptAsso table and' +
                                    ' the transcript sequences.')
        
        # Get all the entries of the ORFTranscriptAsso table for which the relative
        # start position is registered and for which the transcript sequence is known
        ota_to_process_query = SQLManagerPRO.get_instance().get_session().query( 
                                                                                    ORFTranscriptAsso.id,
                                                                                    ORFTranscriptAsso.rel_start_pos,
                                                                                    ORFTranscriptAsso.kozak_context,
                                                                                    Transcript.sequence 
                                                                                ).filter(
                                                                                            ORFTranscriptAsso.transcript_id == Transcript.id 
                                                                                        ).filter(
                                                                                                    ORFTranscriptAsso.rel_start_pos != None,
                                                                                                    Transcript.sequence != None
                                                                                                )
        if ( not self.force_overwrite ):
            ota_to_process_query = ota_to_process_query.filter( ORFTranscriptAsso.kozak_context_comp == None )
            
        ota_to_process = ota_to_process_query.all()        
        SQLManagerPRO.get_instance().close_session()
        
        
        Logger.get_instance().debug( 'The Kozak context will be estimated for ' + 
                                     str( len( ota_to_process ) ) + ' ORFTranscriptAsso entries.')
        
        Logger.get_instance().info( 'The following regular expressions will be used to identifiate the' +
                                    ' Kozak contexts: ' + 
                                    str( ComputeKozakContextStrategy.KOZAK_CONTEXT_REGEX ) + '.')
        
        # Instantiate a dictionary that will associate to each unique 
        # ORFTranscriptAsso ID a tuple containing the kozak context,
        # the start codon sequence and the flanking sequence 
        # (i.e. the sequence from the -6 to the +4 position)
        ota_with_kozak_context = {}
                                                               
        for ota in ota_to_process:
            
            # Get the start relative position and the transcript sequence
            start_pos = ota.rel_start_pos
            transcript_sequence = ota.sequence
            
            # Make sure the sequences flanking the start codon 
            # may be found on the transcript sequence
            if ( ( start_pos - 7 >= 0 ) 
                 and ( ( start_pos + 3 ) < len( transcript_sequence ) ) ):
            
                # Extract the start codon sequence as well as flanking sequences
                # (from the -6 position to the +4 position)
                start_codon_seq = transcript_sequence[ start_pos-1 : start_pos+2 ]
                start_codon_flanking_seq = transcript_sequence[ start_pos-7 : start_pos+3 ]
                
                # Look for Kozak context, starting to search for an optimal context
                # and pursuing up to find the appropriate type of Kozak context
                # (optimal, strong, moderate, weak or absent)
                regex_index = 0
                match_regex = False
                
                while not match_regex:
                    
                    # Get the type of Kozak context to look for
                    kozak_ctxt_type = ComputeKozakContextStrategy.KOZAK_CONTEXT_PRIORITY_ORDER[ regex_index ]
                    
                    # Get the corresponding regex
                    kozak_regex = ComputeKozakContextStrategy.KOZAK_CONTEXT_REGEX[ kozak_ctxt_type ]
                    
                    # Check if the flanking sequence matches the regex
                    match_regex = re.match( kozak_regex, start_codon_flanking_seq )
                    regex_index += 1
                    
                    
                if match_regex:
                    ota_with_kozak_context[ ota.id ] = ( kozak_ctxt_type, 
                                                         start_codon_seq,
                                                         start_codon_flanking_seq )
        
        
        # Update all the ORFTranscriptAsso entries for which a Kozak context has been found
        ota_to_process = SQLManagerPRO.get_instance().get_session().query( 
                                                                                ORFTranscriptAsso 
                                                                            ).filter(
                                                                                        ORFTranscriptAsso.id.in_( ota_with_kozak_context.keys() )
                                                                                    ).all()
                                                                                    
        for ota in ota_to_process:
            
            # Get the information related to the Kozak context description
            kozak_info = ota_with_kozak_context.get( ota.id )
            kozak_ctxt_type = kozak_info[ 0 ]
            start_codon_seq = kozak_info[ 1 ]
            start_codon_flanking_seq = kozak_info[ 2 ] 
            
            # Check if the start codon found matches with the one registered 
            # in the database.
            # If not, this is probably due to versionning problem, in such case
            # log an error message and remove the relative position from the 
            # entry as they are probably wrong.
            if ( ( ota.start_codon_seq != None ) 
                 and ( ota.start_codon_seq != start_codon_seq ) ):            
                ota.rel_start_pos = None
                ota.rel_stop_pos = None                
                Logger.get_instance().warning( 'The ORFTranscriptAsso entry with the ID "' + str( ota.id ) + 
                                               ' has been registered as starting with the codon ' + 
                                               ota.start_codon_seq + ' whilst the start codon found using' +
                                               ' the relative start position and the transcript sequence is ' +
                                               start_codon_seq + '. This may be relate to versioning' +
                                               '-related issues when computing the relative start and' +
                                               ' stop positions. Hence these positions will be removed' +
                                               ' for this entry.' +
                                               ' Warning code: ' + LogCodes.WARN_RELCOORD_CONFL_STARTCODON + '.' )
                
            else:                
                ota.kozak_context_comp = kozak_ctxt_type
                ota.start_codon_seq = start_codon_seq
                ota.start_flanking_seq = start_codon_flanking_seq
        
        SQLManagerPRO.get_instance().commit()
        SQLManagerPRO.get_instance().close_session()
        