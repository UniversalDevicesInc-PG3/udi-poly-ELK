
from udi_interface import LOGGER
from nodes import BaseNode
from node_funcs import get_valid_node_name

from elkm1_lib.const import (
    Max,
    TextDescriptions,
    ThermostatFan,
    ThermostatMode,
    ThermostatSetting,
)

class ThermostatNode(BaseNode):

    def __init__(self, controller, address, elk):
        self.elk    = elk
        self.controller = controller
        self.id = f'Thermostat{controller.temperature_unit}'
        self.init   = False
        self.physical_status = -2
        self.logical_status = -2
        self.poll_voltage = 0
        self.voltage = None
        self.triggered = None
        self.last_changeset = {}
        self.offnode = None
        self.offnode_obj = None
        self.logger    = controller.logger
        try:
            name        = get_valid_node_name(self.elk.name)
            if name == "":
                name = f'Thermostat_{self.elk.index + 1}'
            #self.has_temperature = True # Just for Testing!!!
            LOGGER.info(f'ThermostatNode:init:{name}')
            self.drivers = [
                {'driver': 'CLITEMP', 'value': 0, 'uom': controller.temperature_uom, "name": "Temperature"},
                {'driver': 'CLIMD',   'value': 0, 'uom': 67, "name": "Mode"},
                {'driver': 'CLIHUM',  'value': 0, 'uom': 21, "name": "Humidity"},
                {'driver': 'CLISPH',  'value': 0, 'uom': controller.temperature_uom, "name": "Heat Set Point"},
                {'driver': 'CLISPC',  'value': 0, 'uom': controller.temperature_uom,  "name": "Cool Set Point"},
                {'driver': 'CLIFS',   'value': 0, 'uom': 68, "name": "Fan Setting"},
                {'driver': 'GV1',     'value': 0, 'uom': 78,  "name": "Hold"},
            ]
            super(ThermostatNode, self).__init__(controller, controller.address, address, name)
            controller.poly.subscribe(controller.poly.START, self.start, address)
            LOGGER.debug("{self.lpfx}: exit: name={self.name} address={self.address}")
        except Exception as ex:
            LOGGER.error('ThermostatNode:init',exc_info=True)
            self.inc_error(f"ThermostatNode:init {ex}")

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        try:
            # Set drivers
            self.set_drivers(force=True,reportCmd=False)
            self.reportDrivers()
            self.elk.add_callback(self.callback)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def query(self):
        try:
            self.set_drivers(force=True)
            self.reportDrivers()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def callback(self, obj, changeset):
        LOGGER.info(f'{self.lpfx} changeset={changeset}')
        try:
            ignore = []
            for cs in changeset:
                if cs == 'mode':
                    self.set_mode(changeset[cs].value)
                elif cs == 'hold':
                    self.set_hold(100 if changeset[cs] is True else 0)
                elif cs == 'fan':
                    self.set_fan(changeset[cs].value)
                elif cs == 'current_temp':
                    self.set_current_temp(changeset[cs])
                elif cs == 'heat_setpoint':
                    self.set_heat_setpoint(changeset[cs])
                elif cs == 'cool_setpoint':
                    self.set_cool_setpoint(changeset[cs])
                elif cs == 'humidity':
                    self.set_humidity(changeset[cs])
                elif cs in ignore:
                    LOGGER.debug(f"Nothing to do for key={cs} val={changeset[cs]}")
                else:
                    self.inc_error(f"{self.lpfx} Unknown callback {cs}={changeset[cs]}")
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=True):
        # setUserValues
        LOGGER.debug(f'{self.lpfx} force={force} elk={self.elk}')
        self.set_mode(force=force)
        self.set_hold(force=force)
        self.set_fan(force=force)
        self.set_current_temp(force=force)
        self.set_heat_setpoint(force=force)
        self.set_cool_setpoint(force=force)
        self.set_humidity(force=force)

    def set_mode(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.mode
        else:
            val = int(val)
        self.set_driver('CLIMD', val, report=reportCmd, force=force)

    def set_hold(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.hold
        else:
            val = int(val)
        if val == 1:
            val = 100
        elif val != 0 and val != 100:
            val = 101
        self.set_driver('GV1', val, report=reportCmd, force=force)

    def set_fan(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.fan
        else:
            val = int(val)
        self.set_driver('CLIFS', val, report=reportCmd, force=force)

    def set_current_temp(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.current_temp
        else:
            val = float(val)
        self.set_driver('CLITEMP', val, report=reportCmd, force=force)

    def set_heat_setpoint(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.heat_setpoint
        else:
            val = float(val)
        self.set_driver('CLISPH', val, report=reportCmd, force=force)

    def set_cool_setpoint(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.cool_setpoint
        else:
            val = float(val)
        self.set_driver('CLISPC', val, report=reportCmd, force=force)

    def set_humidity(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.humidity
        else:
            val = float(val)
        self.set_driver('CLIHUM', val, report=reportCmd, force=force)

    def cmd_set_mode(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val} name={ThermostatMode(val).name}')
            self.elk.set(ThermostatSetting.MODE,ThermostatMode._value2member_map_[val])
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_hold(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f"{self.lpfx} val={command.get('value')}")
            val = True if val == 100 else False
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.elk.set(ThermostatSetting.HOLD,val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_fan(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val} name={ThermostatFan(val).name}')
            self.elk.set(ThermostatSetting.FAN,ThermostatFan._value2member_map_[val])
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_heat_setpoint(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.elk.set(ThermostatSetting.HEAT_SETPOINT,val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_cool_setpoint(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.elk.set(ThermostatSetting.COOL_SETPOINT,val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_setpoint(self,cmd):
        if 'value' in cmd:
            val = float(cmd['value'])
        else:
            val = 1
        if cmd['cmd'] == 'DIM':
            val = val * -1
        if self.elk.mode == ThermostatMode.AUTO or self.elk.mode == ThermostatMode.HEAT:
            self.elk.set(ThermostatSetting.HEAT_SETPOINT,self.elk.heat_setpoint + val)
        else:
            self.elk.set(ThermostatSetting.COOL_SETPOINT,self.elk.cool_setpoint + val)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = '0x010c0100'

    commands = {
        "QUERY": query,
        'CLIMD': cmd_set_mode,
        'CLIFS': cmd_set_fan,
        'GV1':   cmd_set_hold,
        'CLISPH': cmd_set_heat_setpoint,
        'CLISPC': cmd_set_cool_setpoint,
        'BRT': cmd_setpoint,
        'DIM': cmd_setpoint,
        }
