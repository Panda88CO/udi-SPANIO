import sys
import time 
import traceback

from Spanlib import SpanAccess
from udiSpanPanelNode import udiSpanPanelNode
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
    Interface = udi_interface.Interface

except ImportError:
    import logging
    logging.basicConfig(level=30)


VERSION = '0.1.26'
class SPANController(udi_interface.Node):
    from  udiLib import node_queue, wait_for_node_done, mask2key, heartbeat, bool2ISY, my_setDriver

    def __init__(self, polyglot, primary, address, name):
        super(SPANController, self).__init__(polyglot, primary, address, name )

        self.poly = polyglot
        logging.info(f'_init_ TSPAN Controller ver {VERSION} ')
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

        self.Notices = Custom(self.poly, 'notices')

        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)


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
        logging.debug('finish Init ')



    def check_config(self):
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True


    def configDoneHandler(self):
        logging.debug('configDoneHandler - config_done')
        # We use this to discover devices, or ask to authenticate if user has not already done so
        self.poly.Notices.clear()
        self.nodes_in_db = self.poly.getNodesFromDb()
        self.config_done= True

    
    def oauthHandler(self, token):
        self.TPW_cloud.oauthHandler(token)

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

                self.span_ip_list.split(self.customParameters['LOCAL_IP_ADDRESSES'] )
                self.NBR_PANELS = len(self.span_ip_list)
                #oauthSettingsUpdate['client_secret'] = self.customParameters['clientSecret']
                #secret_ok = True
        else:
            logging.warning('No LOCAL_IP_ADDRESS found')
            self.customParameters['LOCAL_IP_ADDRESS'] = 'enter LOCAL_IP_ADDRESS'
            self.LOCAL_IP_ADDRESS = None
        logging.debug('customParamsHandler finish ')
        self.customParam_done = True



    def start(self):
        site_string = ''
        logging.debug('start SPAN:{}'.format(self.TPW_cloud))
        #logging.debug('start 1 : {}'.format(self.TPW_cloud._oauthTokens))
        self.poly.updateProfile()
        #logging.debug('start 2 : {}'.format(self.TPW_cloud._oauthTokens))
        #while not self.customParam_done or not self.TPW_cloud.customNsHandlerDone or not self.TPW_cloud.customDataHandlerDone:
        while not self.customParam_done or not self.config_done:
            logging.info('Waiting for node to initialize')
            logging.debug(' 1 2: {} {}'.format(self.customParam_done , self.config_done))
            time.sleep(1)
        #logging.debug('access {} {}'.format(self.local_access_enabled, self.cloud_access_enabled))
        
        for indx, ipadr in enumerate(self.span_ip_list):
            self.span_panel[indx]= SpanAccess(ipadr)    
            nodename = ipadr
            address = self.poly.getValidAddress(nodename)  
            udiSpanPanelNode(self.poly, address, address, nodename, self.span_panel[indx])    

        if self.cloudAccessUp or self.localAccessUp:            
            #logging.debug('start 3: {}'.format(self.TPW_cloud._oauthTokens))
            self.longPoll()
        else:
            self.poly.Notices['cfg'] = 'Tesla PowerWall NS needs configuration and/or LOCAL_EMAIL, LOCAL_PASSWORD, LOCAL_IP_ADDRESS'
        
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

    def tesla_initialize(self):
        logging.debug('starting Login process')
        try:
            logging.debug('localAccess:{}, cloudAccess:{}'.format(self.localAccess, self.cloudAccess))

            #self.TPW = tesla_info(self.my_Tesla_PW )
            #self.TPW = teslaAccess() #self.name, self.address, self.localAccess, self.cloudAccess)
            #self.localAccess = self.TPW.localAccess()
            #self.cloudAccess = self.TPW.cloudAccess()
            logging.debug('tesla_initialize 1 : {}'.format(self.my_Tesla_PW._oauthTokens))
            if self.cloudAccess:
                logging.debug('Attempting to log in via cloud auth')

                if self.my_Tesla_PW.authendicated():
                    self.cloudAccessUp = True
                else:
                    self.cloudAccessUp =  self.my_Tesla_PW.test_authendication()

                while  not  self.cloudAccessUp:
                    time.sleep(5)
                    logging.info('Waiting to authenticate to complete - press authenticate button')   
                    self.cloudAccessUp =  self.my_Tesla_PW.test_authendication()
    
                #logging.debug('local loging - accessUP {}'.format(self.localAccessUp ))
                self.poly.Notices.clear()

                logging.debug('finished login procedures' )
                logging.info('Creating Nodes')
            
                self.PWs = self.my_Tesla_PW.tesla_get_products()
                logging.debug('self.PWs {}'.format(self.PWs))
                logging.debug('tesla_initialize 2 : {}'.format(self.my_Tesla_PW._oauthTokens))
                for site_id in self.PWs:
                    string = str(self.PWs[site_id]['energy_site_id'])
                    #logging.debug(string)
                    string = string[-14:]
                    #logging.debug(string)
                    node_address =  self.poly.getValidAddress(string)
                    #logging.debug(string)
                    string = self.PWs[site_id]['site_name']
                    #logging.debug(string)
                    node_name = self.poly.getValidName(string)
                    #logging.debug(string)
                    logging.debug('tesla_initialize 3 : {}'.format(self.my_Tesla_PW._oauthTokens))
                    self.TPW = tesla_info(self.TPW_cloud)
                    teslaPWStatusNode(self.poly, node_address, node_address, node_name, self.TPW , site_id)
                    logging.debug('tesla_initialize 4 : {}'.format(self.my_Tesla_PW._oauthTokens))
                    #self.wait_for_node_done()

            else:
                logging.info('Cloud Acces not enabled')
            '''
            if self.localAccess:
                logging.debug('Attempting to log in via local auth')
                try:
                    self.poly.Notices['localPW'] = 'Tesla PowerWall may need to be turned OFF and back ON to allow loacal access'
                    #self.localAccessUp  = self.TPW.loginLocal(local_email, local_password, local_ip)
                    self.localAccessUp  = self.TPW.loginLocal()
                    count = 1
                    while not self.localAccessUp and count < 5:
                        time.sleep(1)
                        self.localAccessUp  = self.TPW.loginLocal()
                        count = count +1
                        logging.info('Waiting for local system access to be established')
                    if not  self.localAccessUp:
                        logging.error('Failed to establish local access - check email, password and IP address')   
                        return
                    logging.debug('local loging - accessUP {}'.format(self.localAccessUp ))

                except:
                    logging.error('local authenticated failed.')
                    self.localAccess = False
            '''
                
 
            
            '''
            node addresses:
               setup node:            pwsetup 'Control Parameters'
               main status node:      pwstatus 'Power Wall Status'
               generator status node: genstatus 'Generator Status'
               
            

            if not self.poly.getNode('pwstatus'):
                node = teslaPWNode(self.poly, self.address, 'pwstatus', 'Power Wall Status', self.TPW, site_id)
                self.poly.addNode(node)
                self.wait_for_node_done()

            if self.TPW.solarInstalled:
                if not self.poly.getNode('solarstatus'):
                    node = teslaPWSolarNode(self.poly, self.address, 'solarstatus', 'Solar Status', self.TPW)
                    self.poly.addNode(node)
                    self.wait_for_node_done()
            else:
                temp = self.poly.getNode('solarstatus')
                if temp:
                    self.poly.delNode(temp)


            if self.TPW.generatorInstalled:
                if not self.poly.getNode('genstatus'):
                    node = teslaPWGenNode(self.poly, self.address, 'genstatus', 'Generator Status', self.TPW)
                    self.poly.addNode(node)
                    self.wait_for_node_done()
            else:
                temp = self.poly.getNode('genstatus')
                if temp:
                    self.poly.delNode(temp)
        
            if self.cloudAccess:
                if not self.poly.getNode('pwsetup'):
                    node = teslaPWSetupNode(self.poly, self.address, 'pwsetup', 'Control Parameters', self.TPW)
                    self.poly.addNode(node)
                    self.wait_for_node_done()
            else:
                self.poly.delNode('pwsetup')
            '''
            logging.debug('Node installation complete')
            self.initialized = True
            self.longPoll()
            self.nodeDefineDone = True
            
            
        except Exception as e:
            logging.error('Exception Controller start: '+ str(e))
            logging.info('Did not connect to power wall')

        #self.TPW.systemReady = True
        logging.debug ('Controller - initialization done')

    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleNotices(self, level):
        logging.info('handleNotices:')


    def addNodeDoneHandler(self, node):
        pass
        # We will automatically query the device after discovery
        #controller.addNodeDoneHandler(node)


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
        logging.debug('System updateISYdrivers - ')       
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
        
    def update_PW_data(self, site_id, level):
        pass   

    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        self.longPoll()


    id = 'controller'
    commands = { 'UPDATE': ISYupdate }
    drivers = [
            {'driver': 'ST', 'value':0, 'uom':25},
            {'driver': 'GV2', 'value':0, 'uom':25},
            {'driver': 'GV3', 'value':99, 'uom':25},
            {'driver': 'GV4', 'value':0, 'uom':25},
            ]

