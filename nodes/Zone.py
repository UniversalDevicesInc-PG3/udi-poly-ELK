
from udi_interface import LOGGER
from nodes import BaseNode,ZoneOffNode
from node_funcs import get_valid_node_name
from const import SYSTEM_TROUBLE_STATUS_ZONE

from elkm1_lib.const import (
    Max,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
)

class ZoneNode(BaseNode):
    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 25, "name": "Logical Status"},
        {'driver': 'GV0', 'value': 0, 'uom': 25, "name": "Physical Status"},
        {'driver': 'GV1', 'value': 0, 'uom': 2, "name": "Triggered Alarm"},
        {'driver': 'GV2', 'value': 0, 'uom': 56, "name": "Area"},
        {'driver': 'GV3', 'value': 0, 'uom': 25, "name": "Definition"},
        {'driver': 'GV4', 'value': 0, 'uom': 25, "name": "Alarm"},
        # DON/DOF Config
        #{'driver': 'GV5', 'value': 0, 'uom': 25, "name": "Send On/Off"},
        #{'driver': 'GV6', 'value': 0, 'uom': 2, "name": "Bypassed"},
        {'driver': 'GV7', 'value': 0, 'uom': 2,  'restore':True, "name": "Off Node"},
        {'driver': 'GV8', 'value': 1, 'uom': 25, 'restore':True, "name": "Send ON for"},
        {'driver': 'GV9', 'value': 2, 'uom': 25, 'restore':True, "name": "Send OFF for"},
        {'driver': 'CV',  'value': 0, 'uom': 72, "name": "Poll Voltage"},
        {'driver': 'GV10', 'value': 0, 'uom': 2, "name": "Voltage"},
        {"driver": "GV11", "value": 0, "uom": 2, "name": "Box Tamper"},
        {"driver": "GV12", "value": 0, "uom": 2, "name": "Transmitter Low Battery"},
        {"driver": "GV13", "value": 0, "uom": 2, "name": "Security Alert"},
        {"driver": "GV14", "value": 0, "uom": 2, "name": "Lost Transmitter"},
        {"driver": "GV15", "value": 0, "uom": 2, "name": "Fire"},
    ]

    def __init__(self, controller, parent, address, elk):
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.area       = parent
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
                name = f'Zone_{self.elk.index + 1}'
            self.has_temperature = False if self.elk.temperature == -60 else True
            #self.has_temperature = True # Just for Testing!!!
            LOGGER.info(f'ZoneNode:init:{name} temperature={self.elk.temperature} has_temperature={self.has_temperature}')
            if self.has_temperature:
                self.id = 'zoneT'
                self.drivers.append({'driver': 'CLITEMP', 'value': self.elk.temperature, 'uom': self.controller.temperature_uom})
            super(ZoneNode, self).__init__(controller, parent.address, address, name)
            controller.poly.subscribe(controller.poly.START, self.start, address)
            LOGGER.debug("{self.lpfx}: exit: name={self.name} address={self.address}")
        except Exception as ex:
            LOGGER.error('ZoneNode:init',exc_info=True)
            self.inc_error(f"ZoneNode:init {ex}")

    def start(self):
        LOGGER.debug(f'{self.lpfx} {self.elk}')
        try:
            # Set drivers that never change
            # Definition Type
            self.set_driver('GV3',self.elk.definition)
            # Zone Area
            self.set_driver('GV2', self.elk.area + 1)
            # Set drivers, but dont report don/dof
            self.set_drivers(force=True,reportCmd=False)
            self.reportDrivers()
            self.elk.add_callback(self.callback)
            # Force get_voltage call
            self.elk.get_voltage()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def shortPoll(self,poll_voltage=False):
        LOGGER.debug(f'{self.lpfx} poll_voltage={poll_voltage} and self.poll_voltage={self.poll_voltage}')
        if poll_voltage and self.poll_voltage == 1:
            self.elk.get_voltage()

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
                if cs == 'triggered_alarm':
                    self._set_triggered(1 if changeset[cs] is True else 0)
                elif cs == 'physical_status':
                    self._set_physical_status(changeset[cs])
                elif cs == 'logical_status':
                    self._set_logical_status(changeset[cs])
                elif 'voltage' in changeset:
                    self._set_voltage(changeset[cs])
                elif cs == 'temperature':
                    self.set_temperature(changeset[cs])
                elif cs in ignore:
                    LOGGER.debug(f"Nothing to do for key={cs} val={changeset[cs]}")
                else:
                    LOGGER.warning(f'{self.lpfx} Unknown callback {cs}={changeset[cs]}')
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False,reportCmd=True):
        # setUserValues
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        #LOGGER.debug('_set_drivers: Zone:{} description:"{}" state:{}={} status:{}={} enabled:{} area:{} definition:{}={} alarm:{}={}'
        #            .format(pyelk.number, pyelk.description, pyelk.state, pyelk.state_pretty(), pyelk.status, pyelk.status_pretty(), pyelk.enabled,
        #                    pyelk.area, pyelk.definition, pyelk.definition_pretty(), pyelk.alarm, pyelk.alarm_pretty()))
        self.set_son(force=force)
        self.set_soff(force=force)
        self.set_offnode(force=force)
        self.set_physical_status(force=force,reportCmd=reportCmd)
        self.set_logical_status(force=force)
        self.set_triggered(force=force)
        self.set_voltage(force=force)
        self.set_poll_voltage(force=force)
        self.set_temperature(force=force)
        self.elk.get_voltage()
        self.set_system_trouble_status(
            self.controller.get_system_trouble_status_for_zone(self.elk.index+1),
            force
        )

    """
        ZDCONF-0 = Send Both
        ZDCONF-1 = Send None
        ZDCONF-2 = ON Only
        ZDCONF-3 = OFF Only
        ZDCONF-4 = Reverse Send Both
        ZDCONF-5 = Reverse On Only
        ZDCONF-6 = Reverse Off Only
    """
    def set_physical_status(self,val=None,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.physical_status
        else:
            val = int(val)
        self._set_physical_status(val,force=force,reportCmd=reportCmd)

    def _set_physical_status(self,val,force=False,reportCmd=True):
        if val == self.physical_status and not force:
            return
        LOGGER.debug(f'{self.lpfx} val={val} current={self.physical_status} force={force} reportCmd={reportCmd}')
        # Only if we are not farcing the same value
        if (not force) and reportCmd:
            LOGGER.info(f'{self.lpfx} son={self.son} soff={self.soff}')
            if val.value == self.son:
                LOGGER.info(f'{self.lpfx} Send DON')
                self.reportCmd("DON")
            elif val.value == self.soff:
                if self.offnode_obj is None:
                    LOGGER.info(f'{self.lpfx} Send DOF ')
                    self.reportCmd("DOF")
                else:
                    LOGGER.info(f'{self.lpfx} Send DOF to {self.offnode_obj.name}')
                    self.offnode_obj.reportCmd("DOF")
        self.set_driver('GV0', val, force=force)
        self.physical_status = val
        if self.offnode_obj is not None:
            self.offnode_obj.set_driver('GV0', val, force=force)

    def set_logical_status(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val}')
        if val is None:
            val = self.elk.logical_status
        else:
            val = int(val)
        self._set_logical_status(val,force=force)

    def _set_logical_status(self,val,force=False):
        if val == self.logical_status and not force:
            return
        LOGGER.debug(f'{self.lpfx} val={val}')
        self.set_driver('ST', val)
        self.logical_status = val
        if val == ZoneLogicalStatus.VIOLATED:
            self.area.set_last_violated_zone(self.elk.index)
        if self.offnode_obj is not None:
            self.offnode_obj.set_driver('ST', val, force=force)
        self.area.set_zone_logical_status(self.elk.index,val)

    def set_temperature(self,val=None,force=False,reportCmd=True):
        LOGGER.info(f'{self.lpfx} has_temperature={self.has_temperature}')
        if not self.has_temperature:
            return
        if val is None:
            val = self.elk.temperature
        self.set_driver('CLITEMP', val, report=reportCmd, force=force, uom=self.controller.temperature_uom, prec=1)

    def set_voltage(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} elk.voltage={self.elk.voltage}')
        if val is None:
            val = self.elk.voltage
        self._set_voltage(val,force=force)

    def _set_voltage(self,val,force=False):
        if val == self.voltage and not force:
            return
        LOGGER.debug(f'{self.lpfx} val={val}')
        self.set_driver('CV', val, prec=1, force=force)
        self.voltage = val

    def set_triggered(self,val=None,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val is None:
            val = self.elk.triggered_alarm
            if val is True:
                val = 1
            elif val is False:
                val = 0
            else:
                msg = f'{self.lpfx} Unknown value {val}, assuming 0'
                LOGGER.error(msg)
                self.inc_error(msg)
                val = 0
        else:
            val = int(val)
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        self._set_triggered(val=val,force=force)

    def _set_triggered(self,val,force=False):
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val == 1:
            self.area.set_last_triggered_zone(self.elk.index)
        if val == self.triggered and not force:
            return
        self.set_driver('GV1', val, force=force)
        self.triggered = val

    def set_son(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.son = self.set_driver('GV8',val,default=1,force=force)

    def set_soff(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} {val}')
        self.soff = self.set_driver('GV9',val,default=2,force=force)

    def set_offnode(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} val={val} offnode={self.offnode} offnode_obj={self.offnode_obj}')
        self.offnode  = self.set_driver('GV7',val,0,force=force)
        if self.offnode == 0:
            # No more off node, delete the node...
            if self.offnode_obj is not None:
                LOGGER.info(f'{self.lpfx} Deleting off node {self.offnode_obj.address}')
                self.controller.poly.delNode(self.offnode_obj.address)
            self.offnode_obj = None
        else:
            # We have a off node, is it new?
            if self.offnode_obj is None:
                LOGGER.info(f'{self.lpfx} Adding off node')
                address = self.address+'_off'
                self.offnode_obj = self.controller.add_node(address,ZoneOffNode(self.controller,self.parent.address,address,self.elk.name+" - Off",
                self.physical_status, self.logical_status))

    def set_poll_voltage(self,val=None,force=False):
        LOGGER.info(f'{self.lpfx} val={val}')
        self.poll_voltage  = int(self.set_driver('GV10',val,0))

    def clear_system_trouble_status(self,force=False):
        try:
            LOGGER.info(f'{self.lpfx} force={force}')
            for status in SYSTEM_TROUBLE_STATUS_ZONE:
                SYSTEM_TROUBLE_STATUS_ZONE[status]['value'] = 0
            for status in SYSTEM_TROUBLE_STATUS_ZONE:
                self.setDriver(SYSTEM_TROUBLE_STATUS_ZONE[status]['driver'],SYSTEM_TROUBLE_STATUS_ZONE[status]['value'],force=force)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_system_trouble_status(self,status_list,force=False):
        try:
            LOGGER.info(f'{self.lpfx} status_list={status_list}')
            for status in SYSTEM_TROUBLE_STATUS_ZONE:
                SYSTEM_TROUBLE_STATUS_ZONE[status]['value'] = 0
            for status in status_list:
                if status in SYSTEM_TROUBLE_STATUS_ZONE:
                    LOGGER.warning(f'{self.lpfx} Setting System Trouble Status for: {status}')
                    SYSTEM_TROUBLE_STATUS_ZONE[status]['value'] = 1
                else:
                    msg = f"{self.lpfx} Unknown system trouble status zone '{status}'"
                    LOGGER.error(msg)
                    self.inc_error(msg)
            # Set all our trouble status's
            for status in SYSTEM_TROUBLE_STATUS_ZONE:
                if SYSTEM_TROUBLE_STATUS_ZONE[status]['value'] == 1:
                    LOGGER.warning(f'{self.lpfx} Setting System Trouble Status Zone for: {status}=True')
                self.setDriver(SYSTEM_TROUBLE_STATUS_ZONE[status]['driver'],SYSTEM_TROUBLE_STATUS_ZONE[status]['value'],force=force)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")


    def cmd_set_son(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.set_son(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_soff(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.set_soff(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_offnode(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.set_offnode(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_poll_voltage(self,command):
        try:
            val = int(command.get('value'))
            LOGGER.debug(f'{self.lpfx} val={val}')
            self.set_poll_voltage(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_set_bypass(self,command):
        try:
            LOGGER.info(f'{self.lpfx} Calling bypass...')
            self.elk.bypass(self.controller.user_code)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_clear_bypass(self,command):
        try:
            LOGGER.info(f'{self.lpfx} Calling bypass...')
            self.elk.clear_bypass(self.controller.user_code)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_trigger(self,command):
        try:
            LOGGER.warning(f'{self.lpfx} Calling trigger...')
            self.elk.trigger()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_don(self,command):
        LOGGER.debug(f'{self.lpfx} Zones do nothing when DON received')

    def cmd_dof(self,command):
        LOGGER.debug(f'{self.lpfx} Zones do nothing when DOF received')

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]

    id = 'zone'
    commands = {
        "QUERY": query,
        'SET_SON': cmd_set_son,
        'SET_SOFF': cmd_set_soff,
        'SET_BYPASS': cmd_set_bypass,
        'CLEAR_BYPASS': cmd_clear_bypass,
        'SET_OFFNODE': cmd_set_offnode,
        'SET_POLL_VOLTAGE': cmd_set_poll_voltage,
        'TRIGGER': cmd_trigger,
        'DON': cmd_don,
        'DOF': cmd_dof,
    }
