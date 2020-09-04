# -*- coding: utf-8 -*-

import pandas as pd

import constants


# Constantsequal_len_count
FILE_SEP = '\t'
HEADER_START = 'start_coordinate'
HEADER_STOP = 'end_coordinate'


def McGillivray2018( data_path ):
	
	# Reading the first rows of the file
	csv_content = pd.read_csv( data_path, 
								sep = FILE_SEP, 
								dtype = 'str', 
								encoding = 'utf-8', 
								nrows = constants.NB_ROWS)
	
	# Get the total number of rows for which length is computed
	total_count = csv_content.shape[ 0 ]
	
	# Count the number of rows for which the genomic length is below a threshold
	equal_len_count = 'NA'
	equal_approx = 'NA'
	below_max_nt = 0
	
	for ( index, row ) in csv_content.iterrows():
	
		# Compute the genomic length (in nucleotides)
		start = row[ HEADER_START ]
		stop = row[ HEADER_STOP ]
		gen_len = abs( int( stop ) - int( start ) )
		
		# Add 1 to the below_max_nt if the genomic length equals the reported one
		if ( gen_len < constants.MAX_LEN ):
			below_max_nt += 1
			
	
				
	return ( total_count, equal_len_count, equal_approx, below_max_nt )
