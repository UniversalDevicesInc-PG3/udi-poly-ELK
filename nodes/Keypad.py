
from polyinterface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

class KeypadNode(BaseNode):

    def __init__(self, controller, parent, area, elk):
        LOGGER.debug(f'KeypadNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.init   = False
        self.address   = f'keypad_{self.elk.index + 1}'
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Keypad_{self.elk.index + 1}'
        LOGGER.debug(f'KeypadNode:init: {name}')
        super(KeypadNode, self).__init__(controller, parent.address, self.address, name)
        self.lpfx = f'{self.name}:'

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        # Set drivers
        self.set_drivers(force=True,reportCmd=False)
        self.reportDrivers()
        self.elk.add_callback(self.callback)

    def shortPoll(self):
        pass

    def query(self):
        self.set_drivers(force=False,reportCmd=False)

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        # Why does it get called multiple times with same data?
        if 'keypad_on' in changeset:
            self.set_onoff(changeset['keypad_on'])

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        self.set_driver('ST',1)
        self.set_user()
        self.set_temperature()

    def set_user(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx}')
        if val is None:
            val = self.elk.last_user
        self.set_driver('GV1',val)

    def set_temperature(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx}')
        if val is None:
            val = self.elk.temperature
        self.set_driver('GV2',val)

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # On/Off
        {'driver': 'ST',  'value':  0, 'uom': 2},
        {'driver': 'GV1', 'value': -1, 'uom': 25},
        {'driver': 'GV2', 'value': -1, 'uom': 17}
    ]
    id = 'keypad'
    commands = {
        'QUERY': cmd_query,
    }
