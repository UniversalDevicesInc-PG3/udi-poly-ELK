
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
        try:
            name        = get_valid_node_name(self.elk.name)
            if name == "":
                name = f'Output_{self.elk.index + 1}'
            LOGGER.debug(f'OutputNode:init: {name}')
            super(OutputNode, self).__init__(controller, controller.address, address, name)
            controller.poly.subscribe(controller.poly.START, self.start, address)
        except Exception as ex:
            LOGGER.error('OutputNode:init:',exc_info=True)
            self.inc_error(f"OutputNode:init: {ex}")

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
        self.set_onoff(force=force,reportCmd=reportCmd)

    def set_time(self,val=0,force=False):
        LOGGER.info(f'{self.lpfx}')
        self.on_time = int(val)
        self.set_driver('TIME',self.on_time)

    def set_onoff(self,val=None,force=False,reportCmd=False):
        try:
            LOGGER.info(f'{self.lpfx} val={val} force={force} reportCmd={reportCmd}')
            if val is None:
                val = 100 if self.elk.output_on else 0
            elif val is True:
                val = 100
            elif val is False:
                val = 0
            self.set_driver('ST',val,force=force)
            if (not force) and reportCmd:
                if self.elk.output_on:
                    LOGGER.debug(f'{self.lpfx} Send DON')
                    self.reportCmd("DON")
                else:
                    LOGGER.debug(f'{self.lpfx} Send DOF')
                    self.reportCmd("DOF")
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_time(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} {val}')
            self.set_time(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_on_wtime(self,command):
        try:
            LOGGER.debug(f'{self.lpfx} {command}')
            self.elk.turn_on(int(command.get('value')))
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_on(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.elk.turn_on(self.on_time)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_off(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.elk.turn_off()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_toggle(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.elk.toggle()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_query(self,command):
        try:
            LOGGER.debug(f'{self.lpfx}')
            self.query()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # On/Off
        {'driver': 'ST',  'value': 101, 'uom': 78, "desc": "Status"},
        {'driver': 'TIME',  'value': 0, 'uom': 58, "desc": "Default On Seconds"},
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
