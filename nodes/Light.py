
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

class LightNode(BaseNode):

    def __init__(self, controller, address, elk):
        LOGGER.debug(f'LightNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.init   = False
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Light_{self.elk.index + 1}'
        LOGGER.debug(f'LightNode:init: {name}')
        super(LightNode, self).__init__(controller, controller.address, address, name)
        controller.poly.subscribe(controller.poly.START, self.start, address)

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        # Set drivers
        self.set_drivers(force=True,reportCmd=False)
        self.reportDrivers()
        self.elk.add_callback(self.callback)

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        try:
            if 'status' in changeset:
                self.set_onoff(100 if changeset['status'] == 1 else 0)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        self.set_onoff(reportCmd=False)

    def set_time(self,val=0,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx}')
        self.set_driver('TIME',val)
        self.on_time = int(val)

    def set_onoff(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} {val}')
        if val is None:
            val = 100 if self.elk.status == 1 else 0
        elif val is True:
            val = 100
        elif val is False:
            val = 0
        self.set_driver('ST',val)
        if (not force) and reportCmd:
            if self.elk.status > 0:
                LOGGER.debug(f'{self.lpfx} Send DON')
                self.reportCmd("DON")
            else:
                LOGGER.debug(f'{self.lpfx} Send DOF')
                self.reportCmd("DOF")

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def cmd_set_on(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.level(100)

    def cmd_set_off(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.level(0)

    def cmd_toggle(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.toggle()

    def cmd_query(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.query()

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # On/Off
        {'driver': 'ST',  'value': 101, 'uom': 78},
    ]
    id = 'light'
    commands = {
        'DON': cmd_set_on,
        'DOF': cmd_set_off,
        'TOGGLE': cmd_toggle,
        'QUERY': cmd_query,
    }
