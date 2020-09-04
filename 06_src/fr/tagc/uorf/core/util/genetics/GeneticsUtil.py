# -*- coding: utf-8 -*-

import os

from collections import Counter

from Bio.Alphabet import generic_dna, generic_protein
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO, AlignIO
from Bio.Align.Applications import MuscleCommandline
from Bio.Align import AlignInfo


from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.genetics import GeneticsConstants
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.exception.geneticsexception.TranslateDNAException import TranslateDNAException
from fr.tagc.uorf.core.util.log.Logger import Logger


## GeneticsUtil
#  ============
#
# This class contains various static methods which aims to simplify the operation
# performed on genetic-related objects, such as strings containing sequences.
#
class GeneticsUtil( object ):
        
    ## translate_dna
    #  -------------
    #
    # This is a static method that allows to translate a DNA sequence 
    # into an amino acid sequence.
    #
    # @param dna_seq: String - The DNA sequence to translate.
    # @param include_stop: Boolean - Should the (last) stop be included in the sequence returned? 
    #                                False by default.
    # @param stop_codon: String - The symbol that has to be used for stop codons.
    #                             '*' (GeneticsConstants.STOP_CODON) by default.
    # @param to_stop: Boolean - Should the translation be halted as soon as the first stop codon is met?
    #                           False by default.
    #
    # @return aa_seq: String - The amino acid sequence corresponding to the translation of the 
    #                          provided DNA sequence.
    #
    # @throw TranslateDNAException: When the length of the DNA sequence to translate is 
    #                               not a multiple of three.
    #
    @staticmethod
    def translate_dna( dna_seq, include_stop=False, stop_codon=GeneticsConstants.STOP_CODON, to_stop=False ):
        
        # Get the sequence in uppercase
        dna_seq = dna_seq.upper()
        
        # Record the initial sequence to translate
        initial_dna_seq = str( dna_seq )
        
        # Get the length of the sequence
        dna_seq_len = len( dna_seq )
        
        # If the length is not a multiple of three, remove the last nucleotides 
        # prior to perform the translation
        remainder = dna_seq_len % 3
        
        if ( remainder != 0 ):
            dna_seq = dna_seq[ : -remainder ]
            
        # Translate the DNA sequence into protein using Biopython
        dna_sequence = Seq( dna_seq, generic_dna )
        aa_seq = str( dna_sequence.translate( table = 1, 
                                              stop_symbol = stop_codon, 
                                              to_stop = to_stop ) )
            
        # Remove the last stop codon if necessary
        if ( ( aa_seq[ -1 ] == stop_codon ) 
             and ( not include_stop ) ):
            aa_seq = aa_seq[ :-1 ]
        
        # If the length of the provided sequence was a multiple of three, 
        # then return the amino acid sequence.
        # Otherwise, raise a TranslateDNAException.
        if ( remainder == 0 ):
            return aa_seq
        
        else:
            raise TranslateDNAException( message = ( 'The length of the DNA sequence provided is not' +
                                                     ' a multiple of three. Hence the sequence has been' +
                                                     ' translated ignoring the last ' + str( remainder ) +
                                                     ' nucleotides.' ),
                                         dna_seq = initial_dna_seq,
                                         aa_seq = aa_seq,
                                         remainder = remainder )
        
    
    
    ## find_sqce_consensus
    #  -------------------
    #
    # This is a static method that allows to find a consensus
    # from several DNA or protein sequences.
    # This sequence uses MUSCLE algorithm to compute the consensus.
    # 
    # @param list_of_sequences: List of strings - The list of sequences that needs 
    #                                             to be use to find the consensus.
    # @param sqce_type: String - The type of sequence to compare. Should equal 'DNA' or 'PROT'.
    #                            'DNA' by default.
    # @param threshold: Float - The threshold value required to add a particular letter to the
    #                           sequence, i.e. the proportion of sequences of the list that needs
    #                           to contain the letter at a particular place to consider it as part 
    #                           of the consensus. 
    #                           E.g. if the threshold is 0.7, at least 70 % of the sequences needs 
    #                           to get the letter 'X' at a given place to include this letter at this 
    #                           place in the consensus; otherwise the ambiguous letter will be added 
    #                           at this place.
    # @param fasta_end_name: String - The string to add at the end of the fasta file name (Optional).
    #
    # @return str( consensus ) - The consensus sequence computed.
    # 
    # @throw DenCellORFException: When the provided sequence type is not 'DNA' or 'PROT'.
    #
    @staticmethod
    def find_sqce_consensus( list_of_sequences, sqce_type=Constants.SEQUENCE_TYPE_DNA, \
                             threshold=Constants.DEFAULT_SQCE_CONSENSUS_AMBIG_THRESHOLD, \
                             fasta_end_name = '' ):
                
        if ( sqce_type == Constants.SEQUENCE_TYPE_DNA ):
            alphabet = generic_dna
            ambiguous = Constants.SEQUENCE_AMBIGUOUS_DNA_BASE
            
        elif ( sqce_type == Constants.SEQUENCE_TYPE_PROT ):
            alphabet = generic_protein
            ambiguous = Constants.SEQUENCE_AMBIGUOUS_PROT_AA
        
        else:
            raise DenCellORFException( 'MergeStrategy.find_sqce_consensus(): The type of sequence provided' +
                                       ' has to be ' + Constants.SEQUENCE_TYPE_DNA + ' or ' +
                                       Constants.SEQUENCE_TYPE_PROT + 
                                       ' (provided type: ' + str( sqce_type ) + ').' )
        
        # Store the input sequences in a fasta file in order to run Muscle
        input_sequences = ( SeqRecord( Seq( s, alphabet) ) for s in list_of_sequences )
        
        if ( not os.path.exists( DefaultTemporaryFolder.TEMPORARY_FOLDER ) ):
            os.makedirs( DefaultTemporaryFolder.TEMPORARY_FOLDER )
            
        input_sequences_file = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER, 
                                             'input_sequences' + fasta_end_name + '.fasta' )
        SeqIO.write( input_sequences, input_sequences_file, 'fasta' )
        
        
        # Perform the multiple sequences alignment and 
        # store the output in a fasta file
        aligned_sequences_file = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER, 
                                               'aligned_sequences' + fasta_end_name + '.fasta' )
        muscle_cline = MuscleCommandline( cmd = '/bin/muscle',
                                          input = input_sequences_file,
                                          out = aligned_sequences_file )
        
        ( stdout, stderr ) = muscle_cline()
        
        
        # Read the fasta file containing aligned sequences
        align = AlignIO.read( aligned_sequences_file, 'fasta' )
        
        summary_align = AlignInfo.SummaryInfo( align )
        
        
        # Compute the consensus
        consensus = summary_align.gap_consensus( threshold = threshold, 
                                                 ambiguous = ambiguous )
        
        
        # Remove the temporary fasta files
        os.remove( input_sequences_file )
        os.remove( aligned_sequences_file )
        
        return str( consensus )


    
    ## find_codon_consensus
    #  --------------------
    #
    # This is a static method that allows to find a consensus for the sequence
    # of a codon (i.e. for a sequence of exactly 3 nucleotides).
    # 
    # @param sequences: List of strings - The list of sequences that needs 
    #                                     to be use to find the consensus.
    # @param threshold: Float - The threshold value required to add a particular letter to the
    #                           sequence, i.e. the proportion of sequences of the list that needs
    #                           to contain the letter at a particular place to consider it as part 
    #                           of the consensus. 
    #                           E.g. if the threshold is 0.7, at least 70 % of the sequences needs 
    #                                to get the letter 'N' at a given place to include this letter 
    #                                at this place in the consensus; otherwise the ambiguous letter 
    #                                will be added at this place.
    # @param ambiguous: String - The letter to use for an ambiguous nucleotide.
    #
    # @return consensus - The consensus computed.
    #
    @staticmethod
    def find_codon_consensus( sequences, threshold=Constants.DEFAULT_SQCE_CONSENSUS_AMBIG_THRESHOLD, \
                              ambiguous=Constants.SEQUENCE_AMBIGUOUS_DNA_BASE ):
                    
        # Remove from the list of sequence any sequence that 
        # would not have exactly 3 nucleotides
        list_of_seq = []
        for seq in sequences:
            if ( len( seq ) == 3 ):
                list_of_seq.append( seq )
    
        # Get the number of sequences to use for the consensus
        sequences_count = len( list_of_seq )
        
        # If there is not any sequence in the list, return None
        if ( sequences_count == 0 ):
            consensus = None
        
        # If there is only one sequence in the list, return it
        elif ( sequences_count == 1 ):
            consensus = list_of_seq[ 0 ]
        
        # Otherwise, compute the consensus for the start codon sequence
        else:
            nt_consensus = []
            
            # First, compute the consensus for each nucleotide
            for nt_pos in range( 3 ):
                
                # For each position, get the number of time a nucleotide is found
                nt_count_dict = dict( Counter( [ seq[ nt_pos ] for seq in list_of_seq ] ) )
                 
                # Get the nucleotide(s) found the highest number of time
                nt_max_count = max( nt_count_dict.values() )
                    
                # Convert the count into a proportion
                nt_max_prop = float( nt_max_count ) / float( sequences_count )
                
                # If the proportion is (strictly) lower than the threshold defined,
                # then replace the nucleotide at this position by the ambiguous letter 
                if ( nt_max_prop < threshold ):
                    nt_consensus.append( ambiguous )
                    
                # Otherwise, use the letter(s) at this positions to compute the consensus
                else:
                    nt_list = [ nt for ( nt, count ) in nt_count_dict.items() if ( count == nt_max_count ) ]
                    # If there is one single nucleotide with this proportion, use it in the consensus
                    if ( len( nt_list ) == 1 ):
                        nt_consensus.append( nt_list[ 0 ] )
                    # Otherwise, use the ambiguous letter for this position
                    else:
                        nt_consensus.append( ambiguous )
            
            # Create a string from the consensus for the three nucleotides
            consensus = ''.join( nt_consensus )
            
        return consensus
