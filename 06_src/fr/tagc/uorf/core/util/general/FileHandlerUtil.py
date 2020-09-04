# -*- coding: utf-8 -*-

import os
import pickle
import csv
import pandas as pd


from fr.tagc.uorf.core.util import DefaultOutputFolder
from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util import LogCodes
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException
from fr.tagc.uorf.core.util.log.Logger import Logger


## FileHandlerUtil
#  ===============
#
# This class contains various static methods which aims 
# to simplify the manipulation of files.
#
class FileHandlerUtil( object ):                        
        
    ## save_obj_to_file
    #  ----------------
    #
    # This is a static method that allows to save Python objects into a binary
    # file. 
    # This allows for instance to recover the objects files created during the 
    # parsing of a source or during the processing stage if the insertion, the
    # update or the commit fails.
    #
    # @param output_folder: String - The path to the output directory.
    #                                Root of the output folder by default.
    # @param filename: String - The name of the file in which the data has to be saved.
    # @param objects_to_save: List - The list of objects that have to be saved.
    # 
    # @throw DenCellORFException: When an exception has been raised trying to save
    #                             the objects in the file.
    # 
    @staticmethod
    def save_obj_to_file( objects_to_save, filename, output_folder=DefaultOutputFolder.OUTPUT_FOLDER ):

        # Create the output folder if it does not yet exist 
        # (and its parent folders if necessary)
        if not os.path.isdir( output_folder ):
            os.makedirs( output_folder )
        
        file_path = os.path.join( output_folder, filename ) + Constants.DENCELLORF_FILES_EXTENSION

        Logger.get_instance().debug( 'FileHandlerUtil.save_obj_to_file(): ' + 
                                     str( len( objects_to_save ) ) + 
                                     ' objects will be saved in ' + file_path + '.' )
        
        # Save the objects in the file
        try:
            with open( file_path, 'wb' ) as objects_to_save_file:
                    obj_to_insert_pickler = pickle.Pickler( objects_to_save_file )
                    obj_to_insert_pickler.dump( objects_to_save )
        except Exception as e:
            raise DenCellORFException( 'FileHandlerUtil.save_obj_to_file(): An error occurred trying' +
                                        ' to save the objects in ' + file_path + 
                                        '. Hence, these data will not be saved.' +
                                        ' Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
        else:
            Logger.get_instance().debug( 'FileHandlerUtil.save_obj_to_file(): ' + 
                                         str( len( objects_to_save ) ) + 
                                         ' objects have been successfully saved in ' + file_path + 
                                         '. This file may be used to recover data later.' +
                                         ' Please see the documentation for more information.')
        
        
        
    ## get_obj_from_file
    #  -----------------
    #
    # This is a static method that allows to get a list of object 
    # from a binary file.
    #
    # @param input_folder: String - The path to the folder where the file is located.
    # @param filename: String - The name of the file containing the data.
    #
    # @throw DenCellORFException: When the file does not exists.
    # @throw DenCellORFException: When an exception has been raised trying to open the 
    #                             file or import its content.
    # 
    @staticmethod
    def get_obj_from_file( input_folder, filename ):

        file_path = os.path.join( input_folder, filename ) + Constants.DENCELLORF_FILES_EXTENSION
        
        # Check the file exists
        if not os.path.exists( file_path ):
            raise DenCellORFException( 'FileHandlerUtil.get_obj_from_file(): No file has been found' +
                                       ' at the path provided (' + file_path + ').' +
                                       ' Please note that some strategies may only be run in certain' +
                                       ' particular cases (e.g. the Restore strategy may only be run' +
                                       ' after a successful run of the Backup strategy).' +
                                       ' Please see the documentation for more information.' )
        
        # Get the list of objects from the file
        Logger.get_instance().debug( 'FileHandlerUtil.get_obj_from_file(): Importing data from ' + 
                                     file_path + '...' )
        
        try:
            with open( file_path, 'rb' ) as saved_objects_file:
                list_of_obj_unpickler = pickle.Unpickler( saved_objects_file )
                list_of_objects = list_of_obj_unpickler.load()
        except Exception as e:
            raise DenCellORFException( 'FileHandlerUtil.get_obj_from_file(): An error occurred trying' +
                                        ' to get the objects saved in ' + file_path + 
                                        '. Hence, these data from this file will not be loaded.' +
                                        ' Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
        else:
            Logger.get_instance().debug( 'FileHandlerUtil.get_obj_from_file(): ' + 
                                         str( len( list_of_objects ) ) + 
                                         ' objects have been successfully loaded from ' + 
                                         file_path + '.' )
        
        return list_of_objects
                        
                        
        
    ## pandas_df_to_csv
    #  ----------------
    #
    # This is a static method that allows to save the content of a 
    # Pandas data frame into a CSV file.
    #
    # @param output_folder: String - The path to the output directory.
    # @param filename: String - The name of the file in which the data frame has to be saved.
    # @param df: Pandas data frame - The Pandas data frame to save.
    # @param file_desc: String - A description of the file to log. 
    # @param sep: String - The field delimiter for the output file. Comma (',') by default.
    # @param ext: String - The extension of the file. 'csv' by default.
    # @param hdr: Boolean - Does the header of the data frame has to be written in the output file?
    #                       True by default.
    # @param idx: Boolean - Does the index of the data frame has to be written in the output file?
    #                       False by default.
    # @param mode: String - The mode in which write the CSV file ('w' or 'a'). 'w' by default.
    # @param encoding: String - The encoding to use for the output file. 'utf-8' by default.
    # 
    # @throw DenCellORFException: When an exception as been raised while saving the data frame
    #                             in the file.
    #
    @staticmethod
    def pandas_df_to_csv( output_folder, filename, df, file_desc='', sep=',', ext='.csv', \
                          hdr=True, idx=False, mode='w', encoding='utf-8' ):

        # Create the output folder if it does not yet exist
        # (and its parent folders if necessary)
        if not os.path.isdir( output_folder ):
            os.makedirs( output_folder )
        
        file_path = os.path.join( output_folder, filename ) + ext

        Logger.get_instance().debug( 'FileHandlerUtil.pandas_df_to_csv(): ' + 
                                     ' The data frame (' + file_desc + ') will be saved in ' + 
                                     file_path + '.' )
        
        # Save the objects in the file
        try:
            df.to_csv( file_path, 
                       sep = sep, 
                       header = hdr, 
                       index = idx,
                       mode = mode,
                       encoding = encoding )
        except Exception as e:
            raise DenCellORFException( 'FileHandlerUtil.pandas_df_to_csv(): An error occurred trying to' +
                                       ' save the pandas dataframe in ' + file_path + 
                                       ' Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
        else:
            Logger.get_instance().debug( 'FileHandlerUtil.pandas_df_to_csv(): ' +
                                         ' The data frame (' + file_desc + 
                                         ') has been successfully saved in ' + file_path + '.' )
                        
        
    ## dict_to_csv
    #  -----------
    #
    # This is a static method that allows to save the content of a dictionary
    # into a CSV file.
    #
    # @param output_folder: String - The path to the output directory.
    # @param filename: String - The name of the file in which the dictionary has to be saved.
    # @param dict: Dictionary - The dictionary to save.
    # @param file_desc: String - A description of the file to log. 
    # @param sort: Boolean - Does the dictionary needs to be writer in the same order as sorted keys?
    #                        False by default.
    # @param sep: String - The field delimiter for the output file. Comma (',') by default.
    # @param ext: String - The extension of the file. 'csv' by default.
    # @param hdr: List - An eventual list of strings that has to be used to create the headers.
    # @param key_func: Function - An optional function to apply to the keys of the dictionary. 
    #                             This would allow for instance to join a list into a string 
    #                             with a particular separator. The function provided could be 
    #                             a lambda function. By default, the identity function.
    # @param val_func: Function - An optional function to apply to the values of the dictionary. 
    #                             This would allow for instance to join a list into a string 
    #                             with a particular separator. The function provided could be 
    #                             a lambda function. By default, the identity function.
    # @param unlist_key: Bool - If True, the keys have to be list (or tuples) that will be unlist
    #                           such as each element will constitute the value of a column. 
    #                           False by default. NB: This parameter is applied AFTER the function.
    # @param unlist_val: Bool - If True, the values have to be list (or tuples) that will be unlist
    #                           such as each element will constitute the value of a column. 
    #                           False by default. NB: This parameter is applied AFTER the function.
    #
    # @throw DenCellORFException: When the header provided does not contain exactly two items.
    # @throw DenCellORFException: When an exception has been raised trying to create the CSV file.
    # 
    @staticmethod
    def dict_to_csv( output_folder, filename, dict, file_desc='', sort=False, sep=',', ext='.csv', \
                     hdr=None, key_func=lambda k: k, val_func=lambda v: v, unlist_key=False, unlist_val=False ):

        # Create the output folder if it does not yet exist 
        # (and its parent folders if necessary)
        if not os.path.isdir( output_folder ):
            os.makedirs( output_folder )
        
        file_path = os.path.join( output_folder, filename ) + ext
        
        Logger.get_instance().debug( 'FileHandlerUtil.dict_to_csv(): The content of the dictionary (' + 
                                     file_desc + ') will be saved in ' + file_path + '.' )
        
        # Save the objects in the file
        try:
            with open( file_path, 'wb' ) as csv_file:
                writer = csv.writer( csv_file, delimiter = sep )
                
                # Write the header if necessary
                if hdr:
                    writer.writerow( hdr )
                
                # Write the dictionary as key, value
                if sort:
                    key_list = sorted( dict.keys() )
                else:
                    key_list = dict.keys() 

                for k in key_list:
                    # Get the value and apply the functions to transform the key 
                    # and value if necessary
                    key = key_func( k )
                    val = val_func( dict.get( k ) )
                    
                    # Write the new row in the file
                    if ( ( not unlist_key ) or ( not isinstance( key, list ) ) ):
                        key = [ key ]
                        
                    if ( ( not unlist_val ) or ( not isinstance( val, list ) ) ):
                        val = [ val ]
                    
                    writer.writerow( key + val )                        
        
        except Exception as e:
            raise DenCellORFException( 'FileHandlerUtil.dict_to_csv(): An error occurred trying to save' +
                                        ' the content of the dictionary in ' + file_path + 
                                        '\n Error code: ' + LogCodes.ERR_FILEHAND + '.', e )
        
        else:
            Logger.get_instance().debug( 'FileHandlerUtil.dict_to_csv(): ' +
                                         ' the content of the dictionary (' + file_desc + 
                                         ') has been successfully saved in ' + file_path + 
                                         '. Please see the documentation for more information.' )
            