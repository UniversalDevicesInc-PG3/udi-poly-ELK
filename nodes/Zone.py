

import polyinterface
LOGGER = polyinterface.LOGGER

class ZoneNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name):
        super(ZoneNode, self).__init__(controller, primary, address, name)

    def start(self):
        self.setDriver('ST', -1)
        self.setDriver('GV1', -1)
        pass

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [{'driver': 'ST', 'value': 0, 'uom': 2}]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 25},
        {'driver': 'GV1', 'value': 0, 'uom': 25},
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        {'driver': 'GV3', 'value': 0, 'uom': 56},
        {'driver': 'GV4', 'value': 0, 'uom': 25},
        {'driver': 'GV5', 'value': 0, 'uom': 25},
    ]
    id = 'zone'
    commands = {
        'DON': setOn,
        'DOF': setOff
    }
