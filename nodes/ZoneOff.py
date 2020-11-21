
from polyinterface import Node,LOGGER

class ZoneOffNode(Node):

    def __init__(self, controller, parent_address, address, name, physical_status, logical_status):
        LOGGER.debug("ZoneOff:__init__: {} {}".format(address,name))
        self.logical_status = logical_status
        self.physical_status = physical_status
        self.logger    = controller.logger
        super(ZoneOffNode, self).__init__(controller, parent_address, address, name)
        self.lpfx = self.name + ':'

    def start(self):
        LOGGER.debug(f'{self.lpfx}')
        super(ZoneOffNode, self).start()
        # Init values from Zone node
        self.setDriver('ST',self.physical_status)
        self.setDriver('GV0',self.logical_status)

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
