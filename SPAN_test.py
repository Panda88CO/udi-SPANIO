#!/usr/bin/env python3
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
f = open('.\span.json', 'w')
f.wrinte('data={')
accessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1ZGkgU1BBTklPIDEyMzQ1NDMyMSIsImlhdCI6MTczMzE3MTgxNX0.rNCj_0qBIckxvqPzdHGkTxoyRJ5B_4nym-urym2fjqk'
spantest = SpanAccess('192.168.1.76', accessToken)
#token = spantest._callApi('GET', '/register')
code, status = spantest.getSpanStatusInfo()
#f.write('status  \n')
f.write(str(json.dumps(status)))
code, panel = spantest.getSpanPanelInfo()
#f.write('Panel  \n')
f.write(str(json.dumps(panel)))
code, circuits = spantest.getSpanCircuitsInfo()
#f.write('Circuits  \n')
f.write(str(json.dumps(circuits)))
#code, storage = spantest._callApi('GET', '/storage')
code, battery = spantest.getSpanBatteryInfo()
#f.write('battery  \n')
f.write(str(json.dumps(battery)))
code, clients = spantest.getSpanClientInfo()
#f.write('client  \n')
#f.write(str(json.dumps(clients)))
#spaces = spantest._callApi('GET', '/spaces')
f.wrinte('datcircuits={')
for cir in circuits:
    code, circuitInf = spantest.getSpanBreakerInfo(cir)
    #f.write(f'circuit {cir} \n')
    f.write(str(json.dumps(circuitInf)))
f.wrinte('}}') 
f.close()
print('end')
