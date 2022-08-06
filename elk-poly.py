#!/usr/bin/env python
"""
This is a ELK NodeServer for Polyglot v3 written in Python3
by JimBoCA jimboca3@gmail.com
"""

from udi_interface import Interface,LOGGER
import sys
import time
from nodes import Controller

if __name__ == "__main__":
    if sys.version_info < (3, 9):
        LOGGER.error("ERROR: Python 3.9 or greater is required not {}.{}".format(sys.version_info[0],sys.version_info[1]))
        sys.exit(1)
    try:
        polyglot = Interface([Controller])
        polyglot.start()
        control = Controller(polyglot, 'controller', 'controller', 'ELK Controller')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
