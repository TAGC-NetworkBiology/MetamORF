# -*- coding: utf-8 -*-

from pyensembl import EnsemblRelease
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger


## EnsemblUtil
#  ===========
#
# This class contains various static methods related to 
# pyensembl which aims to facilitate its use.
#
class EnsemblUtil( object ):
    
    
    ## get_ensembl_db
    #  --------------
    # 
    # This is a static method allowing to download the appropriate Ensembl database 
    # or a particular species and a genome annotation version. 
    # This database may be queried by several processes, e.g. to recover the name of
    # a gene related to a particular Ensembl transcript ID or the features overlapping 
    # with some genomic coordinates. The EnsemblRelease object are used by several 
    # strategies including the Insertion strategy.
    #
    # @param sp: String - The full name of the species, as expected by pyensembl 
    #                     (e.g. homo_sapiens).
    # @param annotation_version: String or Integer - The Ensembl annotation version.
    #
    # @return ensembl_db: EnsemblRelase object - The EnsemblRelease object.
    #
    # @throw DenCellORFException: When an exception has been raised trying to download
    #                             or index the Ensembl database.
    #
    @staticmethod
    def get_ensembl_db( sp, annotation_version ):
        
        Logger.get_instance().debug( 'EnsemblUtil.get_ensembl_db(): Downloading and indexing the Ensembl' +
                                     ' database release ' + str( annotation_version ) + 
                                     ' for ' + sp + '.' )
        
        ensembl_db = EnsemblRelease( release = annotation_version,
                                     species = sp )
        
        # Download and index the database if not yet in the temporary folder
        Logger.get_instance().debug( 'EnsemblUtil.get_ensembl_db(): Downloading the Ensembl' +
                                     ' database release ' + str( annotation_version) + 
                                     ' for ' + sp + '.' )
        try:
            ensembl_db.download()
        except Exception as e:
            raise DenCellORFException( 'EnsemblUtil.get_ensembl_db(): An error occurred trying to' +
                                       ' download the Ensembl database using pyensembl.', e )
            
        
        Logger.get_instance().debug( 'EnsemblUtil.get_ensembl_db(): Indexing the Ensembl' +
                                     ' database release ' + str( annotation_version) + 
                                     ' for ' + sp + '.' )
        try:
            ensembl_db.index()
        except Exception as e:
            raise DenCellORFException( 'EnsemblUtil.get_ensembl_db(): An error occurred trying to' +
                                       ' index the Ensembl database using pyensembl.', e )
        
        return ensembl_db
    