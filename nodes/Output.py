
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
)

class OutputNode(BaseNode):

    def __init__(self, controller, address, elk):
        LOGGER.debug(f'OutputNode:init: {elk}')
        self.elk    = elk
        self.controller = controller
        self.init   = False
        self.on_time = 0
        name        = get_valid_node_name(self.elk.name)
        if name == "":
            name = f'Output_{self.elk.index + 1}'
        LOGGER.debug(f'OutputNode:init: {name}')
        super(OutputNode, self).__init__(controller, controller.address, address, name)
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
            # Why does it get called multiple times with same data?
            if 'output_on' in changeset:
                self.set_onoff(changeset['output_on'],reportCmd=True)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=False):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        self.set_onoff(reportCmd=reportCmd)

    def set_time(self,val=0,force=False):
        LOGGER.info(f'{self.lpfx}')
        self.on_time = int(val)
        self.set_driver('TIME',self.on_time)

    def set_onoff(self,val=None,force=False,reportCmd=False):
        LOGGER.info(f'{self.lpfx} val={val} force={force} reportCmd={reportCmd}')
        if val is None:
            val = 100 if self.elk.output_on else 0
        elif val is True:
            val = 100
        elif val is False:
            val = 0
        self.set_driver('ST',val)
        if (not force) and reportCmd:
            if self.elk.output_on:
                LOGGER.debug(f'{self.lpfx} Send DON')
                self.reportCmd("DON")
            else:
                LOGGER.debug(f'{self.lpfx} Send DOF')
                self.reportCmd("DOF")

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def cmd_set_time(self,command):
        val = int(command.get('value'))
        LOGGER.debug(f'{self.lpfx} {val}')
        self.set_time(val)

    def cmd_set_on_wtime(self,command):
        LOGGER.debug(f'{self.lpfx} {command}')
        self.elk.turn_on(int(command.get('value')))

    def cmd_set_on(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.turn_on(self.on_time)

    def cmd_set_off(self,command):
        LOGGER.debug(f'{self.lpfx}')
        self.elk.turn_off()

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
        {'driver': 'TIME',  'value': 0, 'uom': 58},
    ]
    id = 'output'
    commands = {
        'DON': cmd_set_on,
        'DON_WTIME': cmd_set_on_wtime,
        'DOF': cmd_set_off,
        'SET_TIME': cmd_set_time,
        'TOGGLE': cmd_toggle,
        'QUERY': cmd_query,
    }
