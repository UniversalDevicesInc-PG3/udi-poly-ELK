
import time
import logging
import asyncio
from threading import Thread
from node_funcs import *
from nodes import AreaNode
from polyinterface import Controller,LOGGER,LOG_HANDLER

import sys
#sys.path.insert(0, "../elkm1")
from elkm1_lib import Elk

#asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
mainloop = asyncio.get_event_loop()

class Controller(Controller):
    def __init__(self, polyglot):
        self.name = 'ELK Controller'
        self.hb = 0
        self.elk = None
        self.elk_st = None
        self.driver = {}
        self.logger = LOGGER
        self.lpfx = self.name + ':'
        #Not using because it's called to many times
        #self.poly.onConfig(self.process_config)
        # We track our drsiver values because we need the value before it's been pushed.
        super(Controller, self).__init__(polyglot)

    def start(self):
        LOGGER.info(f'{self.lpfx} start')
        self.server_data = self.poly.get_server_data(check_profile=False)
        self.update_profile() # Always for now.
        LOGGER.info(f"{self.lpfx} Version {self.server_data['version']}")
        self.set_debug_level(10)
        self.setDriver('ST', 1)
        self.heartbeat()
        self.check_params()
        self.elk_start()

    def heartbeat(self):
        LOGGER.debug(f'{self.lpfx} hb={self.hb}')
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def shortPoll(self):
        pass

    def longPoll(self):
        self.heartbeat()
        self.check_connection()

    def setDriver(self,driver,value):
        LOGGER.debug(f'{self.lpfx} {driver}={value}')
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
        LOGGER.debug(f'{self.lpfx} st={st} elk_st={self.elk_st}')
        if self.elk_st != st:
            # We have been connected, but lost it...
            if self.elk_st is True:
                LOGGER.error(f'{self.lpfx} Lost Connection! Will try to reconnect.')
            self.elk_st = st
            if st:
                LOGGER.debug(f'{self.lpfx} Connected')
                self.setDriver('GV1', 1)
            else:
                LOGGER.debug(f'{self.lpfx} NOT Connected')
                self.setDriver('GV1', 0)

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def callback_area(self, element, changeset):
        # Are we needed anymore?
        if self.areas[element.index] is True:
            return # Nope
        LOGGER.debug(f'{self.lpfx} el={element} cs={changeset}')
        i = element.index
        if self.areas[i] is None:
            # First changeset is allstatus like:
            # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
            self.areas[i] = changeset
        else:
            # Keep track of our changes until the node is addded
            for key in changeset:
                self.areas[i][key] = changeset[key]
        # As soon as we get the real name, add the node.
        if 'name' in self.areas[i]:
            self.areas[i] = True
            # Add our zones

    def connected(self):
        LOGGER.info(f"{self.lpfx} Connected!!!")

    def disconnected(self):
        LOGGER.info(f"{self.lpfx} Disconnected!!!")

    def login(self,succeeded):
        if succeeded:
            LOGGER.info("Login succeeded")
        else:
            LOGGER.error(f'{self.lpfx} Login Failed!!!')

    def sync_complete(self):
        LOGGER.info(f"{self.lpfx} Sync of panel is complete!!!")
        # TODO: Add driver for sync complete status, or put in ST?
        LOGGER.info(f'{self.lpfx} adding areas...')
        for an in range(7):
            LOGGER.info(f'{self.lpfx} Area {an}')
            self.addNode(AreaNode(self, self.elk.areas[an]))
            #self.areas.append(None)
            #self.elk.areas[number].add_callback(self.callback_area)
        LOGGER.info('areas done')

    def timeout(self,msg_code):
        LOGGER.error(f"{self.lpfx} Timeout sending message {msg_code}!!!")

    def unknown(self,msg_code, data):
        LOGGER.error(f"{self.lpfx} Unknown message {msg_code}: {data}!!!")

    def elk_start(self):
        self.elk_config = {
            # TODO: Support secure which would use elks: and add 'userid': 'xxx', 'password': 'xxx'
            'url' : 'elk://'+self.host,
        }
        # We have to create a loop since we are in a thread
        #mainloop = asyncio.new_event_loop()
        LOGGER.info(f'{self.lpfx} started')
        logging.getLogger('elkm1_lib').setLevel(logging.DEBUG)
        asyncio.set_event_loop(mainloop)
        self.elk = Elk(self.elk_config,loop=mainloop)
        LOGGER.info(f'{self.lpfx} Waiting for sync to complete...')
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("login", self.login)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.add_handler("timeout", self.timeout)
        self.elk.add_handler("unknown", self.unknown)
        LOGGER.info(f'{self.lpfx} Connecting to Elk...')
        self.elk.connect()
        LOGGER.info(f'{self.lpfx} Starting Elk Thread, will process data when sync completes...')
        self.elk_thread = Thread(name='ELK_RUN',target=self.elk.run)
        self.elk_thread.daemon = True
        self.elk_thread.start()

    def discover(self):
        # TODO: What to do here, kill and restart the thread?
        pass

    def elkm1_run(self):
        self.elk.run()

    def delete(self):
        LOGGER.info(f'{self.lpfx} Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug(f'{self.lpfx} NodeServer stopping...')
        self.elk.disconnect()

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info(f'{self.lpfx} Enter config={config}');
        LOGGER.info(f'{self.lpfx} process_config done');

    def check_params(self):
        """
        This is an example if using custom Params for user and password and an example with a Dictionary
        """
        self.removeNoticesAll()
        # TODO: Only when necessary
        self.update_profile()
        default_host = "Your_ELK_IP_Or_Host:PortNum"
        if 'host' in self.polyConfig['customParams']:
            self.host = self.polyConfig['customParams']['host']
        else:
            self.host = default_host
            LOGGER.error(f'{self.lpfx} host not defined in customParams, please add it.  Using {self.host}')
        default_code = "Your_ELK_User_Code_for_Polyglot"
        if 'user_code' in self.polyConfig['customParams']:
            try:
                self.user_code = int(self.polyConfig['customParams']['user_code'])
            except:
                self.addNotice('ERROR user_code is not an integer, please fix, save and restart this nodeserver','host')
        else:
            self.user_code = default_code
            LOGGER.error(f'{self.lpfx} user_code not defined in customParams, please add it.  Using {self.user_code}')

        # Make sure they are in the params
        self.addCustomParam( {'host': self.host, 'user_code': self.user_code })

        # Add a notice if they need to change the user/password from the default.
        if self.host == default_host:
            # This doesn't pass a key to test the old way.
            self.addNotice('Please set proper host in configuration page, and restart this nodeserver','host')
        if self.user_code == default_code:
            # This doesn't pass a key to test the old way.
            self.addNotice('Please set proper user_code in configuration page, and restart this nodeserver','code')

        #self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def set_all_logs(self,level):
        LOGGER.setLevel(level)
        # TODO: Set Kasa query logger level
        logging.getLogger('elkm1_lib.elk').setLevel(logging.WARNING)
        logging.getLogger('elkm1_lib.proto').setLevel(logging.WARNING)

    def set_debug_level(self,level):
        LOGGER.info(f'level={level}')
        if level is None:
            level = 20
        level = int(level)
        if level == 0:
            level = 20
        LOGGER.info(f'Seting GV1 to {level}')
        self.setDriver('GV1', level)
        # 0=All 10=Debug are the same because 0 (NOTSET) doesn't show everything.
        slevel = logging.WARNING
        if level <= 10:
            self.set_all_logs(logging.DEBUG)
            if level < 10:
                slevel = logging.DEBUG
        elif level == 20:
            self.set_all_logs(logging.INFO)
        elif level == 30:
            self.set_all_logs(logging.WARNING)
        elif level == 40:
            self.set_all_logs(logging.ERROR)
        elif level == 50:
            self.set_all_logs(logging.CRITICAL)
        else:
            LOGGER.error(f"Unknown level {level}")
        LOG_HANDLER.set_basic_config(True,slevel)

    def update_profile(self):
        LOGGER.info(f'{self.lpfx}')
        return self.poly.installprofile()

    def cmd_update_profile(self,command):
        LOGGER.info(f'{self.lpfx}')
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
