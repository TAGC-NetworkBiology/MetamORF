
## This script allows to download the lists of cross references
#  from Ensembl databases (using biomaRt) for species:
#  - H. sapiens
#  - M.musculus
species = c( 'hsapiens', 'mmusculus' )


# Get the path to the output directory from the DefaultOutputFolder.txt file
# NB: This file is expected to contain the OUTPUT_DIR variable
source( "./DefaultOutputFolder.txt" )
file.path( OUTPUT_DIR, "Ensembl")


# Load libraries
library( "biomaRt" )


# Creates the output directory if necessary
if ( ! dir.exists( OUTPUT_DIR ) ){
    dir.create( OUTPUT_DIR )
}


# Query the Ensembl BioMart databases
ensembl = useMart( "ensembl" )

print( '----' )

for ( sp in species ){

    print( paste0(Sys.time(), ':: Starting to download cross-references from Ensembl for ', sp, '.' ) )

    # Download the Ensembl dataset
    dataset = useDataset( paste0( sp, "_gene_ensembl" ), mart=ensembl )

    # Query the datasets to get useful information
    # NB: The list of attributes may be obtained using: listAttributes(dataset)
    print( paste0( Sys.time(), ':: Starting to query of database.' ) )

    # Genes reported to be on a chromosome different than "1"-"23", "X" or "Y" are excluded
    chr = seq( 1, 23, 1 )
    for (c in chr){
        c = toString( c )
    }
    chr = c( chr, "X", "Y", "x", "y" )

    # Get the gene ID references in Ensembl databases
    # NB: Due to limitations set by biomaRt, several querries are performed
	#     instead of a single one Get Ensembl IDs (ENSG)
    GeneList = getBM( attributes = c( "ensembl_gene_id", "chromosome_name" ),
            		  filters = "chromosome_name",
            		  values = chr,
            		  mart = dataset )

            # Exporting data in a CSV file
            output_file = file.path( OUTPUT_DIR, paste0( sp, "_Ensembl_", "Ensembl", ".csv" ) )
    		print( paste0( Sys.time(), ':: Ensembl gene IDs for ', sp,
							' will be written in: ', output_file, '.' ) )
    		write.csv( GeneList, file=output_file, row.names=FALSE )


        # Get the gene IDs from Entrezdirect (NCBI)
    GeneList = getBM( attributes = c( "ensembl_gene_id", "entrezgene", "chromosome_name" ),
					  filters = "chromosome_name",
					  values = chr,
					  mart = dataset)

            # Exporting data in a CSV file
            output_file = file.path( OUTPUT_DIR, paste0( sp, "_Ensembl_", "NCBI", ".csv" ) )
    		print( paste0( Sys.time(), ':: Cross references Ensembl - NCBI gene IDs for ', sp,
							' will be written in: ', output_file, '.' ) )
    		write.csv( GeneList, file=output_file, row.names=FALSE )

        # Get the gene IDs from the HGNC
    GeneList = getBM( attributes = c( "ensembl_gene_id", "hgnc_id", "hgnc_symbol", "chromosome_name" ),
					  filters = "chromosome_name",
					  values = chr,
					  mart = dataset)

            # Exporting data in a CSV file
            output_file = file.path( OUTPUT_DIR, paste0( sp, "_Ensembl_", "HGNC", ".csv" ) )
    		print( paste0( Sys.time(), ':: Cross references Ensembl - HGNC for ', sp,
							' will be written in: ', output_file, '.' ) )
    		write.csv( GeneList, file=output_file, row.names=FALSE )

        # Get the gene IDs from the MGI for M. musculus
    if (sp == "mmusculus"){
        GeneList = getBM( attributes = c( "ensembl_gene_id", "mgi_id", "mgi_symbol", "chromosome_name" ),
						  filters = "chromosome_name",
						  values = chr,
						  mart = dataset )

            # Exporting data in a CSV file
            output_file = file.path( OUTPUT_DIR, paste0( sp, "_Ensembl_", "MGI", ".csv" ) )
    		print( paste0( Sys.time(), ':: Cross references Ensembl - MGI for ', sp,
							' will be written in: ', output_file, '.' ) )
    		write.csv( GeneList, file=output_file, row.names=FALSE )
    }

        # Get the gene IDs from external sources
    GeneList = getBM( attributes = c("ensembl_gene_id", "external_gene_name", "external_gene_source", "chromosome_name" ),
					  filters = "chromosome_name",
					  values = chr,
					  mart = dataset)

            # Exporting data in a CSV file
            output_file = file.path( OUTPUT_DIR, paste0( sp, "_Ensembl_", "OtherSource", ".csv" ) )
    		print( paste0( Sys.time(), ':: Cross references Ensembl - other external sources for ', sp,
							' will be written in: ', output_file, '.' ) )
    		write.csv( GeneList, file=output_file, row.names=FALSE )

    print( paste0( Sys.time(), ':: Download of cross-references from Ensembl for ',
					sp, ' has finished.' ) )

}
