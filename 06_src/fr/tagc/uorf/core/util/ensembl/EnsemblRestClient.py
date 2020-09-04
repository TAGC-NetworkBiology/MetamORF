# -*- coding: utf-8 -*-

import time
from urlparse import urlparse
from urllib import urlencode
from urllib2 import Request, urlopen, HTTPError


from fr.tagc.uorf.core.util import Constants
from fr.tagc.uorf.core.util.exception.httpexception.HTTPException import HTTPException
from fr.tagc.uorf.core.util.log.Logger import Logger


## EnsemblRestClient
#  =================
#
# This class is a client for the REST API of Ensembl, allowing 
# to query the Ensembl databases through HTTP.
#
class EnsemblRestClient( object ):
        
    __instance = None
                
    ## Class variables
    #  ---------------
    #    
    # Maximum number of requests per second
    DEFAULT_REQ_PER_SEC = 15
    
    # Number of failed request at which the method should 
    # stop trying to get the result
    MAX_FAILED_REQUEST = 4500
    
    # Dictionary that associates the species short name
    # to the string to use in the Ensembl URL
    SPECIES_NAME_URL = { Constants.SPECIES_CATALOG[ Constants.HSAPIENS ]: 'human',
                         Constants.SPECIES_CATALOG[ Constants.MMUSCULUS ]: 'mouse' }
    

    ## Constructor of EnsemblRestClient
    #  --------------------------------
    #
    # Instance variable:
    #     - server: String - The address of the server.
    #     - max_reqs_per_sec: Integer - The maximum number of requests per seconds allowed.
    #     - req_count: Integer - The number of requests performed from the last re-initialization 
    #                            of counter. This variable is reset to 0 each time the rate limit 
    #                            has been exceed.
    #     - last_req_time: Float - The date of the last request performed (in number of seconds 
    #                              passed since epoch).
    #
    # @param server: String - The address of the server.
    # @param max_reqs_per_sec: Integer - The maximum number of requests per seconds allowed.
    #
    def __init__( self, server = 'http://rest.ensembl.org', max_reqs_per_sec=DEFAULT_REQ_PER_SEC ):
        
        self.server = server
        self.max_reqs_per_sec = max_reqs_per_sec
        self.req_count = 0
        self.last_req_time = 0
    
    
    
    ## perform_request
    #  ---------------
    #
    # This method allows to perform requests using the Ensembl REST API.
    #
    # @param ext: String - The URL extension to use to perform the request.
    # @param hdrs: Dictionary - An optional dictionary of headers settings.
    # @param params: Dictionary - An optional dictionary of parameters.
    #
    # @return result: String - The result of the request.
    #
    # @throw HTTPException: When the request returns an HTTP error.
    #
    def perform_request( self, ext, hdrs = {}, params = None ):
        
        # If the content type is not provided in the headers, set it to text/plain
        if ( 'Content-Type' not in hdrs ):
            hdrs[ 'Content-Type' ] = 'text/plain'
        
        # If parameters are provided, add them to the extension of the URL
        if params:
            ext = ext + '?' + urlencode( params )
            
        # Check if this is necessary to rate limit
        if ( self.req_count >= self.max_reqs_per_sec ):
            
            # Compute the time to wait prior to be able to perform the next request
            delta = time.time() - self.last_req_time
            
            # If the interval of time between the last request and the current time 
            # is below one second, then wait prior to perform the next request
            if delta < 1:
                time.sleep( 1 - delta )
            
            # Re-initialize the counters
            self.last_req_time = time.time()
            self.req_count = 0
            
        # Perform the request
        # If the request:
        # - succeed, then return the result.
        # - is rejected due to rate limit exceed (error 429), then retry 
        #   until the request returns a result.
        # - fails due to availability of the server (error 503), then retry
        #   until it becomes reachable or exceed a defined number of 
        #   unsuccessful requests.
        #
        result = None
        try_request = True
        unsuccessfull_req = 0
                
        while try_request:
            
            try_request = False
            
            # Increase the request counter of 1
            self.req_count += 1
            
            try:
                request = Request( self.server + ext, headers = hdrs )
                response = urlopen( request )
                result = response.read()
            
            except HTTPError as e:
                # If the exception has been raised due to rate limitation 
                # exceed, then retry after a while
                if ( e.code == 429 ):
                    if ( 'Retry-After' in e.headers ):
                        # Get the time to wait prior to perform the next request
                        retry = e.headers[ 'Retry-After' ]
                        Logger.get_instance().debug( 'EnsemblRestClient.perform_request():' +
                                                     ' Rate-limit has been exceed. Waiting ' + str( retry ) +
                                                     'seconds to perform the next request.' )
                        time.sleep( float( retry ) )
                        try_request = True
                
                # If the server is not available, then retry until it becomes available.
                # If the server is still not available after a large number of request, 
                # then stop and raise a HTTPException exception.
                elif ( e.code == 503 ):
                    unsuccessfull_req += 1
                    
                    if ( unsuccessfull_req < self.MAX_FAILED_REQUEST ):
                        try_request = True
                    else:
                        raise HTTPException( 'EnsemblRestClient.perform_request(): the request failed '+
                                             str( unsuccessfull_req ) + ' times due to HTTP 503 error' +
                                             ' (Ensembl server not available).', e, e.code )
                
                # Otherwise, raise a HTTPException
                else:
                    raise HTTPException( 'EnsemblRestClient.perform_request(): the request failed. '+
                                         ' Status code: {}, Reason: {}'.format( e.code, e.reason ), 
                                         e, e.code )
                    
        return result
    
    
    
    ## get_sequence
    #  ------------
    #
    # This method allows to query a sequence using the Ensembl REST API.
    # See the documentation of the perform_request() method for more 
    # information.
    #
    # @param chr: String - The chromosome name (without 'chr' prefix).
    # @param strand: String - The DNA strand.
    # @param start: Integer or String - The genomic coordinates of the first position.
    # @param stop: Integer or String - The genomic coordinates of the last position.
    # @param sp: String - The short name of the species (e.g. Hsapiens).
    # @param genome_version: String - The NCBI genome version (e.g. GRCh38).
    #
    # @return String - The nucleic sequence of the region (in uppercase).
    #
    def get_sequence( self, chr, strand, start, stop, sp, genome_version ):
        
        # If one of the main feature is missing, return None
        if ( ( chr == None )
             or ( strand == None )
             or ( start == None )
             or ( stop == None ) ):
            return None
        
        # Build the URL extension to use to get the appropriate sequence
        ext = ( '/sequence/region/' +
                EnsemblRestClient.SPECIES_NAME_URL[ sp ] +
                '/{}:{}..{}:{}'.format( chr, start, stop, strand ) )
        
        # Set up the parameters necessary to perform the request
        param = { 'coord_system_version': genome_version }
        
        # Perform the request
        sequence = self.perform_request( ext = ext, params = param )
        sequence.upper()
        
        return sequence
            

    ## get_instance
    #  ------------
    #
    # First time create an instance of EnsemblRestClient, 
    # then return this instance.
    #
    # @return the singleton instance
    #
    @staticmethod
    def get_instance():
        
        if ( EnsemblRestClient.__instance == None ):
            EnsemblRestClient.__instance = EnsemblRestClient()

        return EnsemblRestClient.__instance
    