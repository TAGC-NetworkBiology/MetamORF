# -*- coding: utf-8 -*-

from abc import abstractmethod
import pandas as pd


from fr.tagc.uorf.core.model.DS import *

from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.data.DataManager import DataManager
from fr.tagc.uorf.core.util.ensembl.EnsemblUtil import EnsemblUtil
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception import *
from fr.tagc.uorf.core.util.log import *


## ParserStrategy
#  ==============
#
# This class is an abstract class and metaclass for "ParserStrategy classes" that 
# allow to parse the data from pre-defined data sources (see the "parserstrategy" 
# module for more information about the parsers, one class has been defined for 
# each data source). Hence, this class cannot be instantiated and only contains 
# abstract methods.
#
class ParserStrategy( object ):

    ## Constructor of ParserStrategy
    #  -----------------------------
    #
    # Instance variables:
    #     - data_source: String - The name of the data source.
    #     - data_path: String - The path to the data source file.
    #     - file_content: Pandas data frame - The Pandas data frame containing 
    #                                         the content of the source file.
    #
    # @param data_path: String - The path to the data source file.
    #
    def __init__( self, data_path ):
        
        self.data_source = str( self.__class__.__name__ )
        self.data_path = data_path
        self.file_content = None



    ## execute
    #  -------
    #
    # This is an abstract method to execute the strategy.
    #
    # For each parser inheriting from the current metaclass, the following main steps are performed
    # when executing this method:
    # - The file content is imported.
    # - The headers of the file are checked in order to make sure the file is provided in its
    #   expected format.
    # - Several variables are assigned to some of the useful data contained in the DataManager main
    #   dictionary in order to access these data quickly and easily anywhere in the program. 
    #   These include the dictionaries containing all the entries of the DSORF, DSTranscript, 
    #   DSORFTranscriptAsso and UTDSTranscriptGeneConflict tables as well as the autoincrement 
    #   variable containing the value to use as autoincrement (unique ID) when creating new entries.
    # - The number of rows expected to be treated is saved and used to set up a counter allowing to 
    #   follow the progression of the file whilst the algorithm is running.
    # - Each line of the file is parsed and data are extracted and used to instantiate appropriate 
    #   DenCellORF objects (i.e. to register new entries in the database).
    #     * In order to perform the parsing, for each entry, the information provided are used to 
    #       instantiate new objects. When a new object is created, it is compared to the existing
    #       one (in the dictionary or in 'tracking lists / dictionaries'). If an existing object is 
    #       the same as the newly created (i.e. sharing the same primary key and/or attributes on which 
    #       an unique constraint has been defined), the older one is used (and eventually updated using 
    #       the new information).
    #       Otherwise, the new instance is added to the list of objects to insert in the database and 
    #       the trace of this new object is kept (in the dictionaries / lists) for further use.
    #     * For an easier reading and when feasible the information that will be used several time
    #       (such as the chromosome name or the ORF ID) are saved in local variables prior to the
    #       creation of the objects.
    #     * Some additional information related to the creation of the DenCellORF objects:
    #          - An 'autoincrement' variable is saved and increment of 1 at each new instantiation,
    #            allowing to define unique IDs when necessary.
    #          - For DSORF: The 'start_pos', 'stop_pos', 'sequence' and 'genomic_length' attributes 
    #                       are expected to be computed later during the LiftOver nad ComputeMissingInfo 
    #                       strategies.
    #     * If the transcript ID is missing, an 'unkown' transcript is created.
    #     * If the gene symbol is missing, the program try to get it from the transcript ID or from the
    #       coordinates of the ORF (see documentation of the initialize_ids() methods). If it cannot be 
    #       recovered, an 'unknown' gene is created.
    #
    # @return None
    #
    @abstractmethod
    def execute():
        
        return None

    
    
    # ===============================================================================
    # Methods commonly used by several process
    # ===============================================================================
        
    ## is_empty
    #  --------
    #
    # This is a static method that allows to check if a value extracted from a 
    # Pandas data frame is empty or missing. Please see the documentation of the
    # GeneralUtil.is_empty() method.
    #
    # @param val: String/Float (from data frame) - Value to test.
    # @param empty_val: List - List of values considered as empty / missing.
    #
    # @return Boolean - True if the value is missing.
    #
    @staticmethod
    def is_empty( val, empty_val=Constants.EMPTY_VALUES ):
        
        return GeneralUtil.is_empty( val, empty_val )



    ## get_ensembl_db
    #  --------------
    # 
    # This is a static method allowing to download the appropriate Ensembl database
    # which is used by the initialize_ids() method to find the gene symbol from the 
    # transcript ID or ORF coordinates when it is not provided in the source file.
    # 
    # @param annotation_version: String or Integer - The Ensembl annotation version corresponding
    #                                                to the datasource.
    #
    # @return ensembl_db: EnsemblRelase object - The Ensembl database object.
    #
    @staticmethod
    def get_ensembl_db( annotation_version ):
        
        # Get the name of the species from the DataManager
        sp = DataManager.get_instance().get_data( Constants.SPECIES_FULL )
        
        return EnsemblUtil.get_ensembl_db( sp, annotation_version )

    
    
    # ===============================================================================
    # Methods related to the importation of source content
    # ===============================================================================
        
    ## import_file_content
    #  -------------------
    #
    # This method allows to import the data from a file as a Pandas data frame.
    # 
    # @param file_sep: String - The delimiter to use (see pandas.read_csv() help for more information).
    # @param dtype_val: String - The data type for data or columns (see pandas.read_csv() help 
    #                            for more information). 'str' by default.
    # @param encoding_val: String - Encoding to use for UTF when reading (see pandas.read_csv() help 
    #                               more information). 'utf-8' by default.
    #
    @abstractmethod
    def import_file_content( self, file_sep = ',', dtype_val = 'str', encoding_val = 'utf-8' ):
        
        # Get the content of the file
        self.file_content = pd.read_csv( self.data_path, 
                                         sep = file_sep, 
                                         dtype = dtype_val, 
                                         encoding = encoding_val )
        
        # Replace NA values by None
        self.file_content = self.file_content.where( pd.notnull( self.file_content ), None )
        
        
        
    ## check_headers
    #  -------------
    #
    # This method allows to check if a list of expected headers is included in
    # the pandas data frame column names (containing the content of the file).
    #
    # @throw MissingHeaderException: When one of the expected headers is missing.
    # @throw DuplicateHeaderException: When several headers seems to be identical in the original file.
    #
    @abstractmethod
    def check_headers( self ):
                
        # Get the list of the column names and sort it
        col_names = sorted( list( self.file_content ) )
        
        # Check if the list of expected headers is included in the column name list.
        # Raise a MissingHeaderException if some of the expected headers are missing.
        header_included = set( self.HEADER_LIST ).issubset( col_names )
        
        if ( header_included == False ):
            # Get the list of missing headers and raise a MissingHeaderException
            missing_headers = [ h for h in self.HEADER_LIST if h not in col_names ]
            raise MissingHeaderException( self.data_source + 
                                          '.check_headers(): The following headers are missing: ' +
                                          ', '.join( missing_headers ) + ' in the data file.' +
                                          ' Please see the documentation of the parser for more information.' )
        
        
        # Check if there are several columns harboring the same name
        uniq_list = []
        duplicate_list = []
        
        for n in col_names:
            # NB: When a new header is found to have the same title than a previous column, 
            #     Pandas uses its name and add a dot followed by a unique number.
            nbis = n.split( '.' )
              
            # If the header name does not contain any dot, the header is clearly not a duplicate
            if ( len( nbis ) == 1 ):
                uniq_list.append( n )
                  
            # If the header contains dots in its name but does not finish with an integer, 
            # then it cannot be a duplicate
            elif ( ( len( nbis ) > 1 ) and ( not nbis[ -1 ].isdigit() ) ):
                uniq_list.append( n )
                
            # If the header contains dots and finish with an integer, 
            # then it looks like a duplicate
            elif ( ( len( nbis ) > 1 ) and ( nbis[ -1 ].isdigit() ) ):
                
                # Then search if the header without its last integer exist in the uniq_list.
                # If not, then this is not a duplicate.
                if ( ( '.'.join(nbis[ :-1 ] ) ) not in uniq_list ):
                    uniq_list.append( n )
                
                # Otherwise, if the header without its last integer exists in the uniq_list, 
                # then it should probably be a duplicate
                else:
                    # If this is the first time this duplicate is detected, then add it to the list of 
                    # potential duplicates
                    if ( '.'.join( nbis[ :-1 ] ) not in duplicate_list ):
                        duplicate_list.append( '.'.join( nbis[ :-1 ] ) )
                        
        # If there are several column names that seems to be duplcates, raise a DuplicateHeaderException
        if ( len( duplicate_list ) != 0 ):
            raise DuplicateHeaderException( self.data_source + 
                                            '.check_headers(): The following column names: ' + 
                                            ', '.join( duplicate_list ) + 
                                            ' have been identified as potential duplicates in the header' +
                                            ' of the file located at ' + self.data_path +
                                            '. This parser will use the following columns ' + 
                                            ', '.join( self.HEADER_LIST ) + ' to process the file.' +
                                            ' Please make sure the columns used to parse this file are the right ones.' )

    
    
    # ===============================================================================
    # Methods related to the initialization of
    # the chromosome name, transcript ID and gene ID 
    # ===============================================================================

    ## initialize_ids
    #  --------------
    # 
    # This method allows to:
    #     - Set the chromosome name to None if it is missing,
    #       or to set it to the defined value if it is the mitochondrial chromosome,
    #       or to set it to the defined value if it is the sexual chromosome,
    #     - Generate a "fake" transcript ID if its is not provided,
    #     - Try to get the symbol if it is not provided, using the transcript ID 
    #       (if this is an Ensembl ID) or the ORF coordinates or to generate a "fake"
    #       symbol if the actual cannot be recovered.
    #
    # @param ensembl_db: EnsemblRelease - The EnsemblRelease object related to the appropriate
    #                                     genome annotation.
    # @param orf_id: String - The original ORF ID (as provided in the source).
    # @param chr_name: String - The chromosome name (as provided in the source).
    # @param symbol: String - The symbol or gene ID (as provided in the source).
    # @param transcript_id: String - The transcript ID (as provided in the source).
    # @param orf_start: String (or Integer) - The ORF start genomic coordinates.
    # @param orf_stop: String (or Integer) - The ORF stop genomic coordinates.
    # @param orf_strand: String - The strand of the ORF.
    # @param index: Integer - The index of the row being parsed.
    # @param log_symb_from_tr: Boolean - Does the recovery of the gene symbol from the transcript ID 
    #                                    has to be logged? True by default.
    #                                    NB: We advise to set this parameter to False only if the data 
    #                                        source does not provide any information about the gene ID 
    #                                        (see documentation of symbol_from_transcript_id() method 
    #                                        for more information). Setting this parameter to False 
    #                                        allows to decrease the number of logs, thus decreasing 
    #                                        the computation time.
    # @param log_single_symb_from_pos: Boolean - Does the recovery of a unique gene symbol from the ORF
    #                                            coordinates has to be logged? True by default.
    #                                            NB: We advise to set this parameter to False only if the 
    #                                                data source does not provide any information about 
    #                                                the gene ID nor about the transcript ID (see 
    #                                                documentation of symbol_from_orf_loc() method 
    #                                                for more information). Note that if several genes are
    #                                                overlapping with the position or if there are no genes
    #                                                but lncRNAs overlapping with the position, then the 
    #                                                information will always be logged. Setting this 
    #                                                parameter to False allows to decrease the number of 
    #                                                logs, thus decreasing the computation time. 
    #
    # @return chr_name: String (or None) - The chromosome name (set to None if considered as missing).
    # @return symbol: String - The symbol or gene ID (either as provided in the source or found from
    #                          the ORF coordinates or "unknown" gene ID generated).
    # @return transcript_id: String - The transcript ID (either as provided in the source or "fake" ID
    #                               generated).
    #
    @abstractmethod
    def initialize_ids( self, ensembl_db, orf_id, chr_name, symbol, transcript_id, orf_start, \
                        orf_stop, orf_strand, index, log_symb_from_tr=True, log_single_symb_from_pos=True ):
        
        # Process the chromosome name
        chr_name = self.initialize_chromosome_name( chr_name = chr_name )
        
        # Process the transcript ID
        transcript_id = self.initialize_transcript_id( transcript_id = transcript_id, 
                                                       orf_id = orf_id,
                                                       index = index )
        
        # Pocess the symbol 
        symbol = self.initialize_gene_symbol( ensembl_db = ensembl_db, 
                                              orf_id = orf_id, 
                                              chr_name = chr_name, 
                                              symbol = symbol, 
                                              transcript_id = transcript_id, 
                                              orf_start = orf_start, 
                                              orf_stop = orf_stop,
                                              orf_strand = orf_strand,
                                              log_symb_from_tr = log_symb_from_tr,
                                              log_single_symb_from_pos = log_single_symb_from_pos )
        
        return ( chr_name, symbol, transcript_id )
    


    ## initialize_chromosome_name
    #  --------------------------
    # 
    # This method allows to set the chromosome name to None if it is missing, 
    # or to set it to the defined value if it is the mitochondrial chromosome,
    # or to set it to the defined value if it is the sexual chromosome.
    #
    # @param chr_name: String - The chromosome name (as provided in the source).
    #
    # @return chr_name: String / None - The chromosome name (set to None if missing).
    #
    @staticmethod
    def initialize_chromosome_name( chr_name ):
        
        chr_name = str( chr_name )
        
        # Get the name of the sexual chromosome for the species in the database
        sp_short_name = DataManager.get_instance().get_data( Constants.SPECIES_SHORT )
        sex_chr = Constants.SEX_CHROMOSOME[ sp_short_name ]
        
        # If the chromosome name is missing, set it to none
        if ParserStrategy.is_empty( chr_name ):
            return None
            
        # If the chromosome name is mitochondrial, set it to the appropriate value
        elif ( chr_name in Constants.MITOCHONDRIAL_CHR_LIST ):
            return Constants.MITOCHONDRIAL_CHR
        
        # If the chromosome name is an alias of the sexual chromosome (e.g. 23 for H. sapiens), 
        # set it to 'X|Y'
        elif ( chr_name == sex_chr ):
            return Constants.CHROMOSOME_NAME_XY
        
        else:
            return chr_name



    ## initialize_transcript_id
    #  ------------------------
    # 
    # This method allows to generate a "fake" transcript ID if 
    # it is not provided by the data source.
    #
    # @param transcript_id: String - The transcript ID (as provided in the source).
    # @param orf_id: String - The ORF ID (as provided in the source).
    # @param index: Integer - The index of the row being parsed.
    #
    # @return transcript_id: String - The transcript ID (either as provided in the source or 
    #                                 as a "fake ID" generated by the method).
    #
    @abstractmethod
    def initialize_transcript_id( self, transcript_id, orf_id, index ):

        # If the transcript ID is missing, generate a "fake" ID,
        # by concatenating the name of the data source and the entry index
        if ParserStrategy.is_empty( transcript_id ):
            transcript_id = Constants.PREFIX_FAKE_TRANSCRIPT + self.data_source + '_' + str( index )
            # NB: The following warning has been disabled as the number of "fake" transcripts
            #     created for a particular source may be easily recover using the following raw SQL query: 
            #             SELECT COUNT( * ) 
            #             FROM `DSTranscript` 
            #             WHERE ( ( `transcript_id` LIKE 'UNKNOWN_%' ) 
            #                     AND ( `data_source` = 'DatasourceName' ) )
            #Logger.get_instance().warning( 'There was no transcript associated with the ORF with ID: "' + 
            #                               orf_id + '" in ' + self.data_source +
            #                               '. Hence, this ORF will be associated with the "unknown" transcript ' + 
            #                               transcript_id + '.' +
            #                               ' Warning code: ' + LogCodes.WARN_ORFASSO_TR + '.' )
            
        # Otherwise, make sure this is a string
        else:
            transcript_id = str( transcript_id )
                                
        return transcript_id



    ## initialize_gene_symbol
    #  ----------------------
    # 
    # This method allows to try to get the symbol if it is not provided, using the 
    # transcript ID (if this is an Ensembl ID) or the ORF coordinates or to generate 
    # a "fake" symbol if the actual cannot be recovered.
    #
    # @param ensembl_db: EnsemblRelease - The EnsemblRelease object related to the appropriate
    #                                     genome annotation.
    # @param orf_id: String - The ORF ID (as provided in the source).
    # @param chr_name: String - The chromosome name (after use of the initialize_chromosome_name() method).
    # @param symbol: String - The symbol or gene ID (as provided in the source).
    # @param transcript_id: String - The transcript ID (after use of the initialize_transcript_id() method).
    # @param orf_start: String (or Integer) - The ORF start genomic coordinates.
    # @param orf_stop: String (or Integer) - The ORF stop genomic coordinates.
    # @param orf_strand: String - The ORF strand.
    # @param log_symb_from_tr: Boolean - Does the recovery of the gene symbol from the transcript ID 
    #                                    has to be logged? True by default.
    #                                    NB: We advise to set this parameter to False only if the data 
    #                                        source does not provide any information about the gene ID 
    #                                        (see documentation of symbol_from_transcript_id() method 
    #                                        for more information). Setting this parameter to False 
    #                                        allows to decrease the number of logs, thus increasing 
    #                                        the computation time.
    # @param log_single_symb_from_pos: Boolean - Does the recovery of a unique gene symbol from the ORF
    #                                            coordinates has to be logged? True by default.
    #                                            NB: We advise to set this parameter to False only if the 
    #                                                data source does not provide any information about 
    #                                                the gene ID nor about the transcript ID (see 
    #                                                documentation of symbol_from_orf_loc() method 
    #                                                for more information). Note that if several genes are
    #                                                overlapping with the position or if there are no genes
    #                                                but lncRNAs overlapping with the position, then the 
    #                                                information will always be logged. Setting this 
    #                                                parameter to False allows to decrease the number of 
    #                                                logs, thus decreasing the computation time. 
    #
    # @return symbol: String - The symbol or gene ID (either an "actual" symbol, as provided in the source 
    #                          or found in the Ensembl database using the transcript ID or ORF coordinates, 
    #                          or as a "fake" ID generated if the actual gene ID is unknown and may not be
    #                          recover).
    #
    @abstractmethod
    def initialize_gene_symbol( self, ensembl_db, orf_id, chr_name, symbol, transcript_id, orf_start, \
                                orf_stop, orf_strand, log_symb_from_tr=True, log_single_symb_from_pos=True ):
    
        # If the symbol is provided, make sure it is a string      
        if ( not ParserStrategy.is_empty( symbol ) ):
            symbol = str( symbol )
        
        # Otherwise, if the gene symbol is missing try to get it using the ORF coordinates
        else:
            # Try to get the gene symbol using the transcript ID if it is provided
            symbol = self.symbol_from_transcript_id( ensembl_db = ensembl_db, 
                                                     orf_id = orf_id,
                                                     transcript_id = transcript_id,
                                                     log_warning = log_symb_from_tr )
            
            # If the symbol ID cannot be recovered using the transcript ID, try to get it using the coordinates
            if ( symbol == None ):
                symbol = self.symbol_from_orf_loc( ensembl_db = ensembl_db,
                                                   orf_id = orf_id, 
                                                   chr_name = chr_name, 
                                                   orf_start = orf_start, 
                                                   orf_stop = orf_stop, 
                                                   orf_strand = orf_strand,
                                                   log_single_symb_from_pos = log_single_symb_from_pos )
        
        return symbol
    


    ## symbol_from_transcript_id
    #  -------------------------
    # 
    # This method allows to try to get the symbol corresponding
    # to an Ensembl transcript ID.
    #
    # @param ensembl_db: EnsemblRelease - The EnsemblRelease object related to the appropriate
    #                                     genome annotation.
    # @param orf_id: String - The ORF ID (as provided in the source).
    # @param transcript_id: String - The transcript ID (get using the initialize_transcript_id() method).
    # @param log_warning: Boolean - Does the recovery of the gene symbol from the transcript ID 
    #                               has to be logged? True by default.
    #                               NB: We advise to set this parameter to False only if the data 
    #                                   source does not provide any information about the gene ID 
    #                                   (see documentation of symbol_from_transcript_id() method 
    #                                   for more information). Setting this parameter to False 
    #                                   allows to decrease the number of logs, thus increasing 
    #                                   the computation time.
    #
    # @return symbol: String / None - The symbol corresponding to the provided transcript ID.
    #
    @abstractmethod
    def symbol_from_transcript_id( self, ensembl_db, orf_id, transcript_id, log_warning=True ):
                
        # If the transcript ID is an Ensembl ID, try to get the gene symbol using the transcript ID
        if ( ( not ParserStrategy.is_empty( transcript_id ) ) and 
             ( transcript_id.startswith( 'ENS' ) ) ):
            try:
                symbol = ensembl_db.gene_name_of_transcript_id( transcript_id )
            except:
                symbol = None
            else:
                # If requested, log the recovery of the gene symbol from the transcript ID
                if log_warning:
                    Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                                   orf_id + '" in ' + self.data_source + 
                                                   ' but the transcript associated with this ORF ("' +
                                                   transcript_id + 
                                                   '") has been found associated with the gene symbol "' +
                                                   symbol + '" in the Ensembl database.' +
                                                   ' Hence, this ORF will be associated with this gene.' +
                                                   ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_FROM_TR_ID + '.' )
        
        # Otherwise, set the symbol to None
        else:
            symbol = None
            
        return symbol
        


    ## symbol_from_orf_loc
    #  -------------------
    # 
    # This method allows to try to get the symbol associated with an ORF
    # using its coordinates.
    #
    # @param ensembl_db: EnsemblRelease - The EnsemblRelease object related to the appropriate
    #                                     genome annotation.
    # @param orf_id: String - The ORF ID (as provided in the source).
    # @param chr_name: String - The chromosome name (get using the initialize_chromosome_name() method).
    # @param orf_start: String (or Integer) - The ORF start genomic coordinates.
    # @param orf_stop: String (or Integer) - The ORF stop genomic coordinates.
    # @param orf_strand: String - The ORF strand.
    # @param log_single_symb_from_pos: Boolean - Does the recovery of a unique gene symbol from the ORF
    #                                            coordinates has to be logged? True by default.
    #                                            NB: We advise to set this parameter to False only if the 
    #                                                data source does not provide any information about 
    #                                                the gene ID nor about the transcript ID (see 
    #                                                documentation of symbol_from_orf_loc() method 
    #                                                for more information). Note that if several genes are
    #                                                overlapping with the position or if there are no genes
    #                                                but lncRNAs overlapping with the position, then the 
    #                                                information will always be logged. Setting this 
    #                                                parameter to False allows to decrease the number of 
    #                                                logs, thus decreasing the computation time.
    #
    # @return symbol: String - The symbol or gene ID (either an "actual" symbol found in the Ensembl 
    #                          database using the ORF coordinates, or as a "fake" ID generated if the 
    #                          actual gene ID may not be recover).
    #
    @abstractmethod
    def symbol_from_orf_loc( self, ensembl_db, orf_id, chr_name, orf_start, orf_stop, orf_strand, \
                             log_single_symb_from_pos=True ):     
                    
        # If the chromosome name is missing, set the value of the symbol to an "unknown" gene 
        # (on an "unknown" chromosome)
        if ParserStrategy.is_empty( chr_name ):
            symbol = Constants.PREFIX_UNKNOWN_GENE + 'chr_UNKNOWN'
            Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                           orf_id + '" in ' + self.data_source +
                                           ' and the chromosome name is not known.' +
                                           ' Hence, this ORF will be associated with the "unknown" gene "' + 
                                           symbol + '".' +
                                           ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_UNKN_MISCHR + '.' )
        
        # Otherwise, try to get the symbol from the ORF coordinates
        else:            
            # If the ORF strand is missing, create an "unknown gene" (on the provided chromosome)
            if ParserStrategy.is_empty( val = orf_strand, empty_val = Constants.EMPTY_VALUES_WO_DASH ):
                symbol = Constants.PREFIX_UNKNOWN_GENE + 'chr_' + chr_name
                Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                               orf_id + '" in ' + self.data_source +
                                               ' and the strand of this ORF was missing, so overlapping' +
                                               ' genes or lncRNAs cannot be found in the Ensembl database' +
                                               ' using the ORF coordinates.' +
                                               ' Hence, this ORF will be associated with the "unknown"' +
                                               ' gene "' + symbol + '".' +
                                               ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_UNKN_MISSTRAND + '.' )
                
            # Otherwise, try to get the gene(s) or lncRNA(s) overlapping with the ORF coordinates
            else:
                # Get the list of Ensembl objects (gene, lncRNA, miRNA...) overlapping with this location
                genes_at_location = ensembl_db.genes_at_locus( contig = chr_name,
                                                               position = int( orf_start ),
                                                               end = int( orf_stop ),
                                                               strand = orf_strand )
                
                # Get the list of genes at these coordinates
                genes_at_loc = [ g.gene_name for g in genes_at_location if ( g.biotype == 'protein_coding' ) ]
                
                # If there is one single gene overlapping with these coordinates, get it
                if ( len( genes_at_loc ) == 1 ):
                    symbol = genes_at_loc[ 0 ]
                    # Only log this operation if required
                    if log_single_symb_from_pos:
                        Logger.get_instance().warning( 'There was no gene associated with the ORF with' +
                                                       ' original ID "' + orf_id + '" in ' + self.data_source +
                                                       ', but the ORF coordinates have been found' +
                                                       ' overlapping the gene "' + symbol + 
                                                       '" in the Ensembl database.' +
                                                       ' Hence, the ORF will be associated with this gene.' +
                                                       ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_SING + '.' )
                
                # If there are several genes overlapping with these coordinates, concatenate them to create a gene id
                elif ( len( genes_at_loc) > 1 ):
                    
                    # If the ORF is overlapping exactly two genes, concatenate them to create the gene id
                    if ( len( genes_at_loc ) == 2 ):
                        symbol = ( Constants.PREFIX_OVERLAPPING_GENES + 
                                   '_'.join( sorted( genes_at_loc ) ) + 
                                   '_chr' + chr_name )
                        
                    # Otherwise, only use the first and last genes to create the ID
                    else:
                        symbol = ( Constants.PREFIX_OVERLAPPING_GENES + 
                                   genes_at_loc[ 0 ] + '_to_' + genes_at_loc[ -1 ] + 
                                   '_chr' + chr_name )
                        
                    Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' +
                                                   orf_id + '" in ' + self.data_source +
                                                   ' but the ORF coordinates have been found overlapping' +
                                                   ' with the following genes "' + 
                                                   ', '.join( genes_at_loc ) + '" in the Ensembl database.' +
                                                   ' Hence, this ORF will be associated with the "overlapping" gene "' + 
                                                   symbol + '".' +
                                                   ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_SEV + '.' )
                
                # Otherwise, if there is no gene overlapping with these coordinates,
                # try check the lncRNAs that may be overlapping with these coordinates. 
                else:
                    # Get the list of lncRNAs at these coordinates
                    lncRNAs_at_loc = [ g.gene_name for g in genes_at_location if ( g.biotype == 'lincRNA' ) ]
                
                     # If there is one single lncRNA overlapping with these coordinates, get it
                    if ( len( lncRNAs_at_loc ) == 1 ):
                        symbol = lncRNAs_at_loc[ 0 ]
                        Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                                       orf_id + '" in ' + self.data_source +
                                                       ' nor overlapping with these coordinates,' +
                                                       ' but the ORF coordinates have been found overlapping' +
                                                       ' with the lncRNA "' + symbol + '" in the Ensembl database.' +
                                                       ' Hence, the ORF will be associated with this lncRNA' +
                                                       ' (registered as an entry in the Gene table).' + 
                                                       ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_LNCR_SING + '.' )
                        
                    # If there are several lncRNAs overlapping with these coordinates, 
                    # concatenate them to create a gene id
                    elif ( len( lncRNAs_at_loc ) > 1 ):
                        
                        # If the ORF is overlapping exactly two lncRNAs, 
                        # concatenate them to create the gene id
                        if ( len( lncRNAs_at_loc ) == 2 ):
                            symbol = ( Constants.PREFIX_OVERLAPPING_LNCRNAS + 
                                       '_'.join( sorted( lncRNAs_at_loc ) ) + 
                                       '_chr' + chr_name )
                        
                        # Otherwise, only use the first and last lncRNAs to create the ID
                        else:
                            symbol = ( Constants.PREFIX_OVERLAPPING_LNCRNAS + 
                                       lncRNAs_at_loc[ 0 ] + '_to_' + lncRNAs_at_loc[ -1 ] + 
                                       '_chr' + chr_name )
                        
                        Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                                       orf_id + '" in ' + self.data_source +
                                                       ' nor overlapping with these coordinates,' +
                                                       ' but the ORF coordinates have been found overlapping' +
                                                       ' with the following lncRNAs "' +
                                                       ', '.join( lncRNAs_at_loc ) + '" in the Ensembl database.' +
                                                       ' Hence, this ORF will be associated with "' + symbol + 
                                                       '" (registered as an entry in the Gene table).' +
                                                       ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_LNCR_SEV + '.' )
                
                    # Otherwise, if there is no gene nor lncRNAs overlapping with these coordinates, create an "intergenic" gene. 
                    else:
                        symbol = Constants.PREFIX_INTERGENIC_GENE + 'chr' + chr_name
                        Logger.get_instance().warning( 'There was no gene associated with the ORF with original ID "' + 
                                                       orf_id + '" in ' + self.data_source +
                                                       ' and no gene nor lncRNA has been found overlapping' +
                                                       ' the ORF coordinates in the Ensembl database.' +
                                                       ' Hence, this ORF will be associated with the "intergenic" gene "' + 
                                                       symbol + '".' +
                                                       ' Warning code: ' + LogCodes.WARN_ORFASSO_GENE_INTERG + '.' )
        
        return symbol

    
    
    # ===============================================================================
    # Methods related to the Gene, GeneAlias and UTGeneFromAlias entries
    # ===============================================================================
        
    ## get_gene_from_symbol
    #  --------------------
    #
    # This method allows to get the unique Gene entry associated with a (symbol, chromosome)
    # pair, when this is possible. In order to minimize the computation time, all associations
    # that have already been searched are saved in a dictionary of the DataManager main dictionary.
    # The object are saved in this dictionary with value for the (symbol, chromosome) key that 
    # may be either an instance of the Gene class or an instance of an exception (when it was not 
    # possible to find an unique gene corresponding to the pair). In such cases, the message related
    # to the exception is logged as a GeneRef warning.
    # If this association has never been searched, the find_gene_from_symbol() method is called
    # in order to get the instance corresponding to the (symbol, chromosome) pair.
    #
    # @param symbol: String - The symbol or alias of the gene.
    # @param chr_name: String - The chromosome name of the gene.
    # @param orf_id: String - The ORF ID related to this gene (as provided in the source file).
    #
    # @return gene: Gene - Return the Gene instance associated with the provided alias and chromosome.
    # @return new_obj_to_insert: List - List of objects to insert if new objects have been created 
    #                                   in the process.
    # 
    @abstractmethod
    def get_gene_from_symbol( self, symbol, chr_name, orf_id ):
        
        # Initialize the list of new objects that will have to be inserted
        new_obj_to_insert = []
        
        # Get the dictionary which associate to each (symbol, chromosome) tuple, 
        # the Gene or the Exception previously instantiated
        all_gene_symbol_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_SYMBOL_ASSO )
        
        # If the gene associated with this (symbol, chromosome) tuple has already been searched, get it.
        # Otherwise, search for it and record the result (Gene or Exception) in the DataManager dictionary.
        gene = all_gene_symbol_asso.get( ( symbol, chr_name ) )
        
        if ( not gene ):
            # Get the instance related to this tuple and store it in the DataManager
            # NB: See the documentation of the find_gene_from_symbol() method for more
            #     information about this step.
            ( gene, new_obj_to_insert ) = self.find_gene_from_symbol( symbol, chr_name )
            all_gene_symbol_asso[ ( symbol, chr_name ) ] = gene
                
        # If the object associated with the (symbol, chr_name) tuple in the dictionary is an exception,
        # log the appropriate GeneRefLogger warning and return the "fake" gene
        if ( not isinstance( gene, Gene ) ):
            
            if isinstance( gene, RefConflictException ):
                GeneRefLogger.get_instance().conflict_info_warning( gene.get_message() + 
                                                                    ' Hence the ORF with original ID "' + 
                                                                    orf_id + '" (from ' + self.data_source  + 
                                                                    ') will be associated with the "fake" gene "' + 
                                                                    str( gene.get_gene().gene_id ) + '".' )
                
            elif isinstance( gene, RefGeneSearchException ):
                GeneRefLogger.get_instance().gene_search_warning( gene.get_message() + 
                                                                  ' Hence the ORF with original ID "' + 
                                                                  orf_id + '" (from ' + self.data_source  +
                                                                  ') will be associated with the "fake" gene "' + 
                                                                  str( gene.get_gene().gene_id ) + '".' )
            gene = gene.get_gene()
                
        return ( gene, new_obj_to_insert )
        
        
        
    ## find_gene_from_symbol
    #  ---------------------
    #
    # This method allows to get the Gene entry related to a provided symbol or alias
    # and chromosome.
    # It first get all the entries of the Gene table that are related to the provided alias 
    # and try to find if there is one of them which is located on the chromosome.
    #
    # If there is one single gene on this chromosome, the method returns this gene.
    # If there is one single gene associated with that symbol and that is missing its chromosome name, 
    # the method updates the chromosome name of the gene, log a GeneRefLogger warning and return 
    # the updated Gene.
    # Otherwise, if no gene can be found using the provided alias, the method returns the exception.
    #
    # @param symbol: String - The symbol or alias provided in the source as being associated with this ORF.
    # @param chr_name: String - The chromosome name provided in the source for this ORF.
    #
    # @return gene: Gene, 
    #               or RefGeneUpdateException, 
    #               or RefConflictException,
    #               or RefGeneSearchException - Return the instance associated with the provided 
    #                                           gene alias and chromosome pair.
    # @return new_obj_to_insert: List - List of objects to insert if new objects have been created in 
    #                                   the process.
    #    
    @abstractmethod
    def find_gene_from_symbol( self, symbol, chr_name ):
        
        # Initialize the list of new objects that will have to be inserted
        new_obj_to_insert = []
        
        # Get the necessary information from the DataManager
        all_genes = DataManager.get_instance().get_data( Constants.DM_ALL_GENES )
        all_genealiases = DataManager.get_instance().get_data( Constants.DM_ALL_GENEALIASES )
        all_genesfromaliases = DataManager.get_instance().get_data( Constants.DM_ALL_GENESFROMALIASES )
        all_gene_id_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_ID_ASSO )
        all_gene_symbol_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_SYMBOL_ASSO )
            
        # Get all the gene IDs corresponding to this symbol using the UTGeneFromAlias table
        # To do this, instantiate a new UTGeneFromAlias object and if this UTGeneFromAlias already
        # exists (meaning there is at least a Gene and a GeneAlias entry for this symbol), get it.
        utgenefromalias = UTGeneFromAlias( alias = symbol )
        
        existing_utgenefromalias = all_genesfromaliases.get( utgenefromalias )
        
        if existing_utgenefromalias:
            utgenefromalias = existing_utgenefromalias
                        
            # Get the list of gene IDS from the string
            gene_ids = utgenefromalias.gene_ids.split( Constants.GENEFROMALIAS_SEPARATOR_IDS )
                
            # Get the list of Gene objects corresponding to these gene IDs
            list_of_genes = []
            for id in gene_ids:
                list_of_genes += all_gene_id_asso.get( id )
                    
            # If there is an unique gene located on the expected chromosome or one single gene
            # without chromosome name, get it. If this is not possible, catch the exception 
            # returned.
            # NB: See the documentation of the get_uniq_gene_on_chromosome() method for more
            #     information about this step.
            gene = ParserStrategy.get_uniq_gene_on_chromosome( chr_name, list_of_genes )
            
            if isinstance( gene, RefGeneUpdateException ):
                GeneRefLogger.get_instance().gene_update_warning( gene.get_message() +
                                                                  ' Information from ' + 
                                                                  self.data_source + '.' )
                # Get the gene associated with the exception
                gene = gene.get_gene()
                
                # Update the entries of the data manager 
                # registering this gene
                all_gene_id_asso[ gene.gene_id ] = [ gene ]
                all_genes[ gene ] = gene
                
                # Add the entry to the list of objects to add to the session
                new_obj_to_insert.append( gene )
                
            # If the object returned by the get_uniq_gene_on_chromosome() method is an other RefException, 
            # create a "fake" gene in order to keep the relational integrity of the database and store this
            # Gene instance as an attribute of the exception.
            elif ( isinstance( gene, RefConflictException ) 
                   or isinstance( gene, RefGeneSearchException ) ):
                
                # Create a "fake" gene symbol
                fake_symbol = Constants.PREFIX_UNKNOWN_GENE + symbol + '_chr' + str( chr_name )
                
                # Create a new Gene entry
                fake_gene = Gene( gene_id = fake_symbol,
                                  chromosome = chr_name )
                
                # Create a new GeneAlias entry
                genealias = GeneAlias( gene_id = fake_gene.gene_id,
                                       alias = fake_symbol,
                                       crossref = Constants.FAKE_CROSSREF )
                
                # Keep record of the new gene in the UTGeneFromAlias table
                utgenefromalias = UTGeneFromAlias( alias = fake_gene.gene_id,
                                                   gene_ids = fake_gene.gene_id )
                
                # Add the newly created Gene, GeneAlias and UTGeneFromAlias 
                # entries to the list of objects to insert
                new_obj_to_insert.append( fake_gene )              
                new_obj_to_insert.append( genealias )
                new_obj_to_insert.append( utgenefromalias )
                
                # Keep record of these new objects in the DataManager
                all_genes[ fake_gene ] = fake_gene
                all_genealiases[ genealias ] = genealias
                all_genesfromaliases[ utgenefromalias ] = utgenefromalias
                all_gene_id_asso[ fake_gene.gene_id ] = [ fake_gene ]
                all_gene_symbol_asso[ ( symbol, chr_name ) ] = fake_gene
                
                # Register this Gene instance as an attribute of the RefException
                gene.set_gene( fake_gene )
                    
                
        # Otherwise, if there is no Gene nor GeneAlias entry for this symbol, 
        # create a new Gene and GeneAlias, keep record of them and log a GeneRef warning.  
        else:
            # Log the missing reference
            GeneRefLogger.get_instance().missing_ref_warning( 'No gene has been found in the database' +
                                                              ' for the symbol / alias: "' + str( symbol ) + 
                                                              '" (alias from ' + self.data_source + ').' )
                
            # Create a new Gene entry
            gene = Gene( gene_id = symbol,
                         chromosome = chr_name )
                
            # Create a new GeneAlias entry                                  
            genealias = GeneAlias( gene_id = gene.gene_id, 
                                   alias = gene.gene_id,
                                   crossref = self.data_source )
            
            # Keep record of the new gene in the UTGeneFromAlias table
            utgenefromalias = UTGeneFromAlias( alias = gene.gene_id,
                                               gene_ids = gene.gene_id )
                                    
            # Add the newly created Gene, GeneAlias and UTGeneFromAlias instances 
            # to the list of objects to insert
            new_obj_to_insert.append( gene )
            new_obj_to_insert.append( genealias )
            new_obj_to_insert.append( utgenefromalias )
                        
            # Keep record of these new objects in the DataManager
            all_genes[ gene ] = gene
            all_genealiases[ genealias ] = genealias
            all_genesfromaliases[ utgenefromalias ] = utgenefromalias
            all_gene_id_asso[ gene.gene_id ] = [ gene ]
            all_gene_symbol_asso[ ( symbol, chr_name ) ] = gene
                
            # Log the creation of this new Gene entry
            GeneRefLogger.get_instance().new_entry_warning( 'As no gene has been found associated with symbol "' + 
                                                            symbol + '" in the database, a new Gene and' +
                                                            ' GeneAlias have been created on the chromosome ' + 
                                                            chr_name + ' using this symbol' +
                                                            ' (alias and chromosome from ' + 
                                                            self.data_source + ').' )
        
        return ( gene, new_obj_to_insert )
    
        

    ## get_uniq_gene_on_chromosome
    #  ---------------------------
    #
    # This is a static method that allows to get the only gene located (or suspected to 
    # be located) on a particular chromosome in a provided list of genes .
    # 
    # Please find below the algorithm run by this function to return the gene 
    # (or to return an exception containing an unique gene):
    # If there is one single gene in the list:
    #    - and the expected chromosome name is known:
    #        - and this single gene is missing its chromosome information, 
    #          then update the gene and return it (using a RefGeneUpdateException).
    #        - and the chromosome name of this single gene is known:
    #            - and the two chromosome names are the same, then return this gene.
    #            - and the two chromosomes names are not equal but are in fact the same 
    #                          (in a biological way: this happens when the chromosome name equals 
    #                           'X' or 'Y' while the gene chromosome equals 'X|Y', or in the opposite
    #                           situation, i.e. the chromosome name equals 'X|Y' whilst the gene 
    #                           chromosome is 'X' or 'Y'), then return this gene.
    #            - and the two chromosome names are different, then return a RefConflictException.
    #    - and the expected chromosome name is not provided, then return the gene.
    #
    # Else, if there are several genes in the list:
    #    - and there are genes which are on the expected chromosome:
    #        - and there is one single gene on the expected chromosome, then return this gene.
    #        - and there are several genes on the expected chromosome, then return a RefGeneSearchException.
    #    - and there is no gene on the expected chromosome
    #        - and the expected chromosome is 'X' or 'Y' while there are genes of the list on 'X|Y',
    #            - and there is one single gene in that list, then return this gene.
    #            - and there are several genes on the expected chromosome, 
    #              then return a RefGeneSearchException.
    #        - and the expected chromosome name is provided and there are genes missing their 
    #          chromosome information:
    #            - and there is one single gene missing its chromosome information,
    #              then update the gene and return it (through a RefGeneUpdateException).
    #            - and there are several genes missing their chromosome information, 
    #              then return a RefGeneSearchException.
    #        - and    the expected chromosome name is not provided
    #              OR there is no gene of the list missing its chromosome information, 
    #              then return a RefGeneSearchException.
    # NB: Please not that the exceptions (RefGeneUpdateException, RefConflictException and 
    #     RefGeneSearchException) are returned by this method and NOT raised!
    #
    #
    # @param chr: String - The chromosome name of the expected location of the gene.
    # @param list_of_genes: List of Gene objects - The list of genes to search in.
    #
    # @return Gene - The instance corresponding to the single gene located on the expected chromosome.
    # @return RefGeneUpdateException: When one single gene missing its chromosome information is found, 
    #                                 then this location is updated using the expected location.
    # @return RefConflictException: When there is one single gene is in the list and its chromosome 
    #                               location does not match the expected one.
    # @return RefGeneSearchException: When there are several genes on the expected chromosome.
    # @return RefGeneSearchException: When there is no gene on the expected chromosome and.
    #                                 several missing their chromosome name.
    # @return RefGeneSearchException: When there is no gene on the expected chromosome and 
    #                                 no one missing its chromosome name.
    #       
    @staticmethod
    def get_uniq_gene_on_chromosome( chr, list_of_genes ):
        
        # If there is a single gene in the list, then get it first,
        if ( len( list_of_genes ) == 1 ):
            gene = list_of_genes[ 0 ]
            
            # If the expected chromosome of the gene is known,
            if ( chr != None ):
                # and if this single gene is missing its chromosome information, then update it using the 
                # expected location and return a RefGeneUpdateException
                if ( gene.chromosome == None ):
                    gene.chromosome = chr
                    return RefGeneUpdateException( 'The gene with ID "' + str( gene.gene_id ) + 
                                                   '" was missing its chromosome information.' +
                                                   ' This gene has been associated with chromosome ' + 
                                                   chr + '.', 
                                                   gene = gene )
                    
                # Else, if this single gene has a chromosome information
                else:
                    # and this chromosome is the same as the expected one, then return the gene
                    if ( gene.chromosome == chr ):
                        return gene
                    
                    # and this chromosome does not equal the expected one but is in fact the same 
                    # (as it is equal to X or Y),
                    # then return the gene
                    elif ( ( ( chr == Constants.CHROMOSOME_X ) 
                             or ( chr == Constants.CHROMOSOME_Y ) 
                             or ( chr == Constants.CHROMOSOME_NAME_XY ) )
                            and ( gene.chromosome == Constants.CHROMOSOME_NAME_XY ) ):
                        return gene
                    
                    # and this chromosome does not equal the expected one but is in fact the sexual 
                    # chromosome and the chromosome registered in the gene entry is X or Y
                    elif ( ( chr == Constants.CHROMOSOME_NAME_XY )
                           and ( ( gene.chromosome == Constants.CHROMOSOME_Y )
                                 or ( gene.chromosome == Constants.CHROMOSOME_X ) ) ):
                        # Update the gene to change X or Y by the sexual chromosome (X|Y)
                        exception_message = ( 'The gene with ID "' + str( gene.gene_id ) + 
                                              '" is located on the sexual chromosome (' +
                                              str( chr ) + ') while it was previously registered on' +
                                              ' the chromosome ' + str( gene.chromosome ) + 
                                              ' in the database. Hence, the chromosome of this gene has' +
                                              ' been set to ' + str( chr ) + '.' )
                        gene.chromosome = Constants.CHROMOSOME_NAME_XY
                        return RefGeneUpdateException( exception_message,
                                                       gene = gene )
                        
                    # otherwise, if the two chromosomes are different, then return a RefConflictException
                    else:
                        return RefConflictException( 'The gene with ID "' + str( gene.gene_id ) + 
                                                     '" is located on chromosome ' +
                                                     str( gene.chromosome ) + ' according to the Gene table' +
                                                     ' while it was expected to be on chromosome ' + str( chr ) + 
                                                     ' according to the data parsed.' )
            
            # Otherwise, if the expected location of the gene is not known, return this gene
            else:
                return gene
        
                
        # Else, if there are several genes in the list, then first create a dictionary that 
        # associate with each chromosome names and the lists of genes
        else:
            genes_chr_asso = {}
            for g in list_of_genes:
                if ( g.chromosome not in genes_chr_asso.keys() ):
                    genes_chr_asso[ g.chromosome ] = [ g ]
                else:
                    genes_chr_asso[ g.chromosome ].append( g )
                    
            # If there are genes of the list located on the expected chromosome,
            if ( chr in genes_chr_asso.keys() ):
                # If there is one single gene on the expected chromosome, return it
                if ( len( genes_chr_asso[ chr ] ) == 1 ):
                    return genes_chr_asso[ chr ][ 0 ]
                
                # If there are several genes on the expected chromosome, then return a RefGeneSearchException
                else:
                    if ( chr != None ):
                        return RefGeneSearchException( 'Several genes of the list have been found on the' +
                                                       ' chromosome ' + chr + '.' )
                    else:
                        return RefGeneSearchException( 'The expected location of the gene was not provided and' +
                                                       ' several genes of the list have been found without any' +
                                                       ' chromosome information.' )
                    
            # If there is no gene of the list on the expected chromosome
            else:
                # and the expected chromosome is 'X' or 'Y' while are genes 
                # located on 'X|Y' according to the list
                if ( ( ( chr == Constants.CHROMOSOME_X ) or ( chr == Constants.CHROMOSOME_Y ) ) 
                     and ( Constants.CHROMOSOME_NAME_XY in genes_chr_asso.keys() ) ):
                    # and there is one single gene on 'X|Y', then return it
                    if ( len( genes_chr_asso[ Constants.CHROMOSOME_NAME_XY ] ) == 1 ):
                        return genes_chr_asso[ Constants.CHROMOSOME_NAME_XY ]
                    
                    # and there are several genes on 'X|Y', then return a RefGeneSearchException
                    else:
                        return RefGeneSearchException( 'Several genes of the list have been found on the' +
                                                       ' chromosome ' + Constants.CHROMOSOME_NAME_XY + '.' )
                
                # and the expected chromosome is provided, and there are genes 
                # missing their chromosome information 
                elif ( ( chr != None ) and ( None in genes_chr_asso.keys() ) ):
                    # and there is one single gene missing its chromosome information, 
                    # then update this gene and return a RefGeneUpdateException
                    if len( genes_chr_asso[ None ] ) == 1:
                        gene = genes_chr_asso[ None ][ 0 ]
                        gene.chromosome = chr
                        return RefGeneUpdateException( 'The gene with ID "' + str( gene.gene_id ) + 
                                                       '" was missing its chromosome information.' +
                                                       ' This gene has been associated with chromosome ' + 
                                                       chr + '.', 
                                                       gene = gene )
                    
                    # and there are several genes missing their chromosome information,
                    # then return a RefGeneSearchException
                    else:
                        return RefGeneSearchException( 'No gene of the lis was located on chromosome ' + 
                                                       chr + ' and there were several genes of the list' +
                                                       ' missing their chromosome information.' )
                
                # and the expected chromosome is not provided
                #     OR there is no gene missing their chromosome information,
                #     then return a RefGeneSearchException
                else:
                    if ( chr == None ):
                        return RefGeneSearchException( 'The expected chromosome name has not been provided' +
                                                       ' and there was no gene missing its chromosome information.' )
                    else:
                        return RefGeneSearchException( 'No gene of the list has been found on the expected' +
                                                       ' chromosome (' + chr + ') and no gene of the list' +
                                                       ' was missing its chromosome information.' )
    
                        
    
    ## get_gene_from_conflict_id
    #  -------------------------
    #
    # This method allows to get the unique Gene entry associated with a particular "fake" gene ID
    # that have been created due to a conflict found on the gene ID / symbol during the merging of 
    # two DSTranscript. 
    # In order to reduce the computation time, all pairs (fake gene ID, chromosome) that 
    # have already been created are saved in a dictionary of the DataManager main dictionary. 
    # The instances are saved in this dictionary with associate to each unique (symbol, chromosome) 
    # key the correspond Gene. If this association has never been met before, new entries are
    # created in the Gene, GeneAlias and UTGeneFromAlias tables.
    #
    # @param conflict_symbol: String - The "conflict" symbol of the gene (without its chromosome name).
    # @param chr_name: String - The chromosome name on which the transcript is located.
    #
    # @return gene: Gene - Return the Gene object associated with the provided conflict symbol 
    #                      and chromosome.
    # @return new_obj_to_insert: List - List of objects to insert if new objects have been created
    #                                   in the process.
    # 
    @abstractmethod
    def get_gene_from_conflict_id( self, conflict_symbol, chr_name ):
        
        # If the chromosome is known, add it to the name of the "conflict" symbol
        if ( not ParserStrategy.is_empty( chr_name ) ):
            conflict_symbol = conflict_symbol + '_chr_' + chr_name
        else:
            conflict_symbol = conflict_symbol + '_chr_UNKNOWN'
        
        # Initialize the list of new objects that will have to be inserted
        new_obj_to_insert = []
        
        # Get the necessary information from the DataManager
        all_gene_symbol_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_SYMBOL_ASSO )
        
        all_genes = DataManager.get_instance().get_data( Constants.DM_ALL_GENES )
        all_genealiases = DataManager.get_instance().get_data( Constants.DM_ALL_GENEALIASES )
        all_genesfromaliases = DataManager.get_instance().get_data( Constants.DM_ALL_GENESFROMALIASES )
        all_gene_id_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_ID_ASSO )
        all_gene_symbol_asso = DataManager.get_instance().get_data( Constants.DM_ALL_GENE_SYMBOL_ASSO )
        
        # If this "conflict" symbol has already been created get it
        existing_gene = all_gene_symbol_asso.get( ( conflict_symbol, chr_name ) )
        
        # Otherwise, create a new entry in the Gene, GeneAlias and UTGeneFromAlias tables and log it
        if not existing_gene:
                
            # Create a new Gene entry
            gene = Gene( gene_id = conflict_symbol,
                         chromosome = chr_name )
                
            # Create a new GeneAlias entry
            genealias = GeneAlias( gene_id = gene.gene_id, 
                                   alias = gene.gene_id,
                                   crossref = self.data_source )
            
            # Keep record of the new gene in the UTGeneFromAlias table
            utgenefromalias = UTGeneFromAlias( alias = gene.gene_id,
                                               gene_ids = gene.gene_id )
            
            # Add the newly created Gene, GeneAlias and UTGeneFromAlias entries to the list of objects to insert
            new_obj_to_insert.append( gene )
            new_obj_to_insert.append( genealias )
            new_obj_to_insert.append( utgenefromalias )
            
            # Keep record of these new objects in the DataManager
            all_genes[ gene ] = gene
            all_genealiases[ genealias ] = genealias
            all_genesfromaliases[ utgenefromalias ] = utgenefromalias
            all_gene_id_asso[ gene.gene_id ] = [ gene ]
            all_gene_symbol_asso[ ( conflict_symbol, chr_name ) ] = gene
                
            # Log the creation of this new gene
            GeneRefLogger.get_instance().new_entry_warning( 'A new Gene and GeneAlias entries have been' +
                                                            ' created on chromosome ' + chr_name +
                                                            ' for the "conflicting" gene with gene ID "' + 
                                                            conflict_symbol + ' (conflict found in ' + 
                                                            self.data_source + ').' )
            
        else:
            gene = existing_gene
                
        return ( gene, new_obj_to_insert )
        