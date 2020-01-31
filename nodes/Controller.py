

import time
import polyinterface
import logging
import asyncio
from threading import Thread
from node_funcs import *
from nodes import ZoneNode
from nodes import AreaNode
from elkm1_lib import Elk

LOGGER = polyinterface.LOGGER

class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'ELK Controller'
        self.hb = 0
        self.elk_st = None
        self.driver = {}
        #Not using because it's called to many times
        #self.poly.onConfig(self.process_config)
        # We track our driver values because we need the value before it's been pushed.

    def start(self):
        LOGGER.info('Started ELK NodeServer')
        self.setDriver('ST', 1)
        self.heartbeat()
        #self.setDriver('GV1', 0) # This can cause race where later set to 1 gets ignored?
        self.check_params()
        self.discover()

    def shortPoll(self):
        pass

    def longPoll(self):
        self.heartbeat()
        self.check_connection()

    def heartbeat(self):
        LOGGER.debug('heartbeat: hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def setDriver(self,driver,value):
        LOGGER.debug("setDriver: {}={}".format(driver,value))
        self.driver[driver] = value
        super(Controller, self).setDriver(driver,value)

    def getDriver(self,driver):
        if driver in self.driver:
            return self.driver[driver]
        else:
            return super(Controller, self).getDriver(driver)

    # Should not be needed with new library?
    def check_connection(self):
        if self.elk is None:
            st = False
        elif self.elk.is_connected:
            st = True
        else:
            st = False
        # Did connection status change?
        LOGGER.debug("check_connection: st={} elk_st={}".format(st,self.elk_st))
        if self.elk_st != st:
            # We have been connected, but lost it...
            if self.elk_st is True:
                LOGGER.error("check_connection: Lost Connection! Will try to reconnect.")
            self.elk_st = st
            if st:
                LOGGER.debug('check_connection: Connected')
                self.setDriver('GV1', 1)
            else:
                LOGGER.debug('check_connection: NOT Connected')
                self.setDriver('GV1', 0)

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        config = {
            # TODO: Support secure which would use elks: and add 'userid': 'xxx', 'password': 'xxx'
            'url' : 'elk://'+self.host,
        }
        # We have to create a loop since we are in a thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        LOGGER.setLevel(logging.DEBUG)
        self.elk = Elk(config)
        LOGGER.info("Connecting to Elk...")
        self.elk.connect()
        self.check_connection()
        if self.elk_st:
            self.elk_thread = Thread(name='ELK_RUN',target=self.elk.run())
            for number in range(7):
                LOGGER.info('discover: Area {}'.format(number))
                self.addNode(
                    AreaNode(
                        self,
                        self.elk.areas[number]
                    )
                )
            print('discover: add zones done...')

    def delete(self):
        LOGGER.info('Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        self.ELK.stop()
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info("process_config: Enter config={}".format(config));
        LOGGER.info("process_config: Exit");

    def check_params(self):
        """
        This is an example if using custom Params for user and password and an example with a Dictionary
        """
        self.removeNoticesAll()
        # TODO: Only when necessary
        self.update_profile()
        default_host = "YourELK_IP_Or_Host:PortNum"
        if 'host' in self.polyConfig['customParams']:
            self.host = self.polyConfig['customParams']['host']
        else:
            self.host = default_host
            LOGGER.error('check_params: host not defined in customParams, please add it.  Using {}'.format(self.host))

        # Make sure they are in the params
        self.addCustomParam( {'host': self.host })

        # Add a notice if they need to change the user/password from the default.
        if self.host == default_host:
            # This doesn't pass a key to test the old way.
            self.addNotice('Please set proper host in configuration page, and restart this nodeserver','default')
        else:
            self.discover()
        self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def update_profile(self):
        LOGGER.info('update_profile:')
        return self.poly.installprofile()

    def cmd_update_profile(self,command):
        LOGGER.info('cmd_update_profile:')
        return self.update_profile()

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': cmd_update_profile,
    }
    drivers = [
        {'driver': 'ST',   'value': 0, 'uom': 2},
        {'driver': 'GV1',  'value': 0, 'uom': 2},
    ]
