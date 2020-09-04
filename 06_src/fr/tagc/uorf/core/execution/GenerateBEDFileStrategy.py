# -*- coding: utf-8 -*-

import os
import subprocess
import pandas as pd


from fr.tagc.uorf.core.model.PRO import *

from fr.tagc.uorf.core.execution.GenerateBEDContentStrategy import GenerateBEDContentStrategy
from fr.tagc.uorf.core.util import DefaultTemporaryFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger


# ===============================================================================
# Description of the BED file
# ===============================================================================

# References:
# - http://genome-euro.ucsc.edu/FAQ/FAQformat.html#format3
# - https://genome.ucsc.edu/goldenPath/help/customTrack.html#TRACK
# - https://software.broadinstitute.org/software/igv/TrackLine

# For the description of the BED file, see the documentation of the 
# GenerateBEDContentStrategy class.

# Track line
# - name: String <max. 15 char.> - Track name (displayed on the left of the track in genome browsers)
# - description : String <max. 60 char.> - Track short description
# - type: String <altGraphX, bam, bed, bed5FloatScore, bedGraph, bedRnaElements, bigBarChart, 
#                 bigBed, bigInteract, bigPsl, bigChain, bigMaf, bigWig, broadPeak, chain, 
#                 clonePos, coloredExon, ctgPos, downloadsOnly, encodeFiveC, expRatio, 
#                 factorSource, genePred, gvf, hic, ld2, narrowPeak, netAlign, peptideMapping, 
#                 psl, rmsk, snake, vcfTabix, wig, wigMaf> - Track type.
# - visibility: Integer or String <0-4> - Defines the initial display mode of the annotation track.
#                                         0: hide, 1: dense, 2: full, 3: pack, 4: squish.
# - color: String <R,G,B> - Defines the main color for the annotation track. 
#                                   Default value: 0,0,0.
# - itemRgb: String <On> - If present and set to "On", the genome browser will use the RGB value
#                          of the itemRgb field.
# - colorByStrand: String <R,G,B R,G,B> - Set colors for + and - strands, in that order.
# - useScore: Integer <1> - If present and set to 1, the score field will be used to determine 
#                           the level of shading in which the feature is displayed.
#                           The track will display in shades of gray unless the color attribute
#                           is set to 100,50,0 (brown) or 0,60,120 (blue). Default value: 0.
# - group: String - Defines the annotation track group in which the custom track will display in 
#                   the genome browser. By default 'user': causes custom tracks to display at the 
#                   top track listing in the group 'Custom Tracks'. To get a list of allowable 
#                   group names for an assembly, go to the table browser and select 
#                   "group: All Tables" > "table: grp" and "get output". 
# - priority: Integer - When the group attribute is set, defines the display position of the track 
#                       relative to other tracks within the same group.
# - db: String - When set, indicates the specific genome assembly for which the annotation data is
#                intended; the custom track manager will display an error is a user attempts to load 
#                the track onto a different assembly. UCSC assembly ID (e.g. hg38, mm10).
# - offset: Integer - Number to be added to all coordinates in the annotation track. 0 by default.
# - maxItems: Integer - Defines the maximum number of items the track can contain. 250 by default.
# - url: String - Defines a URL for an external link associated with the track.
# - htmlUrl: String - Defines a URL for an HTML description page to be displayed with the track.
# - bigDataUrl: String - Defines a URL to the data file for BAM, CRAM, bigBed, bigWig or VCF tracks 
#                       (required for thoss track types).
# - doWiggle: String <on> - Enables BAM custom tracks to be displayed as bar graphs where the height
#                           is proportional to the number of reads mapped to each genomic position.




# ===============================================================================
# Strategy
# ===============================================================================
        

