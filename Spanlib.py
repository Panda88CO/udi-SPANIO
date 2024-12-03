

import requests
import time
import urllib.parse
from datetime import datetime, timezone
#from udi_interface import LOGGER, Custom
#from oauth import OAuth
try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

class SpanAccess(object):
    def __init__ (self, IPaddress):
        yourSPANip = IPaddress
        self.accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1ZGkgU1BBTklPIDEyMzQ1NDMyMSIsImlhdCI6MTczMzE3MTgxNX0.rNCj_0qBIckxvqPzdHGkTxoyRJ5B_4nym-urym2fjqk'


        self.yourApiEndpoint = f'http://{yourSPANip}/api/v1'
        self.STATUS      = '/status'
        #self.SPACES      = '/spaces'
        self.CIRCUITS    = '/circuits'
        self.PANEL       = '/panel'
        self.REGISTER    = '/register'
        self.accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1ZGkgU1BBTklPIDEyMzQ1NDMyMSIsImlhdCI6MTczMzE3MTgxNX0.rNCj_0qBIckxvqPzdHGkTxoyRJ5B_4nym-urym2fjqk'

    def getAccessToken(self):
        logging.debug('getAccessToken')
        return(self.accessToken)

    
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
                return response.json()
            except requests.exceptions.JSONDecodeError:
                return response.text

        except requests.exceptions.HTTPError as error:
            logging.error(f"Call { method } { completeUrl } failed: { error }")
            return None
