
from polyinterface import Node

class ZoneOffNode(Node):

    def __init__(self, controller, parent_address, address, name, physical_status, logical_status):
        LOGGER.debug("ZoneOff:__init__: {} {}".format(address,name))
        self.logical_status = logical_status
        self.physical_status = physical_status
        self.logger    = controller.logger
        super(ZoneOffNode, self).__init__(controller, parent_address, address, name)
        self._lstring = "%s:%s:" % (self.id,self.name)
        self._lstring += '%s: '

    def start(self):
        self.l_debug('start','')
        super(ZoneOffNode, self).start()
        # Init values from Zone node
        self.setDriver('ST',self.physical_status)
        self.setDriver('GV0',self.logical_status)

    def l_info(self, name, string, *argv):
        fst = '%s%s' % (self._lstring,string)
        self.logger.info(fst,name,*argv)

    def l_error(self, name, string, exc_info=False, *args):
        self.logger.error("%s:%s:%s: %s" % (self.id,self.name,name,string), exc_info=exc_info)

    def l_warning(self, name, string):
        self.logger.warning("%s:%s: %s" % (self.id,name,string))

    def l_debug(self, name, string, exc_info=False):
        self.logger.debug("%s:%s: %s" % (self.id,name,string), exc_info=exc_info)


    "Hints See: https://github.com/UniversalDevicesInc/hints"
    hint = [1,2,3,4]
    drivers = [
        # physical status
        {'driver': 'ST',  'value': 0, 'uom': 25},
        # logical status
        {'driver': 'GV0', 'value': 0, 'uom': 25},
    ]
    id = 'zoneoff'
    commands = {
    }
