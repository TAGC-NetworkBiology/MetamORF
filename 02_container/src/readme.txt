
This image contains:

 - Python 2.7
      With the following Python packages:
     - SQLAlchemy (ORM)
     - Pandas
     - PyEnsembl
     - PyBiomart
     - PyLiftOver
     - wget
     - statistics
     - BioPython
     - mysql-connector-python
     - pathos
 
 - sqlite 3
 - python-mysqldb
 
 - MUSCLE (Multiple sequence alignment)
     
 - USCS utils
   - fetchChromSizes
   - bedToBigBed
 
 - R
   - getopt
   - devtools with:
     - tidyverse/dbplyr
     - r-lib/vctrs
     - tidyverse/glue
     - tidyverse/tidyselect
     - r-lib/ellipsis
     - r-lib/generics
   - Bioconductor with:
     - ensembldb
     - AnnotationHub
  

# ===========================================
# COMPILE THE IMAGE
# ===========================================

docker build -t tagc-uorf-orf-datafreeze-src \
  $WORKING_DIR/02_container/src


# ===========================================
# RUN THE DOCKER
# ===========================================

docker run -it --name tagc-uorf-orf-datafreeze-src \
  -v ~/data/MetamORF:/data \
  -e PYTHONPATH=$WORKING_DIR/06_src \
  tagc-uorf-orf-datafreeze-src


# ===========================================
# START / STOP THE DOCKER
# ===========================================

docker start -i tagc-uorf-orf-datafreeze-src
docker stop tagc-uorf-orf-datafreeze-src


# ===========================================
# SOURCE CODE
# ===========================================

Please see the documentation (manual and source code documentation)
located in the 01_documentation folder.


# ===========================================
# LOAD THE IMAGE FROM THE ARCHIVE
# ===========================================

# To load the image, run the following lines:
gunzip tagc-uorf-orf-datafreeze-src.tar.gz
docker image load -i tagc-uorf-orf-datafreeze-src.tar
