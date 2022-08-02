

import time
from threading import Thread,Event
from udi_interface import LOGGER
from node_funcs import get_valid_node_name
from nodes import BaseNode,ZoneNode,KeypadNode
from elkm1_lib.const import (
    Max,
    ArmedStatus,
    ZoneType,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
    ChimeMode,
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
        super(AreaNode, self).__init__(controller, address, address, name)
        controller.poly.subscribe(controller.poly.START, self.start, address)

    def start(self):
        LOGGER.debug(f"{self.lpfx}")
        try:
            self.elk.add_callback(self.callback)
            self.set_drivers(force=True)
            self.reportDrivers()
            # elkm1_lib uses zone numbers starting at zero.
#            for zn in range(Max.ZONES.value):
#                LOGGER.debug(f'{self.lpfx} index={zn} area={self.controller.elk.zones[zn].area} definition={self.controller.elk.zones[zn].definition}')
#                # Add zones that are in my area, and are defined.
#                if self.controller.elk.zones[zn].definition !=  ZoneType.DISABLED and self.controller.elk.zones[zn].area == self.elk.index:
#                    LOGGER.info(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} adding zone node {zn} '{self.controller.elk.zones[zn].name}'")
#                    address = f'zone_{zn+1}'
#                    node = self.controller.add_node(address, ZoneNode(self.controller, self, address, self.controller.elk.zones[zn]))
#                    if node is not None:
#                        self._zone_nodes[zn] = node
            for n in range(Max.KEYPADS.value):
                if self.controller.elk.keypads[n].area == self.elk.index:
                    LOGGER.info(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} adding keypad node {n} '{self.controller.elk.keypads[n]}'")
                    address = f'keypad_{n+1}'
                    node = self.controller.add_node(address,KeypadNode(self.controller, self, address, self.controller.elk.keypads[n]))
                    if node is not None:
                        self._keypad_nodes[n] = node
                else:
                    LOGGER.debug(f"{self.lpfx} area {self.elk.index} {self.elk.name} node={self.name} skipping keypad node {n} '{self.controller.elk.keypads[n]}'")
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")
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
        LOGGER.warning(f'{self.lpfx} cs={changeset}')
        try:
            for cs in changeset:
                if cs == 'alarm_state':
                    self.set_alarm_state(changeset[cs])
                elif cs == 'armed_status':
                    self.set_armed_status(changeset[cs])
                elif cs == 'arm_up_state':
                    self.set_arm_up_state(changeset[cs])
                elif cs == 'last_log':
                    # Need to investigate this more, do we really need this if keypad callback is setting it?
                    if 'user_number' in changeset[cs]:
                        self.set_user(int(changeset[cs]['user_number']))
                elif cs == 'chime_mode':
                    # chime_mode=('Chime', <ChimeMode.Chime: 1>)
                    # So pass element 1 which is the enum
                    self.set_chime_mode(changeset[cs])
                else:
                    LOGGER.warning(f'{self.lpfx} Unknown callback {cs}={changeset[cs]}')
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    # armed_status:0 arm_up_state:1 alarm_state:0 alarm_memory:None is_exit:False timer1:0 timer2:0 cs={'name': 'Home'}
    # {'armed_status': '0', 'arm_up_state': '1', 'alarm_state': '0'}
    def set_drivers(self,force=False):
        LOGGER.info(f'{self.lpfx} Area:{self.elk.index} {self.elk.name}')
        self.set_alarm_state(force=force)
        self.set_armed_status(force=force)
        self.set_arm_up_state(force=force)
        self.set_chime_mode(force=force)
        self.set_poll_voltages(force=force)
        self.set_entry_exit_trigger(force=force)
        self.set_driver('GV3',self.zones_violated,force=force)
        self.set_driver('GV4',self.zones_bypassed,force=force)

    # This is called by Keypad or callback
    def set_user(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV6',val,force=force)

    # This is only called by Keypad's
    def set_keypad(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV7',val,force=force)

    # This is only called by Zones's when it goes violated
    # This is passed the elkm1_lib zone number, so we add 1 for our zone numbers
    def set_last_violated_zone(self, val, force=False, reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val} EntryExitTrigger={self.entry_exit_trigger}')
        val = int(val)
        self.set_driver('GV8',val+1,force=force)
        # ELK only sends a violated zone for entry/exit zones when it
        # starts the timer, but this option sets it as triggered
        # if entry_exit_trigger is enabled.
        if self.entry_exit_trigger:
            LOGGER.debug(f'{self.lpfx} alarm_state={self.elk.alarm_state} zone.definition={self.controller.elk.zones[val].definition} armed_status={self.elk.armed_status}')
            # Say nothing for 'Non Alarm'
            if self.controller.elk.zones[val].definition != ZoneType.NON_ALARM:
                LOGGER.debug("a")
                # Mode Stay, Away, Night, or Vacation?
                if self.elk.armed_status == ArmedStatus.ARMED_AWAY or self.elk.armed_status == ArmedStatus.ARMED_STAY or self.elk.armed_status == ArmedStatus.ARMED_STAY_INSTANT or self.elk.armed_status == ArmedStatus.ARMED_TO_NIGHT_INSTANT or self.elk.armed_status == ArmedStatus.ARMED_TO_VACATION:
                    LOGGER.debug("b")
                    # Send for Entry/Exit Delay
                    if self.controller.elk.zones[val].definition == ZoneType.BURGLAR_ENTRY_EXIT_1 or int(self.controller.elk.zones[val].definition) == ZoneType.BURGLAR_ENTRY_EXIT_2: 
                        LOGGER.debug("c")
                        self.set_last_triggered_zone(val)
                # Night mode?
                elif self.elk.armed_status == ArmedStatus.ARMED_TO_NIGHT:
                    LOGGER.debug("d")
                    # Send for Interior Night Delay
                    if int(self.controller.elk.zones[val].definition) == 7:
                        self.set_last_triggered_zone(val)

    # This is only called by Zone's when it triggers an alarm
    # This is passed the elkm1_lib zone number, so we add 1 for our zone numbers
    def set_last_triggered_zone(self,val,force=False):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.set_driver('GV9',val+1,force=force)

    def set_zone_logical_status(self, zn, st, force=False):
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
        self.set_driver('GV3',self.zones_violated,force=force)
        self.set_driver('GV4',self.zones_bypassed,force=force)

    def set_alarm_state(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        # Send DON for Violated?
        #if val == 2:
        #    self.reportCmd("DON",2)
        #else:
        #    self.reportCmd("DOF",2)
        self.set_driver('ST', val, restore=False, default=self.elk.alarm_state, force=force)

    def set_armed_status(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV0',val,restore=False,default=self.elk.armed_status,force=force)

    def set_arm_up_state(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV1', val, restore=False,default=self.elk.arm_up_state,force=force)

    def set_chime_mode(self,val=None,force=False):
        LOGGER.warning(f'{self.lpfx} {val} elk.chime_mode={self.elk.chime_mode}')
        self.set_driver('GV2', val, restore=False,default=self.elk.chime_mode,force=force)

    def set_poll_voltages(self,val=None, force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.set_driver('GV5', val, default=0, force=force)
        self.poll_voltages = False if self.get_driver('GV5') == 0 else True

    def set_entry_exit_trigger(self,val=None, force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        val = self.set_driver('GV10', val, default=1)
        self.entry_exit_trigger = False if val == 0 else True

    def cmd_set_armed_status(self,command):
        try:
            val = command.get('value')
            LOGGER.info(f'{self.lpfx} elk.arm({val},****')
            # val is a string, not integer :(
            self.elk.arm(val,self.controller.user_code)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_bypass(self,command):
        try:
            val = command.get('value')
            LOGGER.info(f'{self.lpfx} Calling bypass...')
            self.elk.bypass(self.controller.user_code)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_clear_bypass(self,command):
        try:
            val = command.get('value')
            LOGGER.info(f'{self.lpfx} Calling clear bypass...')
            self.elk.clear_bypass(self.controller.user_code)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_poll_voltages(self,command):
        try:
            val = command.get('value')
            LOGGER.info(f'{self.lpfx} {val}')
            self.set_poll_voltages(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_entry_exit_trigger(self,command):
        try:
            val = command.get('value')
            LOGGER.info(f'{self.lpfx} {val}')
            self.set_entry_exit_trigger(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    #  command={'address': 'area_1', 'cmd': 'GV11', 'query': {'Beep.uom2': '0', 'OffTimer.uom56': '60', 'Content.uom145': 'program[0]: node[#]=node[#]'}}
    # Clear, 0=clear message, 1=clear message with * key, 2=Display until timeout
    #     def display_message(self, clear, beep, timeout, line1, line2)
    def cmd_display_message(self,command):
        LOGGER.debug(f'command={command}')
        try:
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
                msg = 'No content sent in message?'
                LOGGER.error(msg)
                self.inc_error(msg)
                return
            lines = content.splitlines()
            if len(lines) < 1:
                msg = f"No lines in content '{content}'"
                LOGGER.error(msg)
                self.inc_error(msg)
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
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def clean_dm(self,line):
        fixed = line.encode("ascii", "ignore").decode()
        if (line != fixed):
            LOGGER.warning(f"Removed non-ascii characters from '{line}' to '{fixed}'")
        return fixed

    def cmd_clear_message(self,command):
        try:
            LOGGER.info(f'display_message(0, False, 0, "", "")')
            self.elk.display_message(
                0, False, 0, "", ""
            )
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

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
