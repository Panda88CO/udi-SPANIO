

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
        #self.STATUS      = '/status'
        #self.SPACES      = '/spaces'
        ##self.CIRCUITS    = '/circuits'
        #self.PANEL       = '/panel'
        #self.REGISTER    = '/register'
        self.span_data = {}
        self.accum_data = {}


    def update_panel_status(self):
        try:
            code, status = self.getSpanStatusInfo()
            if code == 200:
                self.span_data['status'] = status                
                return(ConnectionAbortedError)
            else:
                self.span_data['status'] = None
            return(code)
        except Exception as e:
            logging.error(f'EXCEPTION: update_panel_status: {e}')
            return(None)

    def update_panel_info(self):
        try:
            code, panel = self.getSpanPanelInfo()
            if code == 200:
               self.span_data['panel_info'] = panel
            else:
                self.span_data['panel_info'] = None
            return(code )
        except Exception as e:
            logging.error(f'EXCEPTION: update_panel_info: {e}')
            return(None)

    def update_battery_info(self):
        try:
            code, battery = self.getSpanBatteryInfo()
            if code == 200:
               self.span_data['battery_info'] = battery
            else:
                self.span_data['battery_info'] = None
            return(code )
        except Exception as e:
            logging.error(f'EXCEPTION: update_battery_info: {e}')
            return(None)
        

    def update_circuit_info(self):
        try:
            code, circuits = self.getSpanCircuitsInfo()
            if code == 200:
               self.span_data['circuit_info'] = circuits
               self.update_Accum_Energy()
            else:
                self.span_data['circuit_info'] =  None
            return(code )
        except Exception as e:
            logging.error(f'EXCEPTION: update_battery_info: {e}')
            return(None)

    def update_Accum_Energy(self, breaker_id = None):
        logging.debug(f'update_Accum_Energy {breaker_id}')
        if breaker_id == None:
            for breaker_id in self.span_data['circuit_info']:
                self.update_Accum_EnergyBreaker(breaker_id)
        else:
            self.update_Accum_EnergyBreaker(breaker_id)

    def update_Accum_EnergyBreaker(self, breaker_id):
        logging.debug(f'update_Accum_Energy {breaker_id}')
        update_time = self.span_data['circuit_info'][breaker_id]['energyAccumUpdateTimeS']
        produced_energy = self.span_data['circuit_info'][breaker_id]['producedEnergyWh']
        consumed_energy = self.span_data['circuit_info'][breaker_id]['consumedEnergyWh']
        if breaker_id not in self.accum_data:
            self.accum_data[breaker_id] = []
        self.accum_data[breaker_id].append({'time':update_time, 'producedWh':produced_energy, 'consumedWh':consumed_energy})
        time_1_hour = update_time - 60*60
        time_24_hour = update_time - 60*60*24
        t_1hour = update_time
        t_24hour = update_time
        prod_1_hour = produced_energy
        cons_1_hour = consumed_energy
        prod_24_hour =produced_energy
        cons_24_hour = consumed_energy
        hour_ok = False
        day_ok = False
        for indx, meas in enumerate (self.accum_data[breaker_id]):
            if meas['time'] <= time_1_hour:
                hour_ok = True
            if meas['time'] <= time_24_hour:
                day_ok = True
            if (abs(meas['time'] - time_1_hour) < abs(t_1hour-time_1_hour)):
                t_1hour = meas['time']
                prod_1_hour = meas['producedWh']
                cons_1_hour = meas['consumedWh']
            if (abs(meas['time'] - time_24_hour) < abs(t_24hour-time_24_hour)):
                t_24hour = meas['time']
                prod_24_hour = meas['producedWh']
                cons_24_hour = meas['consumedWh']
        remove_list = []
        for indx, meas in enumerate (self.accum_data[breaker_id]):
            if meas['time'] < t_24hour:
                remove_list.append(meas)
        for indx, meas in enumerate(remove_list):
            self.accum_data[breaker_id].remove(meas)


        if  update_time != t_1hour and hour_ok:
            self.span_data['circuit_info'][breaker_id]['prod_1hour'] = (produced_energy-prod_1_hour)*3600/(update_time-t_1hour)
            self.span_data['circuit_info'][breaker_id]['cons_1hour'] = (consumed_energy-cons_1_hour)*3600/(update_time-t_1hour)
            logging.debug(f'1 hour average: prod {produced_energy} - {prod_1_hour} - cons {consumed_energy} - {cons_1_hour} - time {update_time}-{t_1hour}')
        else:
            self.span_data['circuit_info'][breaker_id]['prod_1hour'] = None
            self.span_data['circuit_info'][breaker_id]['cons_1hour'] = None
        if  update_time != t_24hour and day_ok:
            self.span_data['circuit_info'][breaker_id]['prod_24hour'] = (produced_energy-prod_24_hour)*24*3600/(update_time-t_24hour)
            self.span_data['circuit_info'][breaker_id]['cons_24hour'] = (consumed_energy-cons_24_hour)*24*3600/(update_time-t_24hour)
            logging.debug(f'24 hour average: prod {produced_energy} - {prod_24_hour} - cons {consumed_energy} - {cons_24_hour} - time {update_time}-{t_24hour}')
        else:
            self.span_data['circuit_info'][breaker_id]['prod_24hour'] = None
            self.span_data['circuit_info'][breaker_id]['cons_24hour'] = None


            
    def get1HourAverage(self, breaker_id):
        logging.debug(f'get1HourAverage {breaker_id}')
        return(self.span_data['circuit_info'][breaker_id]['prod_1hour'], self.span_data['circuit_info'][breaker_id]['cons_1hour'] )

    def get24HourAverage(self, breaker_id):
        logging.debug(f'get24HourAverage {breaker_id}')
        return(self.span_data['circuit_info'][breaker_id]['prod_24hour'], self.span_data['circuit_info'][breaker_id]['cons_24hour'] )


    def update_panel_breaker_info(self, breaker_id):
        try:
            code, breaker_info = self.getSpanBreakerInfo(breaker_id)
            if code == 200:
               self.span_data['circuit_info'][breaker_id] = breaker_info
               self.update_Accum_EnergyBreaker(breaker_id)
            else:
                self.span_data['circuit_info'][breaker_id]  = None
            return(code )
        except Exception as e:
            logging.error(f'EXCEPTION: update_panel_breaker_info: {e}')
            return(None)

    def update_span_data(self):
        logging.debug(f'updateSpanData ({self.IP_address})')
        self.update_panel_status()
        logging.debug('panel status {}'.format(self.span_data['status']))
        self.update_panel_info()     
        logging.debug('panel info {}'.format(self.span_data['panel_info']))
        self.update_battery_info()
        logging.debug('battery info {}'.format(self.span_data['battery_info']))
        self.update_circuit_info()        
        logging.debug('circuit info {}'.format(self.span_data['circuit_info']))

    def get_panel_door_state(self):
        logging.debug('get_panel_door_state')
        try:
            return(self.span_data['status']['system']['doorState'])
        except Exception as e:
            return(None)
        

    def get_battery_percentage(self):
        logging.debug('get_battery_percentage')
        logging.debug('data {}'.format(self.span_data['battery_info']))
        try:
            return(self.span_data['battery_info']['soe']['percentage'])
        except Exception as e:
            return(None)


    def get_main_panel_breaker_state(self):
        logging.debug('get_main_panel_breaker_state')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['mainRelayState'])
        except Exception as e:
            return(None)    


    def get_grid_state(self):
        logging.debug('get_grid_state')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['dsmGridState'])
        except Exception as e:
            return(None)    


    def get_dms_state(self):        
        logging.debug('get_dms_state')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['dsmState'])
        
        except Exception as e:
            return(None)    


    def get_dms_run_config(self):    
        logging.debug('get_dms_run_config')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['currentRunConfig'])
        except Exception as e:
            return(None)    


    def get_instant_grid_power(self):         
        logging.debug('get_instant_grid_power')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['instantGridPowerW'])
        except Exception as e:
            return(None)    

    def get_feedthrough_power(self):              
        logging.debug('get_feedthrough_power')
        logging.debug('data {}'.format(self.span_data['panel_info']))
        try:
            return(self.span_data['panel_info']['feedthroughPowerW'] )
        except Exception as e:
            return(None)    


    def get_breaker_state(self, breaker_id):
        logging.debug(f'get_breaker_state {breaker_id}')
        logging.debug('data {}'.format(self.span_data['circuit_info'][breaker_id]))
        try:
            return(self.span_data['circuit_info'][breaker_id]['relayState'] )
        except Exception as e:
            return(None)    

    def get_breaker_priority(self, breaker_id):
        logging.debug(f'get_breaker_priority {breaker_id}')
        logging.debug('data {}'.format(self.span_data['circuit_info'][breaker_id]))
        try:
            return(self.span_data['circuit_info'][breaker_id]['priority'] )
        except Exception as e:
            return(None)    


    def get_breaker_instant_power(self, breaker_id):
        logging.debug(f'get_breaker_instant_power {breaker_id}')
        logging.debug('data {}'.format(self.span_data['circuit_info'][breaker_id]))
        try:
            pwr = self.span_data['circuit_info'][breaker_id]['instantPowerW']
            delay_time = int(time.time() -self.span_data['circuit_info'][breaker_id]['instantPowerUpdateTimeS'])
            return(pwr,  delay_time )
        except Exception as e:
            return(None)    

    def get_breaker_energy_info(self, breaker_id):
        logging.debug('get_breaker_energy_info {breaker_id}')
        try:
            produced_energy =  self.span_data['circuit_info'][breaker_id]['producedEnergyWh']
            consumed_energy = self.span_data['circuit_info'][breaker_id]['consumedEnergyWh'] 
            delay_time = int(time.time() -self.span_data['circuit_info'][breaker_id]['energyAccumUpdateTimeS'])
            return(produced_energy, consumed_energy, delay_time)
        except Exception as e:
            return(None)    

    def set_breaker_state(self, breaker_id, state):
        logging.debug(f'set_breaker_state {breaker_id} {state}')
        code, return_data = self.setBreakerState(breaker_id, state)
        logging.debug(f'return {code}, {return_data}')
        if code == 200:
            self.span_data['circuit_info'][breaker_id] = return_data
        return(code == 200)

    def set_breaker_priority(self, breaker_id, priority):
        logging.debug(f'set_breaker_priority {breaker_id} {priority}')
        code, return_data = self.setBreakerPriority(breaker_id, priority)
        logging.debug(f'return {code}, {return_data}')
        if code == 200:
            self.span_data['circuit_info'][breaker_id] = return_data
        return( code == 200)


