

import time
from threading import Thread,Event
from udi_interface import LOGGER
from node_funcs import get_valid_node_name
from nodes import BaseNode,ZoneNode,KeypadNode
from elkm1_lib.const import (
    Max,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
)

# For faster lookups
BYPASSED = ZoneLogicalStatus['BYPASSED'].value
VIOLATED = ZoneLogicalStatus['VIOLATED'].value


class AreaNode(BaseNode):

    def __init__(self, controller, address, elk):
        self.elk    = elk
        self.init   = False
        self.status = None
        self.state  = None
        self.zones_bypassed = 0
        self.zones_violated = 0
        self.zones_logical_status = [None] * Max.ZONES.value
        self.zones_physical_status = [None] * Max.ZONES.value
        self._zone_nodes = {}
        self._keypad_nodes = {}
        self.poll_voltages = False
        self.ready = False
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Area_{self.elk.index + 1}'
        controller.poly.subscribe(controller.poly.START, self.start, address)
        controller.poly.subscribe(controller.poly.ADDNODEDONE, self.handler_addnodedone)
        super(AreaNode, self).__init__(controller, address, address, name)

    def start(self):
        pass

    def handler_addnodedone(self,data):
        LOGGER.debug(f"{self.lpfx} address={data['address']}")
        if data['address'] == self.address:
            self.elk.add_callback(self.callback)
            self.set_drivers()
            self.reportDrivers()
            # elkm1_lib uses zone numbers starting at zero.
            for zn in range(Max.ZONES.value):
                LOGGER.debug(f'{self.lpfx} index={zn} area={self.controller.elk.zones[zn].area} definition={self.controller.elk.zones[zn].definition}')
                # Add zones that are in my area, and are defined.
                if self.controller.elk.zones[zn].definition > 0 and self.controller.elk.zones[zn].area == self.elk.index:
                    LOGGER.info(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} adding zone node {zn} '{self.controller.elk.zones[zn].name}'")
                    address = f'zone_{zn+1}'
                    node = self.controller.add_node(address, ZoneNode(self.controller, self, address, self.controller.elk.zones[zn]))
                    if node is not None:
                        self._zone_nodes[zn] = node
            for n in range(Max.KEYPADS.value):
                if self.controller.elk.keypads[n].area == self.elk.index:
                    LOGGER.info(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} adding keypad node {n} '{self.controller.elk.keypads[n]}'")
                    address = f'keypad_{n+1}'
                    node = self.controller.add_node(address,KeypadNode(self.controller, self, address, self.controller.elk.keypads[n]))
                    if node is not None:
                        self._keypad_nodes[n] = node
                else:
                    LOGGER.debug(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} skipping keypad node {n} '{self.controller.elk.keypads[n]}'")
            self.ready = True

    def shortPoll(self):
        # Only Poll Zones if we want voltages
        LOGGER.debug(f'{self.lpfx} ready={self.ready} poll_voltages={self.poll_voltages}')
        if not self.ready:
            return False
        if self.poll_voltages:
            for zn in self._zone_nodes:
                self._zone_nodes[zn].shortPoll(poll_voltage=self.poll_voltages)

    def longPoll(self):
        pass

    # Area:callback: area_1:Home: cs={'last_log': {'event': 1174, 'number': 1, 'index': 0, 'timestamp': '2021-02-06T14:47:00+00:00', 'user_number': 1}}
    # user_number=1 was me
    def callback(self, element, changeset):
        LOGGER.info(f'{self.lpfx} cs={changeset}')
        if 'alarm_state' in changeset:
            self.set_alarm_state(changeset['alarm_state'])
        if 'armed_status' in changeset:
            self.set_armed_status(changeset['armed_status'])
        if 'arm_up_state' in changeset:
            self.set_arm_up_state(changeset['arm_up_state'])
        # Need to investigate this more, do we really need this if keypad callback is setting it?
        if 'last_log' in changeset:
            if 'user_number' in changeset['last_log']:
                self.set_user(int(changeset['last_log']['user_number']))

    # armed_status:0 arm_up_state:1 alarm_state:0 alarm_memory:None is_exit:False timer1:0 timer2:0 cs={'name': 'Home'}
    # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
    def set_drivers(self):
        LOGGER.info(f'{self.lpfx} Area:{self.elk.index} {self.elk.name}')
        self.set_alarm_state()
        self.set_armed_status()
        self.set_arm_up_state()
        self.set_poll_voltages()
        self.set_entry_exit_trigger()
        self.set_driver('GV3',self.zones_violated)
        self.set_driver('GV4',self.zones_bypassed)
        #self.setDriver('GV2', pyelk.chime_mode)

    # This is called by Keypad or callback
    def set_user(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV6',val)

    # This is only called by Keypad's
    def set_keypad(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV7',val)

    # This is only called by Zones's when it goes violated
    # This is passed the elkm1_lib zone number, so we add 1 for our zone numbers
    def set_last_violated_zone(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val} EntryExitTrigger={self.entry_exit_trigger}')
        val = int(val)
        self.set_driver('GV8',val+1)
        # ELK only sends a violated zone for entry/exit zones when it
        # starts the timer, but this option sets it as triggered
        # if entry_exit_trigger is enabled.
        if self.entry_exit_trigger:
            LOGGER.debug(f'{self.lpfx} alarm_state={self.elk.alarm_state} zone.definition={self.controller.elk.zones[val].definition} armed_status={self.elk.armed_status}')
            # Say nothing for 'Non Alarm'
            if not int(self.controller.elk.zones[val].definition) == 16:
                LOGGER.debug("a")
                # Mode Stay, Away, Night, or Vacation?
                if int(self.elk.armed_status) == 1 or int(self.elk.armed_status) == 2 or int(self.elk.armed_status) == 4 or int(self.elk.armed_status) == 6:
                    LOGGER.debug("b")
                    # Send for Entry/Exit Delay
                    if int(self.controller.elk.zones[val].definition) == 1 or int(self.controller.elk.zones[val].definition) == 2: 
                        LOGGER.debug("c")
                        self.set_last_triggered_zone(val)
                # Night mode?
                elif int(self.elk.armed_status) == 4:
                    LOGGER.debug("d")
                    # Send for Interior Night Delay
                    if int(self.controller.elk.zones[val].definition) == 7:
                        self.set_last_triggered_zone(val)

    # This is only called by Zone's when it triggers an alarm
    # This is passed the elkm1_lib zone number, so we add 1 for our zone numbers
    def set_last_triggered_zone(self,val):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV9',val+1)

    def set_zone_logical_status(self, zn, st):
        LOGGER.info(f'{self.lpfx} zn={zn} st={st}')
        self.zones_logical_status[zn] = st
        self.zones_bypassed = 0
        self.zones_violated = 0
        for val in self.zones_logical_status:
            if val is not None:
                if val == BYPASSED:
                    self.zones_bypassed += 1
                elif val == VIOLATED:
                    self.zones_violated += 1
        self.set_driver('GV3',self.zones_violated)
        self.set_driver('GV4',self.zones_bypassed)

    def set_alarm_state(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        # Send DON for Violated?
        #if val == 2:
        #    self.reportCmd("DON",2)
        #else:
        #    self.reportCmd("DOF",2)
        self.set_driver('ST', val, default=self.elk.alarm_state, force=force)

    def set_armed_status(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV0',val,default=self.elk.armed_status,force=force)

    def set_arm_up_state(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV1', val, default=self.elk.arm_up_state)

    def set_poll_voltages(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV5', val, default=0)
        self.poll_voltages = False if self.get_driver('GV5') == 0 else True

    def set_entry_exit_trigger(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        val = self.set_driver('GV10', val, default=1)
        self.entry_exit_trigger = False if val == 0 else True

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

    def cmd_set_poll_voltages(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_poll_voltages(val)

    def cmd_set_entry_exit_trigger(self,command):
        val = command.get('value')
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_entry_exit_trigger(val)

    #  command={'address': 'area_1', 'cmd': 'GV11', 'query': {'Beep.uom2': '0', 'OffTimer.uom56': '60', 'Content.uom145': 'program[0]: node[#]=node[#]'}}
    # Clear, 0=clear message, 1=clear message with * key, 2=Display until timeout
    #     def display_message(self, clear, beep, timeout, line1, line2)
    def cmd_display_message(self,command):
        LOGGER.debug(f'command={command}')
        query = command.get('query')
        beep = query.get('Beep.uom2')
        beep = False if beep == "0" else True
        clear = query.get('Clear.uom25')
        clear = 2 if clear is None else int(clear)
        off_timer = query.get('OffTimer.uom56')
        off_timer = 0 if off_timer is None else int(off_timer)
        content = query.get('Content.uom145')
        LOGGER.debug(f'clear={clear} beep={beep} off_timer={off_timer} content={content}')
        if content is None:
            LOGGER.error('No content sent?')
            return
        lines = content.splitlines()
        if len(lines) < 1:
            LOGGER.error(f"No lines in content '{content}'")
        line1 = self.clean_dm(lines[0])
        if (len(lines) < 2):
            lines.append('')
            line2 = ''
        else:
            line2 = self.clean_dm(lines[1])
        LOGGER.info(f'display_message({clear}, {beep}, {off_timer}, "{line1}", "{line2}")')
        self.elk.display_message(
            clear, beep, off_timer, line1, line2
        )

    def clean_dm(self,line):
        fixed = line.encode("ascii", "ignore").decode()
        if (line != fixed):
            LOGGER.warning(f"Removed non-ascii characters from '{line}' to '{fixed}'")
        return fixed

    def cmd_clear_message(self,command):
        LOGGER.info(f'display_message(0, False, 0, "", "")')
        self.elk.display_message(
            0, False, 0, "", ""
        )

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
        {'driver': 'GV5',  'value': 0, 'uom': 2},
        {'driver': 'GV6',  'value': 0, 'uom': 25},
        {'driver': 'GV7',  'value': 0, 'uom': 25},
        {'driver': 'GV8',  'value': 0, 'uom': 25},
        {'driver': 'GV9',  'value': 0, 'uom': 25},
        {'driver': 'GV10',  'value': 1, 'uom': 2},
    ]
    id = 'area'
    commands = {
            'SET_ARMED_STATUS': cmd_set_armed_status,
            'SET_POLL_VOLTAGES': cmd_set_poll_voltages,
            'SET_BYPASS': cmd_set_bypass,
            'CLEAR_BYPASS': cmd_clear_bypass,
            'SET_ENTRY_EXIT_TRIGGER': cmd_set_entry_exit_trigger,
            'CLEAR_MESSAGE': cmd_clear_message,
            'GV11': cmd_display_message,
    }
