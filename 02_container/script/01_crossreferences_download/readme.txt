
This image contains:

 - R 3.5.0
 - Bioconductor
 
 - R packages:
   - Bioconductor: BiomaRt
  

# ===========================================
# COMPILE THE IMAGE
# ===========================================

docker build -t tagc-uorf-orf-datafreeze-script-cross_ref_dl \
  $WORKING_DIR/02_container/script/01_crossreferences_download


# ===========================================
# RUN THE DOCKER
# ===========================================

docker run -it --name tagc-uorf-orf-datafreeze-script-cross_ref_dl \
  -v $WORKING_DIR/data:/data \
  tagc-uorf-orf-datafreeze-script-cross_ref_dl


# ===========================================
# START / STOP THE DOCKER
# ===========================================

docker start -i tagc-uorf-orf-datafreeze-script-cross_ref_dl
docker stop tagc-uorf-orf-datafreeze-script-cross_ref_dl


# ===========================================
# DOWNLOAD THE DATA
# ===========================================

bash $WORKING_DIR/05_script/01_crossreferences_download/download.sh


# ===========================================
# LOAD THE IMAGE FROM THE ARCHIVE
# ===========================================

# To load the image, run the following lines:
gunzip tagc-uorf-orf-datafreeze-script-cross_ref_dl.tar.gz
docker image load -i tagc-uorf-orf-datafreeze-script-cross_ref_dl.tar
