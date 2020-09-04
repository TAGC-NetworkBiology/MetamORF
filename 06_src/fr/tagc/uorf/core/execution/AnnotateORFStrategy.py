# -*- coding: utf-8 -*-

import ConfigParser
import os

import requests
import pyensembl

from fr.tagc.uorf.core.model import *

from fr.tagc.uorf.core.execution.DatabaseCheckStrategy import DatabaseCheckStrategy

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.sql.SQLManagerPRO import SQLManagerPRO
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.general.FileHandlerUtil import FileHandlerUtil
from fr.tagc.uorf.core.util.graphics.ProgressionBar import ProgressionBar
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log.Logger import Logger
        

## AnnotateORFStrategy
#  ===================
#
# This class is a strategy aiming to:
# - Complete the ORFCategory table using solely the information 
#   provided by the datasources.
# - Complete the ORFAnnotation table (i.e. compute the ORF class) 
#   using both the information provided by the datasource 
#   (ORF coordinates and related transcript) and the information 
#   about the transcript (CDS coordinates, eventually download).
#
class AnnotateORFStrategy( object ):
    
    
    ## Constructor of AnnotateORFStrategy
    #  ----------------------------------
    #
    # Instance variables:
    #     - compute_category: Boolean - Compute the ORF categories from datasource categories?
    #     - compute_annotation: Boolean - Annotate ORFs using both datasource and transcript information?
    #     - configfile: String - The path to the config file.
    #     - orf_category_corresp: Dictionary - The dictionary that associates to lists of provided 
    #                                          ORF categories (list of strings - values of the dictionary) 
    #                                          the computed ORF categories (strings - keys of the dictionary).
    #     - force_overwrite: Boolean - Does the computation need to be performed again?
    #                                  If True all the entries of the tables that need to be computed 
    #                                  (i.e. all the entries of the ORFCategory and ORFCategoryCatalog 
    #                                  tables or all the entries of the ORFAnnotation and ORFAnnotationCatalog 
    #                                  tables will be deleted and the content of these tables will be computed
    #                                  again).
    #
    # @throw DenCellORFException: When the config file is not provided or cannot be found at the
    #                             path provided.
    #
    def __init__( self ):
        
        self.compute_category = OptionManager.get_instance().get_option( OptionConstants.OPTION_ANNOTATE_ORF_FROM_PROV,
                                                                         not_none = False )
        
        self.compute_annotation = OptionManager.get_instance().get_option( OptionConstants.OPTION_ANNOTATE_ORF_FROM_COORD,
                                                                           not_none = False )

        configfile = OptionManager.get_instance().get_option( OptionConstants.OPTION_CONFIG_FILE_PATH, 
                                                              not_none = True )
            
        if configfile:
            self.configfile = configfile
            if ( not os.path.exists( configfile ) ):
                raise DenCellORFException( 'No config file may be found at the path provided (' + 
                                           self.configfile + ').' )
            self.parse_config()
            
        else:
            raise DenCellORFException( 'A config file has to be provided.' +
                                       ' See the documentation for more information.' )
            
        # Check if the forceOverwrite option has been selected
        if OptionManager.get_instance().get_option( OptionConstants.OPTION_FORCE_OVERWRITE, not_none = False ):
            self.force_overwrite = True
        else:
            self.force_overwrite = False
        


    ## parse_config
    #  ------------
    #
    # Parse the config file to retrieve required information.
    #
    # @throw DenCellORFException: When the orf_category_corresp string ("cell context dictionary") 
    #                             cannot be converted into a Python dictionary.
    # @throw DenCellORFException: When the value provided for the maximal size for an ORF to be 
    #                             considered as short is not a positive integer.
    #
    def parse_config( self ):
        
        # Read the configfile
        config = ConfigParser.ConfigParser()
        config.optionxform = lambda option: option
        config.read( self.configfile )
                
        # If necessary, get the dictionary to use to compute the ORF categories
        if self.compute_category:
            
            if config.has_option( Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS, Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_CATEGORY_DICT ):
                self.orf_category_corresp = config.get( Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS, 
                                                        Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_CATEGORY_DICT )
                try:
                    self.orf_category_corresp = eval( self.orf_category_corresp )
                except Exception as e:
                    raise DenCellORFException( 'AnnotateORFStrategy.parse_config():' +
                                               ' An error occurred trying to convert the category dictionary' +
                                               ' provided as a string into an actual Python dictionary.', e )
            
            else:
                self.orf_category_corresp = Constants.ORF_CATEGORY_CORRESP
                Logger.get_instance().debug( 'AnnotateORFStrategy.parse_config():' +
                                             ' As there was no dictionary provided to compute the ORF' +
                                             ' categories in the config file, the default dictionary (' + 
                                             str( Constants.ORF_CATEGORY_CORRESP ) + ') will be used.' )
                
        # If necessary, get the size threshold that define the short ORFs
        if self.compute_annotation:
            
            if config.has_option( Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS, Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_SHORT_ORF_SIZE_THRESHOLD ):
                self.short_orf_threshold = config.get( Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS, 
                                                       Constants.CONFIG_SECTION_ANNOTATE_ORF_PARAMETERS_ITEM_SHORT_ORF_SIZE_THRESHOLD )
                try:
                    self.short_orf_threshold = int( self.short_orf_threshold )
                except Exception as e:
                    raise DenCellORFException( 'AnnotateORFStrategy.parse_config(): The value for the' +
                                               ' maximal size for an ORF to be considered as short' +
                                               ' needs to be an integer (provided value: ' +
                                               str( self.short_orf_threshold ) + ').' )
                else:
                    if ( self.short_orf_threshold < 0 ):
                        raise DenCellORFException( 'AnnotateORFStrategy.parse_config(): The value for the' +
                                                   ' maximal size for an ORF to be considered as short' +
                                                   ' needs to be a positive integer (provided value: ' +
                                                   str( self.short_orf_threshold ) + ').' )
            else:
                self.short_orf_threshold = Constants.DEFAULT_SHORT_ORF_ANNOTATION_SIZE_THRESHOLD
                Logger.get_instance().debug( 'AnnotateORFStrategy.parse_config(): As there was value for' +
                                             ' the maximal size for an ORF to be considered as short in' +
                                             ' the config file, the default value of ' +
                                             str( Constants.DEFAULT_SHORT_ORF_ANNOTATION_SIZE_THRESHOLD ) +
                                             ' will be used.' )
    
    
    ## execute
    #  -------
    #
    # Execute the strategy to compute the ORF categories.
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
        
        
        # Check there is at least one ORFTranscriptAsso entry in the database prior 
        # to compute the ORF categories / annotations.
        orftranscriptasso_count = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso ).count()
        if ( orftranscriptasso_count == 0 ):
            raise DenCellORFException( 'There is not any entry in the ORFTranscriptAsso table of the ' + 
                                       SQLManagerPRO.get_instance().db_name + ' database (PRO database).' +
                                       ' Hence, the computation of missing information will be stopped.' )
        
        # Compute ORF categories
        if self.compute_category:
            
            # NB: If there is at least one entry in the ORFCategoryCatalog table and the forceOverwrite 
            #     option has not been selected, then this step will not be performed
            all_orfcategorycatalog_count = SQLManagerPRO.get_instance().get_session().query( ORFCategoryCatalog ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( ( all_orfcategorycatalog_count == 0 ) or ( self.force_overwrite ) ):
                self.compute_orf_category()
            else:
                Logger.get_instance().info( 'Entries have been found in the ORFCategoryCatalog table' +
                                            ' and the "forceOverwrite" option has not been selected.' +
                                            ' Hence, the assignment of categories to the ORFs using' +
                                            ' the provided categories will not be performed again.' )
            
            
        # Compute the ORF annotations
        if self.compute_annotation:

            # NB: If there is at least one entry in the ORFAnnotationCatalog table and the forceOverwrite 
            #     option has not been selected, then this step will not be performed
            all_orfannotationcatalog_count = SQLManagerPRO.get_instance().get_session().query( ORFAnnotationCatalog ).count()
            SQLManagerPRO.get_instance().close_session()
            if ( ( all_orfannotationcatalog_count == 0 ) or ( self.force_overwrite ) ):
                self.compute_orf_annotation()
            else:
                Logger.get_instance().info( 'Entries have been found in the ORFAnnotationCatalog table' +
                                            ' and the "forceOverwrite" option has not been selected.' +
                                            ' Hence, the annotation of the ORF using ORF and transcript' +
                                            ' information will not be performed again.' )
    
        
    
    # ===============================================================================
    # Methods to the compute the ORF categories using the provided ones
    # ===============================================================================
        
    ## compute_orf_category
    #  --------------------
    #
    # This method allows to compute the categories of the ORFTranscriptAsso entries 
    # using the categories provided by the data sources.
    # 
    # @throw DenCellORFException: When an error occurs while trying to delete the ORFCategoryCatalog
    #                             entries (when the "-f" option has been selected).
    # 
    def compute_orf_category( self ):
        
        Logger.get_instance().info( 'Starting the computation of the ORF categories' +
                                    ' using the categories provided by the datasources.')
        
        # First, reset the ORFCategory and ORFCategoryCatalog table contents if necessary
        if self.force_overwrite:
            orfcategorycatalog_query = SQLManagerPRO.get_instance().get_session().query( ORFCategoryCatalog )
            orfcategorycatalog_count = orfcategorycatalog_query.count()
            
            if ( orfcategorycatalog_count != 0 ):
            
                Logger.get_instance().info( str( orfcategorycatalog_count ) + 
                                            ' entries have been found in the ORFCategoryCatalog table' +
                                            ' and will be deleted prior to the computation of ORF categories.' )
                
                entries_to_delete_str = ', '.join( [ occ.category for occ in orfcategorycatalog_query.all() ] )
                try:
                    orfcategorycatalog_query.delete( synchronize_session = 'fetch' )
                    SQLManagerPRO.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'AnnotateORFStrategy.compute_orf_category():' +
                                               ' An error occurred trying to remove the following' +
                                               ' ORFCategoryCatalog entries from the session' +
                                               ' and to commit changes: ' + entries_to_delete_str + '.', e )
                    
            SQLManagerPRO.get_instance().close_session()
        
        objects_to_insert = []
        
        # The correspondences between the provided categories and the "computed" ones is expected to
        # be provided as a dictionary, such as the keys are the "computed" categories and the values
        # are lists of provided categories corresponding to them.
        # Using this dictionary, prepare a dictionary (prov_cat) that associate 
        # to each provided category its computed categorie(s).
        category_dict = {}
        for ( comp_cat, prov_categories ) in self.orf_category_corresp.items():
            for prov_cat in prov_categories:
                
                # If the provided category has to be ignored, associate it to an empty list
                if ( ( str( comp_cat ) == 'None' ) 
                     and ( comp_cat == Constants.ORF_ANNOTATION_TO_IGNORE ) ):
                    comp_cat_to_add = []
                else:
                    comp_cat_to_add = [ comp_cat ]
                
                existing_prov_cat = category_dict.get( prov_cat )
                if existing_prov_cat:
                    existing_prov_cat += comp_cat_to_add
                else:
                    category_dict[ prov_cat ] = comp_cat_to_add
        
        # For all computed categories, create an entry in the ORFCatagoryCatalog table
        for comp_cat in self.orf_category_corresp.keys():
            if ( ( str( comp_cat ) != 'None' ) and ( comp_cat != Constants.ORF_ANNOTATION_TO_IGNORE ) ):
                orfcategorycatalog = ORFCategoryCatalog( category = comp_cat )
                objects_to_insert.append( orfcategorycatalog )
         
            
        # For each entry of the ORFTranscriptAsso table, create the corresponding entries in the ORFCategory table
        all_orftranscriptasso_query = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso )
        all_orftranscriptasso = all_orftranscriptasso_query.all()
        
        # Get the number total number of entries expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = all_orftranscriptasso_query.count() )
        
        for orftranscriptasso in all_orftranscriptasso:
                        
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Get the list of all the provided categories corresponding to the entry
            prov_categories = SQLManagerPRO.get_instance().get_session().query( ProvidedCategory.provided_category ).filter( ProvidedCategory.orftranscriptasso_id == orftranscriptasso.id ).all()
            prov_categories = GeneralUtil.query_result_to_list( prov_categories )
            
            # Get the list of "computed" categories corresponding to these
            comp_categories = []
            for prov_cat in prov_categories:
                
                existing_prov_cat = category_dict.get( prov_cat, False )
                if ( existing_prov_cat != False ):
                    comp_categories += existing_prov_cat
                        
                else:
                    Logger.get_instance().warning( 'The category "' + prov_cat + '" has been found in the' +
                                                   ' provided categories associated with the ORFTranscriptAsso' +
                                                   ' with ID "' + str( orftranscriptasso.id ) + 
                                                   '", and this provided category is not associated to any' +
                                                   ' "computed" category in the dictionary.' +
                                                   ' Hence, this ORF annotation will not be considered.' +
                                                   ' Warning code: ' + LogCodes.WARN_ORFCAT_PROV_NOTIN_DICT + '.' )
            
            # For each unique "computed" category, create an entry in the ORFCategory table
            for comp_cat in set( comp_categories ):
                orfcategory = ORFCategory( orftranscriptasso_id = orftranscriptasso.id,
                                           orf_category = comp_cat )
                objects_to_insert.append( orfcategory )
                
        SQLManagerPRO.get_instance().close_session()
                    
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert,
                                     processfile = 'orf_category',
                                     process = 'compute_orf_category(): Computation of ORF categories' )
        
        Logger.get_instance().info( 'The computation of the ORF categories using the provided' +
                                    ' categories has finished.')
    
    
    
    
    # ===============================================================================
    # Methods to the compute the ORF annotation using the registered information
    # ===============================================================================
        
    ## compute_orf_annotation
    #  ----------------------
    #
    # This method allows to compute the "annotations" of the ORFTranscriptAsso entries 
    # using the ORF and transcript coordinates provided by the data sources and/or 
    # previously download.
    # 
    # @throw DenCellORFException - When an error occurs while trying to delete the ORFAnnotationCatalog
    #                              entries (when the "-f" option has been selected).
    # @throw DenCellORFException - When one "computed" annotation term is belonging to several families.
    # 
    def compute_orf_annotation( self ):
        
        Logger.get_instance().info( 'Starting the computation of the ORF annotations using' +
                                    ' the information from the ORF and Transcript tables.' )
        
        # First, reset the ORFAnnotation and ORFAnnotationCatalog table contents if necessary
        if self.force_overwrite:
            orfannotationcatalog_query = SQLManagerPRO.get_instance().get_session().query( ORFAnnotationCatalog )
            orfannotationcatalog_count = orfannotationcatalog_query.count()
            
            if ( orfannotationcatalog_count != 0 ):
            
                Logger.get_instance().info( str( orfannotationcatalog_count ) + 
                                            ' entries have been found in the ORFAnnotationCatalog table' +
                                            ' and will be deleted prior to the computation of ORF annotations.' )
                
                entries_to_delete_str = ', '.join( [ oac.annotation for oac in orfannotationcatalog_query.all() ] )
                try:
                    orfannotationcatalog_query.delete( synchronize_session = 'fetch' )
                    SQLManagerPRO.get_instance().commit()
                except Exception as e:
                    raise DenCellORFException( 'AnnotateORFStrategy.compute_orf_annotation():' +
                                               ' An error occurred trying to remove the following' +
                                               ' ORFAnnotationCatalog entries from the session' +
                                               ' and to commit changes: ' + entries_to_delete_str + '.', e )
                    
            SQLManagerPRO.get_instance().close_session()
        
            
            
        # Annotate the ORF, using:
        # - Length criteria
        # - Transcript biotype
        # - CDS coordinates (when the transcript harbors a CDS and 
        #   the coordinates have been registered in the database)  
          
        # The correspondences between the biotype categories and the "computed annotation"
        # is registered as a dictionary, such as the keys are the "computed annotations"
        # and the values are lists of existing biotypes for which the annotation should 
        # be used.
        # Using this dictionary, prepare a dictionary (annotation_dict) that associates 
        # to each provided biotype its computed annotation(s).
        annotation_dict = {}
        for ( orf_annotation, rna_biotype ) in Constants.ORF_BIOTYPE_ANNOT_CORRESP.items():
            for biotype in rna_biotype:
                
                existing_biotype = annotation_dict.get( biotype )
                if existing_biotype:
                    existing_biotype.append( orf_annotation )
                else:
                    annotation_dict[ biotype ] = [ orf_annotation ]
                    
                    
        # The correspondences between the "computed annotations" and the "family" to which
        # they belong is registered as a dictionary, such as the keys are the "families" and
        # the values are lists of existing "computed annotation".
        # Using this dictionary, prepare a dictionary (annotation_family_dict) that associates
        #  to each computed annotation the family to which it belongs.
        annotation_family_dict = {}
        for ( annot_family, orf_annotation ) in Constants.ORF_ANNOTATION_CATALOG_FAMILY_CORRESP.items():
            for orf_annot in set( orf_annotation ):
                
                # Each annotation term can only belong to ONE single family.
                # Hence if this is not the case raise an exception.
                existing_orf_annot = annotation_family_dict.get( orf_annot )
                if existing_orf_annot:
                    raise DenCellORFException( 'AnnotateORFStrategy.compute_orf_annotation():' +
                                               ' The computed annotation term "' + orf_annot + 
                                               '" has been found belonging to at least two families (' +
                                               existing_orf_annot + ', ' + annot_family + 
                                               '). Each annotation term can only belong to one single family!' +
                                               ' Please check the ORF_ANNOTATION_CATALOG_TYPE_CORRESP dictionary' +
                                               ' defined in the Constants file (' + 
                                               str( ORF_ANNOTATION_CATALOG_TYPE_CORRESP ) + ').' )
                else:
                    annotation_family_dict[ orf_annot ] = annot_family
                    
                    
        all_orfannotation_catalog = []
        objects_to_insert = []
        
        # The annotations are computed using information from the ORF and Transcript tables.
        # NB: It may be necessary to run the ComputeMissingInfo strategy to recover missing
        #     information in the Transcript table (CDS coordinates, transcript biotype...)
        all_orftranscriptasso_query = SQLManagerPRO.get_instance().get_session().query( ORFTranscriptAsso )
        all_orftranscriptasso = all_orftranscriptasso_query.all()
        
        # Get the number total number of entries expected to be treated and 
        # reset the ProgressionBar instance to follow the progression
        ProgressionBar.get_instance().reset_instance( total = all_orftranscriptasso_query.count() )
        
        
        # For each entry of the ORFTranscriptAsso table, create the necessary entries 
        # in the ORFAnnotation and ORFAnnotationCategory tables
        for orftranscriptasso in all_orftranscriptasso:
                        
            # Update and display the progression bar on the console
            ProgressionBar.get_instance().increase_and_display()
            
            # Get the related ORF entry
            orf = SQLManagerPRO.get_instance().get_session().query( ORF ).filter( ORF.id == orftranscriptasso.orf_id ).one()
            
            # Get the related Transcript entry
            transcript = SQLManagerPRO.get_instance().get_session().query( Transcript ).filter( Transcript.id == orftranscriptasso.transcript_id ).one()
            SQLManagerPRO.get_instance().close_session()
            
            # Annotate short ORFs
            # If the maximal length in amino acid (ORFTranscriptAsso entry) is below the threshold,
            # then annotate the ORF as short ORF
            max_aa_len = orftranscriptasso.length_aa_max 
            if orf.genomic_length: 
                orf_gen_len_aa = float( orf.genomic_length ) / 3
            else:
                orf_gen_len_aa = None
            annotation = Constants.ORF_ANNOTATION_SHORT_ORF
            
            if ( max_aa_len and ( max_aa_len <= self.short_orf_threshold ) ):
                
                orfannotation = ORFAnnotation( orftranscriptasso_id = orftranscriptasso.id,
                                               orf_annotation = annotation,
                                               criteria = Constants.ANNOTATE_CRITERIA_MAX_AA_LEN )
                objects_to_insert.append( orfannotation )
                
                # If the annotation used has not been yet registered in the 
                # ORFAnnotationCatalog table, then add it
                if ( annotation not in all_orfannotation_catalog ):
                    all_orfannotation_catalog.append( annotation )
                    orfannotationcatalog = ORFAnnotationCatalog( annotation = annotation,
                                                                 family = annotation_family_dict[ annotation ] )
                    objects_to_insert.append( orfannotationcatalog )
            
            # If the exonic sum length of the related ORF entry is 
            # below the threshold, then annotate the ORF as short ORF
            if ( orf_gen_len_aa and ( orf_gen_len_aa <= self.short_orf_threshold ) ):
                
                orfannotation = ORFAnnotation( orftranscriptasso_id = orftranscriptasso.id,
                                               orf_annotation = annotation,
                                               criteria = Constants.ANNOTATE_CRITERIA_EXONIC_LEN )
                objects_to_insert.append( orfannotation )
                
                # If the annotation used has not been yet registered in the 
                # ORFAnnotationCatalog table, then add it
                if ( annotation not in all_orfannotation_catalog ):
                    all_orfannotation_catalog.append( annotation )
                    orfannotationcatalog = ORFAnnotationCatalog( annotation = annotation,
                                                                 family = annotation_family_dict[ annotation ] )
                    objects_to_insert.append( orfannotationcatalog )
                 
            
            # If the biotype of the transcript provides information about the ORF class,
            # add entries to the ORFAnnotation table
            # Get the annotation(s) corresponding to the biotype
            annotation_rel_to_biotype = annotation_dict.get( transcript.rna_biotype )
            
            if annotation_rel_to_biotype:
                for annotation in annotation_rel_to_biotype:
                    orfannotation = ORFAnnotation( orftranscriptasso_id = orftranscriptasso.id,
                                                   orf_annotation = annotation,
                                                   criteria = Constants.ANNOTATE_CRITERIA_BIOTYPE )
                    objects_to_insert.append( orfannotation )
                    
                    # If the annotation used has not been yet registered in the 
                    # ORFAnnotationCatalog table, then add it
                    if ( annotation not in all_orfannotation_catalog ):
                        all_orfannotation_catalog.append( annotation )
                        orfannotationcatalog = ORFAnnotationCatalog( annotation = annotation,
                                                                     family = annotation_family_dict[ annotation ] )
                        objects_to_insert.append( orfannotationcatalog )
            
            
            # If the transcript harbors a CDS (i.e. an annotated ORF) and 
            # the information is registered about the CDS coordinates in 
            # the database, then compute the ORF annotations.
            
            # Check both the Transcript and the ORF entries are located on the same strand
            if ( ( transcript.strand != None )
                 and ( orf.strand != None ) ):
                if ( transcript.strand == orf.strand ):
                    orf_transcript_on_same_str = True
                else:
                    orf_transcript_on_same_str = False
                    Logger.get_instance().warning( 'The ORF with ID "' + str( orf.id ) + 
                                                   '" is located on the ' + orf.strand + ' strand,'
                                                   ' while its related transcript (ID "' + 
                                                   str( transcript.id ) + '") is located on the ' + 
                                                   transcript.strand + ' strand' +
                                                   ' (ORFTranscriptAsso ID: "' + str( orftranscriptasso.id ) + 
                                                   '").' +
                                                   ' Warning code: ' + LogCodes.WARN_ORFANNOT_CONFL_STRD + '.' )
            else:
                orf_transcript_on_same_str = None
                
                
            # Get all the annotations that could be given to the ORF as a list
            annotation_list = []
            
            # Log an error if (a part of the) ORF is located 
            # outside of its transcript
            if ( ( transcript.start_pos != None ) 
                 and ( transcript.end_pos != None ) 
                 and ( ( transcript.start_pos > orf.start_pos )
                       or ( orf.stop_pos > transcript.end_pos ) ) ):
                Logger.get_instance().error( 'The ORF with ID "' + str( orf.id ) +
                                             '"" has been found associated with the transcript with ID "' +
                                             str( transcript.id ) + '" (biotype: ' + transcript.rna_biotype +
                                             ', ORFTranscriptAsso ID: "' + str( orftranscriptasso.id )+ 
                                             '") whilst the ORF coordinates (' + str( orf.start_pos ) + '-' +
                                             str( orf.stop_pos ) + ') are outside of the transcript bounds (' +
                                             str( transcript.start_pos ) + '-' + str( transcript.end_pos ) +
                                             ').' +
                                             ' Error code: ' + LogCodes.ERR_ORF_ANNOT_CONFL_POS_OUT + '.', 
                                             ex  = False )
                
            # If the CDS coordinates are avaiable and the ORF is located on the 
            # transcript, then annotate the ORF using the CDS coordinates
            elif ( ( transcript.cds_start_pos != None )
                   and ( transcript.cds_stop_pos != None ) ):
                
                # Perform the annotation in the case where the ORF 
                # and the Transcript are located on same strand
                if orf_transcript_on_same_str:
                    
                    if ( orf.strand == '+' ):
                        
                        # Annotate the ORFs with a start codon located upstream
                        # of the CDS start codon
                        if ( orf.start_pos < transcript.cds_start_pos ):
                            
                            # If the ORF start codon is located upstream of the CDS start codon,
                            # and the ORF stop codon is located upstream of the CDS stop codon,
                            # then annotate the ORF as upstream
                            if ( orf.stop_pos <= transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_UPSTREAM )
                                
                                # Moreover, if the ORF stop codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( ( orf.stop_pos > transcript.cds_start_pos )
                                     and ( orf.stop_pos <= transcript.cds_stop_pos ) ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                            # If the ORF start codon is located upstream of the CDS start codon,
                            # and the ORF stop codon is located downstream of the CDS stop codon,
                            # then annotate the ORF as new CDS
                            else:
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                                
                        # Annotate the ORFs with both the start and stop codons 
                        # located in the CDS
                        elif ( ( orf.start_pos >= transcript.cds_start_pos )
                               and ( orf.stop_pos <= transcript.cds_stop_pos ) ):
                            
                            # If the ORF stop codon is located at the CDS stop codon,
                            # then the ORF is the annotated CDS
                            if ( orf.stop_pos == transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_CDS )
                            
                            # If the ORF stop codon is located upstream of the CDS 
                            # stop codon, then the ORF is annotated as overlapping
                            # and as "in CDS"
                            else:
                                annotation_list += [ Constants.ORF_ANNOTATION_OVERLAP,
                                                     Constants.ORF_ANNOTATION_IN_CDS ]
                        
                        # Annotate the ORFs with a stop codon located downstream
                        # of the CDS stop codon
                        elif ( orf.stop_pos > transcript.cds_stop_pos ):
                            
                            # If the ORF start codon is located downstream of the CDS start codon,
                            # and stop codon is located downstream of the CDS stop codon
                            # then annotate the ORF as downstream
                            if ( orf.start_pos > transcript.cds_start_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_DOWNSTREAM )
                                
                                # Moreover, if the ORF start codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( orf.start_pos < transcript.cds_stop_pos ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                    
                    
                    else:
                        
                        # Annotate the ORFs with a start codon located upstream
                        # of the CDS start codon
                        if ( orf.stop_pos > transcript.cds_stop_pos ):
                            
                            # If the ORF start codon is located upstream of the CDS start codon,
                            # and the ORF stop codon is located upstream of the CDS stop codon,
                            # then annotate the ORF as upstream
                            if ( orf.start_pos >= transcript.cds_start_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_UPSTREAM )
                                
                                # Moreover, if the ORF stop codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( ( orf.start_pos < transcript.cds_stop_pos )
                                     and ( orf.start_pos >= transcript.cds_start_pos ) ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                            # If the ORF start codon is located upstream of the CDS start codon,
                            # and the ORF stop codon is located downstream of the CDS stop codon,
                            # then annotate the ORF as new CDS
                            else:
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                                
                        # Annotate the ORFs with both the start and stop codons 
                        # located in the CDS
                        elif ( ( orf.stop_pos <= transcript.cds_stop_pos )
                               and ( orf.start_pos >= transcript.cds_start_pos ) ):
                            
                            # If the ORF stop codon is located at the CDS stop codon,
                            # then the ORF is the annotated CDS
                            if ( orf.start_pos == transcript.cds_start_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_CDS )
                            
                            # If the ORF stop codon is located upstream of the CDS 
                            # stop codon, then the ORF is annotated as overlapping
                            # and as "in CDS"
                            else:
                                annotation_list += [ Constants.ORF_ANNOTATION_OVERLAP,
                                                     Constants.ORF_ANNOTATION_IN_CDS ]
                        
                        # Annotate the ORFs with a stop codon located downstream
                        # of the CDS stop codon
                        elif ( orf.start_pos < transcript.cds_start_pos ):
                            
                            # If the ORF start codon is located downstream of the CDS start codon,
                            # and stop codon is located downstream of the CDS stop codon
                            # then annotate the ORF as downstream
                            if ( orf.stop_pos < transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_DOWNSTREAM )
                                
                                # Moreover, if the ORF start codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( orf.stop_pos > transcript.cds_start_pos ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                        
                # Perform the annotation in the case where the ORF 
                # and the Transcript are located on opposite strands
                elif ( orf_transcript_on_same_str == False ):
                    
                    annotation_list.append( Constants.ORF_ANNOTATION_OPPOSITE )
                    
                    # Transcript on the '+' strand, ORF located on the '-' strand
                    if ( orf.strand == '-' ):
                        
                        # Annotate the ORFs with a stop codon located upstream
                        # of the CDS start codon
                        if ( orf.start_pos < transcript.cds_start_pos ):
                            
                            # If the ORF stop codon is located upstream of the CDS start codon,
                            # and the ORF start codon is located upstream of the CDS stop codon,
                            # then annotate the ORF as upstream
                            if ( orf.start_pos <= transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_UPSTREAM )
                                
                                # Moreover, if the ORF start codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( ( orf.stop_pos > transcript.cds_start_pos )
                                     and ( orf.stop_pos <= transcript.cds_stop_pos ) ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                            # If the ORF stop codon is located upstream of the CDS start codon,
                            # and the ORF start codon is located downstream of the CDS stop codon,
                            # then annotate the ORF as new CDS
                            else:
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                                
                        # Annotate the ORFs with both the start and stop codons 
                        # located in the CDS
                        elif ( ( orf.start_pos >= transcript.cds_start_pos )
                               and ( orf.stop_pos <= transcript.cds_stop_pos ) ):
                            
                            # If the ORF start codon is located at the CDS stop codon,
                            # then the ORF exactly overlap the annotated CDS on the
                            # opposite strand
                            if ( orf.stop_pos == transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                            
                            # If the ORF start codon is located upstream of the CDS 
                            # stop codon, then the ORF is annotated as overlapping
                            # and as "in CDS"
                            else:
                                annotation_list += [ Constants.ORF_ANNOTATION_OVERLAP, 
                                                     Constants.ORF_ANNOTATION_IN_CDS ]
                        
                        # Annotate the ORFs with a start codon located downstream
                        # of the CDS stop codon
                        elif ( orf.stop_pos > transcript.cds_stop_pos ):
                            
                            # If the ORF stop codon is located downstream of the CDS start codon,
                            # and the ORF start codon is located downstream of the CDS stop codon
                            # then annotate the ORF as downstream
                            if ( orf.start_pos > transcript.cds_start_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_DOWNSTREAM )
                                
                                # Moreover, if the ORF stop codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( orf.start_pos < transcript.cds_stop_pos ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                    # Transcript on the '-' strand, ORF located on the '+' strand
                    if ( orf.strand == '+' ):
                        
                        # Annotate the ORFs with a stop codon located upstream
                        # of the CDS start codon
                        if ( orf.stop_pos > transcript.cds_stop_pos ):
                            
                            # If the ORF stop codon is located upstream of the CDS start codon,
                            # and the ORF start codon is located upstream of the CDS stop codon,
                            # then annotate the ORF as upstream
                            if ( orf.start_pos >= transcript.cds_stop_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_UPSTREAM )
                                
                                # Moreover, if the ORF start codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( ( orf.start_pos < transcript.cds_start_pos )
                                     and ( orf.start_pos >= transcript.cds_start_pos ) ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
                                    
                            # If the ORF stop codon is located upstream of the CDS start codon,
                            # and the ORF start codon is located downstream of the CDS stop codon,
                            # then annotate the ORF as new CDS
                            else:
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                                
                        # Annotate the ORFs with both the start and stop codons 
                        # located in the CDS
                        elif ( ( orf.stop_pos <= transcript.cds_start_pos )
                               and ( orf.start_pos >= transcript.cds_stop_pos ) ):
                            
                            # If the ORF stop codon is located at the CDS stop codon,
                            # then the ORF exactly overlap the annotated CDS on the
                            # opposite strand
                            if ( ( orf.start_pos == transcript.cds_stop_pos )
                                 and ( orf.stop_pos == transcript.cds_start_pos ) ):
                                annotation_list.append( Constants.ORF_ANNOTATION_NEW_CDS )
                            
                            # If the ORF start codon is located upstream of the CDS 
                            # stop codon, then the ORF is annotated as overlapping
                            # and as "in CDS"
                            else:
                                annotation_list += [ Constants.ORF_ANNOTATION_OVERLAP,
                                                     Constants.ORF_ANNOTATION_IN_CDS ]
                        
                        # Annotate the ORFs with a start codon located downstream
                        # of the CDS stop codon
                        elif ( orf.start_pos < transcript.cds_start_pos ):
                            
                            # If the ORF start codon is located downstream of the CDS stop codon,
                            # and ORF stop codon is located downstream of the CDS start codon
                            # then annotate the ORF as downstream
                            if ( orf.start_pos < transcript.cds_start_pos ):
                                annotation_list.append( Constants.ORF_ANNOTATION_DOWNSTREAM )
                                
                                # Moreover, if the ORF stop codon is located in the CDS,
                                # then annotate the ORF as overlapping
                                if ( orf.stop_pos > transcript.cds_start_pos ):
                                    annotation_list.append( Constants.ORF_ANNOTATION_OVERLAP )
        
        
                # If the ORF and the transcript are located on the same strand,
                # then check if the ORF start codon is in the same frame than the
                # CDS start codon
                if orf_transcript_on_same_str:
                
                    start_to_start_dist = abs( orf.start_pos - transcript.cds_start_pos)
                    
                    if ( ( start_to_start_dist % 3 ) != 0 ):
                        annotation_list.append( Constants.ORF_ANNOTATION_ALT ) 
                                    
                            
            # Add all the annotations to the database
            for annotation in annotation_list:
                orfannotation = ORFAnnotation( orftranscriptasso_id = orftranscriptasso.id,
                                               orf_annotation = annotation,
                                               criteria = Constants.ANNOTATE_CRITERIA_COORD )
                objects_to_insert.append( orfannotation )
                
                # If the annotation used has not been yet registered in the 
                # ORFAnnotationCatalog table, then add it
                if ( annotation not in all_orfannotation_catalog ):
                    all_orfannotation_catalog.append( annotation )
                    orfannotationcatalog = ORFAnnotationCatalog( annotation = annotation,
                                                                 family = annotation_family_dict[ annotation ] )
                    objects_to_insert.append( orfannotationcatalog )
                                
        self.batch_insert_to_PRO_db( objects_to_insert = objects_to_insert, 
                                     processfile = 'orf_annotation',
                                     process = 'compute_orf_category(): Computation of ORF categories' )
               
        Logger.get_instance().info( 'The computation of the ORF annotations using the information' +
                                    ' from the ORF and Transcript tables has finished.')
        
                
    
    # ===============================================================================
    # Common methods
    # ===============================================================================    

    ## batch_insert_to_PRO_db
    #  ----------------------
    # 
    # This method allows to insert a list of objects in the database.
    # Large sets of objects are split into several batches which are inserted one at a time.
    #
    # @param objects_to_insert: List - The list of objects to insert in the database.
    # @param processfile: String - The name of the file in which save the objects that are 
    #                              expected to be inserted.
    # @param process: String - The name of the process that generated this list.
    #
    @staticmethod
    def batch_insert_to_PRO_db( objects_to_insert, processfile, process='Undefined process' ):
        
        # Save into a temporary file the data that should be inserted.
        # This allows to recover the data later if an exception is raised during 
        # the insertion, saving thus the computation time.
        try:
            FileHandlerUtil.save_obj_to_file( objects_to_save = objects_to_insert,
                                              filename = processfile,
                                              output_folder = Constants.ANNOTATE_DATA_FOLDER )
        except Exception as e:
            Logger.get_instance().error( 'AnnotateORFStrategy.batch_insert_to_PRO_db():' +
                                         ' An error occurred trying to save data from ' + process + 
                                         ': \n' + str( e ) +
                                         ' Error code: ' + LogCodes.ERR_FILEHAND + '.',
                                         ex = False )
        
        SQLManagerPRO.get_instance().batch_insert_to_db( objects_to_insert = objects_to_insert,
                                                         process = process )
    