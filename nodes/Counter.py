
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
        controller.poly.subscribe(controller.poly.START, self.start, address)
        controller.poly.subscribe(controller.poly.ADDNODEDONE, self.handler_addnodedone)
        super(CounterNode, self).__init__(controller, controller.address, address, name)
        self.lpfx = f'{self.name}:'

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')

    def handler_addnodedone(self,data):
        if data['address'] == self.address:
            LOGGER.debug(f'{self.lpfx} {self.elk}')
            # Set drivers
            #self.set_drivers(force=True)
            #self.reportDrivers()
            self.elk.add_callback(self.callback)
            self.set_val()

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        if 'value' in changeset:
            self.set_val(changeset['value'])

    def set_drivers(self,force=False):
        LOGGER.debug(f'{self.lpfx} force={force}')
        self.set_val(force=force)

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
            LOGGER.error(f'{self.lpfx} Can not convert {val} to an integer.')
            return
        self.set_driver('ST',val)


    def query(self):
        self.elk.get()
        self.reportDrivers()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    def cmd_set(self,command):
        val = int(command.get('value'))
        LOGGER.debug(f'{self.lpfx} {val}')
        self.elk.set(int(val))

    def cmd_inc(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.set(int(self.elk.value) + 1)

    def cmd_dec(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.set(int(self.elk.value) - 1)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 56},
    ]
    id = 'counter'
    commands = {
        'SET': cmd_set,
        'INC': cmd_inc,
        'DEC': cmd_dec,
    }