## GenerateBEDFileStrategy
#  =======================
#
# This class is a strategy aiming to generate a BED file using the
# information in the ORF table of the PRO database.
#
class GenerateBEDFileStrategy( GenerateBEDContentStrategy ):
    
    ## Class variables
    #  ---------------
    # BED and BigBed extensions
    BED_FILE_EXTENSION = '.bed'
    BIGBED_FILE_EXTENSION = '.bb'
    
    # BED Track line 
      # Items
    BED_TRACK_LINE_ITEM_NAME = 'name'
    BED_TRACK_LINE_ITEM_DESC = 'description'
    BED_TRACK_LINE_ITEM_VISIBILITY = 'visibility'
    BED_TRACK_LINE_ITEM_COLOR = 'color'
    BED_TRACK_LINE_ITEM_RGB = 'itemRgb'
    BED_TRACK_LINE_ITEM_COLOR_BY_STRAND = 'colorByStrand'  
    BED_TRACK_LINE_ITEM_USE_SCORE = 'useScore'
    BED_TRACK_LINE_ITEM_GROUP = 'group'
    BED_TRACK_LINE_ITEM_PRIORITY = 'priority'
    BED_TRACK_LINE_ITEM_URL = 'url'
    BED_TRACK_LINE_ITEM_HTML_URL = 'htmlUrl'
    BED_TRACK_LINE_ITEM_DB = 'db'
    
      # Default values
    BED_TRACK_LINE_NAME = "'ORF datafreeze'"
    BED_TRACK_LINE_DESC = "'ORF datafreeze'"
    BED_TRACK_LINE_VISIBILITY = 'full'
    BED_TRACK_LINE_COLOR = '0,0,0'
    BED_TRACK_LINE_RGB = 'On'
    BED_TRACK_LINE_COLOR_BY_STRAND = None 
    BED_TRACK_LINE_USE_SCORE = None
    BED_TRACK_LINE_GROUP = None
    BED_TRACK_LINE_PRIORITY = None
    BED_TRACK_LINE_URL = Constants.WEBSITE_URL
    BED_TRACK_LINE_HTML_URL = Constants.WEBSITE_URL
    
    # List of chromosomes accepted in the BED file
    # By default all chromosome with a number in the 1-23 range are accepted,
    # as well as X and Y chromosomes. Hence mitochondrial chromosomes and
    # scaffolds are excluded.
    AUTHORIZED_CHR_LIST = ( map( str, range( 23 ) ) + 
                            [ Constants.CHROMOSOME_X, Constants.CHROMOSOME_Y ] )
        
    # Auto-sql file
    AUTOSQL_FILE_EXTENSION = '.as'
    AUTOSQL_FILE_CONTENT = \
    'table bedORFtable\n\
    "{db_name} - ORFs"\n\
    (\n\
        string              chrom;              "The name of the chromosome or scaffold."\n\
        uint                chromStart;         "The ORF start position on the chromosome (i.e. the genomic absolute coordinates of the first nucleotide of the start codon). The first base in a chromosome is numbered 0."\n\
        uint                chromEnd;           "The ORF stop position on the chromosome (i.e. the genomic absolute coordinates of the first nucleotide of the stop codon). The chromEnd base is not included in the display of the feature."\n\
        string              name;               "The ORF ID in the {db_name} database."\n\
        uint                score;              "Feature score. (Not used)"\n\
        char[1]             strand;             "The ORF strand. \'+\', \'-\' or \'.\' (unknown)"\n\
        uint                thickStart;         "The ORF start position on the chromosome (i.e. the genomic absolute coordinates of the first nucleotide of the start codon)."\n\
        uint                thickEnd;           "The ORF stop position on the chromosome (i.e. the genomic absolute coordinates of the first nucleotide of the stop codon)."\n\
        uint                reserved;           "An RGB value of the form R,G,B (e.g. 255,0,0). ORFs are colored according to their strand."\n\
        int                 blockCount;         "The number of exons constituting the ORF."\n\
        int[blockCount]     blockSizes;         "A comma-separated list of the exon sizes."\n\
        int[blockCount]     chromStarts;        "A comma-separated list of the exon relative start positions."\n\
        string              {transcripts};      "A comma-separated list of transcript harboring this ORF."\n\
        string              {rna_biotypes};     "A comma-separated list of transcript biotypes harboring this ORF."\n\
        string              {cell_types};       "A comma-separated list of cell types in which the ORF has already been identified."\n\
        string              {orf_annotations};  "A comma-separated list of the annotations of the ORF."\n\
        string              {kozak_contexts};   "A comma-separated list of the Kozak contexts found for this ORF."\n\
    )'.format( db_name = Constants.PROJECT_NAME,
               transcripts = GenerateBEDContentStrategy.BED_HEADER_TRANSCRIPTS,
               rna_biotypes = GenerateBEDContentStrategy.BED_HEADER_RNA_BIOTYPES,
               cell_types = GenerateBEDContentStrategy.BED_HEADER_CELL_TYPES,
               orf_annotations = GenerateBEDContentStrategy.BED_HEADER_ORF_ANNOTATIONS,
               kozak_contexts = GenerateBEDContentStrategy.BED_HEADER_KOZAK_CONTEXTS )
    
    # Value to use when replacing too long strings in the BigBed file
    BIGBED_TOO_LONG_STR = 'TOO_LONG'
    

    ## Constructor of GenerateBEDFile
    #  ------------------------------
    #
    # Instance variables:
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    #     - output_folder: String - The name of the folder where to export the BED file.
    #     - filename: String - The name of the BED file.
    #     - generate_bed_content: Boolean - Should the content of the UTBEDContent table be computed?
    #     - track_line: Boolean - Should a trackline be added at the beginning of the file?
    #     - non_conv_chr: Boolean - Should the ORFs on "non conventional" chromosomes be removed from the file?
    #     - convert_bigbed: Boolean - Should the bed file be converted at bigBed format?
    #     - common_file_path: String - The file path common to Bed, BigBed and AS files (without extension hence).
    #
    def __init__( self ):
        
        GenerateBEDContentStrategy.__init__( self )
        
        # Get the output folder
        self.output_folder = OptionManager.get_instance().get_option( OptionConstants.OPTION_OUTPUT_FOLDER, 
                                                                      not_none = False )
        # By default, save the file in a BED folder
        if ( not self.output_folder ):
            self.output_folder = Constants.BED_FOLDER
        
        # Get the eventual filename
        self.filename = OptionManager.get_instance().get_option( OptionConstants.OPTION_BED_FILENAME, 
                                                                 not_none = False )
        # Set the default name of the file
        if ( not self.filename ):
            self.filename = Constants.DEFAULT_BED_FILENAME
            
        # 
        self.generate_bed_content = OptionManager.get_instance().get_option( OptionConstants.OPTION_BED_GENERATE_CONTENT,
                                                                             not_none = False )
            
        # Get the trackline option
        self.track_line = OptionManager.get_instance().get_option( OptionConstants.OPTION_BED_TRACK_LINE, 
                                                                   not_none = False )
        
        # Get the "non conventional" chromosomes option
        self.non_conv_chr = OptionManager.get_instance().get_option( OptionConstants.OPTION_BED_NON_CONV_CHR, 
                                                                     not_none = False )
        
        # Should additional columns be added to the bed file?
        self.extend_bed = OptionManager.get_instance().get_option( OptionConstants.OPTION_BED_EXTENDED,
                                                                   not_none = False )
        
        # Should the file be converted at bigBed format?
        self.convert_bigbed = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONVERT_TO_BIGBED, 
                                                                       not_none = False )
            
        # Set the file path
        self.common_file_path = os.path.join( self.output_folder, self.filename )
        
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to generate the BED file.
    #
    # @throw DenCellORFException: When an exception has been raised creating a session to the database.
    # 
    def execute( self ):
        
        # Create a session to the "PRO-like" database
        SQLManagerPRO.get_instance().set_db_settings( self.db_settings )

        try:
            SQLManagerPRO.get_instance().get_session()
        except Exception as e:
            raise DenCellORFException( 'GenerateBEDFile.execute(): An error occurred trying to' +
                                       ' create a session to the database.' +
                                        '\n Error code: ' + LogCodes.ERR_SQL_SESSION + '.', e)
        SQLManagerPRO.get_instance().close_session()
        
        # Compute the content of the UTBEDContent table if necessary
        utbedcontent_count = SQLManagerPRO.get_instance().get_session().query( UTBEDContent ).count()
        SQLManagerPRO.get_instance().close_session()
        if ( self.generate_bed_content
             or ( utbedcontent_count == 0 ) ):
            self.compute_bed_content()
            
        # Create the BED file
        self.write_bed_file()
        
        # Create the BigBed file if necessary
        if ( self.convert_bigbed ):
            self.convert_bed_to_bigbed()
        
    
    
    ## write_bed_file
    #  --------------
    #
    # This method allows to create the bed file by querying 
    # the UTBEDContent table.
    # 
    def write_bed_file( self ):
        
        Logger.get_instance().info( 'Starting to build the BED file.' )
            
        # Create the output folder if it does not yet exist
        # (and its parent folders if necessary )
        if ( not os.path.isdir( self.output_folder ) ):
            os.makedirs( self.output_folder )                
        bed_file_path = self.common_file_path + self.BED_FILE_EXTENSION
        
            
        # Track line
        # ----------
        # Header information are registered as a dictionary
        header_dict = { self.BED_TRACK_LINE_ITEM_NAME: self.BED_TRACK_LINE_NAME,
                        self.BED_TRACK_LINE_ITEM_DESC: self.BED_TRACK_LINE_DESC,
                        self.BED_TRACK_LINE_ITEM_VISIBILITY: self.BED_TRACK_LINE_VISIBILITY,
                        self.BED_TRACK_LINE_ITEM_COLOR: self.BED_TRACK_LINE_COLOR,
                        self.BED_TRACK_LINE_ITEM_RGB: self.BED_TRACK_LINE_RGB,
                        self.BED_TRACK_LINE_ITEM_COLOR_BY_STRAND: self.BED_TRACK_LINE_COLOR_BY_STRAND,
                        self.BED_TRACK_LINE_ITEM_USE_SCORE: self.BED_TRACK_LINE_USE_SCORE,
                        self.BED_TRACK_LINE_ITEM_GROUP: self.BED_TRACK_LINE_GROUP,
                        self.BED_TRACK_LINE_ITEM_PRIORITY: self.BED_TRACK_LINE_PRIORITY,
                        self.BED_TRACK_LINE_ITEM_URL: self.BED_TRACK_LINE_URL,
                        self.BED_TRACK_LINE_ITEM_HTML_URL: self.BED_TRACK_LINE_HTML_URL }
        
        # Add the annotation version
        current_annotation = SQLManagerPRO.get_instance().get_session().query( 
                                                                                PROMetadata
                                                                            ).filter( 
                                                                                        PROMetadata.parameter == Constants.METATABLE_CURRENT_ANNOTATION 
                                                                                    ).one().value
        SQLManagerPRO.get_instance().close_session()
        current_annot_ucsc = Constants.CORRESPONDING_UCSC_FROM_NCBI[ current_annotation ]
        header_dict[ self.BED_TRACK_LINE_ITEM_DB ] = current_annot_ucsc
        
        # Compute the header
        header_list = []
        for ( specifier, val ) in header_dict.items():
            if ( val != None ):
                header_list.append( str( specifier ) + '=' + str( val ) )
        header = 'track ' + ' '.join( header_list )
        
        # If necessary, create an empty file and 
        # add the track line at its beginning
        if self.track_line:            
            # Create the BED file with the header
            try:
                with open( bed_file_path, 'w' ) as bed_file:
                    bed_file.write( header + '\n' )
            except Exception as e:
                raise DenCellORFException( 'GenerateBEDFileStrategy.execute(): An error occurred trying' +
                                           ' to create the BED file at ' + bed_file_path + 
                                           ' and/or writing the BED header', e )
            else:
                Logger.get_instance().debug( 'GenerateBEDFileStrategy.execute(): ' + 
                                             ' An empty BED file have been created at ' + 
                                             bed_file_path + '.' )
            bed_file_writting_mode = 'a'
            
        else:
            Logger.get_instance().info( 'The following track line may be used in genomic browsers:\n' + 
                                        header )
            bed_file_writting_mode = 'w'
        
        
        # Get BED file content
        # --------------------
        
        Logger.get_instance().debug( 'Starting to compute the BED lines.' )
        
        if self.extend_bed:
            bed_full_content_query = SQLManagerPRO.get_instance().get_session().query( 
                                                                                        UTBEDContent.bed_col,
                                                                                        UTBEDContent.bed_add_col
                                                                                      )
        else:
            bed_full_content_query = SQLManagerPRO.get_instance().get_session().query(  
                                                                                        UTBEDContent.bed_col
                                                                                      )
        
        # By default, exclude all the ORFs with "non conventional" chromosomes 
        # (i.e. mitochondrial chromosome and scaffolds)
        if ( not self.non_conv_chr ):
            bed_full_content_query = bed_full_content_query.filter( 
                                                                        ORF.chromosome.in_( self.AUTHORIZED_CHR_LIST ),
                                                                        UTBEDContent.orf_id == ORF.id 
                                                                    )
            
        # Reorder the rows by index
        bed_full_content_query = bed_full_content_query.order_by( UTBEDContent.bed_index )
        
        # Get the BED lines and store them in a data frame
        bed_full_content = bed_full_content_query.all()
        SQLManagerPRO.get_instance().close_session()
        
        
        # Write the BED file
        # ------------------
        
        # If there are extra-columns, then create the auto-sql file 
        # necessary to convert the bed file at BigBed format
        if self.extend_bed:
            autosql_file_path = self.common_file_path + GenerateBEDFileStrategy.AUTOSQL_FILE_EXTENSION
            with open( autosql_file_path, 'w' ) as autosql_file:
                autosql_file.write( GenerateBEDFileStrategy.AUTOSQL_FILE_CONTENT )        
        
        
        # Register the content of the BED file data frame into the file
        with open( bed_file_path, bed_file_writting_mode ) as bed_file:
            for bed_line in bed_full_content:
                if self.extend_bed:
                    bed_file.write( '\t'.join( [ bed_line[ 0 ],
                                                 bed_line[ 1 ] ] ) + '\n' )
                else:
                    bed_file.write( bed_line[ 0 ] + '\n' )
        
        Logger.get_instance().info( 'The BED file has been successfully generated and stored in the ' +
                                    self.output_folder + ' directory.' )
        
        
        
    ## convert_bed_to_bigbed
    #  ---------------------
    #
    # This method allows to convert the bed file at the bigBed format.
    #
    def convert_bed_to_bigbed( self ):
        
        Logger.get_instance().info( 'Starting to convert the Bed file into bigBed format.' )
        
        # Get the appropriate UCSC genome version
        current_annotation = SQLManagerPRO.get_instance().get_session().query( 
                                                                                PROMetadata.value 
                                                                               ).filter(
                                                                                            PROMetadata.parameter == Constants.METATABLE_CURRENT_ANNOTATION
                                                                                        ).one()
        ucsc_genome_version = Constants.CORRESPONDING_UCSC_FROM_NCBI[ current_annotation[ 0 ] ]
        
        # Fetch the chromosome sizes file from UCSC
        chrom_sizes_file_path = os.path.join( self.output_folder, 
                                              ucsc_genome_version + '.chrom.sizes' )
        
        if ( not os.path.exists( chrom_sizes_file_path ) ):
            fetch_command = [ 'fetchChromSizes', ucsc_genome_version ]
            
            with open( chrom_sizes_file_path, 'w' ) as chrom_sizes_file:
                fetchchr = subprocess.Popen( fetch_command, 
                                             stdout = chrom_sizes_file, 
                                             stderr = subprocess.PIPE )
                ( stdout, stderr ) = fetchchr.communicate()
            
            if ( stderr != '' ):
                Logger.get_instance().debug( 'GenerateBEDFileStrategy.convert_bed_to_bigbed(): The command ' +
                                             ' '.join( fetch_command ) + 'returned the message:\n' + 
                                             stderr )
            Logger.get_instance().debug( 'The chromosome sizes file has been saved in ' + chrom_sizes_file_path + '.' )
        
        else:
            Logger.get_instance().debug( 'The chromosome sizes file located at ' + chrom_sizes_file_path + 
                                         ' will be used to perform the conversion.' )
        
        # Copy the bed file and remove the track line if necessary
        bed_file_path = self.common_file_path + self.BED_FILE_EXTENSION
        tmp_bed_file_path = os.path.join( DefaultTemporaryFolder.TEMPORARY_FOLDER,
                                          self.filename + '_wo_trackline' + self.BED_FILE_EXTENSION )
        
        with open( bed_file_path, 'r' ) as bed_file, \
             open( tmp_bed_file_path, 'w' ) as tmp_bed_file:
            
            if ( self.track_line ):
                line = bed_file.readline()
            
            line = bed_file.readline()
            while ( line != '' ):
                # Remove the strings exceeding 255 characters in the bed file
                # as BigBed do not allow to store strings longer than this
                if self.extend_bed:
                    spl_line = line.split( '\t' )
                    spl_line_start = spl_line[ :12 ]
                    spl_line_end = map( lambda x: x if len( x ) <= 255 else self.BIGBED_TOO_LONG_STR,
                                        spl_line[ 12: ] )
                    line = '\t'.join( spl_line_start + spl_line_end )
                
                tmp_bed_file.write( line )
                line = bed_file.readline()
        
        
        # Convert the bed file into bigBed format
        bigbed_file_path = self.common_file_path + self.BIGBED_FILE_EXTENSION
        
        if self.extend_bed:
            bed_to_bigbed_command = [ 'bedToBigBed', '-type=bed12+5', 
                                      '-as=' + self.common_file_path + GenerateBEDFileStrategy.AUTOSQL_FILE_EXTENSION,
                                      '-extraIndex=name,transcripts,cell_types,orf_annotations,kozak_contexts',
                                      tmp_bed_file_path, chrom_sizes_file_path, bigbed_file_path ]
            
            
        else:
            bed_to_bigbed_command = [ 'bedToBigBed', tmp_bed_file_path, chrom_sizes_file_path, bigbed_file_path ]
        
        bed_to_bigbed = subprocess.Popen( bed_to_bigbed_command, 
                                          stdout = subprocess.PIPE, 
                                          stderr = subprocess.PIPE )
        ( stdout, stderr ) = bed_to_bigbed.communicate()
        
        if ( stderr != '' ):
            Logger.get_instance().debug( 'GenerateBEDFileStrategy.convert_bed_to_bigbed(): The command ' +
                                         ' '.join( bed_to_bigbed_command ) + 'returned the message:\n' + 
                                         stderr )
        
        Logger.get_instance().info( 'The BigBed file has been successfully generated and stored in the ' +
                                    self.output_folder + ' directory.' )
        