

import time
import polyinterface
LOGGER = polyinterface.LOGGER

class AreaNode(polyinterface.Node):

    def __init__(self, controller, elk):
        self.elk    = elk
        self.init   = False
        self.status = -1
        self.state  = -1
        address     = 'area_{}'.format(self.elk.index)
        name        = self.elk.name
        super(AreaNode, self).__init__(controller, address, address, name)

    def start(self):
        self.set_drivers()

    def callback(self, changeset):
        LOGGER.debug('AreaNode:callback: cs={}'.format(changeset))

    # armed_status:0 arm_up_state:1 alarm_state:0 alarm_memory:None is_exit:False timer1:0 timer2:0 cs={'name': 'Home'}
    # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
    def set_drivers(self):
        LOGGER.debug('set_drivers: Area:{} {}'
                    .format(self.elk.index,self.elk.name))
        self.set_alarm_state()
        self.set_armed_status()
        self.set_arm_up_state()
        #self.setDriver('GV2', pyelk.chime_mode)

    def set_alarm_state(self,val=None,force=False):
        if val is None:
            val = self.elk.alarm_state
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

    def set_armed_status(self,val=None):
        if val is None:
            val = self.elk.armed_status
        else:
            val = int(val)
        self.setDriver('GV0', val)

    def set_arm_up_state(self,val=None):
        if val is None:
            val = self.elk.arm_up_state
        else:
            val = int(val)
        self.setDriver('GV1', val)

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
