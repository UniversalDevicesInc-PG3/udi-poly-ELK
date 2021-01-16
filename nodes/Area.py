

import time
from polyinterface import LOGGER
from node_funcs import get_valid_node_name
from nodes import BaseNode,ZoneNode
from elkm1_lib.const import (
    Max,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
)

class AreaNode(BaseNode):

    def __init__(self, controller, elk):
        self.elk    = elk
        self.init   = False
        self.status = None
        self.state  = None
        self.zones_bypassed = 0
        self.zones_violated = 0
        address     = f'area_{self.elk.index + 1}'
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Area_{self.elk.index + 1}'
        super(AreaNode, self).__init__(controller, address, address, name)

    def start(self):
        self.elk.add_callback(self.callback)
        self.set_drivers()
        self.reportDrivers()
        # We used zero based number, so zone node name matches the zone number.
        for zn in range(Max.ZONES.value-1):
            #LOGGER.debug(f{self.lpfx} i={} n={} area={}'.format(i,ni,self.elk.zones[ni].area))
            if self.controller.elk.zones[zn].area == self.elk.index:
                LOGGER.debug(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} adding zone node {zn} '{self.controller.elk.zones[zn].name}'")
                self.controller.addNode(ZoneNode(self.controller,self,self,self.controller.elk.zones[zn]))
                time.sleep(.1)
 
    def callback(self, element, changeset):
        LOGGER.info(f'{self.lpfx} cs={changeset}')
        if 'alarm_state' in changeset:
            self.set_alarm_state(changeset['alarm_state'])
        if 'armed_status' in changeset:
            self.set_armed_status(changeset['armed_status'])
        if 'arm_up_state' in changeset:
            self.set_arm_up_state(changeset['arm_up_state'])

    def zone_bypass_add(self):
        self.zones_bypassed += 1
        self.set_driver('GV4',self.zones_bypassed)

    def zone_bypass_sub(self):
        self.zones_bypassed -= 1
        self.set_driver('GV4',self.zones_bypassed)

    def zone_violated_add(self):
        self.zones_violated += 1
        self.set_driver('GV3',self.zones_violated)

    def zone_violated_sub(self):
        self.zones_violated -= 1
        self.set_driver('GV3',self.zones_violated)

    def xxupdate_zone_status(self):
        LOGGER.info(f'{self.lpfx}')
        bypassed = 0
        violated = 0
        for zn in range(Max.ZONES.value-1):
            #LOGGER.debug(f{self.lpfx} i={} n={} area={}'.format(i,ni,self.elk.zones[ni].area))
            if self.controller.elk.zones[zn].area == self.elk.index:
                #LOGGER.debug(f'{self.lpfx} {self.controller.elk.zones[zn].name} logical_status={self.controller.elk.zones[zn].logical_status} name={ZoneLogicalStatus(self.controller.elk.zones[zn].logical_status).name}')
                if ZoneLogicalStatus(self.controller.elk.zones[zn].logical_status).name == 'BYPASSED':
                    bypassed += 1
                elif ZoneLogicalStatus(self.controller.elk.zones[zn].logical_status).name == 'VIOLATED':
                    violated += 1
        self.set_driver('GV3',violated)
        self.set_driver('GV4',bypassed)

    # armed_status:0 arm_up_state:1 alarm_state:0 alarm_memory:None is_exit:False timer1:0 timer2:0 cs={'name': 'Home'}
    # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
    def set_drivers(self):
        LOGGER.info(f'{self.lpfx} Area:{self.elk.index} {self.elk.name}')
        self.set_alarm_state()
        self.set_armed_status()
        self.set_arm_up_state()
        self.set_driver('GV3',self.zones_violated)
        self.set_driver('GV4',self.zones_bypassed)
        #self.setDriver('GV2', pyelk.chime_mode)

    def set_alarm_state(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        val = self.elk.alarm_state if val is None else int(val)
        # Send DON for Violated?
        #if val == 2:
        #    self.reportCmd("DON",2)
        #else:
        #    self.reportCmd("DOF",2)
        self.set_driver('ST', val, force=force)

    def set_armed_status(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        val = self.elk.armed_status if val is None else int(val)
        self.set_driver('GV0',val,force=force)

    def set_arm_up_state(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        val = self.elk.arm_up_state if val is None else int(val)
        self.set_driver('GV1', val)

    def query(self):
        LOGGER.info(f'{self.lpfx}')
        self.set_drivers()
        self.reportDrivers()

    def cmd_set_armed_status(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} elk.arm({val},****')
        # val is a string, not integer :(
        self.elk.arm(val,self.controller.user_code)

    def cmd_set_bypass(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} Calling bypass...')
        self.elk.bypass(self.controller.user_code)

    def cmd_clear_bypass(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} Calling clear bypass...')
        self.elk.clear_bypass(self.controller.user_code)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        {'driver': 'GV0',  'value': 0, 'uom': 25},
        {'driver': 'GV1',  'value': 0, 'uom': 25},
        {'driver': 'GV2',  'value': 0, 'uom': 25},
        {'driver': 'GV3',  'value': 0, 'uom': 25},
        {'driver': 'GV4',  'value': 0, 'uom': 25},
    ]
    id = 'area'
    commands = {
            'SET_ARMED_STATUS': cmd_set_armed_status,
            'SET_BYPASS': cmd_set_bypass,
            'CLEAR_BYPASS': cmd_clear_bypass,
    }
