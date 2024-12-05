

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


spantest = SpanAccess('192.168.1.76')
#token = spantest._callApi('GET', '/register')
code, status = spantest.getSpanStatusInfo()
code, panel = spantest.getSpanPanelInfo()
code, circuits = spantest.getSpanCircuitsInfo()
#code, storage = spantest._callApi('GET', '/storage')
code, battery = spantest.getSpanBatteryInfo()
code, clients = spantest.getSpanClientInfo()
#spaces = spantest._callApi('GET', '/spaces')
print('end')
