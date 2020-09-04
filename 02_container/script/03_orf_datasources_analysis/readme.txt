
This image contains:

 - Python 2.7
      With the following Python packages:
     - Pandas
  

# ===========================================
# COMPILE THE IMAGE
# ===========================================

docker build -t tagc-uorf-orf-datafreeze-script-orf_ds_analysis \
  $WORKING_DIR/02_container/script/03_orf_datasources_analysis


# ===========================================
# RUN THE DOCKER
# ===========================================

docker run -it --name tagc-uorf-orf-datafreeze-script-orf_ds_analysis \
  -v ~/$WORKING_DIR/data:/data \
  tagc-uorf-orf-datafreeze-script-orf_ds_analysis


# ===========================================
# START / STOP THE DOCKER
# ===========================================

docker start -i tagc-uorf-orf-datafreeze-script-orf_ds_analysis
docker stop tagc-uorf-orf-datafreeze-script-orf_ds_analysis


# ===========================================
# LOAD THE IMAGE FROM THE ARCHIVE
# ===========================================

# To load the image, run the following lines:
gunzip tagc-uorf-orf-datafreeze-script-orf_ds_analysis.tar.gz
docker image load -i tagc-uorf-orf-datafreeze-script-orf_ds_analysis.tar
