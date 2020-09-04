
This docker compose uses:

 - MySQL 8.0.16 server image (downloaded from Docker-hub)
 - Adminer 4.7.1 image (downloaded from Docker-hub)
  

# ===========================================
# RUN THE DOCKER-COMPOSE
# ===========================================

cd $WORKING_DIR/02_container/mysql
docker-compose up -d


# ===========================================
# ADD NEW USERS TO THE DATABASE
# ===========================================

# Add read-only user to database
  # Connect to MySQL server as root
  docker exec -it tagc-uorf-orf-datafreeze-mysql-server '/bin/bash'
  mysql -u root -p
  
  # Create the new user with read-only permission
  # on all databases on the MySQL server
  CREATE USER 'metamORF-read-user'@'%' IDENTIFIED BY 'MetamORFDB';
  FLUSH PRIVILEGES;

  # Provide access to all databases
  GRANT SELECT ON *.* TO 'uORF-read-user'@'%';
  FLUSH PRIVILEGES;

  # Check grants for new user (Optional)
  SHOW GRANTS FOR 'uORF-read-user'@'%';

  # Quit MySQL server and docker
  exit
  exit


# ===========================================
# UPDATE ADMINER UPLOAD SIZE LIMITS
# ===========================================

# Adminer may reject import of large databases when they 
# exceed the PHP server limit
# To update these, use the following command line 
docker exec -it -u root tagc-uorf-orf-datafreeze-mysql-adminer /bin/sh -c \
  'printf "upload_max_filesize = 700M\n\
   post_max_size = 700 M\n\
   memory_limit = 3G\n\
   max_execution_time = 700\n\
   max_input_vars = 10000" \
   > /usr/local/etc/php/conf.d/0-upload_large_dumps.ini'


# ===========================================
# LOAD THE IMAGES FROM THE ARCHIVE
# ===========================================

# To load the image, run the following lines:
gunzip mysql.tar.gz
docker image load -i mysql.tar

gunzip adminer.tar.gz
docker image load -i adminer.tar
