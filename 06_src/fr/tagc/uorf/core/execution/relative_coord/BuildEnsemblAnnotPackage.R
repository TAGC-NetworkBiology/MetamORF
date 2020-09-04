#!/usr/local/bin/R

library( getopt )
suppressMessages( library( devtools, verbose = FALSE ) )
suppressMessages( library( AnnotationHub, verbose = FALSE ) )
suppressMessages( library( ensembldb, verbose = FALSE ) )


# This script aims to build an compatible annotation package 
# for the Ensembl release that has to be used to perform 
# the conversion of absolute genomic coordinates into transcript 
# relative coordinates and that may be read by ensembldb.


# ===============================================================================
# Parse the command-line arguments
# ===============================================================================

# List of available options
option_list = list(
  c( 'ensemblRelease', 'e', '', 'character' ),
  c( 'speciesFullName', 'n', '', 'character' ),
  c( 'speciesShortName', 's', '', 'character' ),
  c( 'speciesCommonName', 'c', '', 'character' ),
  c( 'annotPackageDir', 'd', '', 'character' ),
  c( 'help', 'h', 0, 'logical' )
)

option_matrix = matrix( unlist( option_list ),
                        byrow = TRUE, 
                        nrow = length( option_list ) )
                    
# Get the provided arguments
opt = getopt( option_matrix )

# Print help if necessary
if ( ! is.null( opt$help ) ){
  stop( getopt( option_matrix, usage=TRUE ) )
}

# Get the ensembl version
if ( ! is.null( opt$ensemblRelease ) ){
  ensembl_release = as.numeric( opt$ensemblRelease )
}

# Get the species full scientific name (e.g. Homo sapiens)
if ( ! is.null( opt$speciesFullName ) ){
  species_full_name = as.character( opt$speciesFullName )
}

# Get the species short scientific name (e.g. Hsapiens)
if ( ! is.null( opt$speciesShortName ) ){
  species_short_name = as.character( opt$speciesShortName )
}

# Get the species common name (e.g. human)
if ( ! is.null( opt$speciesCommonName ) ){
  species_common_name = opt$speciesCommonName
}

# Get the directory where to eventually 
# create the annotation package
if ( ! is.null( opt$annotPackageDir ) ){
  annot_package_directory = opt$annotPackageDir
}



# ===============================================================================
# Build the appropriate R annotation package
# ===============================================================================

# Define the names of the package
annot_package = paste0( 'EnsDb.', species_short_name, '.v', ensembl_release )
load_annot_package = paste0( 'library(', annot_package, ')' )

print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: The package ', annot_package, 
               ' will be prepared to be used during the computation of relative coordinates.' ) )


# Try to load the package if possible
# If not build it, and finally load it
tryCatch(
           {             
             print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: Trying to load the R package ', 
                            annot_package, '.' ) )
             eval( parse( text = load_annot_package ) )
           },
           error=function(cond) {
             # Try to build the package using an existing AnnotationHub
             # NB: If the package cannot be loaded from AnnotationHub, then a new
						 #     package could be created by fetching the Ensembl database.
      			 #		 This could be done using the fetchTablesFromEnsembl fucntion 
      			 #		 the ensembldb package. This function needs the Ensembl Perl API
      			 #		 installed to work properly. Nevertheless, as this API is currently 
      			 #		 experiencing issues, this option has not been implemented in the current script.
      			 # 		 If you want to do so, then you need to use the following commands:
      			 #	   ```
      			 #	   # Define a fetch_tables_tmp_directory variable containing the path to
      			 #		 # the directory where the tables from Ensembl have to be fetched.
      			 #		 # Move to the temporary directory where to fetch the Ensembl database
      			 #		 setwd( fetch_tables_tmp_directory )
      			 #		 # Fetch the database from Ensembl
      			 #     fetchTablesFromEnsembl( version = ensembl_release,
      			 #														 ensembl_api = '/usr/bin/ensembl/modules',
      			 #														 species = species_common_name )
      			 #		 # Make a SQLite file from the tables
      			 #		 DBFile = makeEnsemblSQLiteFromTables()
      			 #		 # Generate the package
      			 #		 makeEnsembldbPackage( ensdb = DBFile,
      			 #		 											 destDir = annot_package_directory,
      			 #		 											 version = "1.0.0",
      			 #		 											 author = "Sébastien A. Choteau"
      			 #		 											 maintainer = "Sébastien A. Choteau <sebastien.choteau@univ-amu.fr>" )
      			 #		 # Move to the package directory, build and install the package
      			 #		 setwd( file.path( annot_package_directory, annot_package )
      			 #		 build()
      			 #		 install()
      			 #		 ```
      			 #     You may consult the revision 36 of the current file for an example.      
             print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: The package ', annot_package, 
                            ' cannot be loaded. It is probably missing and will be created in the',
                            ' directory ', annot_package_directory, 
                            ' and installed using AnnotationHub and ensembldb R packages.' ) )
                    
             # Load all AnnotationHub
             ah = AnnotationHub()
            
             # Query AnnotationHub to get the appropriate database
             ahDb = query( ah, pattern = c( species_full_name, 'EnsDb', ensembl_release ) )
             
             # Convert AnnotationHub information into a data frame
             ahDb_info_df = as.data.frame( mcols( ahDb ) )
             
             # Get the entry corresponding to the appropriate database
             # by checking Ensembl version and species name
             ahDb_info_df = ahDb_info_df[ which( grepl( ensembl_release, ahDb_info_df$title, ignore.case = TRUE ) ), ]
             ahDb_info_df = ahDb_info_df[ which( grepl( species_full_name, ahDb_info_df$title, ignore.case = TRUE ) ), ]
             if ( dim( ahDb_info_df )[1] != 1 ){
               print( paste0( 'CRITICAL :: BuildEnsemblAnnotPackage.R :: ', dim( ahDb_info_df ), 
                              ' AnnotationHubs have been found for ', species_full_name,
                              ' Ensembl release ', ensembl_release, '.',
                              ' If this error is happening, then the code of the', 
                              ' BuildEnsemblAnnotPackage.R script has to be implemented to perform',
                              ' the download of Ensembl databases in such case. Please see the',
                              ' documentation of this script for more information.' ) )
             }
             ahDb_appropriate_ah = rownames( ahDb_info_df )[1]
             
             # Get the ensembl database
             ahEdb = ahDb[[ ahDb_appropriate_ah ]]
            
             # Make a package from the ensembl database
             # NB: If the DESCRIPTION file of this package may be found, 
             #		 then it means the library has probably been deleted 
             # 		 but not the source code of the package. Then skip the
             #     creation of the package.
             if ( ! file.exists( file.path( annot_package_directory, annot_package, 'DESCRIPTION' ) ) ){
               print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: Making the package...' ) )
               makeEnsembldbPackage( ensdb =  dbfile( dbconn( ahEdb ) ), 
                                     destDir = file.path( annot_package_directory ), 
                                     version = "1.0.0", 
                                     author = "Sebastien Choteau", 
                                     maintainer = "Sebastien A. Choteau <sebastien.choteau@univ-amu.fr>" )
             }
                                            
             # Move to the package directory, build and install the package
             setwd( file.path( annot_package_directory, annot_package ) )
             print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: Building the package...' ) )
             build()
             print( paste0( 'DEBUG :: BuildEnsemblAnnotPackage.R :: Installing the package...' ) )
             install()                          
           },
           finally={
             eval( parse( text = load_annot_package ) )
           }
        )
        