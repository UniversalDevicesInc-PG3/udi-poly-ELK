

import polyinterface
LOGGER = polyinterface.LOGGER

class ZoneNode(polyinterface.Node):

    def __init__(self, controller, parent_address, address, name, pyelk_obj):
        super(ZoneNode, self).__init__(controller, parent_address, address, name)
        self.pyelk  = pyelk_obj
        self.state  = -2
        self.status = -2

    def start(self):
        self.set_drivers(force=True,reportCmd=False)
        self.pyelk.callback_add(self.pyelk_callback)

    def set_drivers(self,force=False,reportCmd=True):
        self._set_drivers(self.pyelk,force=force,reportCmd=reportCmd)

    def _set_drivers(self,pyelk,force=False,reportCmd=True):
        LOGGER.debug('_set_drivers: Zone:{} description:"{}" state:{}={} status:{}={} enabled:{} area:{} definition:{}={} alarm:{}={}'
                    .format(pyelk.number, pyelk.description, pyelk.state, pyelk.state_pretty(), pyelk.status, pyelk.status_pretty(), pyelk.enabled,
                            pyelk.area, pyelk.definition, pyelk.definition_pretty(), pyelk.alarm, pyelk.alarm_pretty()))
        # Others need this set
        self.set_onoff()
        # ISY Calls this Status, PyELK calls it state
        self.set_state(pyelk.state,force,reportCmd)
        # ISY Calls this Physical Status? PyELK Calls it Status
        self.set_status(pyelk.status,force)
        if pyelk.enabled:
            self.setDriver('GV1', 1)
        else:
            self.setDriver('GV1', 0)
        self.setDriver('GV2', pyelk.area)
        self.setDriver('GV3', pyelk.definition)
        self.setDriver('GV4', pyelk.alarm)

    """
        ZDCONF-0 = Send Both
        ZDCONF-1 = Send None
        ZDCONF-2 = ON Only
        ZDCONF-3 = OFF Only
        ZDCONF-4 = Reverse Send Both
        ZDCONF-5 = Reverse On Only
        ZDCONF-6 = Reverse Off Only
    """
    def set_state(self,val,force=False,reportCmd=True):
        self.l_info('set_state','val={} onoff={}'.format(val,self.onoff))
        val = int(val)
        if force or val != self.state:
            self.state = val
            # Send DON for Violated?
            if reportCmd and self.onoff != 1:
                if (val == 1 and (self.onoff == 0 or self.onoff == 2)) or (val == 3 and (self.onoff == 4 or self.onoff == 6)):
                    self.reportCmd("DON",2)
                elif (val == 3 and (self.onoff == 0 or self.onoff == 3)) or (val == 1 and (self.onoff == 4 or self.onoff == 5)):
                    self.reportCmd("DOF",2)
            self.setDriver('ST', val)

    def set_status(self,val,force=False):
        val = int(val)
        self.setDriver('GV0', val)

    def pyelk_callback(self,obj,data):
        LOGGER.debug('pyelk_callback:zone: obj={} data={}'.format(obj,data))
        self._set_drivers(data)

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
        mdrv = 'GV5'
        if val is None:
            try:
                val = self.getDriver(mdrv)
                self.l_info(mname,val)
            except:
                self.l_error(mname,'getDriver({}) failed'.format(mdrv),True)
                val = 0
        val = int(val)
        try:
            self.setDriver(mdrv, val)
            self.onoff = val
        except:
            self.l_error(mname,'setDriver({},{}) failed'.format(mdrv,val),True)

    def cmd_set_onoff(self,command):
        val = int(command.get('value'))
        self.l_info("cmd_set_onoff",val)
        self.set_onoff(val)

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
        # status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # state
        {'driver': 'GV0', 'value': 0, 'uom': 25},
        # enabled
        {'driver': 'GV1', 'value': 0, 'uom': 2},
        # area
        {'driver': 'GV2', 'value': 0, 'uom': 56},
        # definition type
        {'driver': 'GV3', 'value': 0, 'uom': 25},
        # alarm configuration
        {'driver': 'GV4', 'value': 0, 'uom': 25},
        # DON/DOF Config
        {'driver': 'GV5', 'value': 0, 'uom': 25},
    ]
    id = 'zone'
    commands = {
        'SET_ONOFF': cmd_set_onoff,
    }
