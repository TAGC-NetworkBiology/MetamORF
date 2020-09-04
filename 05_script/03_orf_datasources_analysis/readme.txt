
Quantifying the occurrence of splicing in ORFs
----------------------------------------------

Related folder: 'estimate_splicing'

The scripts located in the 'estimate_splicing' folder allow to compute, for a subset
of the ORF datasources (the n-th first lines, as defined in the 'constants.py' file),
their expected length using their genomic coordinates (hence, assuming there is not
any splicing, as this information is not clearly provided in the metadata or files 
associated with the publications). Then, the scripts compare the computed genomic 
length to the one provided by the data source. 
The logs provide for each datasource: 
- the number and the proportion of entries for which the computed length equals the one 
  provided,
- the number and proportion of entries for which the (absolute) difference between computed
  length and the one provided is below a particular value (6 by default),
- the number and proportion of entries for which the computed length is below a provided
  thereshold (300 by default).

To generate the log file, run the 'main.py' script of the 'estimate_splicing' folder.

