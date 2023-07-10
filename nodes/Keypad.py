
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name
import time

from elkm1_lib.const import (
    Max,
    FunctionKeys
)

DNAMES = {
    'status':      'ST',
    'user':        'GV1',
    'temperature': 'GV2',
    'keypress':    'GV3',
    'function_key': 'GV4',
}

class KeypadNode(BaseNode):

    def __init__(self, controller, parent, address, elk):
        LOGGER.info(f'KeypadNode:init: {elk} index={elk.index}')
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.area       = parent
        try:
            self.init   = False
            self.on_time = 0
            self.has_temperature = False if self.elk.temperature == -40 else True
            LOGGER.info(f'KeyPadNode:init: has_temperature={self.has_temperature}')
            name        = get_valid_node_name(self.elk.name)
            if name == "":
                name = f'Keypad_{self.elk.index + 1}'
            self.uoms = {
                DNAMES['status']:       2,
                DNAMES['user']:        25,
                DNAMES['temperature']: self.controller.temperature_uom,
                DNAMES['keypress']:    25,
                DNAMES['function_key']:25,
            }
            self.drivers = [
                # On/Off
                {'driver': DNAMES['status'],      'value':  0,  'uom': self.uoms[DNAMES['status']], "desc": "Status"},
                {'driver': DNAMES['user'],        'value': -1,  'uom': self.uoms[DNAMES['user']], "desc": "Last User"},
                {'driver': DNAMES['keypress'],    'value': -1,  'uom': self.uoms[DNAMES['keypress']], "desc": "Last Keypress"},
                {'driver': DNAMES['function_key'],'value': -1,  'uom': self.uoms[DNAMES['function_key']], "desc": "Last Function Key"},
            ]
            LOGGER.debug(f'KeypadNode:init: name="{name}" uom={self.uoms}')
            if self.has_temperature:
                self.id = 'keypadT'
                self.drivers.append({'driver': DNAMES['temperature'], 'value': self.elk.temperature, 'uom': self.uoms[DNAMES['temperature']]})
            LOGGER.debug(f'KeypadNode:init: name="{name}" drivers={self.drivers}')
            super(KeypadNode, self).__init__(controller, parent.address, address, name)
            controller.poly.subscribe(controller.poly.START, self.start, address)
        except Exception as ex:
            LOGGER.error('KeypadNode:init',exc_info=True)
            self.inc_error(f"KeypadNode:init {ex}")

    def start(self):
        try:
            LOGGER.debug(f'{self.lpfx} {self.elk}')
            # Set drivers
            self.set_drivers(force=True,reportCmd=False)
            self.reportDrivers()
            self.elk.add_callback(self.callback)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    # 2022-07-26 21:08:36,625 ELK-6095   udi_interface      DEBUG    Keypad:callback: keypad_2:Down Hall: changeset={'last_keypress': ('ELK', 21)}
    def callback(self, obj, changeset):
        LOGGER.info(f'{self.lpfx} changeset={changeset}')
        # Catch this since it causes the ELK connection to crash
        try:
            ignore = ['last_user_time','code']
            for cs in changeset:
                if cs == 'last_user':
                    self.set_user(int(changeset[cs]) + 1)
                    self.area.set_keypad(self.elk.index + 1)
                elif cs == 'last_log':
                    if 'user_number' in changesset[cs]:
                        self.set_user(int(changeset[cs]['user_number']) + 1)
                        self.area.set_keypad(self.elk.index + 1)
                elif cs == 'last_keypress':
                    #  changeset={'last_keypress': ('ELK', 21)}
                    kp = changeset[cs]
                    i = 0
                    while i < len(kp):
                        LOGGER.debug(f"key={kp[i]} val={kp[i+1]}")
                        self.set_key(kp[i+1])
                        i += 2
                elif cs == 'last_function_key':
                    if hasattr(changeset[cs][1],'value'):
                        self.set_last_function_key(changeset[cs][1].value)
                    else:
                        msg = f'Callback not sent enum, got {cs}={changeset[cs][1]}'
                        LOGGER.error(f'{self.lpfx}: {msg}',exc_info=True)
                        self.inc_error(f"{self.lpfx} {msg}")
                elif cs == 'temperature':
                    self.set_temperature(changeset[cs])
                elif cs in ignore:
                    LOGGER.debug(f"Nothing to do for key={cs} val={changeset[cs]}")
                else:
                    LOGGER.warning(f'{self.lpfx} Unknown callback {cs}={changeset[cs]}')
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
#        self.elk.get_chime_mode()
        self.set_driver(DNAMES['status'],1,force=force)
        self.set_user(force=force)
        self.set_temperature(force=force)
        self.set_key(force=force)
        self.set_last_function_key(force=force)

    def set_last_function_key(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val is None:
            if hasattr(self.elk.last_function_key,'value'):
                val = self.elk.last_function_key.value
            else:
                val = 0
        if val == "*":
            val = 7
        elif val == "C":
            val = 8
        self.set_driver(DNAMES['function_key'],val,force=force)

    def set_key(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val is None:
            val = -1
        self.set_driver(DNAMES['keypress'],val,force=force)

    def set_user(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.last_user + 1
        self.set_driver(DNAMES['user'],val,force=force)
        self.area.set_user(val)

    def set_temperature(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} has_temperature={self.has_temperature}')
        if not self.has_temperature:
            return
        driver = DNAMES['temperature']
        if val is None:
            val = self.elk.temperature
        self.set_driver(driver, val, report=reportCmd, force=force, uom=self.uoms[driver], prec=1)

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    # For others to call, AreaNode uses this.
    def press_key_chime(self):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.press_function_key(FunctionKeys.CHIME)

    def cmd_key_chime(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.press_key_chime()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    id = 'keypad'
    commands = {
        'QUERY': cmd_query,
        'KEY_CHIME': cmd_key_chime,
    }
