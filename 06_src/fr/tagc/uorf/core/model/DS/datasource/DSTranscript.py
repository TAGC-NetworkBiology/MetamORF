# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes

from fr.tagc.uorf.core.util.sql.Base import BaseDS
from fr.tagc.uorf.core.util.sql.SQLCollationManager import SQLCollationManager

from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


## DSTranscript
#  ============
#
# Each Transcript contains:
#     - id: Integer - A unique transcript ID.
#     - transcript_id: String - The unique Transcript ID.
#     - data_source: String - The name of the source.
#     - gene_id: String - The unique gene ID.
#     - raw_strand: String - The strand of the transcript (in the original annotation version).
#     - raw_start_pos: Integer - The genomics coordinates of the first nucleotide of the transcript
#                                (in the original annotation version).
#     - raw_end_pos: Integer - The genomics coordinates of the last nucleotide of the transcript 
#                              (in the original annotation version).
#     - strand: String - The strand of the transcript.
#     - start_pos: Integer - The genomics coordinates of the first nucleotide of the transcript 
#                            (in the current annotation version).
#     - end_pos: Integer - The genomics coordinates of the last nucleotide of the transcript 
#                          (in the current annotation version).
#     - raw_cds_start_pos: Integer - The genomics coordinates of the start codon of the CDS 
#                                    (in the original annotation version).
#     - raw_cds_stop_pos: Integer - The genomics coordinates of the stop codon of the CDS 
#                                   (in the original annotation version).
#     - cds_start_pos: Integer - The genomics coordinates of the start codon of the CDS 
#                                (in the current annotation version).
#     - cds_stop_pos: Integer - The genomics coordinates of the stop codon of the CDS 
#                               (in the current annotation version).
#     - rna_biotype: String - The RNA biotype.
#
class DSTranscript( BaseDS ):

    __tablename__ = 'DSTranscript'
            
    id = Column( Integer )
    transcript_id = Column( String( 255, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    data_source = Column( String( 50, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                          ForeignKey( 'DataSource.name', ondelete='CASCADE', onupdate='CASCADE' ) )
    gene_id = Column( String( Constants.MAX_LEN_STRING, collation = SQLCollationManager.get_instance().get_db_collation() ), 
                      ForeignKey( 'Gene.gene_id', ondelete='CASCADE', onupdate='CASCADE' ) )
    raw_strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    raw_start_pos = Column( Integer )
    raw_end_pos = Column( Integer )
    strand = Column( String( 2, collation = SQLCollationManager.get_instance().get_db_collation() ) )
    start_pos = Column( Integer )
    end_pos = Column( Integer )
    raw_cds_start_pos = Column( Integer )
    raw_cds_stop_pos = Column( Integer )
    cds_start_pos = Column( Integer )
    cds_stop_pos = Column( Integer )
    rna_biotype = Column( String( 255, collation=SQLCollationManager.get_instance().get_db_collation() ) )

    # Define the primary key and the unique constraint on the "primary key-like" attributes
    __table_args__ = (
                        PrimaryKeyConstraint( 'id' ),
                        UniqueConstraint( 'transcript_id', 'data_source' ),
                    )

    # Define the one-to-many relationship
    DSORFTranscriptAsso_list = relationship( 'DSORFTranscriptAsso', cascade = 'all', backref = 'DSTranscript' )



    ## __eq__
    #  ------
    #
    # Tests the equality between two instances of this class.
    # Two instances are considered equals if their "primary key-like" attributes 
    # (i.e. the attributes with unique constraint) are all equals.
    #
    # @param other: DSTranscript - Another DSTranscript object to compare to this object.
    #
    # @return Boolean - Are this object and the other one equal?
    #
    def __eq__( self, other ):
        
        # Check if other object is of the same class
        if ( type( other ) != type( self ) ):
            return False
        
        # Check if the transcript ID and the source are the same
        elif ( ( self.transcript_id == other.transcript_id )
               and ( self.data_source == other.data_source ) ):
            return True
        
        else:
            return False


    ## __hash__
    #  --------
    #
    # Returns the hash value of a DSTranscript object.
    # The hash value of an instance is computed using its "primary key-like" attributes 
    # (i.e. the attributes with unique constraint).
    #
    # @return the hash value of the DSTranscript object.
    #
    def __hash__( self ):
        
        return hash( ( self.transcript_id, self.data_source ) )


    ## update
    #  ------
    #
    # Try to combine two instances of this class when they are "equals"
    # (i.e. share the same values for "primary key-like attributes") by getting the 
    # missing attributes.  It tests the equality between non-primary-key attributes 
    # of two equal instances of this class, and raise an DenCellORFObjUpdateException 
    # if DSTranscript compared have different values for their non-primary key 
    # attributes. 
    # If:
    #     - The self object is missing some values the other object has, then it updates
    #       the current object. 
    #     - The information provided by both objects are contradictory, it logs a warning.
    #
    # @param other: DSTranscript - Another DSTranscript object "equal" to the current one.
    # @param gene_id_conflicts: List - The list of all gene IDs that have been found associated 
    #                                  to the DSTranscript entry. None by default.
    #
    # @throw DenCellORFTrUpdateException: When different values are found for the same attributes
    #                                     of two objects assumed to be the same.
    #
    def update( self, other, gene_id_conflicts=None ):
        
        # For each non-primary-key attribute, check if it is provided,
        # try to update the current object by completing missing information
        # using information provided by the other one and if there are attributes
        # which have different values, raise an excpetion
        attributes_to_check = [ 'raw_strand', 'raw_start_pos', 'raw_end_pos', 
                                'raw_cds_start_pos', 'raw_cds_stop_pos', 'rna_biotype' ]
        
        # List of the attributes for which the value should be set to 
        # 'AMBIGUOUS' if they are found different
        att_to_flag_if_conflict = [ 'rna_biotype' ]

        # Initialize a dictionary attributes for which there is a conflict
        conflicting_att = {}
        
        # Check the gene IDs. If the two gene IDs are different, create a new ID 
        # by concatenating the names of the two genes.
        self_gene = self.gene_id
        other_gene = other.gene_id
        
        if ( self_gene != other_gene ):
            
            init_gene_id_conflicts = gene_id_conflicts
            
            # If a conflict has already been registered for this DSTranscript, 
            # then get the list of genes associated to it.
            # Otherwise, register this first conflict.
            if gene_id_conflicts:
                # Get the name of the gene which does not start with the CONFLICT prefix
                if ( ( not self_gene.startswith( Constants.PREFIX_CONFLICT_GENE_TRANSCRIPT ) )
                     and ( self_gene not in gene_id_conflicts ) ):
                    gene_id_conflicts.append( self_gene )
                    
                if ( ( not other_gene.startswith( Constants.PREFIX_CONFLICT_GENE_TRANSCRIPT ) )
                    and ( other_gene not in gene_id_conflicts ) ):
                    gene_id_conflicts.append( other_gene )
                
            else:
                # Register this new conflict and order the gene IDs
                gene_id_conflicts = [ self_gene, other_gene ]
        
            # Order the IDs in order to always get the same new ID when the same gene IDs are conflicting
            gene_id_conflicts.sort()
        
            # Register the new list of conflict on gene IDs only if it has been updated
            if ( gene_id_conflicts != init_gene_id_conflicts ):
                # Create a new "conflict" id 
                new_gene_id = Constants.PREFIX_CONFLICT_GENE_TRANSCRIPT + '_'.join( gene_id_conflicts )            
                self.gene_id = new_gene_id
                conflicting_att[ 'gene_id' ] = ( self_gene, other_gene, self.gene_id )
        
        
        # Check all the other non-primary-key attributes
        for att in attributes_to_check:
            
            self_att = getattr( self, att )
            other_att = getattr( other, att )
            
            # If the attribute treated is the raw strand, the '-' value 
            # should not be considered as missing value
            if ( att == 'raw_strand' ):
                self_att_is_empty = GeneralUtil.is_empty( val = self_att, 
                                                          empty_val = Constants.EMPTY_VALUES_WO_DASH )
                other_att_is_empty = GeneralUtil.is_empty( val = other_att, 
                                                           empty_val = Constants.EMPTY_VALUES_WO_DASH )
            else:
                self_att_is_empty = GeneralUtil.is_empty( self_att )
                other_att_is_empty = GeneralUtil.is_empty( other_att )
        
            # If the other attribute is provided    
            if ( not other_att_is_empty ):
                
                # and if the self attribute is empty, fill it using the information of the other object
                if self_att_is_empty:
                    setattr( self, att, other_att )
                
                # and if the self attribute is filled and the two values of the attribute are different, 
                # reset the value to 'AMBIGUOUS' and keep track of this attribute and its values
                elif ( ( not self_att_is_empty ) and ( other_att != self_att ) ):
                    if att in att_to_flag_if_conflict:
                        setattr( self, att, Constants.DENCELLORFOBJ_AMBIGUOUS_ATT )
                    else:
                        setattr( self, att, None )
                    conflicting_att[ att ] = ( self_att, other_att, getattr(self, att) )
        
        # If there are attributes for which there is a conflict, 
        # raise a DenCellORFTrUpdateException
        if conflicting_att != {}:
            except_message = []
            for (att, val) in conflicting_att.items():
                except_message.append( 'the attribute ' + att + ' has been found with the values "' + 
                                       str( val[0] ) + '" and "' + str( val[1] ) + '",' +
                                       ' hence its value has been set to "' + str( val[2] ) + '"' )
            except_message = ', '.join( except_message ) + '.'
            
            # If a conflict has been found regarding the gene ID, raise the exception 
            # with the value of the new gene ID to create and to associate to this transcript
            if ( 'gene_id' in conflicting_att.keys() ):
                raise DenCellORFTrUpdateException( message = except_message, 
                                                   gene_id = self.gene_id, 
                                                   gene_id_conflicts = gene_id_conflicts )
            else:
                raise DenCellORFTrUpdateException( message = except_message )
