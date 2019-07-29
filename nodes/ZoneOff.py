

import polyinterface
LOGGER = polyinterface.LOGGER

class ZoneOffNode(polyinterface.Node):

    def __init__(self, controller, parent, address, name, state):
        super(ZoneOffNode, self).__init__(controller, parent.address, address, name)
        self.status = state

    def start(self):
        self.set_status(self.status,True)

    def set_status(self,val,force=False):
        val = int(val)
        if force or val != self.status:
            self.status = val
            # Send DOF for SHORT?
            if val == 0:
                self.reportCmd("DOF",2)
        self.setDriver('ST', val)

    def query(self):
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # status
        {'driver': 'ST',  'value': 0, 'uom': 25},
    ]
    id = 'zoneoff'
    commands = {
    }
