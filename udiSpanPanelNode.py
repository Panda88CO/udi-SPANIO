#!/usr/bin/env python3

#import time
from SPANlib import SpanAccess
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)



class udiSpanPanelNode(udi_interface.Node):
    from  udiLib import node_queue, wait_for_node_done, mask2key, bool2ISY, round2ISY, my_setDriver

    def __init__(self, polyglot, primary, address, name, span_ipadr, token):
        #super(teslaPWStatusNode, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Span Panel Status Node {span_ipadr}, {token}')
        self.poly = polyglot
        self.span_ipadr = span_ipadr
        self.token = token
        self.ISYforced = False

        self.node_ok = False
        self.address = address
        self.primary = primary
        self.name = name
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)

        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        #self.TPW = tesla_info(self.my_TeslaPW, self.site_id)
        #self.TPW.tesla_get_site_info(self.site_id)
        #self.TPW.tesla_get_live_status(self.site_id)
        
        #polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):   
        logging.debug('Start Tesla Power Wall Status Node')
        #self.TPW = tesla_info(self.my_TeslaPW, self.site_id)
        logging.info('Adding power wall sub-nodes')
        self.span_panel = SpanAccess(self.span_ipadr, self.token)
       
           
  


        self.updateISYdrivers()
        self.node_ok = True

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def node_ready(self):
        return(self.node_ok)




    def updateISYdrivers(self):


        logging.debug('StatusNode updateISYdrivers')
        '''
        #tmp = self.TPW.getTPW_backup_time_remaining()
        #logging.debug('GV0: {}'.format(tmp))
        self.my_setDriver('ST', self.bool2ISY(self.TPW.getTPW_onLine()))
        self.my_setDriver('GV0', self.round2ISY(self.TPW.getTPW_chargeLevel(self.site_id),1), 51)
        self.my_setDriver('GV1', self.round2ISY(self.TPW.getTPW_solarSupply(self.site_id),2), 30)
        self.my_setDriver('GV2', self.round2ISY(self.TPW.getTPW_batterySupply(self.site_id),2), 30)
        self.my_setDriver('GV3', self.round2ISY(self.TPW.getTPW_load(self.site_id),2), 30)
        self.my_setDriver('GV4', self.round2ISY(self.TPW.getTPW_gridSupply(self.site_id),2), 30)
                
        self.my_setDriver('GV5', self.TPW.getTPW_operationMode(self.site_id))
        self.my_setDriver('GV6', self.TPW.getTPW_gridStatus(self.site_id))
        self.my_setDriver('GV7', self.TPW.getTPW_gridServiceActive(self.site_id))

        self.my_setDriver('GV8', self.round2ISY(self.TPW.getTPW_daysConsumption(self.site_id),2), 33)
        self.my_setDriver('GV9', self.round2ISY(self.TPW.getTPW_daysSolar(self.site_id),2), 33)
        self.my_setDriver('GV10', self.round2ISY(self.TPW.getTPW_daysBattery_export(self.site_id),2), 33)       
        self.my_setDriver('GV11', self.round2ISY(self.TPW.getTPW_daysBattery_import(self.site_id),2), 33)
        self.my_setDriver('GV12', self.round2ISY(self.TPW.getTPW_daysGrid_export(self.site_id),2), 33) 
        self.my_setDriver('GV13', self.round2ISY(self.TPW.getTPW_daysGrid_import(self.site_id),2), 33)
        self.my_setDriver('GV14', self.round2ISY(self.TPW.getTPW_daysGrid_export(self.site_id)- self.TPW.getTPW_daysGrid_import(self.site_id) ,2), 33)


        #self.my_setDriver('GV29', self.round2ISY(self.TPW.getTPW_daysGrid_import(self.site_id) - self.TPW.getTPW_daysGrid_export(self.site_id),2), 33)
        self.my_setDriver('GV28', self.round2ISY(self.TPW.getTPW_daysGeneratorUse(self.site_id),2), 33)
        '''
    '''
    def update_PW_data(self, site_id, level):
        self.TPW.pollSystemData(site_id, level) 
    '''

    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        #self.update_PW_data(self.site_id, 'all')
        self.TPW.pollSystemData(self.site_id, 'all') 
        self.updateISYdrivers()

 

    id = 'pwstatus'
    commands = { 'UPDATE': ISYupdate, 
                }
 
    drivers = [
            {'driver': 'ST', 'value': 99, 'uom': 25},  #online         
            {'driver': 'GV0', 'value': 0, 'uom': 51},       
            {'driver': 'GV1', 'value': 0, 'uom': 33},
            {'driver': 'GV2', 'value': 0, 'uom': 33},  
            {'driver': 'GV3', 'value': 0, 'uom': 33}, 
            {'driver': 'GV4', 'value': 0, 'uom': 33},  
                     
            ]

    
