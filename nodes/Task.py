
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

class TaskNode(BaseNode):

    def __init__(self, controller, address, elk):
        LOGGER.debug(f'TaskNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.init   = False
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Task_{self.elk.index + 1}'
        LOGGER.debug(f'TaskNode:init: {name}')
        super(TaskNode, self).__init__(controller, controller.address, address, name)
        controller.poly.subscribe(controller.poly.START, self.start, address)

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        # Set drivers
        #self.set_drivers(force=True)
        #self.reportDrivers()
        self.elk.add_callback(self.callback)

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        try:
            if 'value' in changeset:
                self.set_val(changeset['value'])
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False):
        LOGGER.debug(f'{self.lpfx} force={force}')
        self.set_val(force=force)

    def query(self):
        self.reportDrivers()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    def cmd_activate(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.activate()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 56},
    ]
    id = 'task'
    commands = {
        'ACTIVATE': cmd_activate
    }
