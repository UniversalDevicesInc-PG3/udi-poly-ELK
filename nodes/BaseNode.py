"""
    My BaseNode to define common methods all the nodes need
"""

from sys import exc_info
from udi_interface import Node,LOGGER
from const import NODE_DEF_MAP,ELK_TO_INDEX
from node_funcs import myfloat

class BaseNode(Node):

    def __init__(self, controller, primary_address, address, name):
        self.__my_drivers = {}
        self.controller = controller
        super(BaseNode, self).__init__(controller.poly, primary_address, address, name)
        self.lpfx = f'{self.address}:{self.name}:'

    def set_drivers(self):
        LOGGER.debug(f'{self.lpfx} does not have set_drivers')

    def query(self):
        LOGGER.info(f'{self.lpfx}')
        self.set_drivers()
        self.reportDrivers()

    def shortPoll(self):
        pass

    def longPoll(self):
        pass

    """
    Create our own get/set driver methods because getDriver from Polyglot can be
    delayed, we sometimes need to know the value before the DB is updated
    and Polyglot gets the update back.
    if  default is None or restore is True then restore previous value from DB
    otherwise use the default.
    """
    def set_driver(self,mdrv,val,default=None,restore=True,force=False,report=True,prec=0,uom=None):
        LOGGER.debug(f'{self.lpfx} {mdrv},{val} default={default} force={force},report={report}')
        if val is None:
            # No val passed in, restore from DB 
            if default is None or restore is True:
                # Restore from DB for existing nodes
                try:
                    val = self.getDriver(mdrv)
                    LOGGER.info(f'{self.lpfx} Using getDriver({mdrv})={val}')
                except:
                    LOGGER.warning(f'{self.lpfx} getDriver({mdrv}) failed which can happen on new nodes, using {default}')
            else:
                # Use the passed in default since that comes from the elk object.
                val = default
        if prec == 0:
            if val in ELK_TO_INDEX:
                val = ELK_TO_INDEX[val]
            else:
                try:
                    val = int(val)
                except Exception as err:
                    LOGGER.error(f'{self.lpfx} Error converting {val} to integer, will use default={default} for {mdrv}',exc_info=True)
        else:
            try:
                val = myfloat(val,prec)
            except Exception as err:
                LOGGER.error(f'{self.lpfx} Error converting {val} to float, will use default={default} for {mdrv}',exc_info=True)
        try:
            if not mdrv in self.__my_drivers or val != self.__my_drivers[mdrv] or force:
                self.setDriver(mdrv,val,report=report,uom=uom)
                try:
                    info = ''
                    if self.id in NODE_DEF_MAP and mdrv in NODE_DEF_MAP[self.id]:
                        info += f"'{NODE_DEF_MAP[self.id][mdrv]['name']}' = "
                        if 'keys' in NODE_DEF_MAP[self.id][mdrv]:
                            info += f"'{NODE_DEF_MAP[self.id][mdrv]['keys'][val]}'" if val in NODE_DEF_MAP[self.id][mdrv]['keys'] else "'NOT IN NODE_DEF_MAP'"
                        else:
                            info += str(val)
                    self.__my_drivers[mdrv] = val
                    LOGGER.info(f'{self.lpfx} set_driver({mdrv},{val}) {info}')
                except Exception as err:
                    LOGGER.error(f'{self.lpfx} Internal error getting node driver info for {mdrv}',exc_info=True)
                    LOGGER.info(f'{self.lpfx} set_driver({mdrv},{val})')
            #else:
            #    LOGGER.debug(f'{self.lpfx} not necessary')
        except:
            LOGGER.error(f'{self.lpfx} set_driver({mdrv},{val}) failed',exc_info=True)
            return None
        return val


    def get_driver(self,mdrv):
        return self.__my_drivers[mdrv] if mdrv in self.__my_drivers else None
