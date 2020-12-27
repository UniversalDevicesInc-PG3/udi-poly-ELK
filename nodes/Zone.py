
from polyinterface import Node,LOGGER
from nodes import ZoneOffNode
from elkm1_lib.const import (
    Max,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
)

class ZoneNode(Node):

    def __init__(self, controller, parent, area, elk):
        self.elk    = elk
        self.controller = controller
        self.parent     = parent
        self.area       = area
        self.init   = False
        self.physical_status = -2
        self.logical_status = -2
        self.last_changeset = {}
        self.offnode = None
        self.offnode_obj = None
        self.address   = 'zone_{}'.format(self.elk.index)
        self.parent_address = 'area_{}'.format(self.elk.area)
        self.logger    = controller.logger
        super(ZoneNode, self).__init__(controller, self.parent_address, self.address, self.elk.name)
        self.lpfx = f'{self.name}:'

    def start(self):
        LOGGER.debug(f'{self.lpfx} in area={self.area.name}')
        # Set drivers that never change
        # Definition Type
        self.setDriver('GV3',self.elk.definition)
        # Zone Area
        self.setDriver('GV2', self.elk.area)
        # Set drivers, but dont report don/dof
        self.set_drivers(force=True,reportCmd=False)
        self.reportDrivers()
        self.elk.add_callback(self.callback)

    def query(self):
        self.set_drivers(force=False,reportCmd=False)

    def callback(self, obj, changeset):
        LOGGER.debug(f'{self.lpfx} changeset={changeset}')
        # Why does it get called multiple times with same data?
        if 'physical_status' in changeset:
            self._set_physical_status(changeset['physical_status'])
        if 'logical_status' in changeset:
            self._set_logical_status(changeset['logical_status'])

    def set_drivers(self,force=False,reportCmd=True):
        LOGGER.debug(f'{self.lpfx} force={force} reportCmd={reportCmd}')
        #LOGGER.debug('_set_drivers: Zone:{} description:"{}" state:{}={} status:{}={} enabled:{} area:{} definition:{}={} alarm:{}={}'
        #            .format(pyelk.number, pyelk.description, pyelk.state, pyelk.state_pretty(), pyelk.status, pyelk.status_pretty(), pyelk.enabled,
        #                    pyelk.area, pyelk.definition, pyelk.definition_pretty(), pyelk.alarm, pyelk.alarm_pretty()))
        self.set_onoff()
        self.set_physical_status(force=force,reportCmd=reportCmd)
        self.set_logical_status(force=force)
        self.set_offnode()
        self.set_triggered()

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
        LOGGER.debug(f'{self.lpfx} val={val} onoff={self.onoff}')
        if val is None:
            val = self.elk.physical_status
        else:
            val = int(val)
        self._set_physical_status(val,force=force,reportCmd=reportCmd)

    def _set_physical_status(self,val,force=False,reportCmd=True):
        if val == self.physical_status and not force:
            return            
        LOGGER.debug(f'{self.lpfx} val={val} current={self.physical_status} force={force} onoff={self.onoff}')
        # Send DON for Violated?
        # Only if we are not farcing the same value
        if (not force) and reportCmd:
            if (val == 1 and (self.onoff == 0 or self.onoff == 2)) or (val == 3 and (self.onoff == 4 or self.onoff == 6)):
                LOGGER.debug(f'{self.lpfx} Send DON')
                self.reportCmd("DON")
            elif (val == 3 and (self.onoff == 0 or self.onoff == 3)) or (val == 1 and (self.onoff == 4 or self.onoff == 5)):
                if self.offnode_obj is None:
                    LOGGER.debug(f'{self.lpfx} Send DOF ')
                    self.reportCmd("DOF")
                else:
                    LOGGER.debug(f'{self.lpfx} Send DOF to {self.offnode_obj.name}')
                    self.offnode_obj.reportCmd("DOF")
        self.setDriver('ST', val)
        self.physical_status = val
        if self.offnode_obj is not None:
            self.offnode_obj.setDriver('ST', val)

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
        self.setDriver('GV0', val)
        if ZoneLogicalStatus(val).name == 'BYPASSED':
            # Already set?
            if self.logical_status < 0 or ZoneLogicalStatus(self.logical_status).name != 'BYPASSED':
                self.area.zone_bypass_add()
        else:
            # Already set?
            if self.logical_status >= 0 and ZoneLogicalStatus(self.logical_status).name == 'BYPASSED':
                self.area.zone_bypass_sub()
        if ZoneLogicalStatus(val).name == 'VIOLATED':
            # Already set?
            if self.logical_status < 0 or ZoneLogicalStatus(self.logical_status).name != 'VIOLATED':
                self.area.zone_violated_add()
        else:
            # Already set?
            if self.logical_status >= 0 and ZoneLogicalStatus(self.logical_status).name == 'VIOLATED':
                self.area.zone_violated_sub()
        self.logical_status = val
        if self.offnode_obj is not None:
            self.offnode_obj.setDriver('GV0', val)

    def set_triggered(self,val=None,force=False):
        if val is None:
            val = self.elk.triggered_alarm
            if val is True:
                val = 1
            elif val is False:
                val = 0
            else:
                LOGGER.error(f'{self.lpfx} Unknown value {val}, assuming 0')
                val = 0
        else:
            val = int(val)
        LOGGER.debug(f'{self.lpfx} val={val}')
        self.setDriver('GV1', val)


    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def set_driver(self,mdrv,val,default=0):
        if val is None:
            # Restore from DB for existing nodes
            try:
                val = self.getDriver(mdrv)
                LOGGER.info(f'{self.lpfx} {val}')
            except:
                LOGGER.warning(f'{self.lpfx} getDriver({mdrv}) failed which can happen on new nodes, using {default}')
                val = default
        val = default if val is None else int(val)
        try:
            LOGGER.debug(f'{self.lpfx} setDriver({mdrv},{val})')
            self.setDriver(mdrv, val)
        except:
            LOGGER.error(f'{self.lpfx} setDriver({mdrv},{val}) failed')
            return None
        return val

    def set_onoff(self,val=None):
        LOGGER.info(f'{self.lpfx} {val}')
        self.onoff = self.set_driver('GV5',val)

    def set_offnode(self,val=None):
        LOGGER.info(f'{self.lpfx} val={val} offnode={self.offnode} offnode_obj={self.offnode_obj}')
        self.offnode  = self.set_driver('GV7',val)
        if self.offnode == 0:
            # No more off node, delete the node...
            if self.offnode_obj is not None:
                LOGGER.info(f'{self.lpfx} Deleting off node {self.offnode_obj.address}')
                self.controller.delNode(self.offnode_obj.address)
            self.offnode_obj = None
        else:
            # We have a off node, is it new?
            if self.offnode_obj is None:
                LOGGER.info(f'{self.lpfx} Adding off node')
                self.offnode_obj = self.controller.addNode(ZoneOffNode(self.controller,self.parent_address,self.address+'_off',self.elk.name+" - Off",
                self.physical_status, self.logical_status))

    def cmd_set_onoff(self,command):
        val = int(command.get('value'))
        LOGGER.debug(f'{self.lpfx} val={val}')
        self.set_onoff(val)

    def cmd_set_offnode(self,command):
        val = int(command.get('value'))
        LOGGER.debug(f'{self.lpfx} val={val}')
        self.set_offnode(val)

    def cmd_set_bypass(self,command):
        LOGGER.info(f'{self.lpfx} Calling bypass...')
        self.elk.bypass(self.controller.user_code)

    def cmd_clear_bypass(self,command):
        LOGGER.info(f'{self.lpfx} Calling bypass...')
        self.elk.clear_bypass(self.controller.user_code)

    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # physical status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # logical status
        {'driver': 'GV0', 'value': 0, 'uom': 25},
        # triggered
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        # area
        {'driver': 'GV2', 'value': 0, 'uom': 56},
        # definition type
        {'driver': 'GV3', 'value': 0, 'uom': 25},
        # alarm configuration
        {'driver': 'GV4', 'value': 0, 'uom': 25},
        # DON/DOF Config
        {'driver': 'GV5', 'value': 0, 'uom': 25},
        # bypassed
        #{'driver': 'GV6', 'value': 0, 'uom': 2},
        # off node
        {'driver': 'GV7', 'value': 0, 'uom': 2},
    ]
    id = 'zone'
    commands = {
        'SET_ONOFF': cmd_set_onoff,
        'SET_OFFNODE': cmd_set_offnode,
        'SET_BYPASS': cmd_set_bypass,
        'CLEAR_BYPASS': cmd_clear_bypass,
    }
