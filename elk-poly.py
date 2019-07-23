#!/usr/bin/env python
"""
This is a ELK NodeServer for Polyglot v2 written in Python3
by JimBoCA jimboca3@gmail.com
"""

import polyinterface
import sys
import time
from nodes import Controller

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('ELK')
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
