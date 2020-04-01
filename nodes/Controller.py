
import time
import logging
import asyncio
from threading import Thread
from node_funcs import *
from nodes import BaseController
from nodes import AreaNode


import sys
#sys.path.insert(0, "../elkm1")
from elkm1_lib import Elk

#asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
mainloop = asyncio.get_event_loop()

class Controller(BaseController):
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'ELK Controller'
        self.hb = 0
        self.elk = None
        self.elk_st = None
        self.driver = {}
        #Not using because it's called to many times
        #self.poly.onConfig(self.process_config)
        # We track our drsiver values because we need the value before it's been pushed.

    def start(self):
        self.l_info('start',self.name)
        self.server_data = self.poly.get_server_data(check_profile=False)
        self.update_profile() # Always for now.
        self.l_info('start','{} Version {}'.format(self.name,self.server_data['version']))
        self.setDriver('ST', 1)
        self.heartbeat()
        self.check_params()
        self.connect_and_discover()
        self.check_connection()

    def shortPoll(self):
        pass

    def longPoll(self):
        self.heartbeat()
        self.check_connection()

    def setDriver(self,driver,value):
        self.l_debug("setDriver","{}={}".format(driver,value))
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
        self.l_debug('check_connection','st={} elk_st={}'.format(st,self.elk_st))
        if self.elk_st != st:
            # We have been connected, but lost it...
            if self.elk_st is True:
                self.l_error('check_connection','Lost Connection! Will try to reconnect.')
            self.elk_st = st
            if st:
                self.l_debug('check_connection','Connected')
                self.setDriver('GV1', 1)
            else:
                self.l_debug('check_connection','NOT Connected')
                self.setDriver('GV1', 0)

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def callback_area(self, element, changeset):
        # Are we needed anymore?
        if self.areas[element.index] is True:
            return # Nope
        self.l_debug('callback_area','el={} cs={}'.format(element,changeset))
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


    def connect_and_discover(self):
        self.elk_config = {
            # TODO: Support secure which would use elks: and add 'userid': 'xxx', 'password': 'xxx'
            'url' : 'elk://'+self.host,
        }
        # We have to create a loop since we are in a thread
        #mainloop = asyncio.new_event_loop()
        self.logger.setLevel(logging.DEBUG)
        self.l_info('discover','started')
        logging.getLogger('elkm1_lib').setLevel(logging.DEBUG)
        asyncio.set_event_loop(mainloop)
        self.elk = Elk(self.elk_config,loop=mainloop)
        self.l_info('discover','Connecting to Elk...')
        self.elk.connect()
        self.l_info('discover','Waiting for sync to complete...')
        mainloop.run_until_complete(self.elk.sync_complete())
        self.l_info('discover','sync_complete')
        #self.config_complete_timer = self.elk.loop.call_later(1, self.config_complete)
        #if  self.elk.is_connected():
        self.l_info('discover','areas...')
        for an in range(7):
            self.l_info('discover','Area {}'.format(an))
            self.addNode(AreaNode(self, self.elk.areas[an]))
            #self.areas.append(None)
            #self.elk.areas[number].add_callback(self.callback_area)
        print('discover','areas done')
        self.elk_thread = Thread(name='ELK_RUN',target=self.elk.run)
        self.elk_thread.daemon = True
        self.elk_thread.start()

    def elkm1_run(self):
        self.elk.run()


    def delete(self):
        self.l_info('delete','Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        self.l_debug('stop','NodeServer stopping...')
        self.elk.disconnect()

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        self.l_info("process_config","Enter config={}".format(config));
        self.l_info("process_config","Exit");

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
            self.l_error('check_params','host not defined in customParams, please add it.  Using {}'.format(self.host))
        default_code = "Your_ELK_User_Code_for_Polyglot"
        if 'user_code' in self.polyConfig['customParams']:
            try:
                self.user_code = int(self.polyConfig['customParams']['user_code'])
            except:
                self.addNotice('ERROR user_code is not an integer, please fix, save and restart this nodeserver','host')
        else:
            self.user_code = default_code
            self.l_error('check_params','user_code not defined in customParams, please add it.  Using {}'.format(self.host))

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

    def update_profile(self):
        self.l_info('update_profile','')
        return self.poly.installprofile()

    def cmd_update_profile(self,command):
        self.l_info('cmd_update_profile','')
        return self.update_profile()

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': connect_and_discover,
        'UPDATE_PROFILE': cmd_update_profile,
    }
    drivers = [
        {'driver': 'ST',   'value': 0, 'uom': 2},
        {'driver': 'GV1',  'value': 0, 'uom': 2},
    ]
