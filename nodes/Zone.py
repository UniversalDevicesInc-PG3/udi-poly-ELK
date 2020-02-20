
import polyinterface
LOGGER = polyinterface.LOGGER
from nodes import ZoneOffNode


class ZoneNode(polyinterface.Node):

    def __init__(self, controller, elk):
        LOGGER.debug("Zone:__init__: {}".format(elk))
        self.elk    = elk
        self.controller = controller
        self.init   = False
        self.physical_status = -2
        self.logical_status = -2
        self.offnode = None
        self.offnode_obj = None
        self.address   = 'zone_{}'.format(self.elk.index)
        self.parent_address = 'area_{}'.format(self.elk.area)
        super(ZoneNode, self).__init__(controller, self.parent_address, self.address, self.elk.name)

    def start(self):
        self.l_debug('start','')
        # Set drivers that never change
        # Definition Type
        self.setDriver('GV3',self.elk.definition)
        # Zone Area
        self.setDriver('GV2', self.elk.area)
        # Set drivers that change
        self.set_drivers(force=True,reportCmd=False)
        self.elk.add_callback(self.callback)

    def query(self):
        self.set_drivers(force=False,reportCmd=False)

    def callback(self, obj, changeset):
        self.l_debug('callback','changeset={}'.format(changeset))
        if 'physical_status' in changeset:
            self.set_physical_status(changeset['physical_status'])
        if 'logical_status' in changeset:
            self.set_logical_status(changeset['logical_status'])

    def set_drivers(self,force=False,reportCmd=True):
        self.l_debug('set_drivers','')
        #LOGGER.debug('_set_drivers: Zone:{} description:"{}" state:{}={} status:{}={} enabled:{} area:{} definition:{}={} alarm:{}={}'
        #            .format(pyelk.number, pyelk.description, pyelk.state, pyelk.state_pretty(), pyelk.status, pyelk.status_pretty(), pyelk.enabled,
        #                    pyelk.area, pyelk.definition, pyelk.definition_pretty(), pyelk.alarm, pyelk.alarm_pretty()))
        self.set_onoff()
        self.set_physical_status(force=force,reportCmd=reportCmd)
        self.set_logical_status(force=force)
        self.set_offnode()
        self.set_triggered()
        self.set_bypassed()

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
        if val is None:
            val = self.elk.physical_status
        else:
            val = int(val)
        self.l_info('set_physical_status','val={} onoff={}'.format(val,self.onoff))
        if force or val != self.physical_status:
            self.physical_status = val
            # Send DON for Violated?
            if reportCmd and self.onoff != 1:
                if (val == 1 and (self.onoff == 0 or self.onoff == 2)) or (val == 3 and (self.onoff == 4 or self.onoff == 6)):
                    self.reportCmd("DON",2)
                elif (val == 3 and (self.onoff == 0 or self.onoff == 3)) or (val == 1 and (self.onoff == 4 or self.onoff == 5)):
                    if self.offnode_obj is None:
                        self.reportCmd("DOF",2)
                    else:
                        self.offnode_obj.reportCmd("DOF",2)
            self.setDriver('ST', val)
            if self.offnode_obj is not None:
                self.offnode_obj.setDriver('ST', val)

    def set_logical_status(self,val=None,force=False):
        if val is None:
            val = self.elk.logical_status
        else:
            val = int(val)
        self.l_debug('set_logical_status','{}'.format(val))
        self.logical_status = val
        self.setDriver('GV0', val)
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
                self.l_error('set_triggered','Unknown value {}, assuming 0'.format(val))
                val = 0
        else:
            val = int(val)
        self.l_debug('set_triggered','{}'.format(val))
        self.setDriver('GV1', val)

    def set_bypassed(self,val=None,force=False):
        if val is None:
            val = self.elk.bypassed
            if val is True:
                val = 1
            elif val is False:
                val = 0
            else:
                self.l_error('set_bypassed','Unknown value {}, assuming 0'.format(val))
                val = 0
        else:
            val = int(val)
        self.l_debug('set_bypassed','{}'.format(val))
        self.setDriver('GV6', val)

    def setOn(self, command):
        self.setDriver('ST', 1)

    def setOff(self, command):
        self.setDriver('ST', 0)

    def query(self):
        self.set_drivers()
        self.reportDrivers()

    def set_onoff(self,val=None):
        mname = 'set_onoff'
        self.l_info(mname,val)
        # Restore onoff setting from DB for existing nodes
        mdrv = 'GV5'
        if val is None:
            try:
                val = self.getDriver(mdrv)
                self.l_info(mname,val)
            except:
                self.l_error(mname,'getDriver({}) failed'.format(mdrv),True)
                val = 0
        if val is None:
            val = 0
        else:
            val = int(val)
        try:
            self.setDriver(mdrv, val)
            self.onoff = val
        except:
            self.l_error(mname,'setDriver({},{}) failed'.format(mdrv,val),True)

    def set_offnode(self,val=None):
        mname = 'set_offnode'
        self.l_info(mname,'val={} offnode={} offnode_obj={}'.format(val,self.offnode,self.offnode_obj))
        # Restore offnode setting from DB for existing nodes
        mdrv = 'GV7'
        if val is None:
            try:
                val = self.getDriver(mdrv)
                self.l_info(mname,val)
            except:
                self.l_error(mname,'getDriver({}) failed'.format(mdrv),True)
                val = 0
        if val is None:
            val = 0
        else:
            val = int(val)
        try:
            self.setDriver(mdrv, val)
            self.offnode = val
        except:
            self.l_error(mname,'setDriver({},{}) failed'.format(mdrv,val),True)
        if val == 0:
            if self.offnode_obj is not None:
                self.controller.delNode(self.offnode_obj.address)
            self.offnode_obj = None
        else:
            if self.offnode_obj is None:
                self.l_info(mname,"Adding off node.")
                self.offnode_obj = self.controller.addNode(ZoneOffNode(self.controller,self.parent_address,self.address+'_off',self.elk.name+" - Off",
                self.physical_status, self.logical_status))

    def cmd_set_onoff(self,command):
        val = int(command.get('value'))
        self.l_info("cmd_set_onoff",val)
        self.set_onoff(val)

    def cmd_set_offnode(self,command):
        val = int(command.get('value'))
        self.l_info("cmd_set_offnode",val)
        self.set_offnode(val)

    def l_info(self, name, string):
        LOGGER.info("%s:%s:%s: %s" %  (self.id,self.name,name,string))

    def l_error(self, name, string):
        LOGGER.error("%s:%s:%s: %s" % (self.id,self.name,name,string))

    def l_warning(self, name, string):
        LOGGER.warning("%s:%s:%s: %s" % (self.id,self.name,name,string))

    def l_debug(self, name, string):
        LOGGER.debug("%s:%s:%s: %s" % (self.id,self.name,name,string))

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
        {'driver': 'GV6', 'value': 0, 'uom': 2},
        # off node
        {'driver': 'GV7', 'value': 0, 'uom': 2},
    ]
    id = 'zone'
    commands = {
        'SET_ONOFF': cmd_set_onoff,
        'SET_OFFNODE': cmd_set_offnode,
    }
