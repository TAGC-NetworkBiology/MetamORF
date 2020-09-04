# -*- coding: utf-8 -*-

import os

from abc import abstractmethod

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.engine import Engine
from sqlalchemy import MetaData
from sqlalchemy import inspect
from sqlalchemy import event

from posix import remove


from fr.tagc.uorf.core.model import *
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.sql import SQLConstants
from fr.tagc.uorf.core.util.option.OptionManager import OptionManager
from fr.tagc.uorf.core.util.option import OptionConstants
from fr.tagc.uorf.core.util.general.GeneralUtil import GeneralUtil
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger


## SQLManager
#  ==========
#
# This class is an abstract class and metaclass of singletons aiming to 
# manage SQL connection to the databases. The singletons inheriting from
# this class are able to manage the creation of a SQLAlchemy sessions to 
# the database it has been initiated with. The singletons handle one single
# engine and one single session opened at a time until it is explicitly 
# asked to close it.
#
class SQLManager( object ):

    __instance = None
    

    ## Constructor of SQLManager
    #  -------------------------
    #
    # Instance variable:
    #     - db_type: String - The database type (SQLite or MySQL).
    #     - db_name: String - The database name.
    #     - db_settings: Dictionary - A dictionary of settings. This may include:
    #                                    - The database name (required).
    #                                    - The database type (SQLite / MySQL) (optional).
    #                                    - For SQLite databases: the folder of SQLite file (optional).
    #                                    - For MySQL databases: the MySQL user, password, host IP and 
    #                                                           port (optional).
    #     - db_uri: String - The URI to the database.
    #     - db_url: String - The URL to the database.
    #     - dbpath: String - The path to the database or the name of the database:
    #                        For SQLite databases, the absolute path to the database.
    #                        For MySQL databases, the name of the database.
    #     - session: Session - A SQLAlchemy Session instance allowing to maintain
    #                          the conversation between Python and the database.
    #     - engine: Engine - A SQLAlchemy Engine instance allowing the connection to the database.
    #     - classname: The name of the current class (used for logs).
    #
    def __init__( self ):
        
        self.db_type = None
        self.db_name = None
        self.db_settings = None
        self.db_uri = None
        self.db_url = None
        self.db_path = None
        self.session = None
        self.engine = None
        
        self.classname = str( self.__class__.__name__ )
                
                

    ## set_db_settings
    #  ---------------
    #
    # Set the settings necessary to established the connection 
    # to the database (i.e. used by the SQLAlchemu session).
    #
    # @param db_settings: Dictionnary - The dictionary of settings. This may include:
    #                                    - The database name (required).
    #                                    - The database type (SQLite / MySQL) (optional).
    #                                    - For SQLite databases: the folder of SQLite file (optional).
    #                                    - For MySQL databases: the MySQL user, password, host IP and 
    #                                                           port (optional).
    #
    # @throw DenCellORFException: When the database name is missing.
    #
    @abstractmethod
    def set_db_settings( self, db_settings ):
        
        # Store the settings of the database
        self.db_settings = db_settings
        
        # Store the database name
        self.db_name = db_settings[ Constants.DB_SETTINGS_DB_NAME ]
        
        # Check that a database name is provided
        if ( self.db_name == None or len( self.db_name ) == 0 ):
            raise DenCellORFException( self.classname + 
                                       '.set_db_settings(): A database name needs to be provided!' )
    
        # Set the database type to default if not provided
        if ( ( Constants.DB_SETTINGS_DB_TYPE in self.db_settings.keys() )
             and ( self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ] != None ) ):
            self.db_type = self.db_settings[ Constants.DB_SETTINGS_DB_TYPE ]
        else:
            self.db_type = SQLConstants.DEFAULT_DB_TYPE
            Logger.get_instance().debug( self.classname + '.set_db_settings(): As no type of database' +
                                         ' has been provided, the database type has been set to ' +  
                                         self.db_type + '.' )
        
        # Set all the parameters to default that are not provided to default
        if ( self.db_type == SQLConstants.DB_TYPE_SQLITE ):
            
            if ( ( Constants.DB_SETTINGS_DB_FOLDER not in self.db_settings.keys() ) 
                 or ( self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] == None ) ):
                self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] = SQLConstants.DEFAULT_SQLITE_PATH
            
            if ( self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ][-1] != '/' ):
                self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] += '/'
            
            
        elif ( self.db_type == SQLConstants.DB_TYPE_MYSQL ):
                    
            if ( ( Constants.DB_SETTINGS_MYSQL_USER not in self.db_settings.keys() )
                 or ( self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] == None ) ):
                self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ] = SQLConstants.DEFAULT_MYSQL_USER_NAME
        
            if ( ( Constants.DB_SETTINGS_MYSQL_PASSWD not in self.db_settings.keys() )
                 or ( self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD ] == None ) ):
                self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD  ] = SQLConstants.DEFAULT_MYSQL_USER_PASSWD                
        
            if ( ( Constants.DB_SETTINGS_MYSQL_HOST not in self.db_settings.keys() ) 
                 or ( self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] == None ) ):
                self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ] = SQLConstants.DEFAULT_HOST_IP
        
            if ( ( Constants.DB_SETTINGS_MYSQL_PORT not in self.db_settings.keys() ) 
                 or ( self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] == None ) ):
                self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] = SQLConstants.DEFAULT_MYSQL_PORT
                
        # Create the database URL
        self.create_db_url()
    
    
    
    ## create_db_url
    #  -------------
    #
    # Create the appropriate database URL according to the type of the database 
    # and known settings. The URL is then stored as an instance attribute.
    #
    @abstractmethod
    def create_db_url( self ):
        
        if ( self.db_type == SQLConstants.DB_TYPE_SQLITE ):
            self.db_path = ( self.db_settings[ Constants.DB_SETTINGS_DB_FOLDER ] + 
                             self.db_name + SQLConstants.SQLITE_EXTENSION )
            self.db_uri = SQLConstants.SQLALCHEMY_SQLITE_URI
            self.db_url = self.db_uri + self.db_path
            
            
        elif ( self.db_type == SQLConstants.DB_TYPE_MYSQL ):
            self.db_path = self.db_name
            self.db_uri = ( SQLConstants.SQLALCHEMY_MYSQL_URI_PREFIX +
                            '{}:{}@{}:{}/'.format( self.db_settings[ Constants.DB_SETTINGS_MYSQL_USER ],
                                                   self.db_settings[ Constants.DB_SETTINGS_MYSQL_PASSWD  ],
                                                   self.db_settings[ Constants.DB_SETTINGS_MYSQL_HOST ],
                                                   self.db_settings[ Constants.DB_SETTINGS_MYSQL_PORT ] ) )
            self.db_url = self.db_uri + self.db_name



    ## build_database
    #  --------------
    #
    # This method allows to build the database model at the expected 
    # location (SQLite file or MySQL server) or to check an existing 
    # database (at the provided location) matches the expected model.
    # 
    # @param db_settings: Dictionnary - A dictionary of settings related to the database.
    #                                   This may include:
    #                                    - The database name.
    #                                    - The database type (SQLite / MySQL).
    #                                    - For SQLite databases: the folder of SQLite file.
    #                                    - For MySQL databases: the MySQL user, password, host IP and port.
    # @param species: String - The species of the database.
    # @param sp_mandatory: Boolean - Does the species name of the database is mandatory? 
    #                                True by default.
    # @param force_overwrite: Boolean - Does any existing DB at the provided location has to 
    #                                   be removed? False by default.
    #
    # @throw DenCellORFException: When the species is not provided whilst expected.
    #
    @abstractmethod
    def build_database( self, db_settings, species, sp_mandatory=True, force_overwrite=False ):
        
        # Store the settings necessary to establish the connection
        self.set_db_settings( db_settings )
        
        # Check that a species is provided
        if ( ( sp_mandatory ) 
             and ( ( species == None ) or ( len( species ) == 0 ) ) ):
            raise DenCellORFException( self.classname + 
                                       '.set_db_settings(): A species needs to be provided!' )
            
        # Get the engine to dedicated database
        self.create_engine()
        
        # Check and / or remove the existing database if necessary
        if ( self.db_type == SQLConstants.DB_TYPE_SQLITE ):
            reset_model = self.build_sqlite_database( force_overwrite )
          
        # Check and / or remove the existing database if necessary
        # and / or create the database on the server if necessary
        elif ( self.db_type == SQLConstants.DB_TYPE_MYSQL ):
            reset_model = self.build_mysql_database( force_overwrite )
        
        # Open a session
        self.create_session()
        
        # If the model does not yet exists, create all the required tables
        if reset_model:
            self.BASE.metadata.create_all( self.engine )
            Logger.get_instance().info( 'The database ' + self.db_path + ' has been created.' )
            
        else:
            Logger.get_instance().info( 'The database ' + self.db_path + ' will be used.' )
        
        self.session.close()
        
            
            
    ## build_sqlite_database
    #  ---------------------
    #
    # This method first checks if a SQLite file already exists at the provided path.
    # If the file exists
    #     - and the forceOverwrite option has been selected, then remove the file.
    #     - and the forceOverwrite option has not been selected, then check the database schema.
    #
    # @param force_overwrite: Boolean - Does any existing DB at the provided location has to be removed?
    #
    # @return Boolean - Does the database structure need to be re-build?
    # 
    @abstractmethod
    def build_sqlite_database( self, force_overwrite ):
                        
        # If there is already a database at the path
        if os.path.exists( self.db_path ):                      
            
            # And the forceOverwrite option has been selected, 
            # then remove the database file
            if force_overwrite:
                self.remove_sqlite_db()
                return True
                
            else:
                # Check if the existing database contains the
                # appropriate model
                if not self.check_database_str_integrity():
                    
                    # Ask the user to confirm the deletion of the database
                    confirm_deletion = None
                    Logger.get_instance().info( 'The database provided does not use the appropriate' +
                                                ' model. Hence, the database will be removed and build' +
                                                ' again using the right model.' )
                    
                    while ( confirm_deletion not in [ 'Y', 'N' ] ):
                        print( ' Do you want to confirm the deletion of the database? (Y/N)' )
                        confirm_deletion = raw_input().upper()
                    
                    # If the user refuse the database to be deleted, log a critical error
                    if ( confirm_deletion == 'N' ):
                        Logger.get_instance().critical( 'As the database does not use the appropriate' +
                                                        ' model and the deletion has been canceled by the' +
                                                        ' user, the program will be stopped. Please see' +
                                                        ' the documentation for more information.' )
                    
                    # Otherwise delete the database and create a new one
                    self.remove_sqlite_db()
                    return True
                
                else:
                    return False
                
        else:
            return True



    ## remove_sqlite_db
    #  ----------------
    #
    # This method allows to remove the database SQLite file.
    #
    # @throw DenCellORFException: When an exception has been raised trying to delete the file.
    #
    @abstractmethod
    def remove_sqlite_db( self ):
           
        if os.path.exists( self.db_path ):
            try:
                remove( self.db_path )
            except Exception as e:
                raise DenCellORFException( 'The database located at ' + str( self.db_path ) + 
                                           ' cannot be deleted.' )
            else:
                Logger.get_instance().info( 'The database file located at ' + str( self.db_path ) + 
                                            ' has been deleted.' )
            
        else:
            Logger.get_instance().error( self.classname + '.remove_sqlite_db(): There is no file' +
                                         ' located at' + str( self.db_path ) + '.' +
                                         ' Error code: ' + LogCodes.ERR_SQL_FILE + '.',
                                         ex = False )
            


    ## build_mysql_database
    #  --------------------
    #
    # This method checks if a database of the provided name already exists 
    # on the MySQL server.
    # If the database exists
    #     - and the forceOverwrite option has been selected, then remove all its content.
    #     - and the forceOverwrite option has not been selected, then check the database schema.
    #
    # @param force_overwrite: Boolean - Does any existing DB at the provided location has to be removed?
    #
    # @return Boolean - Does the database structure need to be re-build?
    # 
    @abstractmethod
    def build_mysql_database( self, force_overwrite ):
            
        # Get the list of existing databases on the server
        eng_server = create_engine( self.db_uri )
        existing_db = eng_server.execute( 'SHOW DATABASES;' )
        existing_db = [ d[0] for d in existing_db ]
        
        # If there is a database of this name
        if ( self.db_name in existing_db ):
            
            # And the forceOverwrite option has been selected,
            # then remove the existing database of the server, 
            # and create an empty new one
            if force_overwrite:
                eng_server.execute( 'DROP DATABASE ' +  self.db_name )
                eng_server.execute( 'CREATE DATABASE ' +  self.db_name )
                Logger.get_instance().info( 'All the content related to the ' + self.db_name + 
                                            ' database has been removed from the MySQL server.' )
                return True
                
            else:
                # Check if the existing database contains the appropriate model
                if ( not self.check_database_str_integrity() ):
                    
                    # Ask the user to confirm the deletion of the database
                    confirm_deletion = None
                    Logger.get_instance().info( 'The database provided does not use the appropriate' +
                                                ' model. Hence, the database will be removed and build' +
                                                ' again using the right model.' )
                    
                    while ( confirm_deletion not in [ 'Y', 'N' ] ):
                        print( ' Do you want to confirm the deletion of the database? (Y/N)' )
                        confirm_deletion = raw_input().upper()
                    
                    # If the user refuse the database to be deleted, log a critical error
                    if confirm_deletion == 'N':
                        Logger.get_instance().critical( 'As the database does not use the appropriate' +
                                                        ' model and the deletion has been canceled by the' +
                                                        ' user, the program will be stopped. Please see' +
                                                        ' the documentation for more information.' )
                    
                    # Otherwise delete the database and create a new one
                    eng_server.execute( 'DROP DATABASE ' +  self.db_name )
                    eng_server.execute( 'CREATE DATABASE ' +  self.db_name )
                    Logger.get_instance().info( 'All the content related to the ' + self.db_name + 
                                                ' database has been removed from the MySQL server.' )
                    return True
                else:
                    return False
                         
        # Otherwise, create an empty database on the server
        else:
            eng_server.execute( 'CREATE DATABASE ' +  self.db_name )
            Logger.get_instance().info( 'No database called ' + self.db_name + 
                                        ' may be found on the MySQL server.' +
                                        ' Hence, an empty database of this name will be created.' )
            return True
        
        
        
    ## check_database_str_integrity
    #  ----------------------------
    #
    # This method checks if the schema of the database matches the model.
    # This methods only check the name of the tables, the name of the columns 
    # and the primary keys. Other features such as the relationships or unique 
    # constraints are not checked.
    #
    # @return Boolean - Does the database structure follow the model?
    # 
    @abstractmethod
    def check_database_str_integrity( self ):
        
        Logger.get_instance().info( 'Checking the structure of the database. Please note that only' +
                                    ' the column names and primary keys will be checked.' +
                                    ' Please see the documentation for more information.' )
        
        # Create the engine if it does not yet exists
        if ( self.engine == None ):
            self.create_engine()
        
        # Get the table names of the existing database
        iengine = inspect( self.engine )
        tables = iengine.get_table_names()
        
        # Build a dictionary of the classes defined in the model
        dict_model_classes = {}
        for ( cl_name, cl_object ) in self.BASE._decl_class_registry.items():
            if not str( cl_name) == '_sa_module_registry':
                dict_model_classes[ str( cl_name ) ] = cl_object
            
        
        db_str_ok = True
        
        # Check that the table names in the database are the same as the one of the model
        model_table_names = sorted( dict_model_classes.keys() )
        db_table_names = sorted( iengine.get_table_names() )
        if ( model_table_names != db_table_names ):
            Logger.get_instance().debug( self.classname + '.check_database_str_integrity():' +
                                         ' The database contains the following tables: "' +
                                         ', '.join( db_table_names ) + '" whilst the tables "' + 
                                         ', '.join( model_table_names ) + '" are expected to be present.' )
            db_str_ok = False
        
        # For each table, check the columns and the primary key
        # NB: Unique constraints, foreign keys and relationships are not checked
        key_iterator = iter( dict_model_classes )
        t = next( key_iterator, None )
        
        while ( t != None ) and ( db_str_ok ):
            
            Logger.get_instance().debug( self.classname + '.check_database_str_integrity():' +
                                         ' Checking the structure of the table ' + str( t ) + '.' )
            
            # Get the corresponding class in the model
            model_cl = dict_model_classes[ t ]
            model_mapper = inspect( model_cl )
            
            # Compare the column names
            db_col_names = [ k[ 'name' ] for k in iengine.get_columns( t ) ]            
            model_col_names = model_mapper.column_attrs.keys()
            if ( db_col_names == [] ):
                Logger.get_instance().debug( self.classname + '.check_database_str_integrity():' +
                                             ' The table ' + str( t ) + ' does not contain any' +
                                             ' column in the database.' )
                db_str_ok = False         
            elif ( sorted( db_col_names ) != sorted( model_col_names ) ):
                Logger.get_instance().debug( self.classname + '.check_database_str_integrity():' +
                                             ' The table ' + str( t ) + ' contains the columns "' + 
                                             ', '.join( db_col_names ) + 
                                             '" whilst the following column names are expected "' + 
                                             ', '.join( model_col_names ) + '" to be present.' )
                db_str_ok = False
                
            # Compare the primary key
            db_pk = iengine.get_primary_keys( t )
            model_pk = [ k.name for k in model_mapper.primary_key ]
            if ( db_str_ok and ( sorted( db_pk ) != sorted( model_pk ) ) ):
                Logger.get_instance().debug( self.classname + '.check_database_str_integrity():' +
                                             ' The table ' + str( t ) + ' of the database has "' + 
                                             ', '.join( db_col_names ) + '" for primary key' +
                                             ' whilst the primary key is expected to be "' + 
                                             ', '.join( model_col_names ) + '".' )
                db_str_ok = False
            
            t = next( key_iterator, None )
            
        return db_str_ok
    

    ## get_session
    #  -----------
    #
    # This method returns the current SQLAlchemy session if it exists or 
    # create a new one if no session has been yet open.
    #
    # @return Session - a new or the current SQLAlchemy session.
    #
    @abstractmethod
    def get_session( self ):

        # Create the session if necessary
        if ( self.session == None ):
            self.create_session()

        return self.session


    ## create_session
    #  --------------
    #
    # This method creates a SQLAlchemy session to the DB.
    #
    @abstractmethod
    def create_session( self ):
        
        # Get the engine
        engine = self.get_engine()
        
        # Open the DB session
        session = sessionmaker()
        session.configure( bind = engine, 
                           autoflush = False, 
                           expire_on_commit = False )
        
        self.session = session()


    ## close_session
    #  -------------
    #
    # This method close the session is there is one opened.
    #
    @abstractmethod
    def close_session( self ):
        
        if ( self.session != None ):
            self.session.close()
            self.session = None


    ## session_exists
    #  --------------
    #
    # This method has only been created for debugging purpose.
    # It returns True if a session is currently opened to the database.
    #
    # @return Boolean: Does a session is currently opened?
    #
    @abstractmethod
    def session_exists( self ):
        
        if ( self.session == None ):
            return False

        else:
            return True


    ## commit
    #  ------
    #
    # This method allows to commit the actual session and to close it right after.
    # If the commit fails, the session is rollbacked and closed and a 
    # DenCellORFException is raised.
    #
    # @throw DenCellORFException: When an exception is raised trying to commit the session.
    #
    @abstractmethod
    def commit( self ):
        try:
            self.get_session().commit()
        except exc.SQLAlchemyError as e:
            self.rollback_session()
            raise DenCellORFException( self.classname + '.commit(): A SQLAlchemy error occurred trying' +
                                       ' to commit the session. Hence the session has been roll backed.', e )
        except Exception as e:
            self.rollback_session()
            raise DenCellORFException( self.classname + '.commit(): An error occurred trying' +
                                       ' to commit the session. Hence the session has been roll backed.', e )
        finally:
            self.close_session()


    ## rollback_session
    #  ----------------
    #
    # This method allows to rollback the session.
    #
    # @throw DenCellORFException: When an exception is raised trying to rollback the session.
    #
    @abstractmethod
    def rollback_session( self ):
        
        try:
            self.get_session().rollback()
        except exc.SQLAlchemyError as e:
            raise DenCellORFException( self.classname + '.rollback(): A SQLAlchemy error occurred trying to' +
                                       ' rollback the session.', e )
        except Exception as e:
            raise DenCellORFException( self.classname + '.rollback(): An error occurred trying to' +
                                       ' rollback the session.', e )



    ## get_engine
    #  ----------
    #
    # This method returns the SQLAlchemy engine to the DB.
    # If the engine do not yet exist, it creates the engine.
    #
    # @return engine: The SQLAlchemy engine of the DB.
    #
    @abstractmethod
    def get_engine( self ):

        if ( self.engine == None ):
            
            if ( self.db_url != None ):
                self.create_engine()
            else:
                return None
        
        return self.engine


    ## create_engine
    #  -------------
    #
    # This method allows to create the SQLAlchemy engine of the DB.
    #
    # @throw DenCellORFException: When an the database type selected by the user is not allowed.
    #
    @abstractmethod
    def create_engine( self ):
        
        if ( self.db_type in SQLConstants.AUTORIZED_DB_TYPES ):
            
            if ( self.db_url != None ):
                
                # Create the engine
                if ( self.db_type == SQLConstants.DB_TYPE_MYSQL ):
                    engine = create_engine( self.db_url + '?charset=utf8mb4', encoding='utf-8', pool_pre_ping=True )
                
                    # Set the maximal allowed size for packet of MySQL
                    @event.listens_for( engine, 'connect' )
                    def set_max_allowed_packet( dbapi_connection, connection_record ):
                        cursor = dbapi_connection.cursor()
                        cursor.execute( 'SET GLOBAL max_allowed_packet = ' + str( SQLConstants.MYSQL_MAX_ALLOWED_PACKET ) )
                        cursor.close()                    
                                        
                    # Set the maximum size of strings get by concatenating objects during queries
                    @event.listens_for( engine, 'connect' )
                    def set_group_concat_max_len( dbapi_connection, connection_record ):
                        cursor = dbapi_connection.cursor()
                        cursor.execute( 'SET group_concat_max_len = ' + str( SQLConstants.MYSQL_GROUP_CONCAT_MAX_LEN ) )
                        cursor.close()
                        
                elif ( self.db_type == SQLConstants.DB_TYPE_SQLITE ):
                    engine = create_engine( self.db_url, encoding='utf-8', pool_pre_ping=True )
                    
                    # Enforce foreign key constraints
                    @event.listens_for( engine, 'connect' )
                    def set_sqlite_pragma( dbapi_connection, connection_record ):
                        cursor = dbapi_connection.cursor()
                        cursor.execute( 'PRAGMA foreign_keys=ON' )
                        cursor.close()
                    
                # Set the maximum memory allowed for the range optimizer
                @event.listens_for( engine, 'connect' )
                def set_range_optimizer_max_mem_size( dbapi_connection, connection_record ):
                    cursor = dbapi_connection.cursor()
                    cursor.execute( 'SET GLOBAL range_optimizer_max_mem_size = ' + str( SQLConstants.RANGE_OPTIMIZER_MAX_MEM_SIZE ) )
                    cursor.close()  
                    
            
            else:
                engine = None
            
        else:
            raise DenCellORFException( 'SQLManger.create_engine(): the database type selected (' + 
                                       SQLConstants.DEFAULT_DB_TYPE + ') is not correct (accepted' +
                                       ' database types: ' + ', '.join( SQLConstants.AUTORIZED_DB_TYPES ) + 
                                       '). Please see the documentation for more information.' )
            
        self.engine = engine
            

    ## db_exists
    #  ---------
    #
    # This method allows to check if the database already exists.
    #
    # @return Boolean - Does the database already exists?
    #
    @abstractmethod
    def db_exists( self ):
        
        db_exists = False

        if ( self.db_type == SQLConstants.DB_TYPE_SQLITE ):
            if os.path.exists( self.db_path ):
                db_exists = True
            
        elif ( self.db_type == SQLConstants.DB_TYPE_MYSQL ):
            
            # Get the list of existing databases on the server
            eng_server = create_engine( self.db_uri )
            existing_db = eng_server.execute( 'SHOW DATABASES;' )
            existing_db = [ d[0] for d in existing_db ]
            
            # If there is a database of this name
            if ( self.db_name in existing_db ):
                db_exists = True
                
        return db_exists
            

    ## get_db_name
    #  -----------
    #
    # This method returns the database name handled by the instance.
    #
    # @return self.db_name
    #
    @abstractmethod
    def get_db_name( self ):
        
        return self.db_name
            

    ## get_declarative_base
    #  --------------------
    #
    # This method returns the database declarative base instance used by the SQLManager.
    #
    # @return self.BASE
    #
    @abstractmethod
    def get_declarative_base( self ):
        
        return self.BASE
        
    
    ## batch_insert_to_db
    #  ------------------
    # 
    # This method allows to insert a list of objects in the database. 
    # Large sets of objects are first split into several batches which are 
    # inserted one at a time. 
    #
    # @param objects_to_insert: List - The list of DenCellORF objects (classes defined in the model
    #                                  module) to insert in the database.
    # @param process: String - The name of the process that generated this list.
    # 
    @abstractmethod
    def batch_insert_to_db( self, objects_to_insert, process='Undefined process' ):
        
        # Report the state of the session prior to data insertion
        Logger.get_instance().debug( self.classname + '.batch_insert_to_db(): A SQL session is currently' +
                                     ' opened (prior to insertion of data from ' + process + '): ' +
                                     str( self.session_exists() ) + '.' )
        
        if objects_to_insert:
            total_count = len( objects_to_insert )
        
        # Insert objects into the database
        if ( objects_to_insert and ( total_count > 0 ) ):
            
            # Get the number of objects of each type in the list
            types_dict = GeneralUtil.get_type_counts_in_list( objects_to_insert )
            types_dict_str = ', '.join( [ str( tp ) + ': ' + str( val ) for ( tp, val ) in types_dict.items() ] )
            
            # Log in debug mode the count of objects expected to be inserted
            Logger.get_instance().debug( self.classname + '.batch_insert_to_db(): ' + 
                                         str( total_count ) + ' objects (' + types_dict_str +
                                         ', from ' + process + ') are expected to be added to the database.' )
            
            # If the set of objects is small enough, add them directly to the database
            if ( total_count < Constants.MAX_COUNT_TO_INSERT ):
                self.add_and_commit( objects_to_add = objects_to_insert, 
                                     process = process )
                self.close_session()    
                
            
            # Otherwise, split the list of objects to insert into several smaller batches
            # and insert them into the database one at a time
            else:
                # Define the minimal index of the list of objects to insert
                min_bound = 0
                
                while ( min_bound < len( objects_to_insert ) ):
                    
                    if ( min_bound + Constants.MAX_COUNT_TO_INSERT ) <= len( objects_to_insert ):
                        max_bound = min_bound + Constants.MAX_COUNT_TO_INSERT
                    else:
                        max_bound = len( objects_to_insert )
                        
                    # Insert objects into the database
                    self.add_and_commit( objects_to_add = objects_to_insert[ min_bound : max_bound ], 
                                         process = process )
                    
                    # Redefine the minimum bound of the interval
                    min_bound = max_bound
                    
                    self.close_session()

        else:
            Logger.get_instance().warning( self.classname + '.batch_insert_to_db():' +
                                           ' There is no data to insert from ' + process + '.' +
                                           ' Warning code: ' + LogCodes.WARN_INSERT_NODATA + '.' )

    
    ## add_and_commit
    #  --------------
    # 
    # This method allows to add objects to the session and commit the session
    # right after.
    # NB: This method DO NOT close the session after the addition of the objects.
    #
    # @param objects_to_add: List - The list of DenCellORF objects (classes defined in the model
    #                               module) to insert in the database.
    # @param process: String - The name of the process that generated the list. 
    #                          'Undefined process' by default.
    #
    # @throw DenCellORFException: When an exception is raised during the addition of objects to
    #                             the database.
    # @throw DenCellORFException: When an exception is raised during the commit of the session.
    # 
    @abstractmethod
    def add_and_commit( self, objects_to_add, process='Undefined process' ):
        
        # Get the number of objects that are expected to be inserted in the database
        total_count = len( objects_to_add )
        
        # Add the objects to the session
        try:
            self.get_session().add_all( objects_to_add )
        except Exception as e:
            # Get the number of objects of each type in the list
            types_dict = GeneralUtil.get_type_counts_in_list( objects_to_add )
            types_dict_str = ', '.join( [ str( tp ) + ': ' + str( val ) for ( tp, val ) in types_dict.items() ] )
            
            raise DenCellORFException( self.classname + '.add_and_commit():' +
                                       ' An error occurred trying to add ' + str( total_count ) +
                                       ' objects (from ' + process  + ') to the session.' +
                                       ' The list was containing the following objects: ' + 
                                       types_dict_str + '.', e )
        
        # Commit changes
        try:
            self.commit()
        except Exception as e:
            # Get the number of objects of each type in the list
            types_dict = GeneralUtil.get_type_counts_in_list( objects_to_add )
            types_dict_str = ', '.join( [ str( tp ) + ': ' + str( val ) for ( tp, val ) in types_dict.items() ] )
            
            raise DenCellORFException( self.classname + '.add_and_commit():' +
                                       ' An error occurred trying to commit changes after addition of ' +
                                       str( total_count ) + ' objects (from ' + process + ') to the session.' +
                                       ' The list was containing the following objects: ' + 
                                       types_dict_str + '.', e )
            
        # Log in debug mode the number of objects successfully inserted
        Logger.get_instance().debug( self.classname + '.add_and_commit(): ' + 
                                     str( total_count ) + ' objects (from ' + process + 
                                     ') have been successfully added to the database.' )

    
    ## add_and_flush
    #  -------------
    # 
    # This method allows to add objects to the session and flush the session
    # right after (WITHOUT COMMITTING).
    # NB: This method DO NOT commit the session and obviously DO NOT close the 
    # session after the addition of the objects.
    #
    # @param objects_to_add: List - The list of DenCellORF objects (classes defined in the model
    #                               module) to insert in the database.
    # @param process: String - The name of the process that generated the list. 
    #                          'Undefined process' by default.
    #
    # @throw DenCellORFException: When an exception is raised during the addition of objects to
    #                             the database.
    # @throw DenCellORFException: When an exception is raised trying to flush the session.
    # 
    @abstractmethod
    def add_and_flush( self, objects_to_add, process='Undefined process' ):
        
        # Add the objects to the session
        try:
            self.get_session().add_all( objects_to_add )
        except Exception as e:
            # Get the number of objects of each type in the list
            types_dict = GeneralUtil.get_type_counts_in_list( objects_to_add )
            types_dict_str = ', '.join( [ str( tp ) + ': ' + str( val ) for ( tp, val ) in types_dict.items() ] )
            
            raise DenCellORFException( self.classname + '.add_and_flush(): ' + 
                                       ' An error occurred trying to add ' + str( total_count ) + 
                                       ' objects (from ' + process + ') to the session.' +
                                       ' The list was containing the following objects: ' + 
                                       types_dict_str + '.', e )
        
        # Flush changes
        try:
            self.get_session().flush()
        except Exception as e:
            # Get the number of objects of each type in the list
            types_dict = GeneralUtil.get_type_counts_in_list( objects_to_add )
            types_dict_str = ', '.join( [ str( tp ) + ': ' + str( val ) for ( tp, val ) in types_dict.items() ] )
            
            raise DenCellORFException( self.classname + '.add_and_flush():' +
                                       ' An error occurred trying to flush the session after addition of ' + 
                                       str( total_count ) + ' objects (from ' + process + ') to it.' +
                                       ' The list was containing the following objects: ' + 
                                       types_dict_str + '.', e )
            