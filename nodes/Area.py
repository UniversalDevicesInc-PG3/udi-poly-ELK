

import time
#from elkm1_lib import const
from polyinterface import Node,LOGGER
from nodes import ZoneNode

class AreaNode(Node):

    def __init__(self, controller, elk):
        self.elk    = elk
        self.init   = False
        self.status = None
        self.state  = None
        address     = 'area_{}'.format(self.elk.index)
        name        = self.elk.name
        super(AreaNode, self).__init__(controller, address, address, name)
        self.lpfx = f'{self.name}:'

    def start(self):
        self.elk.add_callback(self.callback)
        self.set_drivers()
        self.reportDrivers()
        for zn in range(207):
            #LOGGER.debug(f{self.lpfx} i={} n={} area={}'.format(i,ni,self.elk.zones[ni].area))
            if self.controller.elk.zones[zn].area == self.elk.index:
                LOGGER.debug(f"{self.lpfx} adding zone node {zn} '{self.controller.elk.zones[zn].name}'")
                self.controller.addNode(ZoneNode(self.controller,self.controller,self.controller.elk.zones[zn]))
                time.sleep(.1)

    def callback(self, element, changeset):
        LOGGER.info(f'{self.lpfx} cs={changeset}')
        if 'armed_status' in changeset:
            self.set_armed_status(changeset['armed_status'])

    # armed_status:0 arm_up_state:1 alarm_state:0 alarm_memory:None is_exit:False timer1:0 timer2:0 cs={'name': 'Home'}
    # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
    def set_drivers(self):
        LOGGER.info(f'{self.lpfx} Area:{self.elk.index} {self.elk.name}')
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
        LOGGER.info(f'{self.lpfx} {val}')
        if val is None:
            val = self.elk.armed_status
        else:
            val = int(val)
        self.setDriver('GV0', val)

    def set_arm_up_state(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        if val is None:
            val = self.elk.arm_up_state
        else:
            val = int(val)
        self.setDriver('GV1', val)

    def query(self):
        LOGGER.info(f'{self.lpfx}')
        self.set_drivers()
        self.reportDrivers()

    def cmd_set_armed_status(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} {val}')
        # val is a string, not integer :(
        self.elk.arm(val,self.controller.user_code)

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
            'SET_ARMED_STATUS': cmd_set_armed_status,
}
