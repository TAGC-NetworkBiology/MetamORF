
# MetamORF: A repository of unique short Open Reading Frames identified by both experimental and computational approaches for gene-level and meta analysis

## Goal of the repository

This GitHub repository contains the instructions and material to reproduce the build of the MetamORF database (web interface available at [http://metamorf.hb.univ-amu.fr](http://metamorf.hb.univ-amu.fr)). Extensive documentation, source code, scripts and containers are available in this repository. Builded Docker/Singularity images are available on download and required data may be downloaded from their original sources. Instructions necessary to reproduce the analysis are provided below.

To build the database, you first need to prepare the environments and then follow the steps described there.



## Description of the datasets

In order to reproduce the build of MetamORF, it is first necessary to download data from the 6 original data sources. Data have to be downloaded manually from the editors' or authors' websites.

| Name of the data source         | Species      | Associated publication              | doi                     | URL to the publication                 | Description                                               |           
|---------------------------------|--------------|-------------------------------------|-------------------------|----------------------------------------|-----------------------------------------------------------|
| Erhard2018                      | *H.sapiens*  | Erhard et al., Nat. Meth., 2018     | 10.1038/nmeth.4631      | [https://www.nature.com/articles/nmeth.4631](https://www.nature.com/articles/nmeth.4631)  | "Supplementary Table 3: Identified ORFs (Union of all ORFs detected either by PRICE,RP-BP or ORF-RATER, or contained in the annotation (Ensembl V75))". The two first lines of the file have to be manually removed. |
| Johnstone2016                   | *H.sapiens*  | Johnstone et al., EMBO, 2016        | 10.15252/embj.201592759 | [http://emboj.embopress.org/content/35/7/706.long](http://emboj.embopress.org/content/35/7/706.long)  | "Dataset EV2: Location and translation data for all analyzed transcripts and ORFs in human" |
| Johnstone2016                   | *M.musculus* | Johnstone et al., EMBO, 2016        | 10.15252/embj.201592759 | [http://emboj.embopress.org/content/35/7/706.long](http://emboj.embopress.org/content/35/7/706.long)  | "Dataset EV3: Location and translation data for all analyzed transcripts and ORFs in mouse" |
| Laumont2016                     | *H.sapiens*  | Laumont et al., Nat. Commun., 2016  | 10.1038/ncomms10238     | [https://www.nature.com/articles/ncomms10238](https://www.nature.com/articles/ncomms10238)  | "Supplementary Data 2: List of all cryptic MAPs detected in subject 1. Table presenting the genomic and proteomic features of all cryptic MAPs". The two first rows have to be manually removed. |
| Mackowiak2015                   | *H.sapiens*  | Mackowiak et al., Genome Biol., 2015 | 10.1186/s13059-015-0742-x     | [https://genomebiology.biomedcentral.com/articles/10.1186/s13059-015-0742-x](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-015-0742-x)  | "Additional file 2: Table S1. All sORF information for human". The file header has to be removed manually (45 first rows). |
| Mackowiak2015                   | *M.musculus* | Mackowiak et al., Genome Biol., 2015 | 10.1186/s13059-015-0742-x     | [https://genomebiology.biomedcentral.com/articles/10.1186/s13059-015-0742-x](https://genomebiology.biomedcentral.com/articles/10.1186/s13059-015-0742-x)  | "Additional file 3: Table S2. All sORF information for mouse". The file header has to be removed manually (45 first rows). |
| Samandi2017                     | *H.sapiens*  | Samandi et al., eLIFE, 2017         | 10.7554/eLife.27860            | [https://elifesciences.org/articles/27860](https://elifesciences.org/articles/27860)  | "Homo sapiens alternative protein predictions based on RefSeq GRCh38 (hg38) based on assembly GCF_000001405.26. Release date 01/01/2016". The TSV file has been used. |
| Samandi2017                     | *M.musculus* | Samandi et al., eLIFE, 2017         | 10.7554/eLife.27860            | [https://elifesciences.org/articles/27860](https://elifesciences.org/articles/27860)  | "Mus musculus alternative protein predictions based on annotation version GRCm38. Release date 01/01/2016". The TSV file has been used. |
| sORFs_org_Human                 | *H.sapiens*  | Olexiouk et al., Nucl. Ac. Res., 2018 | 10.1093/nar/gkx1130          | [https://academic.oup.com/nar/article/46/D1/D497/4621340](https://academic.oup.com/nar/article/46/D1/D497/4621340)  | H. sapiens database downloaded from sORFs.org using the Biomart Graphic User Interface. The following parameters were used to query the database: "Homo sapiens" > "no filters" > "select all MAIN_ATTRIBUTES" > "results" > "download data". |
| sORFs_org_Mouse                 | *H.sapiens*  | Olexiouk et al., Nucl. Ac. Res., 2018 | 10.1093/nar/gkx1130          | [https://academic.oup.com/nar/article/46/D1/D497/4621340](https://academic.oup.com/nar/article/46/D1/D497/4621340)  | M. musculus database downloaded from sORFs.org using the Biomart Graphic User Interface. The following parameters were used to query the database: "Mus musculus" > "no filters" > "select all MAIN_ATTRIBUTES" > "results" > "download data". |



## System requirement and dependencies

The source code must be executed with Python 2.7. The MetamORF database has been build on a Linux system using Docker and Singularity containers, but it could be run on any operating system where dependencies are satisfied. A minimum of 62 GB of RAM memory, 12 threads is highly recommended to run the software but we highly recommend to use systems with at least 40 threads, 192 GB of RAM available if you intend to build the full database. A stable connection to the Internet is also required as some information are queried from different databases accessible online.



## Environment preparation

In order to prepare the environment for analysis execution, it is required to:

1. Clone the current GitHub repository and set the `WORKING_DIR` environment variable
2. Download the data sources and the cross-references
3. Download the Docker image (.tar.gz) and Singularity image (.img) files
4. Install [Docker](https://www.docker.com/), [Docker-compose](https://docs.docker.com/compose/ and [Singularity](https://singularity.lbl.gov/)
5. Load the Docker images on your system and start the containers
 
This section provides additional information for each of these steps.
 

### Clone the GitHub repository

Use you favorite method to clone this repository in a chosen folder (see [GitHub documentation](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) for more information). This will create a folder called `MetamORF` containing all the code and documentation. 

Then, set an environment variable called `WORKING_DIR` with a value set to the path to this folder. For instance, if you cloned the repository in `/home/choteaus/workspace`, then the `WORKING_DIR` variable needs be set to `/home/choteaus/workspace/MetamORF`.

**On Linux:**

```
export WORKING_DIR=/home/choteaus/workspace/MetamORF
```
 

### Download the data sources and the cross-references

**Cross-references**

Cross-references have been downloaded manually from the HGNC and NCBI websites. Cross-references from the [HUGO Gene Nomenclature Committee (HGNC)](https://www.genenames.org/) have been downloaded using the graphic user interface. Cross-references for *M.musculus* from the [National Center for Biotechnology Information (NCBI)](ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/) may be download using the following command line (on Linux):

```
mkdir -p $WORKING_DIR/07_input/cross_references \
  && curl -o $WORKING_DIR/07_input/cross_references/mmusculus.gene_info.gz \
    -O ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/Mammalia/Mus_musculus.gene_info.gz \
  && gunzip $WORKING_DIR/07_input/cross_references/mmusculus.gene_info.gz
```

As these databases evolve quickly, a copy of the cross-reference files we used to build MetamORF is available on Zenodo ([![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4014738.svg)](https://doi.org/10.5281/zenodo.4014738)) as a .tar.gz archive. On Linux, run the following command line to download the archive and uncompress it at the appropriate location:

```
wget https://zenodo.org/record/4014738/files/MetamORF_07_input.tar.gz?download=1 -O $WORKING_DIR/MetamORF_07_input.tar.gz \
  && tar xzvf $WORKING_DIR/MetamORF_07_input.tar.gz --directory $WORKING_DIR \
  && rm $WORKING_DIR/MetamORF_07_input.tar.gz
```

| Name of the cross-reference       | Species       | Filename                         |
|-----------------------------------|---------------|----------------------------------|
| HGNC                              | H.sapiens     | hsapiens_HGNC.txt                |
| NCBI                              | M.musculus    | mmusculus.gene_info              |


**Data sources**

Raw data need to be downloaded manually from editors' or authors' website using information provided in the **Description of the datasets** section of the current documentation. Once downloaded, the files need to be saved in the `$WORKING_DIR/07_input/ORF_datasources` folder and renamed using the following rules:

| Name of the data source       | Species       | Filename                         |
|-------------------------------|---------------|----------------------------------|
| Erhard2018                    | H.sapiens     | hsapiens_Erhard2018.csv          |
| Johnstone2016                 | H.sapiens     | hsapiens_Johnstone2016.txt       |
| Johnstone2016                 | M.musculus    | mmusculus_Johnstone2016.txt      |
| Laumont2016                   | H.sapiens     | hsapiens_Laumont2016.csv         |
| Mackowiak2015                 | H.sapiens     | hsapiens_Mackowiak2015.txt       |
| Mackowiak2015                 | M.musculus    | mmusculus_Mackowiak2015.txt      |
| Samandi2017                   | H.sapiens     | hsapiens_Samandi2017.tsv         |
| Samandi2017                   | M.musculus    | mmusculus_Samandi2017.tsv        |
| sORFs_org_Human               | H.sapiens     | hsapiens_sORFs.org.txt           |
| sORFs_org_Mouse               | M.musculus    | mmusculus_sORFs.org.txt          |


Once done, you should obtain the following subfolder structure:

```
07_input
├──cross_references
│   ├── hsapiens_HGNC.txt
│   └── mmusculus.gene_info
└── ORF_datasources
    ├── hsapiens_Erhard2018.csv
    ├── hsapiens_Johnstone2016.txt
    ├── mmusculus_Johnstone2016.txt 
    ├── hsapiens_Laumont2016.csv
    ├── hsapiens_Mackowiak2015.txt
    ├── mmusculus_Mackowiak2015.txt
    ├── hsapiens_Samandi2017.tsv
    ├── mmusculus_Samandi2017.tsv
    ├── hsapiens_sORFs.org.txt
    └── mmusculus_sORFs.org.txt
```


### Download the Docker and Singularity images

Docker image tar file and Singularity img files are available to download on Zenodo ([![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4014738.svg)](https://doi.org/10.5281/zenodo.4014738)).

If you intend to build yourself the containers, the dockerfile and their documentation are available in the `02_container` folder. Note that some links of the dockerfile may be obsolete and we strongly suggest to use the containers stored on Zenodo.

To download the containers from Zenodo, open a shell and execute the following commands to download the tarball file and untar it (on Linux):

```
rm -R $WORKING_DIR/02_container \
  && wget https://zenodo.org/record/4014738/files/MetamORF_02_container.tar.gz?download=1 -O $WORKING_DIR/MetamORF_02_container.tar.gz \
  && tar xzvf $WORKING_DIR/MetamORF_02_container.tar.gz --directory $WORKING_DIR \
  && rm $WORKING_DIR/MetamORF_02_container.tar.gz
```

These commands will replace the `02_container` folder and you should obtain the following subfolder structure:

```
02_container/
├── mysql
│   ├── docker-compose.yml
│   └── readme.txt
├── script
│   ├── 01_crossreferences_download
│   │   ├── dockerfile
│   │   └── readme.txt
│   └── 03_orf_datasources_analysis
│       ├── dockerfile
│       └── readme.txt
└── src
    ├── dockerfile
    ├── readme_dev.txt
    ├── readme.txt
    └── tagc-uorf-orf-datafreeze-src.img
```


### Install Docker and Singularity

You need to install Docker (v18.09), Docker-compose (v1.24) and Singularity (v2.5) on your system. Please, read their official documentation for more information.

- To install Docker, follow the instructions here: https://docs.docker.com/engine/install/

- To install Docker-compose, follow the instructions here: https://docs.docker.com/compose/install/

- To install Singularity v2.6, follow the instructions here: https://sylabs.io/guides/2.5/admin-guide/


### Load Docker images on the system

In order to build the MetamORF database, you must load the provided docker images onto your Docker. Docker must be installed on your system.


#### Start the MySQL service

1. Update the line 12 and 13 of the `02_container/mysql/docker-compose.yml` file. The `~/MetamORF/data/MySQL` path needs to be changed by the place where you are willing to store the MySQL files. The lines 11 to 13 can eventually be removed if you do not intend to mount a volume on the container.
2. Eventually update the line 15 to 17 to update the MySQL user name (15), user (16) or root (17) password.
3. Eventually update the ports used by the server. If you do not know which ports to use, we strongly suggest to keep the one defined there.

Load the MySQL Docker using one of the following command (on Linux):

```
docker load -i $WORKING_DIR/02_container/mysql/mysql:8.0.16.tar.gz
```

or

```
docker pull mysql:8.0.16
```


Load the Adminer Docker one of the following command (on Linux):

```
docker load -i $WORKING_DIR/02_container/mysql/adminer:4.7.17.tar.gz
```

or

```
docker pull adminer:4.7.17
```


Start the Docker using the command

```
cd $WORKING_DIR/02_container/mysql \
  && docker-compose up -d
```

Please, note that Adminer is not necessary to build the database and is only provided in order to allow the use and managment of the database through an user-friendly web interface. Then, more recent version of Adminer or other services (such as phpMyAdmin) may be used instead. You may also wish to run solely the MySQL Docker, without Adminer. 


#### Source code docker image

To run the source code, we advice to use the Singularity image, which do not require the root privileges to be used. Nevertheless, if you are willing to use Docker instead of Singularity, archives necessary to do so are available. In such case, you need to load the Docker image and create a new container. Please, read the documentation associated with the containers and the Docker official documentation for more information.


#### Other containers

Other containers provided in this repository are **not** necessary to run the source code and to build the database. They have been created to allow the download of cross-references (from NCBI, Ensembl and MGI) and to perform an estimate of the proportion of short Open Reading Frames that are spliced in the each data source. Please, read their documentation for more information.

 
### Dependencies

If you do not wish to use Docker and Singularity images, then you need to ensure the following dependencies are successfully installed on your system:

- Python 2.7, with packages:
    - SQLAlchemy
    - Pandas
    - PyEnsembl
    - PyBiomart
    - PyLiftOver
    - wget
    - statistics
    - BioPython
    - mysql-connector-python
    - pathos
- R, with packages:
    - getopt
    - devtools
    - Bioconductor: ensembldb, AnnotationHub
- MySQL
- SQLite3
- MUSCLE (Multiple sequence alignment software)
- UCSC utils
    - fetchChromSizes
    - bedToBigBed

Please note that we highly recommend to use the Docker and Singularity images we provide in order to ensure the reproducibility of the results.
Please see the official documentation of these sotwares and packages for more information regarding their installation.



## Build the database - Quick start

An extensive documentation providing information about the tools provided by the MetamORF builder are available in the **manual**. This section provides the most important and some complementary information to build the MetamORF database.
The source code needs to be run once for each species and will result in the creation of two databases (*DS* and *PRO*) for each.


### Prepare the configuration file

The config file needs to be edited manually. Example of config files are available in the `04_config` folder.

The following lines need to be checked / updated: 

- In the `DATABASE` section:
    - The name of the *DS* database: `DS_DATABASE_NAME`.
    - The name of the *PRO* database: `PRO_DATABASE_NAME`.
    - The name of the species: `DATABASE_SPECIES` (`Hsapiens` and `Mmusculus` allowed).
    - The IP and the port of the MySQL host: `DATABASE_HOST_IP` and `DATABASE_PORT` (NB: SQLite database may also be used, see the manual for more information).
    - The database username and password: `DATABASE_USER_NAME` and `DATABASE_USER_PASSWD`.

- In the `GENE_LIST` and `DATASOURCE` sections, **all** the occurrences of `$WORKING_DIR`**must** be replaced by its actual value (*i.e.* by the absolute path to the working directory).

Numerous options may be set in the config file. Please read the manual for more information regarding this topic. If you do not know how to configure the config file, we advice to use this default setting. 


### Prepare the running scripts

The MetamORF *H.sapiens* and *M.musculus* databases have been build by sequentially running several *strategies*. These *strategies* have been run in the following order: 

- DatabaseCheck
- Insertion
- LiftOver
- Merge
- ComputeMissingInfo
- ComputeRelCoord
- ComputeKozakContext
- AnnotateORF
- GenerateBEDContent

If you intend to run the strategies in a different order or to run other strategies, update the `03_workflow/datafreeze/full_build.sh` or create a new bash script in this folder. The `03_workflow/datafreeze/model.sh` may be used as a template to create a new script. Several other scripts are available in this folder if you are willing to run a particular strategy.

To get more information about the strategies available, their execution, the options that may be used, input and outputs, please read the manual available at pdf and html formats in `01_documentation/manual`. If you do not know which strategies to run, we advice to use the `full_build.sh` script.


### Build the database

To build the database, move to the working directory and start the running script previously created.

You may used one of the following command line (on Linux): 

```
singularity exec 02_container/src/tagc-uorf-orf-datafreeze-src.img \
  03_workflow/datafreeze/full_build_min.sh \
  --config $configfileName \
  > 09_log/MetamORF.log
```

or 

```
singularity exec 02_container/src/tagc-uorf-orf-datafreeze-src.img \
  03_workflow/datafreeze/full_build.sh \
  --config $configfileName \
  --dbtype MySQL \
  --dsdbname $DS_DB \
  --prodbname $PRO_DB \
  --dbhost $DB_HOST \
  --dbport $DB_PORT \
  --dbuser $DB_USER \
  --dbpassword $DB_PASSWD
  > 09_log/MetamORF.log
```

The variable `$configfileName` needs to be replaced by the **name** of the config file.

The variables `$DS_DB`, `$PRO_DB`, `$DB_HOST`, `$DB_PORT`, `$DB_PORT`, `$DB_USER` and `$DB_PASSWD` need to be replaced by the appropriate values. Note that the options to provide may depend on the strategy. This second command line allows to add information about the release in the Metadata table of the databases.

The same procedure should be followed for both *H.sapiens* and *M.musculus*, using the appropriate configuration files.



## Additional information

### Documentation

An user manual is available at the PDF and HTML format in `01_documentation/manual` and provides extensive information about the methods.

A documentation dedicated to developers is available in the `01_documentation/src/html` folder (generated with Doxygen). You need to open the `index.html` file with a web browser to display and navigate through this documentation.


### Dates of download

**Data sources**

| Name of the data source       | Species       | Date of download  |
|-------------------------------|---------------|-------------------|
| Erhard2018                    | H.sapiens     | 04/01/2019        |
| Johnstone2016                 | H.sapiens     | 04/01/2019        |
| Johnstone2016                 | M.musculus    | 04/01/2019        |
| Laumont2016                   | H.sapiens     | 04/01/2019        |
| Mackowiak2015                 | H.sapiens     | 20/03/2019        |
| Mackowiak2015                 | M.musculus    | 20/03/2019        |
| Samandi2017                   | H.sapiens     | 04/01/2019        |
| Samandi2017                   | M.musculus    | 04/01/2019        |
| sORFs_org_Human               | H.sapiens     | 08/06/2020        |
| sORFs_org_Mouse               | M.musculus    | 08/06/2020        |


**Cross-references**

| Name of the cross-reference   | Species       | Date of download  |
|-------------------------------|---------------|-------------------|
| HGNC                          | H.sapiens     | 27/06/2019        |
| NCBI                          | M.musculus    | 06/06/2020        |


### Tree view

At the end of the procedure, *i.e.* after having successfully: 

- Clone the GitHub repository
- Download the data sources and cross-references
- Download the Dockers and Singularity images
- Install Docker, Docker-compose and Singularity
- Load the Docker images on your system and start the containers
- Run the source code to build the databases for one species (either for *H.sapiens* or *M.musculus*)

the tree folder should look like the following one:

```
.
│
├── 01_documentation                            [Documentation of the project]
│   ├── manual                                  [User's manual]
│   │   ├── manual.html
│   │   └── manual.pdf
│   ├── metadata                                [Metadata of the ORF datafreeze]
│   │   ├── DCMI_schema.xsd
│   │   └── metadata.xml
│   ├── src                                     [Source code documentation, generated with doxygen in HTML format]
│   │   └── html
│   └── workbook                                [Useful information regarding the source code]
│       ├── appendices                          [Workbook appendices helping dev and use of the source code]
│       │   ├── cell_contexts                   [Information regarding the cell contexts registered in the database]
│       │   │   └── cell_context.csv
│       │   ├── db_schema                       [Database UML schemas]
│       │   │   └── database_schema.pdf
│       │   ├── log_codes                       [List of error and warning codes that could be logged by the source code]
│       │   │   └── LogCodes.ods
│       │   └── miscellaneous                   [Miscellaneous information susceptible to help the users and developers]
│       │       └── Ensembl_biotypes.csv
│       ├── computation_times.csv               [Information regarding the expected time of execution of the source code]
│       └── datafreeze_workflow.png             [Datafreeze adviced workflow at png format]
├── 02_container                                [Dockerfiles and singularity images]
│   ├── mysql                                   [Docker compose to start mysql and adminer servers]
│   │   ├── adminer:4.7.1.tar.gz
│   │   ├── docker-compose.yml
│   │   ├── mysql:8.0.16.tar.gz
│   │   └── readme.txt
│   ├── script                                  [Containers for scripts]
│   │   ├── 01_crossreferences_download         [Containers for 01_crossreferences_download scripts]
│   │   │   ├── dockerfile
│   │   │   ├── readme.txt
│   │   │   └── tagc-uorf-orf-datafreeze-script-cross_ref_dl.tar.gz
│   │   └── 03_orf_datasources_analysis         [Containers for 03_orf_datasources_analysis scripts]
│   │       ├── dockerfile
│   │       ├── readme.txt
│   │       └── tagc-uorf-orf-datafreeze-script-orf_ds_analysis.tar.gz
│   └── src                                     [Container to run the source code]
│       ├── dockerfile
│       ├── readme.txt
│       ├── tagc-uorf-orf-datafreeze-src.img
│       └── tagc-uorf-orf-datafreeze-src.tar.gz
├── 03_workflow                                 [Scripts and files necessary to run the source code]
│   └── datafreeze                              [Scripts allowing to build the datafreeze]
│       ├── declare_variables.sh                [Script allowing to declare environment variables necessary to run the source code]
│       ├── model.sh                            [Model of script to use to run one or several strategies]
│       ├── AnnotateORF.sh
│       ├── AssessDatabaseContent.sh
│       ├── ComputeKozakContext.sh
│       ├── ComputeMissingInfo.sh
│       ├── ComputeRelCoord.sh
│       ├── DatabaseCheck.sh
│       ├── full_build_min.sh
│       ├── full_build.sh
│       ├── GenerateBEDContent.sh
│       ├── GenerateBEDFile.sh
│       ├── GenerateFastaFile.sh
│       ├── GenerateGFFFile.sh
│       ├── GenerateStatFiles.sh
│       ├── GenerateTrackDbFile.sh
│       ├── Insertion.sh
│       ├── LiftOver.sh
│       ├── Merge.sh
│       └── ResumeMerge.sh
├── 04_config                                   [Config files necessary to run the source code]
│   ├── HsapiensConfigfile
│   └── MmusculusConfigfile
├── 05_script                                   [Scripts for pre-processing analysis]
│   ├── 01_crossreferences_download             [Scripts allowing to download the cross-references]
│   │   ├── DefaultOutputFolder.txt
│   │   ├── download.sh
│   │   ├── ensembl_gene_lists.R
│   │   └── readme.txt
│   ├── 02_orf_datasources_download             [Scripts allowing to download the ORF datasources - Empty]
│   └── 03_orf_datasources_analysis             [Scripts allowing a preliminary analysis of ORF datasources]
│       ├── estimate_splicing
│       └── readme.txt
├── 06_src                                      [See doxygen documentation for full documentation of this folder content]
├── 07_input                                    [Input files]    
│   ├── cross_references                        [Cross references]
│   │   ├── hsapiens_HGNC.txt
│   │   └── mmusculus.gene_info
│   └── ORF_datasources                         [ORF datasources]
│       ├── hsapiens_Erhard2018.csv
│       ├── hsapiens_Johnstone2016.txt
│       ├── hsapiens_Laumont2016.csv
│       ├── hsapiens_Mackowiak2015.txt
│       ├── hsapiens_Samandi2017.tsv
│       ├── hsapiens_sORFs.org.txt
│       ├── mmusculus_Johnstone2016.txt
│       ├── mmusculus_Mackowiak2015.txt
│       ├── mmusculus_Samandi2017.tsv
│       └── mmusculus_sORFs.org.txt
├── 08_output                                   [Output files]
│   └── datafreeze
│       ├── execution.log 
│       ├── generefwarnings.log
│       ├── merged_data_analysis
│       │   ├── dsota_count_for_orf_tr.csv
│       │   └── orf_tr_count_for_dsota.csv
│       ├── content_consistency_assessment
│       │   ├── DSDatabaseAssessment.tsv
│       │   └── PRODatabaseAssessment.tsv
│       ├── bed_files
│       │   ├── MetamORF_Hsapiens.bed
│       │   └── MetamORF_Hsapiens_without_scaffold.bed
│       ├── fasta_files
│       │   ├── MetamORF_Hsapiens_aa.fasta
│       │   ├── MetamORF_Hsapiens_aa_wo_seq_with_stop.fasta
│       │   ├── MetamORF_Hsapiens_nt.fasta
│       │   └── MetamORF_Hsapiens_nt_wo_seq_with_stop.fasta
│       ├── track_files
│       │   ├── hg38.chrom.sizes
│       │   ├── MetamORF.as
│       │   ├── MetamORF.bb
│       │   ├── MetamORF.bed
│       │   └── trackDb.txt
│       └── stat_files
│          ├── log_code_counts.csv
│          └── log_level_counts.csv
└── README.md
```

*NB:* Descriptions of the file / directory and additional information are provided between [brackets].
