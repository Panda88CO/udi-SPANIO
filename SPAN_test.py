

import requests
import json
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

code, battery = spantest.getSpanBatteryInfo()

#code, clients = spantest.getSpanClientInfo()
circuit= {}
for cir in circuits:
    code, circuitInf = spantest.getSpanBreakerInfo(cir)
    circuit[cir]= circuitInf
data = {}
data['status']  = status
data['panel']   = panel
data['circuits'] = circuit
data['battery'] = battery
data['breakers'] = circuit
f = open('.\span.json', 'w')
f.write(str(json.dumps(data)))
f.close()
print('end')
