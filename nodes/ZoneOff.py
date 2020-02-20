
import polyinterface
LOGGER = polyinterface.LOGGER

class ZoneOffNode(polyinterface.Node):

    def __init__(self, controller, parent_address, address, name, physical_status, logical_status):
        LOGGER.debug("ZoneOff:__init__: {} {}".format(address,name))
        self.logical_status = logical_status
        self.physical_status = physical_status
        super(ZoneOffNode, self).__init__(controller, parent_address, address, name)

    def start(self):
        self.l_debug('start','')
        # Init values from Zone node
        self.setDriver('ST',self.physical_status)
        self.setDriver('GV0',self.logical_status)
        super(ZoneOffNode, self).start()

    def l_info(self, name, string):
        LOGGER.info("%s:%s:%s: %s" %  (self.id,self.name,name,string))

    def l_error(self, name, string):
        LOGGER.error("%s:%s:%s: %s" % (self.id,self.name,name,string))

    def l_warning(self, name, string):
        LOGGER.warning("%s:%s:%s: %s" % (self.id,self.name,name,string))

    def l_debug(self, name, string):
        LOGGER.debug("%s:%s:%s: %s" % (self.id,self.name,name,string))

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # physical status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # logical status
        {'driver': 'GV0', 'value': 0, 'uom': 25},
    ]
    id = 'zoneoff'
    commands = {
    }
