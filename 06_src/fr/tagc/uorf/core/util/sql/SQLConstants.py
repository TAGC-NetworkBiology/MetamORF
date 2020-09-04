# -*- coding: utf-8 -*-

from fr.tagc.uorf.core.util import DefaultOutputFolder


# ===============================================================================
# Database types
# ===============================================================================

# Database types
DB_TYPE_SQLITE = 'SQLite'
DB_TYPE_MYSQL = 'MySQL'
AUTORIZED_DB_TYPES = [ DB_TYPE_SQLITE, DB_TYPE_MYSQL ]

# Set the default database type
DEFAULT_DB_TYPE = DB_TYPE_SQLITE


# ===============================================================================
# Database default connection settings
# ===============================================================================

# MySQL constants to use as default
DEFAULT_MYSQL_USER_NAME = 'root'
DEFAULT_MYSQL_USER_PASSWD = 'DenCellORFMySQL'
DEFAULT_HOST_IP = '127.0.0.1'
DEFAULT_MYSQL_PORT = '3306'

# Default path to the SQLite directory
DEFAULT_SQLITE_PATH = DefaultOutputFolder.OUTPUT_FOLDER
SQLITE_EXTENSION = '.sqlite'

# URI of the databases
SQLALCHEMY_SQLITE_URI = 'sqlite:///'

SQLALCHEMY_MYSQL_URI_PREFIX = 'mysql://'


# ===============================================================================
# Database particular settings (collation, text length...)
# ===============================================================================

# Default collation to use for strings in the database
DEFAULT_COLLATION = { DB_TYPE_SQLITE : None,
                      DB_TYPE_MYSQL : 'utf8mb4_0900_as_cs' }
                      # NB: 'utf8mb4_0900_as_cs' collation is case-sensitive

# Default length for TEXT
MAX_LEN_TEXT = 16777215
# NB: 16777215 correspond to MEDIUMTEXT size limit in MySQL.
#     See https://dev.mysql.com/doc/refman/8.0/en/string-type-overview.html 
#     for more information.

# Range optimizer maximum memory size
RANGE_OPTIMIZER_MAX_MEM_SIZE = 0


# ===============================================================================
# MySQL particular settings (max_allowed_packet, group_concat_max_len...)
# ===============================================================================

# MySQL values
  # Value for the max_allowed_packet
MYSQL_MAX_ALLOWED_PACKET = 1073741824
  # Value for the group_concat_max_len
MYSQL_GROUP_CONCAT_MAX_LEN = 18446744073709551615
