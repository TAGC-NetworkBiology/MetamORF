# -*- coding: utf-8 -*-


from fr.tagc.uorf.core.util.exception.refexception.RefException import RefException


## RefGeneSearchException
#  ======================
#
# This class allows to raise exceptions anywhere in the program that are related to problems
# encountered during gene search (such as several genes matching one symbol...).
# It inherits from the RefException.
#
class RefGeneSearchException( RefException ):
    
    pass
