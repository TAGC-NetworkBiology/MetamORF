#!/usr/local/bin/R

library( getopt )
suppressMessages( library( ensembldb, verbose = FALSE ) )


# ===============================================================================
# Functions
# ===============================================================================

# ConvertAbsoluteCoord
# --------------------
#
# This function allows to convert coordinates provided 
# as absolute genomic start and end coordinates into a 
# relative transcript coordinates.
#
# @param chr: Charcter - The chromosome name.
# @param abs_start_pos: Numeric - The absolute start position.
# @param abs_end_pos: Numeric - The absolute end position.
# @param transcript_id: Character - The transcript harboring the feature for which 
#																		the absolute position has to be converted.
# @param edb: ensembldb - The appropriate ensembldb annotation package.
#
# @return rel_pos: Numeric - The relative position of the feature get after conversion.
#														 NaN is returned if the conversion failed.
#
ConvertAbsoluteCoord = function( chr, abs_start_pos, abs_end_pos, transcript_id, edb ){
    
  # Build a GRange object to be used by ensembldb package
  gnm = GRanges( paste0( chr, ':', abs_start_pos, '-', abs_end_pos ) )

  # Convert the absolute coordinates
  gnm_tx = genomeToTranscript( gnm, edb )
  
  # Convert the IRange object into a data frame
  gnm_tx_df = as.data.frame( gnm_tx )
  
  # Extract the row containing the appropriate transcript
  gnm_tx_df = gnm_tx_df[ which( gnm_tx_df[ , 'tx_id' ] == transcript_id ), ]
  
  # Get the relative coordinates
  rel_start_pos = gnm_tx_df[ 1, 'start' ]
  rel_end_pos = gnm_tx_df[ 1, 'end' ]
  
  return( c( rel_start_pos, rel_end_pos ) )

}



# ===============================================================================
# Parse the command-line arguments
# ===============================================================================

# List of available options
option_list = list(
  c( 'ensembl', 'e', '', 'character' ),
  c( 'species', 's', '', 'character' ),
  c( 'csvFile', 'c', '', 'character' ),
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

# Get the species name (at Ensembldb format)
# NB: The species has to be provided as species scientific 
#     short name, such as 'Hsapiens'
if ( ! is.null( opt$species ) ){
  species = opt$species
}

# Get the ensembl version
if ( ! is.null( opt$ensembl ) ){
  ensembl_release = as.numeric( opt$ensembl )
}

# Get the path to the CSV file
if ( ! is.null( opt$csvFile ) ){
  csvFile = opt$csvFile
}


# ===============================================================================
# Compute the relative coordinates
# ===============================================================================

# Try to load the appropriate annotation package
annot_package = paste0( 'EnsDb.', species, '.v', ensembl_release )

# Get the appropriate Ensembl database
eval( parse( text = paste0( 'library(', annot_package, ')' ) ) )

edb = eval( parse( text = annot_package ) )


# Import data frame
df = read.table( file = csvFile,
                 header = TRUE,
                 sep = ',',
                 encoding = 'UTF-8' )


# Convert the absolute start and end coordinates 
# into relative coordinates
relative_coord = apply( df, 1, 
                        function(x) ConvertAbsoluteCoord( x[ 'chromosome' ], 
                                                          x[ 'start_pos' ], 
                                                          x[ 'end_pos' ], 
                                                          x[ 'tr_id' ], 
                                                          edb ) )

df$rel_start_pos = relative_coord[ 1, ]
df$rel_end_pos = relative_coord[ 2, ]


# Export data frame (overwrite the existing CSV file)
write.table( df, 
             file = csvFile, 
             append = FALSE,
             sep = ',',
             col.names = TRUE,
             row.names = FALSE )
