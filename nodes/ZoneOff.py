
from udi_interface import LOGGER
from nodes import BaseNode

class ZoneOffNode(BaseNode):

    def __init__(self, controller, parent_address, address, name, physical_status, logical_status):
        LOGGER.debug("ZoneOff:__init__: {} {}".format(address,name))
        self.controller = controller
        self.logical_status = logical_status
        self.physical_status = physical_status
        try:
            super(ZoneOffNode, self).__init__(controller, parent_address, address, name)
            controller.poly.subscribe(controller.poly.START, self.start, address)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def start(self):
        try:
            LOGGER.debug(f'{self.lpfx}')
            super(ZoneOffNode, self).start()
            # Init values from Zone node
            self.set_driver('GV0',self.physical_status)
            self.set_driver('ST',self.logical_status)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # logical status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # physical status
        {'driver': 'GV0', 'value': 0, 'uom': 25},
    ]
    id = 'zoneoff'
    commands = {
    }
