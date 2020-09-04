# -*- coding: utf-8 -*-

import os

import wget

import pyliftover as pylo


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.sql.SQLManagerDS import SQLManagerDS
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## LiftOverStrategy
#  ================
#
# This class is a strategy aiming to convert all the genomic coordinates
# contained in the DS database (in DSORF and DSTranscript table) from a 
# genome annotation version to the current one.
#
class LiftOverStrategy( object ):
    
    ## Class variables
    #  ---------------
    #
    # URL of chain files (necessary for the conversion of genomic positions)
    CHAIN_FILE_URL = { Constants.ANNOTATION_VERSION_HG19 : 'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/liftOver/hg19ToHg38.over.chain.gz',
                       Constants.ANNOTATION_VERSION_GRCH37 : 'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/liftOver/hg19ToHg38.over.chain.gz' }
    CHAIN_FILENAMES = { Constants.ANNOTATION_VERSION_HG19 : 'hg19ToHg38.over.chain.gz',
                        Constants.ANNOTATION_VERSION_GRCH37 : 'hg19ToHg38.over.chain.gz' }
    
    # Attributes of the DSORF table that need to be converted
    SPLICED_ATT_DSORF = [ 'splice_starts', 'splice_ends' ]
    ATT_TO_CONVERT_DSORF = [ 'start_pos', 'stop_pos' ] + SPLICED_ATT_DSORF
    
    # Attributes of the DSORF table that need to be reset 
    # when the LiftOver failed for the whole DSORF
    ATT_TO_RESET_DSORF = ATT_TO_CONVERT_DSORF + [ 'strand' ]
    
    # Attributes of the DSTranscript table that need to be converted
    CDS_ATT_DSTRANSCRIPT = [ 'cds_start_pos', 'cds_stop_pos' ]
    ATT_TO_CONVERT_DSTRANSCRIPT = [ 'start_pos', 'end_pos' ] + CDS_ATT_DSTRANSCRIPT
    
    # Attributes of the DSTranscript table that need to be reset when the LiftOver failed for the whole DSTranscript
    ATT_TO_RESET_DSTRANSCRIPT = ATT_TO_CONVERT_DSTRANSCRIPT + [ 'strand' ]


    ## Constructor of LiftOverStrategy
    #  -------------------------------
    #
    # Instance variables:
    #     - configfile: String - The path to the config file.
    #     - species: String - The name of the species in the database.
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    # 
    def __init__( self ):

        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none=True )

        if configfile:
            self.configfile = configfile
            if ( not os.path.exists( configfile ) ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' Please see the documentation for more information.' )
        
        self.species = None
    
        
    
    ## execute
    #  -------
    #
    # Execute the strategy to perfom the liftover.
    #
    # @throw DenCellORFException: When an exception has been raised during the DatabaseCheck.
    # @throw DenCellORFException: When an exception has been raised trying to update the
    #                             content of the Metadata table.
    # 
    def execute( self ):
        
        # Run DatabaseCheck in order to check the DS database is reachable prior to 
        # the conversion of genomic coordinates
        Logger.get_instance().info( 'Checking the database prior to the lift over...' )
        try:
            DatabaseCheckStrategy().execute()
        except Exception as e:
            raise DenCellORFException( 'An error occurred whilst checking the database prior to lift over.' +
                                       '\n Error code: ' + LogCodes.ERR_DBCHECK + '.', e )
        
        # Get the species in the database
        self.species = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        
        # Get all the data sources contained in the database
        DataManager.get_instance().store_DS_query_result( Constants.DM_ALL_DATASOURCES, 
                                                          'query( DataSource ).all()' )
        datasources = DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES )
        
        # Build a dictionary which associates each data source to its annotation version
        DataManager.get_instance().store_data( Constants.DM_DATASOURCE_ANNOT, {} )
        datasource_annot = DataManager.get_instance().get_data( Constants.DM_DATASOURCE_ANNOT )
        for ds in datasources.keys():
            datasource_annot[ ds.name ] = ds.annotation_version
        
        # Save the name of the annotation currently used in the metadata table
        metadata_all_query = SQLManagerDS.get_instance().get_session().query( Metadata ).filter( Metadata.parameter == Constants.METATABLE_CURRENT_ANNOTATION )
        metadata_all_count = metadata_all_query.count()
        
        if ( metadata_all_count == 0 ):
            metadata_current_annot = Metadata( parameter = Constants.METATABLE_CURRENT_ANNOTATION,
                                               value = Constants.CURRENT_NCBI_ANNOTATION[ self.species ],
                                               description = Constants.METATABLE_CURRENT_ANNOTATION_DESCRIPTION )
            try:
                SQLManagerDS.get_instance().get_session().add( metadata_current_annot )
                SQLManagerDS.get_instance().commit()
            except Exception as e:
                raise DenCellORFException( 'LiftOverStrategy.execute(): An error occurred trying to add the ' + 
                                           ' annotation version information and committing the session.', e )
                
        else:
            metadata_current_annot = metadata_all_query.one()
            if ( str( metadata_current_annot.value ) != Constants.CURRENT_NCBI_ANNOTATION[ self.species ] ):
                Logger.get_instance().warning( 'An entry with parameter ' + 
                                               str( Constants.METATABLE_CURRENT_ANNOTATION ) + 
                                               ' has been found in the Metadata table and' +
                                               ' this entry contains the value ' + 
                                               str( metadata_current_annot.value ) + 
                                               ' whilst the ensembl release used by the program is ' +
                                               str( Constants.CURRENT_NCBI_ANNOTATION[ self.species ] ) + 
                                               '. Hence, this entry will be updated to current version.' +
                                               ' Warning code: ' + LogCodes.WARN_LIFTOV_META_ANNOT_UP + '.' )
                metadata_current_annot.value = Constants.CURRENT_NCBI_ANNOTATION[ self.species ]
                metadata_current_annot.description = Constants.METATABLE_CURRENT_ANNOTATION_DESCRIPTION
                try:
                    SQLManagerDS.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'LiftOverStrategy.execute(): An error occurred trying' +
                                               ' to update the Metadata entry containing the annotation' +
                                               ' version information.', e )
                    
        SQLManagerDS.get_instance().close_session()
          
        # Convert the genomic coordinates to the current genome assembly
        self.convert_genomic_coordinates()
        
        # Compute the genomic lengths for all the entries of the DSORF table
        self.compute_dsorf_gen_len()

    
    
    # ===============================================================================
    # Methods related to the lift over
    # ===============================================================================
    
    ## convert_genomic_coordinates
    #  ---------------------------
    #
    # This method allows to convert all the genomic coordinates contained in the DSORF 
    # and DSTranscript table of the DS database to the current version.
    # 
    # The entries of these tables are updated during the execution of this method:
    #     - DSORF table: start_pos, stop_pos, splice_starts, splice_stops attributes
    #     - DSTranscript table: start_pos, end_pos, cds_start_pos, cds_stop_pos
    # NB: When the coordinates provided by the source (attributes with a 'raw_' prefix) 
    #     are already in the right annotation version, they are just copied into the 
    #     corresponding field (attribute without 'raw_' prefix). Otherwise, the coordinates 
    #     are converted (using pyliftover) and saved in the corresponding field.
    #
    # /!\ Please be aware that this version of the method uses GRCh38 (hg38) and GRCm38 (mm10)
    #     as current annotation versions, and only allows the conversion of GRCh37 (hg19) 
    #     coordinates to GRCh38 (hg38), as all the file parsed provide coordinates either 
    #     in the GRCh38 (hg38), GRCh37 (hg19) or GRCm38 (mm10) annotation version.
    #     See the Constants file for more information about the annotation version handled
    #     by the program.
    # 
    def convert_genomic_coordinates( self ):
                
        # Get all the data sources contained in the database
        datasources = DataManager.get_instance().get_data( Constants.DM_ALL_DATASOURCES )
        
        # Get the dictionary which associates each data source 
        # to its annotation version
        datasource_annot = DataManager.get_instance().get_data( Constants.DM_DATASOURCE_ANNOT )
        
        # Instantiate an empty list to receive all the objects 
        # that have to be updated
        updated_objects = []
        
        # Get the total number of entries expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        total_entries_count = ( SQLManagerDS.get_instance().get_session().query( DSORF ).count() + 
                                SQLManagerDS.get_instance().get_session().query( DSTranscript ).count() )
        SQLManagerDS.get_instance().close_session()
        
        ProgressionBar.get_instance().reset_instance( total = total_entries_count )
        
        # Get the list of the current annotation version for the species
        current_annotation = [ Constants.CURRENT_NCBI_ANNOTATION[ self.species ], 
                               Constants.CURRENT_UCSC_ANNOTATION[ self.species ] ]
        
        # For each data source, perform the conversion of coordinates 
        # on each DSORF and DSTranscript entry related to it
        for ( ds, annot ) in datasource_annot.items():
            
            Logger.get_instance().debug( 'LiftOverStrategy.convert_genomic_coordinates():' +
                                         ' Starting the conversion of the genomic coordinates of' +
                                         ' DSORF and DSTranscript entries related to ' + 
                                         ds + ' (annotation version: ' + annot + ').' )
            
            # Get all the DSORF entries and all the DSTranscript entries related to this source
            all_dsorfs_for_source = SQLManagerDS.get_instance().get_session().query( DSORF ).filter( DSORF.data_source == ds ).all()
            all_dstranscripts_for_source = SQLManagerDS.get_instance().get_session().query( DSTranscript ).filter( DSTranscript.data_source == ds ).all()
            SQLManagerDS.get_instance().close_session()
            
            # If the annotation of the data source is the current one, 
            # duplicate the provided genomic coordinates
            if annot in current_annotation:
                
                # Treat all the DSORF entries related to the source
                for dsorf in all_dsorfs_for_source:
                    
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Duplicate the genomic coordinates
                    updated_objects.append( self.duplicate_dsorf_coordinates( dsorf ) )
                
                # Treat all the DSTranscript entries related to the source
                for dstranscript in all_dstranscripts_for_source:
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Duplicate the genomic coordinates
                    updated_objects.append( self.duplicate_dstranscript_coordinates( dstranscript ) )
                    
                    
            # Otherwise, first make sure the annotation of the data source is one expected
            elif annot in Constants.ALL_SPECIES_ANNOTATIONS:
                
                # Download and import the appropriate chain file (from the UCSC) 
                # allowing the conversion of annotation version
                Logger.get_instance().debug( 'LiftOverStrategy.convert_genomic_coordinates():' +
                                             ' Downloading the appropriate chain file from the UCSC' +
                                             ' to perfom the conversion of the genomic coordinates.' )
                chain_file_url = LiftOverStrategy.CHAIN_FILE_URL[ annot ]
                
                if ( not os.path.exists( DefaultTemporaryFolder.TEMPORARY_FOLDER ) ):
                    os.makedirs( DefaultTemporaryFolder.TEMPORARY_FOLDER )
                
                chain_file_path = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER, LiftOverStrategy.CHAIN_FILENAMES[ annot ] )
                
                if ( not os.path.exists( chain_file_path ) ):
                    wget.download( chain_file_url, out = chain_file_path, bar = None )
                
                lo = pylo.LiftOver( chain_file_path )
                
                # Treat all the DSORF entries related to the source
                for dsorf in all_dsorfs_for_source:
                    
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Convert the genomic coordinates
                    updated_objects.append( self.convert_dsorf_coordinates( dsorf, lo ) )
                    
                # Treat all the DSTranscript entries related to the source
                for dstranscript in all_dstranscripts_for_source:
                    # Update and display the progression bar on the console
                    ProgressionBar.get_instance().increase_and_display()
                    
                    # Convert the genomic coordinates
                    updated_objects.append( self.convert_dstranscript_coordinates( dstranscript, lo ) )
                
            # Otherwise, log an error
            else:
                Logger.get_instance.error( 'LiftOverStrategy.convert_genomic_coordinates():' +
                                           ' The annotation version provided for the data source ' +
                                           ds + '(' + annot + ') is unexpected.' + 
                                           ' Hence, the genomic coordinates of the entries related to' +
                                           ' this data source will not be converted.' +
                                           ' Please make sure to use one of the following annotation version: ' + 
                                           ', '.join( Constants.ALL_SPECIES_ANNOTATIONS ) + '.',
                                           ex = False )
            
            Logger.get_instance().debug( 'LiftOverStrategy.convert_genomic_coordinates():' +
                                         ' The conversion of genomic coordinates of the' +
                                         ' DSORF and DSTranscript entries related to ' + 
                                         ds + ' has finished.' )
            
        # Update the objects in the database
        if ( len( updated_objects ) != 0 ):
            SQLManagerDS.get_instance().batch_insert_to_db( objects_to_insert = updated_objects,
                                                            process = 'objects_with_updated_coordinates' )
            
    
    
    ## convert_coord
    #  -------------
    #
    # This method returns the genomics coordinates (chromosome, strand and position)
    # after its conversion from an anotation version to an other.
    #
    # @param chr: String - The chromosome name.
    # @param strand: String - The genomic strand.
    # @param position: Integer - The position to convert.
    # @param lo: LiftOver - The LiftOver instance (pyliftover package) necessary 
    #                       to perform the conversion of the genomic coordinates.
    #
    # @return new_chr: String - The chromosome name after the conversion.
    # @return new_strand: String - The genomic strand after the conversion.
    # @return new_pos: The position after the conversion.
    # 
    # @throw ConvertCoordException: When the conversion of the genomic coordinate failed.
    #
    @staticmethod
    def convert_coord( chr, strand, position, lo ):
        
        # Check all the necessary information are provided
        if ( ( chr == None ) or ( strand == None ) or ( position == None ) ):
            raise ConvertCoordException( 'The conversion of the genomic coordinates (' +
                                         str( chr ) + str( strand ) + ':' + str( position ) + 
                                         ') failed as some necessary data are missing.' )
        
        # Make sure the chromosome name contains the 'chr' prefix
        chr = str( chr )
        if ( not chr.startswith( 'chr' ) ):
            chr = 'chr' + chr
        
        # Try to convert the provided coordinates
        new_coord = lo.convert_coordinate( chr,
                                           int( position ),
                                           strand )
        
        if ( ( new_coord != None ) and ( len( new_coord ) == 1 ) ):
            new_chr = new_coord[0][0]
            new_pos = new_coord[0][1]
            new_strand = new_coord[0][2]
            return ( new_chr, new_strand, new_pos )
        
        else:
            raise ConvertCoordException( 'The conversion of the genomic coordinates (' +
                                         str( chr ) + str( strand ) + ':' + str( position ) + 
                                         ') failed.' )
        
        
                
    ## convert_dsorf_coordinates
    #  -------------------------
    #
    # This is a static method that allows to convert all the genomic coordinates 
    # of a DSORF entry.
    # It tries to convert:
    #     - raw_strand (output registered in strand).
    #     - raw_start_pos (output registered in start_pos).
    #     - raw_stop_pos (output registered in stop_pos).
    #     - raw_splice_starts (output registered in splice_starts).
    #     - raw_splice_stops (output registered in splice_stops).
    #
    # If the conversion cannot be performed, then a warning is logged and the value
    # of the attribute is set to None.
    # If the chromosome of one attribute changed during the conversion, then a message
    # is logged, the conversion is stopped for the entry and all the attributes that were
    # going to be converted are re-set to None.
    #
    # @param dsorf: DSORF - The DSORF entry for which the conversion should be performed.
    # @param lo: LiftOver - The LiftOver instance (pyliftover package) necessary to
    #                       perform the conversion of the genomic coordinates. 
    #
    # @return dsorf: DSORF - The updated DSORF object.
    #
    @staticmethod
    def convert_dsorf_coordinates( dsorf, lo ):
        
        # Get the chromosome and the strand of the ORF
        orf_chromosome = 'chr' + str( dsorf.chromosome )
        orf_strand = dsorf.raw_strand
        
        
        # If the chromosome name or the strand is missing, 
        # then do not try to perform any conversion
        if ( ( orf_strand == None ) or ( orf_chromosome == None ) ):
            
            return LiftOverStrategy.reset_dsorf( dsorf )
        
        
        ## Convert the start and stop coordinates
        #  --------------------------------------
        
        # Perform the conversion for the start genomic coordinate
        try:
            ( start_chr, start_strand, start_pos ) = LiftOverStrategy.convert_coord( chr = orf_chromosome,
                                                                                     strand = orf_strand,
                                                                                     position = dsorf.raw_start_pos,
                                                                                     lo = lo )
        except ConvertCoordException as e:
            Logger.get_instance().warning( 'Error during conversion of start coordinate for the' +
                                           ' DSORF with ID "' + str( dsorf.id ) + '". ' + e.get_message() + 
                                           ' Hence this position will not be registered.' +
                                           ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
            ( start_chr, start_strand, start_pos ) = ( None, None, None )
            
        else:
            # Check the chromosome name did not changed during coordinates conversion, 
            # otherwise log an error message
            if ( orf_chromosome != start_chr ):
                if ( start_chr.split( '_' )[ 0 ] == orf_chromosome ):
                    Logger.get_instance().warning( 'The conversion of coordinates for the DSORF with ID "' +
                                                   str( dsorf.id ) + '" returned a start position on a' +
                                                   ' different chromosome (ORF chromosome: "' + orf_chromosome + 
                                                   '", start chromosome: "' + str( start_chr ) + '"),' +
                                                   ' but these chromosomes actually seem to be the same.' +
                                                   ' Hence, this DSORF will be considered as located on "' + 
                                                   orf_chromosome + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                    
                else:
                    Logger.get_instance().error( 'The conversion of coordinates for the DSORF with ID "' + 
                                                 str( dsorf.id ) + '" returned a start position on a' +
                                                 ' different chromosome (ORF chromosome: "' + orf_chromosome + 
                                                 '", start chromosome: "' + str( start_chr ) + '").' +
                                                 ' Hence, the lift over will not be performed for this ORF.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                 ex = False )
                    return LiftOverStrategy.reset_dsorf( dsorf )
                
                
        # Perform the conversion for the stop genomic coordinate
        try:
            ( stop_chr, stop_strand, stop_pos ) = LiftOverStrategy.convert_coord( chr = orf_chromosome,
                                                                                  strand = orf_strand,
                                                                                  position = dsorf.raw_stop_pos,
                                                                                  lo = lo )
            
        except ConvertCoordException as e:
            Logger.get_instance().warning( 'Error during conversion of stop coordinate for the DSORF' +
                                           ' with ID "' + str( dsorf.id ) + '". ' + e.get_message() + 
                                           ' Hence this position will not be registered.' +
                                           ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
            ( stop_chr, stop_strand, stop_pos ) = ( None, None, None )
            
        else:
            # Check the chromosome name did not changed during coordinates conversion,
            # otherwise log an error message and reset the DSORF entry
            if ( orf_chromosome != stop_chr ):
                if ( stop_chr.split( '_' )[ 0 ] == orf_chromosome ):
                    Logger.get_instance().warning( 'The conversion of coordinates for the DSORF with ID "' + 
                                                   str( dsorf.id ) + '" returned a stop position on a' +
                                                   ' different chromosome (ORF chromosome: "' + orf_chromosome + 
                                                   '", stop chromosome: "' + str( stop_chr ) + '"),' +
                                                   ' but these chromosomes actually seem to be the same.' +
                                                   ' Hence, this DSORF will be considered as located on "' + 
                                                   orf_chromosome + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                    
                else:
                    Logger.get_instance().error( 'The conversion of coordinates for the DSORF with ID "' + 
                                                 str( dsorf.id ) + '" returned a stop position on a' +
                                                 ' different chromosome (ORF chromosome: "' + orf_chromosome + 
                                                 '", stop chromosome: "' + str( stop_chr ) + '").' +
                                                 ' Hence, the LiftOver will not be performed for this ORF.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                 ex = False )
                    return LiftOverStrategy.reset_dsorf( dsorf )
            
        
        # Check the agreement between the start and stop coordinates after conversion:
        # - check the strand after conversion
        #     - If the strands of the start and stop positions are both missing,
        #       then stop the conversion and return the dsorf (without saving any 
        #       of the converted position).
        #     - Otherwise
        #         - If the start strand is missing or if the stop strand is missing, 
        #           then, one checks that the provided strand is the same as the raw strand.
        #         - If the both strands are provided,
        #             - and if they are different one from the other, then stop the conversion, 
        #               log an error and return the dsorf (without saving any of the converted 
        #               position)
        #             - and if they are equals, then check if they equal also the raw strand.
        #
        # - If the strand is on the opposite strand than the raw strand, then exchange the start 
        #   and stop coordinates in order to always get the start lower than the stop.
        #
        if ( ( start_strand, stop_strand ) == ( None, None ) ):
            
            return LiftOverStrategy.reset_dsorf( dsorf )

        else:
            reverse_start_stop = False
            
            if ( start_strand == None ):
                dsorf.strand = stop_strand
                if ( stop_strand != orf_strand ):
                    reverse_start_stop = True
                
            elif ( stop_strand == None ):
                dsorf.strand = start_strand
                if ( start_strand != orf_strand ):
                    reverse_start_stop = True
            
            else:
                if ( start_strand != stop_strand ):
                    Logger.get_instance().error( 'The conversion of coordinates for the DSORF with ID "' + 
                                                 str( dsorf.id ) + '" returned a start and a stop position' +
                                                 ' on different strands (orf strand: "' + str( orf_strand ) + 
                                                 '", start strand: "' + str( start_strand ) + 
                                                 '", stop strand: ' + str( stop_strand ) + 
                                                 '"). Hence the converted coordinates of this DSORF will' +
                                                 ' not be registered.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_STRAND + '.',
                                                 ex = False )
                    
                    return LiftOverStrategy.reset_dsorf( dsorf )
                
                else:
                    dsorf.strand = start_strand
                    if ( start_strand != orf_strand ):
                        reverse_start_stop = True
        
        # Save the new strand, start and stop positions after the conversion
        if reverse_start_stop:
            # If the strand has been reversed during the liftOver, but the position
            # get by conversion of the start_pos attribute (i.e. the actual "new" 
            # start position saved in stop_pos attribute for the DSORFs initially 
            # on the + strand, and the actual "new" stop position saved in start_pos 
            # attribute for the DSORFs initially on the - strand) is lower than the 
            # position get by the conversion of the stop_pos attribute (i.e. the actual 
            # "new" stop position saved in start_pos attribute for the DSORFs initially 
            # on the + strand, and the actual "new" start position saved in stop_pos 
            # attribute for the DSORFs initially on the - strand), then reset the DSORF 
            # entry.
            if ( start_pos < stop_pos ):
                Logger.get_instance().error( 'The conversion of the coordinates for the DSORF with ID "' + 
                                             str( dsorf.id ) + '" returned incoherent data: the strand' +
                                             ' has been reversed (new strand: ' + str( dsorf.strand ) + 
                                             ') but the conversion of the raw_start_pos attribute provides' +
                                             ' a lower value than the conversion of the raw_stop_pos attribute.' +
                                             ' Hence, the LiftOver will not be performed for this ORF.' +
                                             ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_POS + '.',
                                             ex = False )
                return LiftOverStrategy.reset_dsorf( dsorf )
            # Otherwise, inverse the value of the start and stop positions as the 
            # strand has changed.
            else:
                dsorf.start_pos = stop_pos
                dsorf.stop_pos = start_pos
                
        else:
            # If the strand has not been reversed during the liftOver, but the position
            # get by conversion of the start_pos attribute (i.e. the actual "new" 
            # start position saved in stop_pos attribute for the DSORFs initially 
            # on the + strand, and the actual "new" stop position saved in start_pos 
            # attribute for the DSORFs initially on the - strand) is greater than the 
            # position get by the conversion of the stop_pos attribute (i.e. the actual 
            # "new" stop position saved in start_pos attribute for the DSORFs initially 
            # on the + strand, and the actual "new" start position saved in stop_pos 
            # attribute for the DSORFs initially on the - strand), then reset the DSORF 
            # entry.
            if ( start_pos > stop_pos ):
                Logger.get_instance().error( 'The conversion of the coordinates for the DSORF with ID "' + 
                                             str( dsorf.id ) + '" returned incoherent data: the strand' +
                                             ' has not been reversed (strand: ' + str( dsorf.strand ) + 
                                             ') but the conversion of the raw_start_pos attribute provides' +
                                             ' a higher value than the conversion of the raw_stop_pos attribute.' +
                                             ' Hence, the LiftOver will not be performed for this ORF.' +
                                             ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_POS + '.',
                                             ex = False )
                return LiftOverStrategy.reset_dsorf( dsorf )
            else:
                dsorf.start_pos = start_pos
                dsorf.stop_pos = stop_pos
            
                   
        
        ## Convert the splicing coordinates
        #  --------------------------------
        
        for att in LiftOverStrategy.SPLICED_ATT_DSORF:
            
            raw_att_value = getattr( dsorf, 'raw_' + att )
            
            # Try to convert the coordinates only if they are provided
            if ( raw_att_value == None ):
                new_att_value = None
            
            # If the splicing value provided in the source exceeded the longest 
            # value that can be stored, use the same "TOO_LONG" string
            elif ( raw_att_value == Constants.REPLACE_TOO_LONG_STRINGS ):
                new_att_value = None
                
            # If splicing coordinates are provided, first parse the string into a list, 
            # convert each element of the list and then rebuild a string with the new coordinates
            else:
                raw_att_value = raw_att_value.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                
                # Try to convert each element of the list,
                # If one of them cannot be converted or if one of them is not on the 
                # same strand as the start and stop positions, then the whole attribute 
                # value is set to None
                impossible_conversion = False
                raw_att_value_index = 0
                
                new_att_value = []
                
                while ( ( not impossible_conversion ) and ( raw_att_value_index < len( raw_att_value ) ) ):
                    
                    try:
                        ( exon_chr, exon_strand, exon_pos ) = LiftOverStrategy.convert_coord( chr = orf_chromosome,
                                                                                              strand = orf_strand,
                                                                                              position = raw_att_value[ raw_att_value_index ],
                                                                                              lo = lo )
                    
                    except ConvertCoordException as e:
                        Logger.get_instance().warning( 'Error during conversion of the ' + att + 
                                                       ' attribute for the DSORF with ID "' + str( dsorf.id ) +
                                                       '". ' + e.get_message() + 
                                                       ' Hence. the value of this attribute has been set to None.' +
                                                       ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
                        impossible_conversion = True
                        new_att_value = None
                    
                    else:
                        raw_att_value_index += 1
                        # If the "exon" is on a different chromosome than the ORF, log a critical message
                        if ( exon_chr != orf_chromosome ):
                            if ( exon_chr.split( '_' )[ 0 ] == orf_chromosome ):
                                Logger.get_instance().warning( 'The conversion of coordinates for the' +
                                                               ' DSORF with ID "' + str( dsorf.id ) + 
                                                               '" returned a splicing position on a different' +
                                                               ' chromosome than the ORF (ORF chromosome: "' +
                                                               orf_chromosome + '", splicing position on: "' + 
                                                               str( exon_chr ) + '"), but these chromosomes' +
                                                               ' actually seem to be the same.' +
                                                               ' Hence, this DSORF will be considered as' +
                                                               ' located on ' + orf_chromosome + '.' +
                                                               ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                            else:
                                Logger.get_instance().error( 'The conversion of coordinates for the DSORF' +
                                                             ' with ID "' + str( dsorf.id ) + 
                                                             '" returned a splicing position on a different' +
                                                             ' chromosome than the ORF (ORF chromosome: "' +
                                                             orf_chromosome + '", splicing position on: "' + 
                                                             str( exon_chr ) + '"),' + ' Hence, the lift' +
                                                             ' over will not be performed for this DSORF.' +
                                                             ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                             ex = False )
                                return LiftOverStrategy.reset_dsorf( dsorf )
                        
                        # If the "exon" is on a different strand than the ORF, 
                        # then log an error and stop the conversion of coordinates
                        if ( exon_strand != dsorf.strand ):
                            Logger.get_instance().error( 'The conversion of coordinates for the DSORF' +
                                                         ' with ID "' + str( dsorf.id ) +
                                                         '" returned a splicing position on a different' +
                                                         ' strand than the ORF (orf strand: "' +
                                                         str( dsorf.strand ) + '", splicing strand: "' + 
                                                         str( exon_strand ) + '"). Hence the converted' +
                                                         ' splicing coordinates of this DSORF will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_STRAND + '.',
                                                        ex = False )
                            impossible_conversion = True
                            new_att_value = None
                            
                        # Otherwise, add the converted position to the list 
                        # and pursue the conversion
                        else:
                            new_att_value.append( exon_pos )
                            
                # Rebuild a string from the list of coordinates
                if ( ( new_att_value != None ) and ( len( new_att_value ) > 0 ) ):
                    
                    # If the converted coordinates of the "exon" are on the + strand
                    # after the liftOver, check that all the values are in the
                    # increasing order. Otherwise, reset the value of the attribute
                    # to None.
                    if ( dsorf.strand == '+' ):
                        if ( sorted( new_att_value ) != new_att_value ):
                            Logger.get_instance().error( 'The conversion of the splicing coordinates (' +
                                                         att + ') for the DSORF with ID "' + str( dsorf.id ) + 
                                                         '" (located on + strand) returned a list of values' +
                                                         ' that are not in the increasing order.' +
                                                         ' Hence, the converted splicing coordinates of' +
                                                         ' this DSORF will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                         ex = False )
                            impossible_conversion = True
                            new_att_value = None
                            
                    # If the converted coordinates of the "exon" are on the - strand
                    # after the liftOver, check that all the values are in the
                    # decreasing order. Otherwise, reset the value of the attribute
                    # to None.
                    elif ( dsorf.strand == '-' ):
                        if ( sorted( new_att_value, reverse=True ) != new_att_value ):
                            Logger.get_instance().error( 'The conversion of the splicing coordinates (' +
                                                         att + ') for the DSORF with ID "' + str( dsorf.id ) + 
                                                         '" (located on - strand) returned a list of values' +
                                                         ' that are not in the decreasing order.' +
                                                         ' Hence, the converted splicing coordinates of' +
                                                         ' this DSORF will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                         ex = False )
                            impossible_conversion = True
                            new_att_value = None
                            
                    # If the strand of the "exon" after the liftOver is unknown, 
                    # make sure all the values are either in the increasing or 
                    # decreasing order. Otherwise, reset the value of the attribute
                    # to None.
                    else:
                        if ( ( sorted( new_att_value ) != new_att_value ) 
                             and ( sorted( new_att_value, reverse=True ) != new_att_value ) ):
                            Logger.get_instance().error( 'The conversion of the splicing coordinates (' +
                                                         att + ') for the DSORF with ID "' + str( dsorf.id ) + 
                                                         '" (strand unknown) returned a list of values' +
                                                         ' that are neither in the increasing nor in the' +
                                                         ' decreasing order. Hence, the converted splicing' +
                                                         ' coordinates of this DSORF will not be registered.' +
                                                         ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                         ex = False )
                            impossible_conversion = True
                            new_att_value = None
                    
                # Rebuild a string from the list of coordinates
                if ( ( new_att_value != None ) and ( len( new_att_value ) > 0 ) ):
                    
                    new_att_value = Constants.ORF_SPLICING_COORD_SEPARATOR.join( map( str, new_att_value ) )
                
                    # If the length of the string exceed the maximum length authorized, 
                    # replace the value by None
                    if ( len( new_att_value ) > Constants.MAX_LEN_STRING ):
                        new_att_value = None
                        
            # Register the value get after conversion
            setattr( dsorf, att, new_att_value )
            
        # Check the coherence of the data between the splice_starts and splice_ends
        # when they are provided
        if ( ( dsorf.splice_starts != None )
               and ( dsorf.splice_ends != None ) ):
            
            # If the DSORF is located on the '+' strand (after the liftOver), make
            # sure that each position of the start of an "exon" is lower that the 
            # position of the end of this "exon", which is itself lower than the 
            # position of the start of the next "exon". If this is not the case, 
            # delete the splicing coordinates for the DSORF entry.
            if ( dsorf.strand == '+' ):
                # Get the list of splicing coordinates
                splice_starts_list = dsorf.splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                splice_ends_list = dsorf.splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                
                # Build the list of splicing coordinates in the "logical" order
                splice_starts_ends_list = []
                for k in range( len( splice_starts_list ) ):
                    splice_starts_ends_list += [ splice_starts_list[ k ], splice_ends_list[ k ] ]
                splice_starts_ends_list = map( int, splice_starts_ends_list )
                
                # If the splicing coordinates are not in the expected order,
                # delete them for the DSORF entry
                if ( splice_starts_ends_list != sorted( splice_starts_ends_list ) ):
                    Logger.get_instance().error( 'The conversion of the splicing coordinates for the' +
                                                 ' DSORF with ID "' + str( dsorf.id ) + 
                                                 '" (located on + strand) returned incoherent lists of' +
                                                 ' splicing coordinates (not in increasing order).' +
                                                 ' Hence, the converted splicing coordinates of' +
                                                 ' this DSORF will not be registered.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                 ex = False )
                    dsorf.splice_starts = None
                    dsorf.splice_ends = None
            
            # If the DSORF is located on the '-' strand (after the liftOver), make 
            # sure that each position of the start of an "exon" is higher that the 
            # position of the end of this "exon", which is itself higher than the 
            # position of the start of the next "exon". If this is not the case, 
            # delete the splicing coordinates for the DSORF entry.
            elif ( dsorf.strand == '-' ):
                # Get the list of splicing coordinates
                splice_starts_list = dsorf.splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                splice_ends_list = dsorf.splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                
                # Build the list of splicing coordinates in the "logical" order
                splice_starts_ends_list = []
                for k in range( len( splice_starts_list ) ):
                    splice_starts_ends_list += [ splice_starts_list[ k ], splice_ends_list[ k ] ]                
                splice_starts_ends_list = map( int, splice_starts_ends_list )
                
                # If the splicing coordinates are not in the expected order,
                # delete them for the DSORF entry
                if ( splice_starts_ends_list != sorted( splice_starts_ends_list, reverse = True ) ):
                    Logger.get_instance().error( 'The conversion of the splicing coordinates for the' +
                                                 ' DSORF with ID "' + str( dsorf.id ) + 
                                                 '" (located on - strand) returned incoherent lists of' +
                                                 ' splicing coordinates (not in decreasing order).' +
                                                 ' Hence, the converted splicing coordinates of' +
                                                 ' this DSORF will not be registered.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                 ex = False )
                    dsorf.splice_starts = None
                    dsorf.splice_ends = None
            
            # Otherwise, if the strand of the DSORF is unknown after the liftOver, 
            # then make sure:
            # - either that each position of the start of an "exon" is higher that the 
            #   position of the end of this "exon", which is itself higher than the 
            #   position of the start of the next "exon".
            # - or that each position of the start of an "exon" is higher that the 
            #   position of the end of this "exon", which is itself higher than the 
            #   position of the start of the next "exon".
            # If this is not the case, delete the splicing coordinates for the DSORF entry.
            else:
                # Get the list of splicing coordinates
                splice_starts_list = dsorf.splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                splice_ends_list = dsorf.splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR )
                
                # Build the list of splicing coordinates in the "logical" order                
                splice_starts_ends_list = []
                for k in range( len( splice_starts_list ) ):
                    splice_starts_ends_list += [ splice_starts_list[ k ], splice_ends_list[ k ] ]
                splice_starts_ends_list = map( int, splice_starts_ends_list )
                
                # If the splicing coordinates are not in the expected order,
                # delete them for the DSORF entry
                if ( ( splice_starts_ends_list != sorted( splice_starts_ends_list ) ) 
                     and ( splice_starts_ends_list != sorted( splice_starts_ends_list, reverse = True ) ) ):
                    Logger.get_instance().error( 'The conversion of the splicing coordinates for the' +
                                                 ' DSORF with ID "' + str( dsorf.id ) + 
                                                 '" (strand after LiftOver unknown) returned incoherent' +
                                                 ' lists of splicing coordinates (neither in increasing' +
                                                 ' nor in decreasing order). Hence, the converted splicing' +
                                                 ' coordinates of this DSORF will not be registered.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_SPLCOORD + '.',
                                                 ex = False )
                    dsorf.splice_starts = None
                    dsorf.splice_ends = None
                    
        elif ( ( dsorf.splice_starts == None )
               or ( dsorf.splice_ends == None ) ):
            dsorf.splice_starts = None
            dsorf.splice_ends = None
            
        return dsorf
        
        
                
    ## reset_dsorf
    #  -----------
    #
    # This is a static method that allows to set all the following 
    # attributes of a DSORF entry to None:
    #     - strand
    #     - start_pos
    #     - stop_pos
    #     - splice_starts
    #     - splice_stops
    #
    # This method is useful when a major error occurred during the conversion of a 
    # coordinates (in particular when the chromosome changed during the lift over), 
    # and the DSORF has to be "reset" to its initial state (prior the conversion of 
    # any coordinates).
    #
    # @param dsorf: DSORF - The DSORF entry that needs to be "reset".
    #
    # @return dsorf: DSORF - The "reseted" DSORF object.
    #
    @staticmethod
    def reset_dsorf( dsorf ):
        
        for att in LiftOverStrategy.ATT_TO_RESET_DSORF:
            setattr( dsorf, att, None )
            
        return dsorf
        
        
        
    ## duplicate_dsorf_coordinates
    #  ---------------------------
    #
    # This is a static method that allows to copy all the genomic coordinates 
    # of a DSORF entry from raw attributes to their corresponding attributes 
    # (performed when the DSORF has already been reported in the desired annotation 
    # version).
    # It copies the value of:
    #     - raw_start_pos in start_pos
    #     - raw_stop_pos in stop_pos
    #     - raw_splice_starts in splice_starts
    #     - raw_splice_stops in splice_stops
    #
    # @param dsorf: DSORF - The DSORF entry for which the coordinates should be duplicated.
    #
    # @return dsorf: DSORF - The updated DSORF object.
    # 
    @staticmethod
    def duplicate_dsorf_coordinates( dsorf ):
            
        dsorf.strand = dsorf.raw_strand
        
        for att in LiftOverStrategy.ATT_TO_CONVERT_DSORF:
            setattr( dsorf, att, getattr( dsorf, 'raw_' + att ) )
            
        return dsorf
    
    

    ## convert_dstranscript_coordinates
    #  --------------------------------
    #
    # This is a static method that allows to convert all the genomic coordinates 
    # of a DSTranscript entry.
    # It tries to convert:
    #     - raw_strand (output registered in strand).
    #     - raw_start_pos (output registered in start_pos).
    #     - raw_end_pos (output registered in end_pos).
    #     - raw_cds_start_pos (output registered in cds_start_pos).
    #     - raw_cds_stop_pos (output registered in cds_stop_pos).
    #
    # If the conversion cannot be performed a warning is logged and the value 
    # of the attribute is set to None.
    # If the chromosome of one attribute changed during the conversion, then a message
    # is logged, the conversion is stopped for the entry and all the attributes that were
    # going to be converted are re-set to None.
    #
    # @param dstranscript: DSTranscript - The DSTranscript entry for which the conversion should be performed.
    # @param lo: LiftOver - The LiftOver instance (pyliftover package) necessary to
    #                       perform the conversion of the genomic coordinates. 
    #
    # @return dstranscript: DSTranscript - The updated DSTranscript object.
    #
    @staticmethod
    def convert_dstranscript_coordinates( dstranscript, lo ):
        
        # Get the strand of the transcript
        transcript_strand = dstranscript.raw_strand
        
        # Get the chromosome of the gene related to this transcript
        transcript_gene = SQLManagerDS.get_instance().get_session().query( Gene ).filter( Gene.gene_id == dstranscript.gene_id ).one()
        SQLManagerDS.get_instance().close_session()
        
        if ( transcript_gene.chromosome == None ):
            transcript_chromosome = None
        else:
            transcript_chromosome = 'chr' + transcript_gene.chromosome
        
        # If the chromosome name or the strand is missing, 
        # do not try to perform any conversion 
        if ( ( transcript_strand == None ) or ( transcript_chromosome == None ) ):
            
            return LiftOverStrategy.reset_dstranscript( dstranscript )
            
        
        ## Convert the start and end coordinates
        #  -------------------------------------
        
        # Perform the conversion for the start genomic coordinate
        try:
            ( start_chr, start_strand, start_pos ) = LiftOverStrategy.convert_coord( chr = transcript_chromosome, 
                                                                                     strand = transcript_strand, 
                                                                                     position = dstranscript.raw_start_pos, 
                                                                                     lo = lo )
        
        except ConvertCoordException as e:
            Logger.get_instance().warning( 'Error during conversion of start coordinate for the' +
                                           ' DSTranscript with ID "' + str( dstranscript.id ) + '". ' + 
                                           e.get_message() + ' Hence this position will not be registered.' +
                                           ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
            ( start_chr, start_strand, start_pos ) = ( None, None, None )
            
        else:
            # Make sure the chromosome name did not changed during coordinates conversion
            if ( transcript_chromosome != start_chr ):
                if ( start_chr.split( '_' )[ 0 ] == transcript_chromosome ):
                    Logger.get_instance().warning( 'The conversion of coordinates for the DStranscript' +
                                                   ' with ID "' + str( dstranscript.id ) + '" returned a' +
                                                   ' start position on a different chromosome' +
                                                   ' (Transcript chromosome: "' + transcript_chromosome + 
                                                   '", start chromosome: "' + str( start_chr ) + '"),' +
                                                   ' but these chromosomes actually seem to be the same.' +
                                                   ' Hence, this DSTranscript will be considered as' +
                                                   ' located on "' + orf_chromosome + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                    
                else:
                    Logger.get_instance().error( 'The conversion of coordinates for the DStranscript' +
                                                 ' with ID "' + str( dstranscript.id ) + '" returned a' +
                                                 ' start position on a different chromosome' +
                                                 ' (Transcript chromosome: "' + transcript_chromosome + 
                                                 '", start chromosome: "' + str( start_chr ) + '").' +
                                                 ' Hence, the lift over will not be performed for this' +
                                                 ' DSTranscript.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                 ex = False )
                    return LiftOverStrategy.reset_dstranscript( dstranscript )
        
        
        # Perform the conversion for the end position
        try:
            ( end_chr, end_strand, end_pos ) = LiftOverStrategy.convert_coord( chr = transcript_chromosome,
                                                                               strand = transcript_strand,
                                                                               position = dstranscript.raw_end_pos,
                                                                               lo = lo )
            
        except ConvertCoordException as e:
            Logger.get_instance().warning( 'Error during conversion of end coordinate for the DSTranscript' +
                                           ' with ID "' + str( dstranscript.id ) + '". ' + e.get_message() + 
                                           ' Hence this position will not be registered.' +
                                           ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
            ( end_chr, end_strand, end_pos ) = ( None, None, None )
            
        else:
            # Make sure the chromosome name did not changed during coordinates conversion
            if ( transcript_chromosome != end_chr ):
                if ( end_chr.split( '_' )[ 0 ] == transcript_chromosome ):
                    Logger.get_instance().warning( 'The conversion of coordinates for the DStranscript' +
                                                   ' with ID "' + str( dstranscript.id ) + '" returned an' +
                                                   ' end position on a different chromosome' +
                                                   ' (Transcript chromosome: "' + transcript_chromosome + 
                                                   '", end chromosome: "' + str( end_chr ) + '"),' +
                                                   ' but these chromosomes actually seem to be the same.' +
                                                   ' Hence, this DSTranscript will be considered as' +
                                                   ' located on "' + orf_chromosome + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                    
                else:
                    Logger.get_instance().error( 'The conversion of coordinates for the DStranscript' +
                                                 ' with ID "' + str( dstranscript.id ) + '" returned an' +
                                                 ' end position on a different chromosome' +
                                                 ' (Transcript chromosome: "' + transcript_chromosome + 
                                                 '", end chromosome: "' + str( end_chr ) + '").' +
                                                 ' Hence, the lift over will not be performed for' +
                                                 ' this DSTranscript.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                 ex = False )
                    return LiftOverStrategy.reset_dstranscript( dstranscript )
        
        
        # Check the agreement between the start and end coordinates after conversion:
        # - check the strand after conversion
        #     - If the strands of the start and end positions are both missing,
        #       then end the translation and return the dsorf (without saving any 
        #       of the converted position).
        #     - Otherwise
        #         - If the start strand is missing or if the end strand is missing, 
        #           then, one checks that the provided strand is the same as the raw strand.
        #         - If the both strands are provided,
        #             - and if they are different one from the other, then end the conversion, 
        #               log an error and return the dsorf (without saving any of the converted 
        #               position)
        #             - and if they are equals, then check if they equal also the raw strand.
        #
        # - If the strand is on the opposite strand than the raw strand, then exchange the start
        #   and end coordinates in order to always get the start lower than the end.
        if ( ( start_strand, end_strand ) == ( None, None ) ):
            
            return LiftOverStrategy.reset_dstranscript( dstranscript )
        
        else:
            reverse_start_end = False
            
            if ( start_strand == None ):
                dstranscript.strand = end_strand
                if end_strand != transcript_strand:
                    reverse_start_end = True
                    
            elif ( end_strand == None ):
                dstranscript.strand = start_strand
                if start_strand != transcript_strand:
                    reverse_start_end = True
                    
            else:
                if ( start_strand != end_strand ):
                    Logger.get_instance().error( 'The conversion of coordinates for the DSTranscript' +
                                                 ' with ID "' + str( dstranscript.id ) + '" returned a' +
                                                 ' start and an end position on different strands' +
                                                 ' (DSTranscript strand: "' + str( transcript_strand ) + 
                                                 '", start strand: "' + str( start_strand ) + '", end strand: "' + 
                                                 str( end_strand ) + '"). Hence the converted coordinates' +
                                                 ' of this DSORF will not be registered.' +
                                                 ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_STRAND + '.',
                                                 ex = False )
                    
                    return LiftOverStrategy.reset_dstranscript( dstranscript )
                
                else:
                    dstranscript.strand = start_strand
                    if ( start_strand != transcript_strand ):
                        reverse_start_stop = True
                                                
        # Save the new strand, start, end positions after the conversion
        if reverse_start_end:                    
            # If the strand has been reversed during the liftOver, but the position
            # get by conversion of the start_pos attribute (i.e. the actual "new" 
            # start position saved in end_pos attribute for the DSTranscripts initially 
            # on the + strand, and the actual "new" end position saved in start_pos 
            # attribute for the DSTranscripts initially on the - strand) is lower than 
            # the position get by the conversion of the end_pos attribute (i.e. the actual 
            # "new" end position saved in start_pos attribute for the DSTranscripts 
            # initially on the + strand, and the actual "new" start position saved in 
            # end_pos attribute for the DSTranscripts initially on the - strand), 
            # then reset the DSTranscript entry.
            if ( start_pos < end_pos ):
                Logger.get_instance().error( 'The conversion of the coordinates for the DSTranscript' +
                                             ' with ID "' + str( dstranscript.id ) + '" returned incoherent' +
                                             ' data: the strand has been reversed (new strand: ' + 
                                             str( dstranscript.strand ) + ') but the conversion of the' +
                                             ' raw_start_pos attribute provides a lower value than the' +
                                             ' conversion of the raw_end_pos attribute.' +
                                             ' Hence, the LiftOver will not be performed for this DSTranscript.' +
                                             ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_POS + '.',
                                             ex = False )
                return LiftOverStrategy.reset_dstranscript( dstranscript )
            
            # Otherwise, inverse the value of the start and stop 
            # positions as the strand has changed.
            else:
                dstranscript.start_pos = end_pos
                dstranscript.end_pos = start_pos
                
        else:
            # If the strand has not been reversed during the liftOver, but the position
            # get by conversion of the start_pos attribute (i.e. the actual "new" 
            # start position saved in end_pos attribute for the DSTranscripts initially 
            # on the + strand, and the actual "new" end position saved in start_pos 
            # attribute for the DSTranscripts initially on the - strand) is greater than 
            # the position get by the conversion of the end_pos attribute (i.e. the actual 
            # "new" end position saved in start_pos attribute for the DSTranscripts 
            # initially on the + strand, and the actual "new" start position saved in 
            # end_pos attribute for the DSTranscripts initially on the - strand), 
            # then reset the DSTranscript entry.
            if start_pos > stop_pos:
                Logger.get_instance().error( 'The conversion of the coordinates for the DSTranscript' +
                                             ' with ID "' + str( dstranscript.id ) + '" returned incoherent' +
                                             ' data: the strand has not been reversed (strand: ' + 
                                             str( dstranscript.strand ) + ') but the conversion of the' +
                                             ' raw_start_pos attribute provides a higher value than the' +
                                             ' conversion of the raw_end_pos attribute.' +
                                             ' Hence, the LiftOver will not be performed for this DSTranscript.' +
                                             ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_POS + '.',
                                             ex = False )
                return LiftOverStrategy.reset_dsorf( dsorf )
            
            else:
                dstranscript.start_pos = start_pos
                dstranscript.end_pos = end_pos
        
        
        ## Convert the CDS coordinates
        #  ---------------------------
        
        for att in LiftOverStrategy.CDS_ATT_DSTRANSCRIPT:
            
            raw_att_value = getattr( dstranscript, 'raw_' + att )
            
            # Try to convert the coordinates only if they are provided
            if ( raw_att_value == None ):
                new_att_value = None
                
            else:
                try:
                    ( new_chr, new_strand, new_att_value ) = LiftOverStrategy.convert_coord( chr = transcript_chromosome, 
                                                                                             strand = transcript_strand, 
                                                                                             position = raw_att_value, 
                                                                                             lo = lo )
                    
                except ConvertCoordException as e:
                    Logger.get_instance().warning( 'Error during conversion of the ' + att + 
                                                   ' attribute for the DSTranscript with ID "' + 
                                                   str( dstranscript.id ) + '". ' + e.get_message() + 
                                                   ' Hence. the value of this attribute has been set to None.' +
                                                   ' Warning code: ' + LogCodes.WARN_LIFTOV_FAIL + '.' )
                    ( new_chr, new_strand, new_att_value ) = ( None, None, None )
                    
                else:
                    # Check the agreement with the start and end coordinates after conversion
                    # If the CDS is on a different chromosome than the transcript, 
                    # log an error message and stop the conversion
                    if ( new_chr != transcript_chromosome ):
                        if ( new_chr.split( '_' )[ 0 ] == transcript_chromosome ):
                            Logger.get_instance().warning( 'The conversion of the ' + att + 
                                                           ' attribute for the DSTranscript with ID "' + 
                                                           str( dstranscript.id ) + '" returned a position' +
                                                           ' on a different chromosome than the transcript' +
                                                           ' (Transcript chromosome: "' + transcript_chromosome + 
                                                           '", attribute chromosome: ' + str( new_chr ) + '"),' + 
                                                           ' but these chromosomes actually seem to be the same.' +
                                                           ' Hence, this DSTranscript will be considered' +
                                                           ' as located on "' + orf_chromosome + '".' +
                                                           ' Warning code: ' + LogCodes.WARN_LIFTOV_DIFFCHR + '.' )
                            
                        else:
                            Logger.get_instance().error( 'The conversion of the ' + att + 
                                                         ' attribute for the DSTranscript with ID "' + 
                                                         str( dstranscript.id ) + '" returned a position' +
                                                         ' on a different chromosome than the transcript' +
                                                         ' (Transcript chromosome: "' + transcript_chromosome + 
                                                         '", end chromosome: "' + str( end_chr ) + '").' +
                                                         ' Hence, the lift over will not be performed for' +
                                                         ' this DSTranscript.' +
                                                         ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_CHR + '.',
                                                         ex = False )
                            return LiftOverStrategy.reset_dstranscript( dstranscript )
                        
                    # If the CDS is on the other strand, log an error and do not register the coordinates
                    if ( new_strand != transcript_strand ):
                        Logger.get_instance().error( 'The conversion of the ' + att + ' attribute for the' +
                                                     ' DSTranscript with ID "' + str( dstranscript.id ) +
                                                     '" returned a position on a different strand than the' +
                                                     ' transcript (DSTranscript strand: "' + str( transcript_strand ) + 
                                                     '", attribute strand: "' + str( att_strand ) + 
                                                     '"). Hence the converted coordinates of this' +
                                                     ' DSTranscript will not be registered.' +
                                                     ' Error code: ' + LogCodes.ERR_LIFTOV_CONFL_STRAND + '.',
                                                     ex = False )
                        ( new_chr, new_strand, new_att_value ) = ( None, None, None )
                        
            # Register the value get after conversion
            setattr( dstranscript, att, new_att_value )
            
        # If the strand of the transcript changed during the conversion, reverse the CDS positions
        if reverse_start_stop:
            ( dstranscript.cds_start_pos, dstranscript.cds_stop_pos ) = ( dstranscript.cds_stop_pos, dstranscript.cds_start_pos )
            
        return dstranscript
        
        
                
    ## reset_dstranscript
    #  ------------------
    #
    # This is a static method that allows to set all the following 
    # attributes of a DSTranscript entry to None:
    #     - strand
    #     - start_pos
    #     - end_pos
    #     - cds_start_pos
    #     - cds_end_pos
    #
    # This method is useful when a major error occurred during the conversion of a 
    # coordinates (in particular when the chromosome changed during the lift over), 
    # and the DSTranscript has to be "reset" to its initial state (prior the conversion 
    # of any coordinates).
    #
    # @param dstranscript: DSTranscript - The DSTranscript entry that needs to be "reset".
    #
    # @return dstranscript: DSTranscript - The "reseted" DSTranscript object.
    #
    @staticmethod
    def reset_dstranscript( dstranscript ):
        
        for att in LiftOverStrategy.ATT_TO_RESET_DSTRANSCRIPT:
            setattr( dstranscript, att, None )
            
        return dstranscript
        
        
        
    ## duplicate_dstranscript_coordinates
    #  ----------------------------------
    #
    # This is a static method that allows to copy all the genomic coordinates 
    # of a DSTranscript entry from raw attributes to their corresponding attributes
    # (performed when the transcript has already been reported in the desired annotation
    # version).
    # It copies the values of:
    #     - raw_start_pos in start_pos
    #     - raw_end_pos in end_pos
    #     - raw_cds_start_pos in cds_start_pos
    #     - raw_cds_stop_pos in cds_stop_pos
    #
    # @param dstranscript: DSTranscript - The DSTranscript entry for which the coordinates
    #                                     should be duplicated.
    #
    # @return dstranscript: DSTranscript - The updated DSTranscript object.
    # 
    @staticmethod
    def duplicate_dstranscript_coordinates( dstranscript ):
 
        for att in LiftOverStrategy.ATT_TO_CONVERT_DSTRANSCRIPT:
            setattr( dstranscript, att, getattr( dstranscript, 'raw_' + att ) )
            
        return dstranscript

    
    
    # ===============================================================================
    # Methods related to the computation of the ORF genomic length
    # ===============================================================================
        
    ## compute_dsorf_gen_len
    #  ---------------------
    #
    # This method allows to compute the genomic lengths (using the coordinates in the 
    # original and current genome version) for all the DSORF entries of the database.
    # The absolute difference between these lengths is then computed.
    # 
    def compute_dsorf_gen_len( self ):
        
        Logger.get_instance().info( 'Starting to compute the genomic lengths for all the entries' +
                                    ' of the DSORF table.' )
        
        # Get all the DSORF entries
        all_dsorfs_query = SQLManagerDS.get_instance().get_session().query( DSORF )
        all_dsorfs = all_dsorfs_query.all()
            
        # Get the number of rows expected to be treated and 
        # reset the ProgressionBar instance
        ProgressionBar.get_instance().reset_instance( total = all_dsorfs_query.count() )
        SQLManagerDS.get_instance().close_session()
        
        # Instantiate an empty list to receive all the DSORF entries 
        # that have to be updated
        updated_objects = []
        for dsorf in all_dsorfs:
            
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
                
            # Compute the genomic length from provided coordinates
            dsorf.raw_genomic_length = self.compute_gen_len( spliced = dsorf.spliced,
                                                             start_pos = dsorf.raw_start_pos, 
                                                             stop_pos = dsorf.raw_stop_pos, 
                                                             splice_starts = dsorf.raw_splice_starts, 
                                                             splice_ends = dsorf.raw_splice_ends,
                                                             raw_len = True )
            
            # Compute the genomic length from the coordinates after liftOver
            dsorf.genomic_length = self.compute_gen_len( spliced = dsorf.spliced,
                                                         start_pos = dsorf.start_pos, 
                                                         stop_pos = dsorf.stop_pos, 
                                                         splice_starts = dsorf.splice_starts, 
                                                         splice_ends = dsorf.splice_ends,
                                                         raw_len = False )
                
            # Compute the difference between the genomic lengths
            # when both are available
            if ( ( dsorf.raw_genomic_length == None ) 
                 or ( dsorf.genomic_length == None ) ):
                dsorf.genomic_length_diff = None
            else:
                dsorf.genomic_length_diff = abs( dsorf.raw_genomic_length - dsorf.genomic_length )
                
            # Check if the liftover failed for at least one
            # of the positions and register the information
            dsorf.liftover_succeed = True
            if ( ( dsorf.start_pos == None )
                 or ( dsorf.stop_pos == None ) ):
                dsorf.liftover_succeed = False
                
            elif ( ( dsorf.spliced 
                     and ( dsorf.raw_splice_starts != None )
                     and ( dsorf.raw_splice_starts != Constants.REPLACE_TOO_LONG_STRINGS )
                     and ( dsorf.splice_starts == None ) )
                   or ( dsorf.spliced 
                        and ( dsorf.raw_splice_ends != None )
                        and ( dsorf.raw_splice_ends != Constants.REPLACE_TOO_LONG_STRINGS )
                        and ( dsorf.splice_ends == None ) ) ):
                dsorf.liftover_succeed = False
            
            updated_objects.append( dsorf )
            
        # Update the objects in the database
        if ( len( updated_objects ) != 0 ):
            SQLManagerDS.get_instance().batch_insert_to_db( objects_to_insert = updated_objects,
                                                            process = 'dsorfs_with_gen_len_updated' )
    
    
    
    ## compute_gen_len
    #  ---------------
    #
    # This is a static method that allows to compute the genomic length 
    # of an ORF using its genomic coordinates and splicing information.
    #
    # @param spliced: Boolean - Is the ORF spliced?
    # @param start_pos: Integer - The genomic coordinates of the start codon.
    # @param stop_pos: Integer - The genomic coordinates of the stop codon.
    # @param splice_starts: String - The genomic coordinates of the starts of the "exons".
    # @param splice_ends: String - The genomic coordinates of the end of the "exons".
    # @param raw_len: Boolean - Do the coordinates provided are the raw or converted coordinates?
    #
    # @return genomic_length: Integer / None - The computed genomic length of the ORF 
    #                                          or None if it cannot be computed.
    # 
    @staticmethod
    def compute_gen_len( spliced, start_pos, stop_pos, splice_starts, splice_ends, raw_len ):
        
        # If the start or the stop position is missing, 
        # then the genomic length cannot be computed
        if ( ( start_pos == None ) 
             or ( stop_pos == None ) ):
            genomic_length = None

        # Otherwise, try to compute the genomic length using
        # the available information
        else:
            if raw_len:
                # If the ORF is not spliced
                # or if there is no information about the splicing status of this ORF,
                # or if the splicing coordinates are missing,
                # then compute the genomic length using the start and stop coordinates.
                if ( ( not spliced )
                     or ( splice_starts == None ) 
                     or ( splice_ends == None ) ):
                    genomic_length = stop_pos - start_pos + 1
                    
                # If the splicing coordinates have been replaced by "TOO_LONG", then
                # set the value of the genomic length to None
                elif ( splice_starts == Constants.REPLACE_TOO_LONG_STRINGS ):
                    genomic_length = None
                
                # Otherwise, compute the length of each "exon" and sum them to get the genomic length
                else:
                    sp_starts = map( int, 
                                     splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                    sp_ends = map( int, 
                                   splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                    
                    exon_lengths = []
                    for k in range( len( sp_starts ) ):
                        exon_lengths.append( abs( sp_ends[ k ] - sp_starts[ k ] ) + 1 )
                        
                    genomic_length = sum( exon_lengths )
                    
            else:
                # If the ORF is not spliced 
                if ( not spliced ):
                    genomic_length = stop_pos - start_pos + 1
                
                else:
                    # Otherwise, if the splicing coordinates are missing,
                    # then set the value of the genomic length to None
                    if ( ( splice_starts == None ) 
                         or ( splice_ends == None ) ):
                        genomic_length = None
                
                    # Otherwise, compute the length of each "exon" and sum them to get the genomic length
                    else:
                        sp_starts = map( int, 
                                         splice_starts.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                        sp_ends = map( int, 
                                       splice_ends.split( Constants.ORF_SPLICING_COORD_SEPARATOR ) )
                        
                        exon_lengths = []
                        for k in range( len( sp_starts ) ):
                            exon_lengths.append( abs( sp_ends[ k ] - sp_starts[ k ] ) + 1 )
                            
                        genomic_length = sum( exon_lengths )
                
        return genomic_length
    