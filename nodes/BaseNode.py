"""
    My BaseNode to define common methods all the nodes need
"""

from polyinterface import Node,LOGGER

class BaseNode(Node):

    def __init__(self, controller, primary_address, address, name):
        self.__my_drivers = {}
        super(BaseNode, self).__init__(controller, primary_address, address, name)
        self.lpfx = f'{self.address}:{self.name}:'


    def set_driver(self,mdrv,val,default=0,force=False,report=True):
        LOGGER.debug(f'{self.lpfx} {mdrv},{val} default={default} force={force},report={report}')
        if val is None:
            # Restore from DB for existing nodes
            try:
                val = self.getDriver(mdrv)
                LOGGER.info(f'{self.lpfx} {val}')
            except:
                LOGGER.warning(f'{self.lpfx} getDriver({mdrv}) failed which can happen on new nodes, using {default}')
        val = default if val is None else int(val)
        try:
            if not mdrv in self.__my_drivers or val != self.__my_drivers[mdrv] or force:
                LOGGER.debug(f'{self.lpfx} set_driver({mdrv},{val})')
                self.setDriver(mdrv,val,report=report)
                self.__my_drivers[mdrv] = val
            else:
                LOGGER.debug(f'{self.lpfx} not necessary')
        except:
            LOGGER.error(f'{self.lpfx} set_driver({mdrv},{val}) failed')
            return None
        return val


    def get_driver(self,mdrv):
        return self.__my_drivers[mdrv] if mdrv in self.__my_drivers else None
