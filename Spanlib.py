

import requests
import time
import urllib.parse
from datetime import datetime, timezone

try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

class SpanAccess(object):
    from  udiLib import random_string

    def __init__ (self, IPaddress, token):
        self.IP_address = IPaddress
        self.accessToken = token
        
        self.yourApiEndpoint = f'http://{self.IP_address}/api/v1'
        self.STATUS      = '/status'
        #self.SPACES      = '/spaces'
        self.CIRCUITS    = '/circuits'
        self.PANEL       = '/panel'
        self.REGISTER    = '/register'



    def getAccessToken(self):
        logging.debug(f'getAccessToken ({self.IP_address})')        
        return(self.accessToken)

    def putAccessToken(self, accessToken):
        self.accessToken = accessToken
    
    def getSpanCircuitsInfo(self):
        logging.debug(f'getSpanCircuitsInfo ({self.IP_address})')        
        code, circuits = self._callApi('GET', '/circuits')
        return(code, circuits)
    
    def getSpanStatusInfo(self):
        logging.debug(f'getSpanStatusIndo ({self.IP_address})')
        code, status = self._callApi('GET', '/status')
        return(code, status)
    
    def getSpanPanelInfo(self):
        logging.debug(f'getSpanPanelInfo ({self.IP_address})')
        code, panel = self._callApi('GET', '/panel')
        return(code, panel)

    def getSpanBatteryInfo(self):
        logging.debug(f'getSpanBatteryInfo ({self.IP_address})')
        code, battery_perc = self._callApi('GET', '/storage/soe')
        return(code, battery_perc)

    def getSpanClientInfo(self):
        logging.debug(f'getSpanClientInfo ({self.IP_address})')
        code, clients = self._callApi('GET', '/auth/clients')
        return(code, clients)


    def registerSpanPanel(self, force=False):
        logging.debug(f'registerSpanPanel ({self.IP_address})')
        try:
            if self.getAccessToken() == None or force:
                
                data ={
                    'name':'udiSPAN-'+self.random_string(10),
                    'description':'UDI integration of SpanIO panels'
                }
                code, panel = self._callApi('POST', '/auth/clients/register', data)
                if 'accessToken' in panel:
                    self.accessToken = panel['accessToken']
                else:
                    return(None)
            return(self.accessToken)   
        except Exception as e:
            return(None)
             


    def _callApi(self, method='GET', url=None, body=None):
        # When calling an API, get the access token (it will be refreshed if necessary)
        try:
            accessToken = self.getAccessToken()
        except ValueError as err:
            logging.warning('Access token is not yet available. Please authenticate.')
            #self.poly.Notices['auth'] = 'Please initiate authentication'
            return
        if accessToken is None:
            logging.error('Access token is not available')
            return None

        if url is None:
            logging.error('url is required')
            return None

        completeUrl = self.yourApiEndpoint + url

        headers = {
            'Authorization': f"Bearer { accessToken }"
        }

        if method in [ 'PATCH', 'POST'] and body is None:
            logging.error(f"body is required when using { method } { completeUrl }")
        logging.debug(' call info url={}, header= {}, body = {}'.format(completeUrl, headers, body))

        try:
            if method == 'GET':
                response = requests.get(completeUrl, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(completeUrl, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(completeUrl, headers=headers, json=body)
            elif method == 'POST':
                response = requests.post(completeUrl, headers=headers, json=body)
            elif method == 'PUT':
                response = requests.put(completeUrl, headers=headers)

            response.raise_for_status()
            try:
                return response.status_code, response.json()
            except requests.exceptions.JSONDecodeError:
                return response.status_code, response.text

        except requests.exceptions.HTTPError as error:
            logging.error(f"Call { method } { completeUrl } failed: { error }")
            return response.status_code,  error
