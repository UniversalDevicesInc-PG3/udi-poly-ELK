
from polyinterface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

DNAMES = {
    'status':      'ST',
    'user':        'GV1',
    'temperature': 'GV2',
}

class KeypadNode(BaseNode):

    def __init__(self, controller, parent, area, elk):
        LOGGER.debug(f'KeypadNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.area = area
        self.init   = False
        self.address   = f'keypad_{self.elk.index + 1}'
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Keypad_{self.elk.index + 1}'
        self.set_uoms()
        self.drivers = [
            # On/Off
            {'driver': DNAMES['status'],      'value':  0,  'uom': self.uom[DNAMES['status']]},
            {'driver': DNAMES['user'],        'value': -1,  'uom': self.uom[DNAMES['user']]}, # Last User
            {'driver': DNAMES['temperature'], 'value': -40, 'uom': self.uom[DNAMES['temperature']]}  # Temperature
        ]
        LOGGER.debug(f'KeypadNode:init: {name}')
        super(KeypadNode, self).__init__(controller, parent.address, self.address, name)
        self.lpfx = f'{self.name}:'

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        # Set drivers
        self.set_drivers(force=True,reportCmd=False)
        self.reportDrivers()
        self.elk.add_callback(self.callback)

    def set_uoms(self):
        self.uom = {
            DNAMES['status']:       2,
            DNAMES['user']:        25,
            # Temperature 17=F 4=C
            DNAMES['temperature']:  4 if self.controller.temperature_uom
        }

    def shortPoll(self):
        pass

    def query(self):
        self.set_drivers(force=False,reportCmd=False)

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        if 'last_user' in changeset:
            self.set_user(int(changeset['last_user']) + 1)
            self.area.set_keypad(self.elk.index + 1)
        elif 'last_log' in changeset:
            if 'user_number' in changesset['last_log']:
                self.set_user(int(changeset['last_log']['user_number']) + 1)
                self.area.set_keypad(self.elk.index + 1)

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        self.set_driver(DNAMES['status'],1)
        self.set_user()
        self.set_temperature()

    def set_user(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.last_user + 1
        self.set_driver(DNAMES['user'],val)
        self.area.set_user(val)

    def set_temperature(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx}')
        driver = DNAMES['temperature']
        if val is None:
            val = self.elk.temperature
        self.set_driver(driver, self.uom[driver])

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
