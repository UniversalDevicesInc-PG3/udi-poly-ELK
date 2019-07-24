

import polyinterface
LOGGER = polyinterface.LOGGER

class ZoneNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name, pyelk_obj):
        super(ZoneNode, self).__init__(controller, primary, address, name)
        self.pyelk = pyelk_obj
        self.state = -2
        self.status = -2

    def start(self):
        self.set_drivers()
        self.pyelk.callback_add(self.pyelk_callback)

    def set_drivers(self):
        self._set_drivers(self.pyelk)

    def _set_drivers(self,pyelk):
        LOGGER.debug('_set_drivers: Zone: {}: state:{}'.format(pyelk.description,pyelk.state))
        self.set_status(pyelk.status)
        self.set_state(pyelk.state)
        self.setDriver('GV2', pyelk.enabled)
        self.setDriver('GV3', pyelk.area)
        self.setDriver('GV4', pyelk.definition)
        self.setDriver('GV5', pyelk.alarm)

    def set_status(self,val):
        val = int(val)
        self.setDriver('ST', val)

    def set_state(self,val):
        val = int(val)
        if val != self.state:
            self.state = val
            # Send DON for Violated?
            if val == 1:
                self.reportCmd("DON",2)
            else:
                self.reportCmd("DOF",2)
        self.setDriver('GV1', val)


    def pyelk_callback(self,data):
        LOGGER.debug('pyelk_callback:zone: self={}, data={}'.format(self,data))
        self._set_drivers(data)

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
        # status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # state
        {'driver': 'GV1', 'value': 0, 'uom': 25},
        # enabled
        {'driver': 'GV2', 'value': 0, 'uom': 2},
        # area
        {'driver': 'GV3', 'value': 0, 'uom': 56},
        # definition type
        {'driver': 'GV4', 'value': 0, 'uom': 25},
        # alarm configuration
        {'driver': 'GV5', 'value': 0, 'uom': 25},
    ]
    id = 'zone'
    commands = {
        'DON': setOn,
        'DOF': setOff
    }
