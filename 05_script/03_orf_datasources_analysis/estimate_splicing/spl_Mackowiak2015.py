# -*- coding: utf-8 -*-

import pandas as pd


import constants


# Constants
FILE_SEP = '\t'
HEADER_START = 'CDS_start'
HEADER_STOP = 'CDS_end'
HEADER_ORF_LEN = 'length'


def Mackowiak2015( data_path ):
	
	# Reading the first rows of the file
	csv_content = pd.read_csv( data_path, 
								sep = FILE_SEP, 
								dtype = 'str', 
								encoding = 'utf-8', 
								nrows = constants.NB_ROWS )
	
	# Get the total number of rows for which length is computed
	total_count = csv_content.shape[ 0 ]
	
	# Count the number of rows for which the genomic length equals the ORF length
	equal_len_count = 0
	equal_approx = 0
	below_max_nt = 0
	
	for ( index, row ) in csv_content.iterrows():
	
		# Compute the genomic length (in nucleotides)
		start = row[ HEADER_START ]
		stop = row[ HEADER_STOP ]
		gen_len = abs( int( stop ) - int( start ) )
	
		# Get the reported length (in nucleotides)
		orf_len = row[ HEADER_ORF_LEN ]
		orf_len_nt = int( orf_len ) * 3 + 3
		
		# Add 1 to the equal_len_count if the genomic length equals the reported one
		if ( orf_len_nt == gen_len ):
			equal_len_count += 1
		elif ( abs( gen_len - orf_len_nt ) <= constants.DIFF_MAX ):
			equal_approx += 1
	    
	    # Add 1 to the equal_len_count if the genomic length equals the reported one
		if ( gen_len < constants.MAX_LEN ):
			below_max_nt += 1
			
	return ( total_count, equal_len_count, equal_approx, below_max_nt )
