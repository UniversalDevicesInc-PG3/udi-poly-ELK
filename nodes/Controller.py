

import polyinterface
from node_funcs import *
from nodes import ZoneNode
import PyElk

LOGGER = polyinterface.LOGGER


class Controller(polyinterface.Controller):
    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(Controller, self).__init__(polyglot)
        self.name = 'ELK Controller'
        #Not using because it's called to many times
        #self.poly.onConfig(self.process_config)

    def start(self):
        LOGGER.info('Started ELK NodeServer')
        self.setDriver('ST', 1)
        self.setDriver('GV1', 0)
        self.check_params()
        self.discover()
        self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    def query(self):
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        config = {'host' : self.host,
            #'zone' : {'include' : '1-38', 'exclude' : '15-20'},
        }

        self.ELK = PyElk.Elk(config, log=LOGGER)
        self.ELK.connect()

        if self.ELK.status == ELK.STATE_DISCONNECTED:
            self.setDriver('GV1', 0)
            _LOGGER.info('discover: Error connecting')
        else:
            _LOGGER.info('discover: Connected, start rescan...')
            self.setDriver('GV1', 1)
            self.ELK.rescan()
            _LOGGER.info('discover: rescan done...')
            time.sleep(1)
            versions = self.ELK.get_version()
            LOGGER.info('discover: versions {}'.format(versions))
            for o in range(0,len(self.ELK.ZONES)):
                zone = self.ELK.ZONES[o]
                # TODO: Is this the right way?  Or use configured?
                if zone.description is not None:
                    LOGGER.info('PyElk-test: Zone: {}: {} state:{}'.format(o,zone.description,zone.state))
                    self.addNode(
                      ZoneNode(
                        self,
                        self.address,
                        get_valid_node_address('zone_%03d' % (zone.number - 1)),
                        zone.description,
                        zone
                      )
                    )
            print('discover: add zones done...')

    def delete(self):
        LOGGER.info('Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
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

    def update_profile(self):
        LOGGER.info('update_profile:')
        return self.cmd_update_profile('')

    def cmd_update_profile(self,command):
        LOGGER.info('cmd_update_profile:')
        return self.poly.installprofile()

    id = 'controller'
    commands = {
        'QUERY': query,
        'DISCOVER': discover,
        'UPDATE_PROFILE': cmd_update_profile,
    }
    drivers = [
        {'driver': 'ST',   'value': 0, 'uom': 22},
        {'driver': 'GV1',  'value': 0, 'uom': 22},
    ]
