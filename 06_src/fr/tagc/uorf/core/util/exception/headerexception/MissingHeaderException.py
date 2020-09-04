# -*- coding: utf-8 -*-Exception


from fr.tagc.uorf.core.util.exception.headerexception.HeaderException import HeaderException


## MissingHeaderException
#  ======================
#
# This class allows to raise exceptions anywhere in the program that are related to
# missing headers in data frames. It inherits from the HeaderException.
#
class MissingHeaderException( HeaderException ):
    
    pass
