

import polyinterface

class BaseController(polyinterface.Controller):

    def __init__(self, polyglot):
        self.logger = polyinterface.LOGGER
        super(BaseController, self).__init__(polyglot)

    def heartbeat(self):
        self.l_debug('heartbeat','hb={}'.format(self.hb))
        if self.hb == 0:
            self.reportCmd("DON",2)
            self.hb = 1
        else:
            self.reportCmd("DOF",2)
            self.hb = 0

    def l_info(self, name, string):
        self.logger.info("%s:%s: %s" %  (self.id,name,string))

    def l_error(self, name, string, exc_info=False):
        self.logger.error("%s:%s:%s: %s" % (self.id,self.name,name,string), exc_info=exc_info)

    def l_warning(self, name, string):
        self.logger.warning("%s:%s: %s" % (self.id,name,string))

    def l_debug(self, name, string, exc_info=False):
        self.logger.debug("%s:%s: %s" % (self.id,name,string), exc_info=exc_info)

class BaseNode(polyinterface.Node):

    def __init__(self, controller, parent, address, name):
        self.logger    = polyinterface.LOGGER
        super(BaseNode, self).__init__(controller, parent, address, name)

    def l_info(self, name, string):
        self.logger.info("%s:%s: %s" %  (self.id,name,string))

    def l_error(self, name, string, exc_info=False):
        self.logger.error("%s:%s:%s: %s" % (self.id,self.name,name,string), exc_info=exc_info)

    def l_warning(self, name, string):
        self.logger.warning("%s:%s: %s" % (self.id,name,string))

    def l_debug(self, name, string, exc_info=False):
        self.logger.debug("%s:%s: %s" % (self.id,name,string), exc_info=exc_info)
