#test
import sys
import time 
import traceback
import requests
import json

#from udiSpanPanelNode import udiSpanPanelNode
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
    Interface = udi_interface.Interface

except ImportError:
    import logging
    logging.basicConfig(level=30)
VERSION = '0.0.1'


if __name__ == "__main__":
    try:
        logging.info('Starting Span Power Panel Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start(VERSION)
        #polyglot.updateProfile()
        #polyglot.setCustomParamsDoc()
        polyglot.ready()
        logging.debug('after subscribe')

        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception:
        logging.error(f"Error starting plugin: {traceback.format_exc()}")
        polyglot.stop()