############################

    def setBreakerState(self, id, state):
        logging.debug(f'setBreakerState {id}  {state}')
        if state in ['OPEN', 'CLOSED']:
            data =  {
                    "relayStateIn":{"relayState":str(state)}
                    }                
            code, breaker_info = self._callApi('POST', '/circuits/'+str(id), data)
            return(code, breaker_info)
        else:
            return None, None

    def setBreakerPriority(self, id, priority):
        logging.debug(f'setBreakerState {id}  {priority}')
        if priority in ['MUST_HAVE', 'NICE_TO_HAVE', 'NOT_ESSENTIAL' ]:
            data =  {
                    "priorityIn":{"priority":str(priority)}
                    }                
            code, breaker_info = self._callApi('POST', '/circuits/'+str(id), data)
            return(code, breaker_info)
        else:
            return None, None


    def getAccessToken(self):
        logging.debug(f'getAccessToken ({self.IP_address})')        
        return(self.accessToken)

    def putAccessToken(self, accessToken):
        self.accessToken = accessToken
    
    def getSpanCircuitsInfo(self):
        logging.debug(f'getSpanCircuitsInfo ({self.IP_address})')        
        code, circuits = self._callApi('GET', '/circuits')
        if code == 200:
            return(code, circuits['circuits'])
        else:
            return(code, circuits)
    

    def getSpanBreakerInfo(self, id):
        logging.debug(f'getSpanBreakerInfo ({self.IP_address})')        
        code, circuitInf = self._callApi('GET', '/circuits/'+str(id))
        return(code, circuitInf)
    

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
