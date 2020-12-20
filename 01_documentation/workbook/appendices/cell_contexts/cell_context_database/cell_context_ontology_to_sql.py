# -*- coding: utf-8 -*-

from optparse import OptionParser
import pandas as pd


# The following script is a small util that allows to generate a sql file 
# easily from the cell context file. This SQL file intends to be used to 
# fill in the CellContext database.


# ===============================================================================
# Constants
# ===============================================================================

# Path to the input csv file
INPUT_FILE_PATH_OPTION = 'INPUT_FILE_PATH'

# Path to the output sql file
OUTPUT_FILE_PATH_OPTION = 'OUTPUT_FILE_PATH'

OPTION_LIST = [ [ '-i', '--input', 'store', 'string', INPUT_FILE_PATH_OPTION, None, 'The path to the input csv file.' ],
                [ '-o', '--output', 'store', 'string', OUTPUT_FILE_PATH_OPTION, None, 'The path to the output sql file.' ] ]


# Association between the ontology database short and full names
ONTOLOGY_DB = {
                'EFO': 'Experimental Factor Ontology',
                'BAO': 'BioAssay Ontology',
                'BTO': 'The BRENDA Tissue Ontology (BTO)',
                'OMIT': 'Ontology for MIRNA Target',
                'CLO': 'Cell Line Ontology',
                'NCIT': 'NCI Thesaurus OBO Edition',
                'HCAO': 'Human Cell Atlas Ontology',
                'CL': 'Cell Ontology',
                'OBI': 'Ontology for Biomedical Investigations',
                'FMA': 'Foundational Model of Anatomy Ontology'
              }



# ===============================================================================
# SQL statements
# ===============================================================================

SQL_CREATE_TABLES = \
"""
CREATE TABLE Ontology
(
    short_name VARCHAR(255) PRIMARY KEY NOT NULL,
    full_name VARCHAR(255)
);

CREATE TABLE CellContext
(
    cell_context VARCHAR(255) PRIMARY KEY NOT NULL,
    description LONGTEXT
);

CREATE TABLE CellContextOntologyAsso
(
    cell_context VARCHAR(255) NOT NULL,
    ontology VARCHAR(255) NOT NULL,
    id VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL,
    CONSTRAINT cellContextOntologyAsso_PK PRIMARY KEY ( cell_context, ontology ),
    FOREIGN KEY ( cell_context ) REFERENCES CellContext( cell_context ),
    FOREIGN KEY ( ontology ) REFERENCES Ontology( short_name )
);
"""

SQL_INSERT_ONTOLOGY = \
"""
INSERT INTO Ontology (short_name, full_name)
VALUES
{values};
"""
                      
SQL_INSERT_CELL_CONTEXT = \
"""
INSERT INTO CellContext (cell_context, description)
VALUES
{values};
"""
                      
SQL_INSERT_CELL_CONTEXT_ONTO_ASSO = \
"""
INSERT INTO CellContextOntologyAsso (cell_context, ontology, id, url )
VALUES
{values};
"""



# ===============================================================================
# Scripts
# ===============================================================================



def generate_sql( input_file_path, output_file_path ):
    
    # Create the SQL file
    with open( output_file_path, 'w' ) as output_file:
        
        # Generate the sql file to create the appropriate tables
        # ------------------------------------------------------
        output_file.write( SQL_CREATE_TABLES )
        
        
        # Fill in the Ontology table
        # --------------------------
        ontology_table_values = ''
        ontology_db_short_names = ONTOLOGY_DB.keys()
        for short_name  in ontology_db_short_names:
            
            full_name = ONTOLOGY_DB.get( short_name )
            
            print( 'New Ontology entry: ', short_name, full_name )
            ontology_table_values += '("' + short_name + '","' + full_name + '")'
            
            if ( short_name != ontology_db_short_names[ -1 ] ):
                ontology_table_values += ','
            
        output_file.write( SQL_INSERT_ONTOLOGY.format( values = ontology_table_values ) )
        
        
        # Fill in the CellContext and CellContextOntologyAsso tables
        # ----------------------------------------------------------
        
        # Get the content of the file containing the cross-references
        csv_file_content = pd.read_csv( input_file_path,
                                        sep = ',',
                                        dtype = 'str',
                                        encoding = 'utf-8' )
        
        # Replace NA values by None
        csv_file_content = csv_file_content.where( pd.notnull( csv_file_content ), None )
        
        cell_context_table_values = ''
        cell_context_ontology_asso_values = ''
        
        # Parse the file line by line
        cell_context_count = csv_file_content.shape[ 0 ]
        
        for ( index, row ) in csv_file_content.iterrows():
            
            # Get the cell context and its description
            cell_context = row[ 'CellContext' ]
            description = row[ 'Description' ]
            
            # Add a new entry to the CellContext table
            print( 'New CellContext entry: ', cell_context, description )
            cell_context_table_values += '("' + cell_context + '","' + description + '")'
            
            if ( index != cell_context_count -1 ):
                cell_context_table_values += ','
            
            
            # For each ontology, get the ID and URL to the ontology term
            for short_name  in ontology_db_short_names:
                
                id = row[ short_name ]
                url = row[ short_name + '_URL' ]
                
                if ( id != None ):
                    print( 'New CellContextOntologyAsso entry: ', cell_context, short_name, id, url )
                    cell_context_ontology_asso_values += ( '("' + cell_context + '","' + 
                                                                 short_name + '","' +
                                                                 id + '","' + 
                                                                 url + '"),' )
                    
        # Remove the last comma of the CellContextOntologyAsso values
        cell_context_ontology_asso_values = cell_context_ontology_asso_values[ :-1 ]
        
        output_file.write( SQL_INSERT_CELL_CONTEXT.format( values = cell_context_table_values ) )
                
        output_file.write( SQL_INSERT_CELL_CONTEXT_ONTO_ASSO.format( values = cell_context_ontology_asso_values ) )
        


# ===============================================================================
# The main function
# ===============================================================================

if __name__ == '__main__':
    
    ## Command-line arguments are parsed.
    # Store the various option values into a dictionary
    optionParser = OptionParser()
    for current_opt in OPTION_LIST:
        optionParser.add_option( current_opt[0],
                                 current_opt[1],
                                 action = current_opt[2],
                                 type = current_opt[3],
                                 dest = current_opt[4],
                                 default = current_opt[5],
                                 help = current_opt[6] )
    (opts, args) = optionParser.parse_args()
    option_dict = vars(opts)
    
    # Get the path to the input file
    input_file_path = option_dict[ INPUT_FILE_PATH_OPTION ]
    
    # Get the path to the output file
    output_file_path = option_dict[ OUTPUT_FILE_PATH_OPTION ]
        
    # Generate the sql file
    print( 'Starting to generate the SQL file.' +
           ' Please note that the script needs to be updated if you include new ontologies and/or' +
           ' if you updated the column names. In addition you need to ensure there are no duplicates' +
           ' in the cell contexts.' )
    generate_sql( input_file_path = input_file_path, 
                  output_file_path = output_file_path )