if __name__ == "__main__":
    try:
        #logging.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start(VERSION)
        #polyglot.updateProfile()
        polyglot.setCustomParamsDoc()


        SPAN =SPANController(polyglot, 'controller', 'controller', 'SPAN Panels')
        #polyglot.addNode(TPW)
        
        logging.debug('before subscribe')
        polyglot.subscribe(polyglot.STOP, SPAN.stop)
        polyglot.subscribe(polyglot.CUSTOMPARAMS, SPAN.customParamsHandler)
        polyglot.subscribe(polyglot.CUSTOMDATA, None) 
        polyglot.subscribe(polyglot.CONFIGDONE, SPAN.configDoneHandler)
        #polyglot.subscribe(polyglot.ADDNODEDONE, TPW.node_queue)        
        polyglot.subscribe(polyglot.LOGLEVEL, SPAN.handleLevelChange)
        polyglot.subscribe(polyglot.NOTICES, SPAN.handleNotices)
        polyglot.subscribe(polyglot.POLL, SPAN.systemPoll)
        polyglot.subscribe(polyglot.START, SPAN.start, 'controller')
        logging.debug('Calling start')
        polyglot.subscribe(polyglot.CUSTOMNS, SPAN.customNsHandler)
        #polyglot.subscribe(polyglot.OAUTH, TPW_cloud.oauthHandler)
        logging.debug('after subscribe')
        polyglot.ready()
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception:
        logging.error(f"Error starting plugin: {traceback.format_exc()}")
        polyglot.stop()