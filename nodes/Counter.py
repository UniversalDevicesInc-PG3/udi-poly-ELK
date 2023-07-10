
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

class CounterNode(BaseNode):

    def __init__(self, controller, address, elk):
        LOGGER.debug(f'CounterNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.init   = False
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Counter_{self.elk.index + 1}'
        LOGGER.debug(f'CounterNode:init: {name}')
        super(CounterNode, self).__init__(controller, controller.address, address, name)
        controller.poly.subscribe(controller.poly.START, self.start, address)

    def start(self):
        try:
            LOGGER.debug(f'{self.lpfx} {self.elk}')
            # Set drivers
            #self.set_drivers(force=True)
            #self.reportDrivers()
            self.elk.add_callback(self.callback)
            self.set_val()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        try:
            if 'value' in changeset:
                self.set_val(changeset['value'])
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False):
        try:
            LOGGER.debug(f'{self.lpfx} force={force}')
            self.set_val(force=force)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_val(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} {val}')
        if val is None:
            val = self.elk.value
            LOGGER.debug(f'{self.lpfx} current value={val}')
            if val is None:
                LOGGER.debug(f'{self.lpfx} counter current value is {val}')
                return
        try:
            val = int(val)
        except:
            msg = f'{self.lpfx} Can not convert {val} to an integer.'
            LOGGER.error(msg)
            self.inc_error(msg)
            return
        self.set_driver('ST',val,force=force)

    def query(self):
        self.elk.get()
        self.set_drivers(force=True)
        self.reportDrivers()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    def cmd_set(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} {val}')
            self.elk.set(int(val))
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_inc(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.elk.set(int(self.elk.value) + 1)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_dec(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.elk.set(int(self.elk.value) - 1)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 56, "desc": "Count"},
    ]
    id = 'counter'
    commands = {
        'SET': cmd_set,
        'INC': cmd_inc,
        'DEC': cmd_dec,
    }
