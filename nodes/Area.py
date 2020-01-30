

import os.time
import polyinterface
LOGGER = polyinterface.LOGGER

class AreaNode(polyinterface.Node):

    def __init__(self, controller, number):
        self.init   = False
        self.status = -1
        self.state  = -1
        self.elk    = controller.ELK.zones[number]
        # We set the call back and wait for it to be called...
        self.elk.add_callback(self.callback)
        LOGGER.debug('Area {} waiting to be initialized...'.format(number))
        while (not self.init):
            sleep 1
        address     = 'area_{}'.format(number)
        name        = self.elk.name
        super(AreaNode, self).__init__(controller, address, address, name)

    def callback(self, element, changeset):
        LOGGER.debug('Area callback: el={} cs={}'.format(element,changeset))
        self.init   = True

    def start(self):
        self.set_drivers()
        self.pyelk.callback_add(self.pyelk_callback)

    def set_drivers(self):
        self._set_drivers(self.pyelk)

    def _set_drivers(self,pyelk):
        LOGGER.debug('_set_drivers: Area:{}'
                    .format(pyelk.number))
        self.set_status(pyelk.status)
        self.setDriver('GV0', pyelk.arm_up)
        self.setDriver('GV1', pyelk._alarm) # No method?
        self.setDriver('GV2', pyelk.chime_mode)

    def set_status(self,val,force=False):
        if val is None:
            val = 0
        else:
            val = int(val)
        if force or val != self.status:
            self.status = val
            # Send DON for Violated?
            #if val == 2:
            #    self.reportCmd("DON",2)
            #else:
            #    self.reportCmd("DOF",2)
        self.setDriver('ST', val)

    def set_state(self,val):
        val = int(val)
        self.setDriver('GV0', val)

    def pyelk_callback(self,obj,data,d2):
        LOGGER.debug('pyelk_callback:area: obj={}, data={} d2={}'.format(obj,data,d2))
        self._set_drivers(data)

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        {'driver': 'GV0',  'value': 0, 'uom': 25},
        {'driver': 'GV1',  'value': 0, 'uom': 25},
        {'driver': 'GV2',  'value': 0, 'uom': 25},

    ]
    id = 'area'
    commands = {
    }
