# -*- coding: utf-8 -*-

import pandas as pd
import math

from statistics import median


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.exception.DenCellORFException import DenCellORFException


## GeneralUtil
#  ===========
#
# This class contains various static methods which may be useful anywhere in the program.
#
class GeneralUtil( object ):
    
    ## is_empty
    #  --------
    #
    # This static method allows to check if a value is considered as 
    # empty or missing.
    #
    # @param val: Integer, Float, String or None - The value to check.
    # @param empty_val: List - A list of values to considered as empty / missing.
    #
    # @return Boolean - True if the value is missing.
    #
    @staticmethod
    def is_empty( val, empty_val = Constants.EMPTY_VALUES ):
        
        if ( ( val in empty_val ) 
             or ( pd.isna( val ) )
             or ( isinstance( val, float ) and ( math.isnan( val ) ) ) ):
            return True
        
        else:
            return False
        
        
        
    ## list_to_dict
    #  ------------
    #
    # This is a static method that allows to generate a dictionary from a list.
    #
    # @param initial_list: List - The list to use to build the dictionary 
    #                             (may be a list of instances of any class).
    #
    # @return dict_from_list: Dictionary - The dictionary build using each feature of 
    #                                      the list as both key AND value.
    #
    @staticmethod
    def list_to_dict( initial_list ):
        
        # If one single attribute is provided as a string, change it into a list
        if isinstance( initial_list, basestring ):
            initial_list = [ initial_list ]
        
        # Build the dictionary from the list
        dict_from_list = {}
        for r in initial_list:
            dict_from_list[ r ] = r
        
        return dict_from_list
        
        
        
    ## string_to_list
    #  --------------
    #
    # This static method allows to convert a string into a list. 
    # When provided, a function (such as int or float) may be applied 
    # to each element of the list.
    #
    # @param str_to_convert: String - The string that needs to be converted.
    # @param fct: String - The (optional) function to apply on each element of 
    #                      the list (e.g. 'int', 'float'...). Can be a lambda function.
    #                      None by default.
    # @param sep: String - The separator used in the string. Comma by by default.
    #
    # @return List - The list of elements get from the string.
    # 
    # @throw DenCellORFException: When the provided object cannot be converted 
    #                             into a list (i.e. is not a string).
    #
    @staticmethod
    def string_to_list( str_to_convert, fct=None, sep=',' ):
        
        if ( str_to_convert == None ):
            return None
        
        if ( isinstance( str_to_convert, basestring ) ):
            str_to_convert = str( str_to_convert ).split( sep )
            
            if fct:
                return map( eval( fct ), str_to_convert )
            
            else:
                return str_to_convert
            
        else:
            raise DenCellORFException( 'GeneralUtil.string_to_list(): The object provided has to be' +
                                       ' a string to be converted (type of the provided object: ' +
                                       str( type( str_to_convert ) ) + ').' )
        
        
        
    ## list_to_string
    #  --------------
    #
    # This static method allows to convert a a list into a string.
    #
    # @param list_to_convert: List - The list that needs to be converted.
    # @param sep: String - The separator to use in the string. Comma by by default.
    # @param not_none: Boolean - If True, the function should raise an exception
    #                            when None is provided instead of the list.
    #                            False by default.
    #
    # @return list_from_str: String - The string computed from the list.
    # 
    # @throw DenCellORFException: When the provided object cannot be converted 
    #                             into a string (i.e. is not a list).
    #
    @staticmethod
    def list_to_string( list_to_convert, sep=',', not_none=False ):
        
        if ( list_to_convert == None ):
            if not_none:
                raise DenCellORFException( 'GeneralUtil.list_to_string(): None has been provided' +
                                           ' instead of a list.' )
            else:
                return None
        
        try:
            list_from_str = sep.join( map( str, list_to_convert ) )
        except Exception as e:
            raise DenCellORFException( 'GeneralUtil.list_to_string(): An error occurred trying to convert' +
                                       ' the list into a string.', e )
        else:
            return list_from_str
        
        
        
    ## query_result_to_list
    #  --------------------
    #
    # This static method allows to convert the result of a query into a list.
    # When one (or several) attribute(s) are specifically queried, the query 
    # returns a list of tuple. This method allows to build a list of all the 
    # values returned by the query for a particular attribute.
    #
    # @param qresult: List of tuples - The result of the SQLAlchemy query.
    # @param att_index: Integer - The index of the attribute to get in the tuple. 
    #                             Equal 0 by default.
    #
    # @return List - The list of attribute values returned by the query.
    # 
    @staticmethod
    def query_result_to_list( qresult, att_index=0 ):
        
        return [ elt[ att_index ] for elt in qresult ]
        
        
        
    ## list_of_2tuples_to_dict
    #  -----------------------
    #
    # This static method allows to convert a list of 2-tuple elements 
    # into a dictionary.
    # The first element of the list is selected as the key of the 
    # dictionary whilst the second is selected as the value.
    #
    # @param tuple_list: List of 2-tuples - The list of 2-tuple elements.
    #
    # @return Dict - The dictionary which associate to each first element of
    #                the tuples in the list heir corresponding second element
    #                of the tuples in the list.
    # 
    @staticmethod
    def list_of_2tuples_to_dict( tuple_list ):
        
        d = {}
        
        for tuple in tuple_list:
            d[ tuple[ 0 ] ] = tuple[ 1 ]
        
        return d
       
    
    
    ## get_type_counts_in_list
    #  -----------------------
    # 
    # This static method allows to build a dictionary containing the 
    # number of objects of each class /type contained in a list.
    #
    # @param ls: List - The list on which the types have to be counted.
    # 
    # @return types_dict: Dictionary - The dictionary that associates the number of 
    #                                  object of each type in the list.
    # 
    @staticmethod
    def get_type_counts_in_list( ls ):
        
        # Get the list of types corresponding to the provided list
        types_list = map( type, ls )
        
        # Get the list of class names corresponding to the provided list
        class_list = map( lambda t: t.__class__.__name__, ls )
        
        # For each type / class, get the number of objects in the list 
        # that are of this type.
        # If there are no duplicates in the class names, use the class name
        # as keys of the dictionary. Otherwise, if there are duplicates in 
        # the class names, use the full name of the type (NB: this could happen 
        # when two classes of the same name have been defined in two different 
        # modules, in such cases the types will be different but not the class
        # names. Nevertheless all the classes defined in that program use
        # distinct class names).
        types_dict = {}
        
        if ( len( set( types_list ) ) == len( set( class_list ) ) ):
            for c in set( class_list ):
                types_dict[ c ] = sum( map( lambda e: e == c, class_list ) )            
            
        else:
            for t in set( types_list ):
                types_dict[ t ] = sum( map( lambda e: e == t, types_list ) )
        
        return types_dict
        
        
        
    ## min_max_median_of_list
    #  ----------------------
    #
    # This static method allows to get the minimal and maximal values of a list.
    # It may convert all the values of the list into a particular type (integer 
    # or float) if necessary.
    #
    # @param list_of_values: List - The list from which get the maximum and minimum.
    #                               This list has to be a list of string, integer or float.
    # @param fct: String - The function to apply on each element of the list ('int' or 'float'). 
    #                      None by default.
    #
    # @return ( min_val, max_val, median_val ) - The minimum, maximum and median values of the list.
    #
    # @throw DenCellORFException: When the provided function is not one of those expected.
    # @throw DenCellORFException: When the list does contains objects which are not integer of float.
    # 
    @staticmethod            
    def min_max_median_of_list( list_of_values, fct=None ):
       
        min_val = None
        max_val = None
        median_val = None
        
        if ( ( list_of_values != None ) and ( len( list_of_values ) > 0 ) ):
        
            if fct:
                # Raise an exception if the provided function is not allowed
                if ( fct not in [ 'int', 'float' ] ):
                    raise DenCellORFException( 'GeneralUtil.min_max_val_of_list(): the function' +
                                               ' provided to convert the element of the list (' +
                                               str( fct ) + ') is not one of those authorized.' +
                                               " It has to be 'int' or 'float'." )
                
                list_of_values = map( eval( fct ), list_of_values )
            
            elif isinstance( list_of_values[ 0 ] , str ):
                raise DenCellORFException( 'GeneralUtil.min_max_val_of_list(): The provided list (' + 
                                           str( list_of_values ) + ' contains strings.' +
                                           ' The elements of the list need to be provided as integer' +
                                           ' or float, or the "fct" option of the method needs to be used.' )
        
            # Get the minimal value of the list
            min_val = min( list_of_values )
            
            # Get the maximal value of the list
            max_val = max( list_of_values )
            
            # Get the median of the list
            median_val = median( list_of_values )            
            
        return( min_val, max_val, median_val )        
    