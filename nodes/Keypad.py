
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

DNAMES = {
    'status':      'ST',
    'user':        'GV1',
    'temperature': 'GV2',
    'keypress':    'GV3'
}

class KeypadNode(BaseNode):

    def __init__(self, controller, parent, address, elk):
        LOGGER.debug(f'KeypadNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.area       = parent
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
        }
        self.drivers = [
            # On/Off
            {'driver': DNAMES['status'],      'value':  0,  'uom': self.uoms[DNAMES['status']]},
            {'driver': DNAMES['user'],        'value': -1,  'uom': self.uoms[DNAMES['user']]}, # Last User
            {'driver': DNAMES['keypress'],    'value': -1,  'uom': self.uoms[DNAMES['keypress']]}, # Last Keypress
        ]
        LOGGER.debug(f'KeypadNode:init: name="{name}" uom={self.uoms}')
        if self.has_temperature:
            self.id = 'keypadT'
            self.drivers.append({'driver': DNAMES['temperature'], 'value': -40, 'uom': self.uoms[DNAMES['temperature']]})
        LOGGER.debug(f'KeypadNode:init: name="{name}" drivers={self.drivers}')
        super(KeypadNode, self).__init__(controller, parent.address, address, name)
        controller.poly.subscribe(controller.poly.START, self.start, address)

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        # Set drivers
        self.set_drivers(force=True,reportCmd=False)
        self.reportDrivers()
        self.elk.add_callback(self.callback)

    # 2022-07-26 21:08:36,625 ELK-6095   udi_interface      DEBUG    Keypad:callback: keypad_2:Down Hall: changeset={'last_keypress': ('ELK', 21)}
    def callback(self, obj, changeset):
        # Catch this since it causes the ELK connection to crash
        try:
            LOGGER.debug(f'{self.lpfx} changeset={changeset}')
            if 'last_user' in changeset:
                self.set_user(int(changeset['last_user']) + 1)
                self.area.set_keypad(self.elk.index + 1)
            elif 'last_log' in changeset:
                if 'user_number' in changesset['last_log']:
                    self.set_user(int(changeset['last_log']['user_number']) + 1)
                    self.area.set_keypad(self.elk.index + 1)
            elif 'last_keypress' in changeset:
                #  changeset={'last_keypress': ('ELK', 21)}
                kp = changeset['last_keypress']
                i = 0
                while i < len(kp):
                    LOGGER.debug(f"key={kp[i]} val={kp[i+1]}")
                    self.set_key(kp[i+1])
                    i += 2
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        self.set_driver(DNAMES['status'],1)
        self.set_user()
        self.set_temperature()
        self.set_key()

    def set_key(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val is None:
            val = -1
        self.set_driver(DNAMES['keypress'],val,force=force)

    def set_user(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.last_user + 1
        self.set_driver(DNAMES['user'],val)
        self.area.set_user(val)

    def set_temperature(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} has_temperature={self.has_temperature}')
        if not self.has_temperature:
            return
        driver = DNAMES['temperature']
        if val is None:
            val = self.elk.temperature
        self.set_driver(driver, val, report=reportCmd, force=force, uom=self.uoms[driver], prec=1)

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    id = 'keypad'
    commands = {
        'QUERY': cmd_query,
    }
