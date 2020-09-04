sORF datafreezer {#mainpage}
================

# Description

This source code has been created to perform a data freeze of **short Open Reading Frame (ORFs) related data**. It is able to perform the parsing and insertion of several data sources and perform normalization, merging and summary of redundant information and computation of several interesting features, such as ORF annotations or estimation of Kozak contexts. We strongly suggest to read the **user's manual** for detailed explanations about the available strategies, and general structure of the algorithms for each of them. The current manual is exclusively **dedicated to developers** and does not intend to explain the interest of each strategy, the expected formats of inputs, formats of outputs or the way the data are handled!

The present page summarizes some useful information about the most important functions and classes defined in the source code. For precise information about a particular class or method, you will be able to find a precise documentation that includes:

- The aim of the class or method,
- The inputs of the method (with detailed explanation of their format).
- The outputs of the method (with detailed explanation of their format).
- The exceptions susceptible to be raised by the method. 
- For the class constructors, the instance attributes defined.

**Any** module of the source code contains **one single and unique class**.



# Entrypoint

The `fr/tagc/uorf/uorf.py` file constitutes the main file of the program (the entrypoint). It contains a `__main__` function that is run when launching the script with a Python interpreter. The user should never try to run a strategy otherwise than using this entrypoint.



# Strategies
 
The program uses strategy patterns to perform the expected tasks. 

For each strategy defined in the user's manual, there is a class that use the same name followed by the suffix `Strategy` that is located in the `fr.tagc.uorf.core.execution` package. This section briefly describes the main modules related to each strategy.

NB: Utils modules (`fr.tagc.uorf.core.util`) and external packages are **not** referenced here. We advice to read the documentation of the strategy for more information regarding the modules or external packages it requires.

 
- **DatabaseCheck**

    - The list of strategies using the **DatabaseCheck** strategy may be found at the end of the `fr.tagc.uorf.core.util.option.OptionConstants` module.
    
    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.DatabaseCheckStrategy`: Strategy class.
        - `fr.tagc.uorf.core.execution.dbcheck` package: defines `CheckDatabase` meta / abstract class and `CheckDSDatabase`, `CheckFILTDatabase`, `CheckPRODatabase` classes.
        
    - Related database models: DS, PRO.


- **AddReleaseVersion**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.AddReleaseVersion`: Strategy class.
        
    - Related database models: DS, PRO.
    
    
- **Insertion**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.InsertionStrategy`: Strategy class.
        - `fr.tagc.uorf.core.execution.insertion` package includes:
            - `ParserWrapper`: A wrapper that allows to execute the appropriate parser and return the list of objects that needs to be inserted in the database.
            - `ParserStrategy`: Meta and abstract class that includes useuful methods for the parsing of data sources.
            - `parserstrategy` packages includes `common`, `human` and `mouse` sub-packages. Any parser of this module is a new class inheriting from the `ParserStrategy` class. Any parser is able to import the data from the source, parse the data and instantiate the appropriate objects that need to be inserted in the database.
        
    - Related database models: DS.


- **ForceInsertion**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.ForceInsertionStrategy`: Strategy class.
        - See modules and packages related to the **Insertion** strategy.
        
    - Related database models: DS.
        

- **Deletion**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.DeletionStrategy`: Strategy class.
        
    - Related database models: DS.


- **LiftOver**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.LiftOverStrategy`: Strategy class.
        
    - Related database models: DS.
    
        
- **Merge**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.MergeStrategy`: Strategy class (and meta class).
        - `fr.tagc.uorf.core.execution.merge` package includes:
            - `MergeDSORF`: A static class that help performing the merge of *DSORF* entries. This module has been adapted to multi-processing.
            - `MergeDSOTA`: A static class that help performing the merge of *DSORFTranscriptAsso* entries. This module has been adapted to multi-processing.
        
    - Related database models: DS, PRO.
    
        
- **ResumeMerge**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.ResumeMergeStrategy`: Strategy class (inherit from the `MergeStrategy` class).
        - See modules and packages related to the **Merge** strategy.
        
    - Related database models: DS, PRO.
    
        
- **ComputeMissingInformation**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.ComputeMissingInformationStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **ComputeRelInformation**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.ComputeRelInformationStrategy`: Strategy class.
        - `fr.tagc.uorf.core.execution.relative_coord` package includes:
            - R scripts that aims to be run as subprocesses.
        
    - Related database models: PRO.
    
        
- **ComputeKozakContext**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.ComputeKozakContextStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **AnnotateORF**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.AnnotateORFStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **Filter**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.FilterStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **GenerateFastaFile**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateFastaFileStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **GenerateBEDContent**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateBEDContentStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **GenerateBEDFile**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateBEDContentStrategy`: Strategy class (inherit from the `GenerateBEDContentStrategy` class).
        - `fr.tagc.uorf.core.execution.GenerateBEDFileStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **GenerateTrackDbFile**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateTrackDbFileFileStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **GenerateGFFFile**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateGFFFileStrategy`: Strategy class.
        
    - Related database models: PRO.
    
        
- **AssessDatabaseContent**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.AssessDatabaseContentStrategy`: Strategy class.
        
    - Related database models: DS, PRO.
    
        
- **GenerateStatFiles**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.GenerateStatFilesStrategy`: Strategy class.
        
    - Related database models: None.
    
        
- **Backup strategy**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.BackupStrategy`: Strategy class.
        
    - Related database models: DS, PRO.
    
        
- **Restore strategy**

    - Main modules related to this strategy:
        - `fr.tagc.uorf.core.execution.RestoreStrategy`: Strategy class.
        
    - Related database models: DS, PRO.




# Database models

The `fr.tagc.uorf.core.model` package contains the database models, *i.e* all the classes that are required by SQLALchemy (ORM) to create the tables of the databases and to handle their content. 

Two models of databases (*DS* standing for DataSource and *PRO* standing for PROcessed) are available. The classes necessary to handle these model have been created in separated sub-packages. For more information about the database structures and table attributes (type, primary keys...), please see the database schemas provided with the source code and the documentation of these classes.

The program is able to handle several databases (with distinct structures) at the same time (see documentation of the `fr.tagc.uorf.core.util.sql` package for more information). 

The `fr.tagc.uorf.core.model` package contains:

- The `DS` package containing the classes necessary to handle the *DS* database. It contains the following packages:

    - `meta` contains the modules related to the tables that aim to store meta data about the database (species, annotation version information...). It contains the `Metadata` and `SpeciesCatalog` modules.
    
    - `datasource` contains the modules related to the tables that aim to store the content that has been parsed from the data sources. It contains the `DataSource`, `DSORF`, `DSTranscript` and `DSORFTranscriptAsso` modules.
    
    - `utilrelation` contains the modules related to the tables that are not *per se* of interest for the user but which essentially aims to store data generated during the execution of the program and that need to persist between the execution of two strategies (*e.g*. because their computation may need a long time). It contains the `UTGeneFromAlias`  and `UTDSTranscriptGeneConflict` modules.
    
    - `Gene` and `GeneAlias` modules define the tables that contain the cross-references.
    

- The `PRO` package containing the classes necessary to handle the *PRO* database. It contains the following packages:

    - `meta` contains the modules related to the tables that aim to store meta data about the database (species, annotation version information...). It contains the `PROMetadata` and `PROSpeciesCatalog` modules.

    - `processed` contains the modules related to the tables that aim to store the content merged from the *DS* database. It contains the `ORF`, `Transcript`, `ORFTranscriptAsso`, `CellContext`, `FLOSSClass`, `ProvidedCategory`, `ORFDSAsso`, `TranscriptDSAsso` and `ORFTranscriptAssoDSAsso` modules. It also contains the sub-package `catalog` with `CellContextCatalog`, `FLOSSClassCatalog` and `ProvidedCategory` modules.
    
    - `computed`contains the modules related to the tables that store computed data. It contains the `ORFCategory`, `ORFCategoryCatalog`, `ORFAnnotation` and `ORFAnnotationCatalog` modules.
    
    - `utilrelation` contains the modules related to the tables that are not *per se* of interest for the user but which essentially aims to store data generated during the execution of the program and that need to persist between the execution of two strategies (*e.g*. because their computation may need a long time). It contains the `UTRNABiotypeCatalog` and `UTBEDContent` modules.
    
    - `PROGene` and `PROGeneAlias` modules define the tables that contain the cross-references.




# Utils

Any class or method defined in the `fr.tagc.uorf.core.util` module are non-specific classes and methods that have been built to be used anywhere in the program.

- **Loggers**: `fr.tagc.uorf.core.util.log` package

    - Two loggers defined:
        - `Logger` module defines the main logger. The class defined is a singleton.
        - `GeneRefLogger` module defines the logger dedicated to gene references problems. The class defined is a singleton. 
    
    - Classes defined in these modules allow to log message anywhere in the program.
    
    - External modules related to this package:
        - `fr.tagc.uorf.core.util.LogCodes`: file defining constants which are used as warning and error codes.
        
        
- **Command line arguments** (options): `fr.tagc.uorf.core.util.option` package

    - Modules:
        - `OptionManager` modules define a command line arguments parser and option manager. The class defined is a singleton.
        - `OptionConstants` module defines constants related to the options that may be provided in the command line and constants helping to manage them. No class defined in this module, constants file.
        
        
- **SQL manager**: `fr.tagc.uorf.core.util.sql` package

    - Modules:
        - `SQLManager` module defines an abstract meta class of singletons which children aim to manage database connections.
        - `SQLManagerDS`, `SQLManagerPRO`, `SQLManagerFILT` modules contains classes inheriting from the `SQLManager` class and aim to manage respectively *DS*, *PRO* (*PRO*-like) and *FILT* databases. The classes defined in these modules are singleton.
        - `Base` module instantiates objects of the `declarative_base` SQLALchemy class. No class defined in this module, procedural-like code defined there.
        - `SQLContants` module defines constants related to the database managment, such as connection settings (user name, URI etc.) or default value for some MySQL variables.
        - `SQLCollationManager` module defines a class to manage the database collation for all the columns of the database containing text (such as `VARCHAR` or `TEXT` columns). The class defined is a singleton.
        
    - Classes defined in these modules facilitate the creation of engine and seessions to the databases. They also facilitates the creation of databases as well as addition, deletion and update of entries in the database. They are able to manage the commit or roll-back of sessions. Methods of these classes are using **SQLAlchemy** (ORM) tools.
        
        
- **Exceptions**: `fr.tagc.uorf.core.util.exception` package

    - `DenCellORFException` module defines a meta class of custom exceptions. The class defined inherit itself from the `Exception` Python class.

    - The instances of the classes defined in this package are exception that may at least contain a message and an other exception. The class defines also methods to display the message of the exception (and an eventual trace track). All class of exceptions defined by these modules obviously aim to be manipulated anywhere in the program.
    
    - Each package contains one or several module(s), each defining one unique exception class:
        - `dencellorfobject` exceptions: Used when an error related to the manipulation of object specific to the present source code is met.
        - `insertexception` exceptions: Used when problems are met during the data insertion.
        - `headerexception` exceptions: Used when problems related to the headers of pandas data frames are met.
        - `refexception` exceptions: Used when problems related to the gene references and cross-references are met.
        - `processingexception` exceptions: Used when problems related to the processing of data are met. 
        - `httpexception` exceptions: Used when exceptions / errors have been raised by an HTTP request. 
        - `geneticsexception` exceptions: Used when problems related to the manipulation of genetics objects are met.
        
        
- **Shared data** (DataManager): `fr.tagc.uorf.core.util.data` package
    
    - Modules:
        - `DataManager` module helps managing objects of any class shared by different classes and/or methods of the program. The class defined is a singleton.
        
        
- **Genetics-related data and data from Ensembl**: `fr.tagc.uorf.core.util.genetics` and `fr.tagc.uorf.core.util.ensembl` packages
    
    - Ensembl modules:
        - `EnsemblUtil` module defines a static class that contains methods helping to use Ensembl tools (and the `PyEnsembl` package).
        - `EnsemblRestClient` module defines a client helping to use the Ensembl REST API. The class defined is a singleton.
    
    - Genetics modules:
        - `GeneticsUtil` module defines a static class that contains methods helping to handle genetics-related data (such as performing DNA translation).
        - `GeneticsConstants` module defines constants related to genetics data. No class defined in this module, constants file.
        
        
- **Graphics**: `fr.tagc.uorf.core.util.graphics` package
    
    - Modules:
        - `ProgressionBar` module aims to help the display of progression bars on the console. The class defined is a singleton.
        
        
- **General and miscellaneous utils**: `fr.tagc.uorf.core.util.general` package

    - This package contains highly generic functions that may be useful anywhere in the program.
    
    - Modules:
        - `GeneralUtil` module defines a static class dedicated to these general utils.
        - `FileHandlerUtil` module defines a static class dedicated to the manipulation of files.
        
        
- **Constants**: `fr.tagc.uorf.core.util.Constants` module (see following section)
        
        
- **Default output and temporary folders**: `fr.tagc.uorf.core.util.DefaultOutputFolder` and `fr.tagc.uorf.core.util.DefaultTemporaryFolder` modules

    - Modules:
        - `DefaultOutputFolder` defines one **unique** variable that contains the path of the folder to use as output folder (in particular for the log files). A different output folder may be defined for some strategies (see **user's manual** for more information).
        - `DefaultTemporaryFolder` defines one **unique** variable that contains the path of the folder to use as temporary folder.




# Constants

The `fr.tagc.uorf.core.util.Constants` module define numerous constants that are used in most of the modules.

Here is a brief description of the sections it contains:

- **Project informations**: General information about the project (project name, alias, URL to user-friendly web interface).

- **Config file constants**: Definition of the config file sections and items.

- **DataManager constants**: Definition of the keys of the DataManager main dictionary.

- **General constants**: General constants, mainly regarding the species allowed.

- **Constants relative to the annotation versions**: Definition of the annotation version and correspondences between the versions (NCBI, UCSC).

- **Constants relative to the Gene / GeneAlias / util tables of the database**: Definition of prefix or separators to use in the gene tables.

- **Constants relative to the connection to the database**: Definition of SQLManager keys.

- **Constants relative to logs**: Default settings of the main logger.

- **Constants relative to gene reference logs**: Default settings of the gene references logger.

- **Constants relative to the files created by the program**: Definition of default path to use for output and temporary files and folders.

- **Constants relative to the insertion of data in the database**: Default settings for the insertion of new entries in the databases.

- **Constants relative to the built of the PRO database**: Default settings mainly related to the strategies manipulating the **PRO** database.

- **Constants relative to the DenCellORFObjects**: Definition of constants related to the database contents. This includes definition of chromosome names, gene and transcript prefixes etc.

- **Constants relative to the Metadata table**: Definition of keys and definitions used in the metadata table.

- **Constants relative to the sequences**: Default settings related to DNA and protein sequences (letter to use for ambiguous residue etc.).

- **Constants relative to the computation of relative coordinates from absolute coordinates relative**: Constants specifically related to the **ComputeRelCoord** strategy. 

- **Constants relative to the merging of CellContext entries**: Default settings for the cell merging (see documentation of the **ComputeMissingInfo** strategy).

- **Constants relative to the ORF annotations**: Default settings for the ORF categories and annotation computation (see documentation of the **AnnotateORF** strategy).

- **Constants relative to the filtering**: Default settings for the filtering of a PRO-like database (see documentation of the **Filter** strategy).   
    

**NB:** The **Information to developers** section of the **user's manual** contains complementary information regarding the constants.




# Authors, license and copyright

Sébastien A. Choteau<sup>1,2</sup>, 
Lionel Spinelli<sup>1,2</sup>,
Philippe Pierre<sup>2</sup>,
Christine Brun<sup>1,3</sup>

1. Aix-Marseille Univ, INSERM, TAGC, CENTURI, Marseille, France
2. Aix-Marseille Univ, CNRS, INSERM, CIML, CENTURI, Marseille, France
3. CNRS, Marseille, France


If you have questions or comments, please write to:

- Sébastien A. Choteau at [sebastien.choteau@univ-amu.fr](mailto:sebastien.choteau@univ-amu.fr)




Last update of this page: **25/05/2020**. Please note that we ensure **continuous maintenance** of all other pages of the current documentation dedicated to developers.
