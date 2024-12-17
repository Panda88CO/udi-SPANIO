#!/usr/bin/env python3

#import time
from Spanlib import SpanAccess
from udiSpanCircuitNode import udiSpanCircuitNode
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)



class udiSpanPanelNode(udi_interface.Node):
    from  udiLib import node_queue, wait_for_node_done,openClose2ISY, priority2ISY, mask2key, bool2ISY, round2ISY, my_setDriver

    def __init__(self, polyglot, primary, address, name, span_ipadr, token, battery):
        #super(teslaPWStatusNode, self).__init__(polyglot, primary, address, name)
        logging.info(f'_init_ Span Panel Status Node {span_ipadr}, {token}')
        self.poly = polyglot
        self.span_ipadr = span_ipadr
        self.panel_node_adr = address
        self.token = token
        self.battery_backup = battery
        self.ISYforced = False
        self.node_ok = False
        self.address = address
        self.primary = primary
        self.name = name
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        #self.TPW = tesla_info(self.my_TeslaPW, self.site_id)
        #self.TPW.tesla_get_site_info(self.site_id)
        #self.TPW.tesla_get_live_status(self.site_id)
        
        #polyglot.subscribe(polyglot.START, self.start, address)
        self.circuit_access = {}
        
    def start(self):   
        logging.debug('StartSpanIO Panel Node')
        #self.TPW = tesla_info(self.my_TeslaPW, self.site_id)
        logging.info('Adding power wall sub-nodes')
        self.span_panel = SpanAccess(self.span_ipadr, self.token)
        self.update_data()        
        self.create_subnodes()
        self.update_data()
        self.updateISYdrivers()
        self.node_ok = True


    def create_subnodes(self):
        logging.debug(f'create_subnodes - {self.name}')
        code, self.circuits = self.span_panel.getSpanCircuitsInfo()
        logging.debug(f'Panel {self.span_ipadr} Circuits info: {code} , {self.circuits }')            
        if code == 200:
            for circuit in self.circuits:
                logging.debug('adding circuit {} = {}'.format(circuit,self.circuits[circuit]['name'] ))
                circuitADR = circuit[-14:]
                nodeaddress  = self.poly.getValidAddress(circuitADR)
                nodename = self.poly.getValidName(self.circuits[circuit]['name'])
                self.circuit_access[circuit] = udiSpanCircuitNode(self.poly, self.panel_node_adr, nodeaddress, nodename, self.span_panel, str(circuit))
                                                                
    def systemPoll(self, pollList):
        logging.info(f'systemPoll {self.span_ipadr }')
        if self.node_ok:
            self.update_data()   
            self.updateISYdrivers()
            for circuit in self.circuit_access:
                self.circuit_access[circuit].updateISYdrivers()

       
    def update_data(self):
        self.span_panel.update_span_data()
                 

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def node_ready(self):
        return(self.node_ok)




    def updateISYdrivers(self):
        logging.debug('Span Panel updateISYdrivers')
        #logging.debug(f'data: {self.span_panel.span_data}')
        self.my_setDriver('ST', self.openClose2ISY(self.span_panel.get_main_panel_breaker_state()))
        self.my_setDriver('GV0', self.openClose2ISY(self.span_panel.get_panel_door_state()))
        self.my_setDriver('GV1', round(self.span_panel.get_instant_grid_power(),1), 73)
        self.my_setDriver('GV2', round(self.span_panel.get_feedthrough_power(),1), 73)
        self.my_setDriver('GV3', 0 ) # Needs to be updated
        self.my_setDriver('GV4', 0 )  # Needs to be updated 
        if self.battery_backup:
            self.my_setDriver('GV7', int(self.span_panel.get_battery_percentage()), 51 )   
        else:
            self.my_setDriver('GV7', None, 25 )


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        #self.update_PW_data(self.site_id, 'all')
        self.update_data()
        self.updateISYdrivers()

 

    id = 'spanpanel'
    commands = { 'UPDATE': ISYupdate, 
                }
 
    drivers = [
            {'driver': 'ST', 'value': 99, 'uom': 25},  #online         
            {'driver': 'GV0', 'value': 0, 'uom': 25},       
            {'driver': 'GV1', 'value': 0, 'uom': 73},
            {'driver': 'GV2', 'value': 0, 'uom': 73},  
            {'driver': 'GV3', 'value': 0, 'uom': 25}, 
            {'driver': 'GV4', 'value': 0, 'uom': 25},  
            #{'driver': 'GV5', 'value': 0, 'uom': 33},  
            #{'driver': 'GV6', 'value': 0, 'uom': 33}, 
            {'driver': 'GV7', 'value': 0, 'uom': 51},  
                                          
            ]

    
