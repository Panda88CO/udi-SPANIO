import sys
import time 
import traceback
import requests
import json

from udiSpanPanelNode import udiSpanPanelNode
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
    Interface = udi_interface.Interface

except ImportError:
    import logging
    logging.basicConfig(level=30)


VERSION = '0.0.1'
class SPANController(udi_interface.Node):
    from  udiLib import node_queue, wait_for_node_done, random_string, mask2key, heartbeat, bool2ISY, my_setDriver

    def __init__(self, polyglot, primary, address, name):
        super(SPANController, self).__init__(polyglot, primary, address, name )

        self.poly = polyglot
        logging.info(f'_init_ SPAN Controller ver {VERSION} ')
        self.ISYforced = False
        self.name = name
        self.primary = primary
        self.address = address
        self.name = name
        self.config_done = False
        self.initialized = False
        self.customParam_done = False
        self.n_queue = []
        self.span_panel = {}
        self.span_ip_list = []

        self.customParameters = Custom(self.poly, 'customparams')
        self.customData = Custom(polyglot, 'customdata')
        self.Notices = Custom(self.poly, 'notices')

        #SPAN =SPANController(polyglot, 'controller', 'controller', 'SPAN Panels')
        #polyglot.addNode(TPW)
        
        logging.debug('before subscribe')
        polyglot.subscribe(polyglot.STOP, self.stop)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.customParamsHandler)
        polyglot.subscribe(polyglot.CUSTOMDATA, self.customDataHandler) 
        polyglot.subscribe(polyglot.CONFIGDONE, self.configDoneHandler)
        polyglot.subscribe(polyglot.ADDNODEDONE, self.node_queue)        
        polyglot.subscribe(polyglot.LOGLEVEL, self.handleLevelChange)
        polyglot.subscribe(polyglot.NOTICES, self.handleNotices)
        polyglot.subscribe(polyglot.POLL, self.systemPoll)

        #polyglot.subscribe(polyglot.OAUTH, TPW_cloud.oauthHandler)

        logging.debug('self.address : ' + str(self.address))
        logging.debug('self.name :' + str(self.name))
        self.hb = 0

        self.poly.Notices.clear()
        self.nodeDefineDone = False
        self.longPollCountMissed = 0

        logging.debug('Controller init DONE')
        
        self.poly.addNode(self)
        self.wait_for_node_done()
        #self.poly.updateProfile()
        self.node = self.poly.getNode(self.address)
        logging.debug('Node info: {}'.format(self.node))
        self.my_setDriver('ST', 1)
        logging.debug('Calling start')       
        polyglot.subscribe(polyglot.START, self.start, 'controller')
        self.poly.updateProfile()
        logging.debug('finish Init ')
        


    
    def customDataHandler(self, Data):
        logging.debug('customDataHandler')
        self.customData.load(Data)
        logging.debug('handleData load - {}'.format(self.customData))
    
 
    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True

    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleNotices(self, level):
        logging.info('handleNotices:')

    def customParamsHandler(self, userParams):
        #logging.debug('customParamsHandler 1 : {}'.format(self.TPW_cloud._oauthTokens))
        self.customParameters.load(userParams)
        logging.debug('customParamsHandler called {}'.format(userParams))

        oauthSettingsUpdate = {}
        #oauthSettingsUpdate['parameters'] = {}
        oauthSettingsUpdate['token_parameters'] = {}
        # Example for a boolean field

        if 'LOCAL_IP_ADDRESSES' in self.customParameters:
            if self.customParameters['LOCAL_IP_ADDRESSES'] != 'x.x.x.x':
                ipstring = self.customParameters['LOCAL_IP_ADDRESSES']
                self.span_ip_list= ipstring.split()
                self.NBR_PANELS = len(self.span_ip_list)
                #oauthSettingsUpdate['client_secret'] = self.customParameters['clientSecret']
                #secret_ok = True
        else:
            logging.warning('No LOCAL_IP_ADDRESS found')
            self.customParameters['LOCAL_IP_ADDRESS'] = 'enter list of LOCAL_IP_ADDRESSES (one per panel)'
            self.LOCAL_IP_ADDRESS = None
        logging.debug('customParamsHandler finish ')
        self.customParam_done = True

    def addNodeDoneHandler(self, node):
        pass
        # We will automatically query the device after discovery
        #controller.addNodeDoneHandler(node)

    def registerSpanPanel(self, ipAddress):
        logging.debug(f'registerSpanPanel ({ipAddress})')
        accessToken = None
        try:       
            randomstr =  self.random_string(10)
            logging.debug(f'randomstr: {randomstr}') 
            headers = {'Content-Type': 'application/json',
                       'accept': 'application/json'}
            data ={
                    'name':'udiSPAN-'+randomstr,
                    'description':'UDI integration of SpanIO panels'
                }
    
            completeUrl = f'http://{ipAddress}/api/v1/auth/register'

            response = requests.post(completeUrl, headers=headers, json=data)
            logging.debug(f'response {response} test {response.text}')

            if response.status_code == 200:
                res =  response.json()
                logging.debug(f'res {res}')
                accessToken = res['accessToken']
            else:
                return(None)
            logging.debug(f'AccessToken {accessToken}')
            return(accessToken)   
        except Exception as e:
            logging.debug(f'exception {e}')
            return(None)


    def start(self):
        site_string = ''
        assigned_addresses = []
        logging.debug('start SPAN')
        #logging.debug('start 1 : {}'.format(self.TPW_cloud._oauthTokens))

        #logging.debug('start 2 : {}'.format(self.TPW_cloud._oauthTokens))
        #while not self.customParam_done or not self.TPW_cloud.customNsHandlerDone or not self.TPW_cloud.customDataHandlerDone:
        while not self.customParam_done or not self.config_done:
            logging.info('Waiting for node to initialize')
            logging.debug(' 1 2: {} {}'.format(self.customParam_done , self.config_done))
            time.sleep(1)
        #logging.debug('access {} {}'.format(self.local_access_enabled, self.cloud_access_enabled))
        
        for indx, IPaddress in enumerate(self.span_ip_list):
            #self.span_panel[indx]= SpanAccess(IPaddress)    
            token = None
            nodename = IPaddress
            address = self.poly.getValidAddress(nodename)
            if IPaddress in self.customData.keys():
                token = self.customData[IPaddress]
            else:
                while token == None:
                    token = self.registerSpanPanel(IPaddress)
                    if token != None:
                        self.customData[IPaddress]= token
                    else:
                        self.poly.Notices['panel'] = 'Click Span Panel door switch 3 times to register Panels'
                        time.sleep(10)
            self.poly.Notices.clear()
    
            self.span_panel[indx] = udiSpanPanelNode(self.poly, address, address, nodename, IPaddress, token)    
            # need to retrieve unique ID and Token and store in customData          
            
  
            assigned_addresses.append(address)
     
        
        while not self.config_done:
            time.sleep(5)
        
        logging.debug('Checking for existing nodes not used anymore: {}'.format(self.nodes_in_db))
        for nde in range(0, len(self.nodes_in_db)):
            node = self.nodes_in_db[nde]
            logging.debug('Scanning db for extra nodes : {}'.format(node))
            if node['primaryNode'] not in assigned_addresses:
                logging.debug('Removing node : {} {}'.format(node['name'], node))
                self.poly.delNode(node['address'])

        self.updateISYdrivers()
        self.initialized = True
        #time.sleep(1)
    #def handleNotices(self):
    #    logging.debug('handleNotices')

   

    def stop(self):
        #self.removeNoticesAll()

        self.poly.Notices.clear()
        try:
            if self.TPW:
                self.TPW.disconnectTPW()
        except Exception as e:
            logging.debug('Local logout failed {}'.format(e))
        self.node.setDriver('ST', 0 )
        self.poly.stop()
        logging.debug('stop - Cleaning up')
    

        
    def systemPoll(self, pollList):
        logging.info('systemPoll {}'.format(pollList))
        if self.initialized:    
            if 'longPoll' in pollList:
                self.longPoll()
            elif 'shortPoll' in pollList and 'longPoll' not in pollList:
                self.shortPoll()
        else:
            logging.info('Waiting for system/nodes to initialize')

    def shortPoll(self):
        logging.info('Tesla Power Wall Controller shortPoll')
        self.heartbeat()
        #if self.TPW.pollSystemData('critical'):
        #should make short loop local long pool cloud 
        for site_id in self.PowerWalls:
            self.TPW.pollSystemData(site_id, 'critical')
        for node in self.poly.nodes():
            if node.node_ready():
                logging.debug('short poll node loop {} - {}'.format(node.name, node.node_ready()))
                #node.update_PW_data('all')
                node.updateISYdrivers()
            else:
                logging.info('Problem polling data from Tesla system - {} may not be ready yet'.format(node.name))

    def longPoll(self):
        logging.info('Tesla Power Wall Controller longPoll')
        for site_id in self.PowerWalls:
            if not self.TPW.pollSystemData(site_id, 'all'):
                self.longPollCountMissed += 1
            else:
                self.longPollCountMissed = 0
        for node in self.poly.nodes():
            logging.debug('long poll node loop {} - {}'.format(node.name, node.node_ready()))
            if node.node_ready():
                #node.update_PW_data('all')
                node.updateISYdrivers()
            else:
                logging.info('Problem polling data from Tesla system - {} may not be ready yet'.format(node.name))
    
    def node_ready(self):
        logging.debug(' main node ready {} '.format(self.initialized ))
        return(self.initialized)
    

    def updateISYdrivers(self):
        logging.debug('System updateISYdrivers')       
        
        '''
        #value = self.TPW_cloud.authenticated()
        #if value == 0:
        #   self.longPollCountMissed = self.longPollCountMissed + 1
        #else:
        #   self.longPollCountMissed = 0
        self.my_setDriver('ST', self.bool2ISY( self.cloudAccessUp  or self.localAccessUp ))
        self.my_setDriver('GV2', self.bool2ISY(self.TPW.getTPW_onLine()))
        self.my_setDriver('GV3', self.longPollCountMissed)
        #self.node.setDriver('GV3', self.longPollCountMissed)     
        if self.cloud_access_enabled == False and self.local_access_enabled == False:
            self.my_setDriver('GV4', 0)
        elif self.cloud_access_enabled == True and self.local_access_enabled == False:
            self.my_setDriver('GV4', 1)
        elif self.cloud_access_enabled == False and self.local_access_enabled == True:
            self.my_setDriver('GV4', 2)
        elif self.cloud_access_enabled == True and self.local_access_enabled == True:
            self.my_setDriver('GV4', 3)

        #logging.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
        #logging.debug('CTRL Update ISY drivers : GV3  value:' + str(self.longPollCountMissed) )

        #value = self.TPW.isNodeServerUp()
        #self.node.setDriver('GV2', value)
        #logging.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )

        '''
        
    def update_data(self, site_id, level):
        pass   

    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        self.longPoll()


    id = 'controller'
    commands = { 'UPDATE': ISYupdate }
    drivers = [
            {'driver': 'ST', 'value':0, 'uom':25},
            {'driver': 'GV1', 'value':0, 'uom':25},
            ]

if __name__ == "__main__":
    try:
        logging.info('Starting Span Power Panel Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start(VERSION)
        #polyglot.updateProfile()
        #polyglot.setCustomParamsDoc()
        polyglot.ready()
        logging.debug('after subscribe')
        SPANController(polyglot, 'controller', 'controller', 'SPANIO panels')

        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception:
        logging.error(f"Error starting plugin: {traceback.format_exc()}")
        polyglot.stop()