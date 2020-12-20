
# Build a new database to register cell context cross-references

The web interface requires a database containing the correspondences between the cell context names used in the ORF datafreeze and the terms of several ontologies (EFO, BAO, BTO, OMIT, CLO, NCIT, HCAO, CL, OBI and FMA). These cross-references needs to be recovered manually, using the [Ontology Lookup Service (OLS)](https://www.ebi.ac.uk/ols/index) and eventually registered in a csv file (following the structure of the `../cell_context_ontology.csv` file).


## Build a new database

Build a new empty database using MySQL command line or Adminer. Ensure to use a `utf8mb4_0900_as_cs` collation.


## Build and fill in new tables

To quickly build the tables and fill them in, you may use the Python util provided in the current folder. This script will generate a sql file that may be executed on the MySQL server. Make sure to run this script in a Python environment where Pandas is installed (such as the Singularity environment provided to run the ORF datafreezer).

Move to the current directory and use the following command line to generate the SQL file:

```
python cell_context_ontology_to_sql.py \
  -i ../cell_context_ontology.csv \
  -o sql_statements.sql
```

Execute the SQL statement on the MySQL server.
