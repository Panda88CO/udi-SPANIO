

import requests
import time
#import urllib.parse
from Spanlib import SpanAccess
#from datetime import datetime, timezone
#from udi_interface import LOGGER, Custom
#from oauth import OAuth
try:
    from udi_interface import LOGGER, Custom, OAuth
    logging = LOGGER
    Custom = Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1ZGkgU1BBTklPIDEyMzQ1NDMyMSIsImlhdCI6MTczMzE3MTgxNX0.rNCj_0qBIckxvqPzdHGkTxoyRJ5B_4nym-urym2fjqk'
spantest = SpanAccess('192.168.1.76', accessToken)
#token = spantest._callApi('GET', '/register')
code, status = spantest.getSpanStatusInfo()
code, panel = spantest.getSpanPanelInfo()
code, circuits = spantest.getSpanCircuitsInfo()
#code, storage = spantest._callApi('GET', '/storage')
code, battery = spantest.getSpanBatteryInfo()
code, clients = spantest.getSpanClientInfo()
#spaces = spantest._callApi('GET', '/spaces')
for cir in circuits:
    code, circuitInf = spantest.getSpanBreakerInfo(cir)
print('end')
