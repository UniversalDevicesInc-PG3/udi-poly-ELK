#!/usr/bin/env python
"""
This is a ELK NodeServer for Polyglot v2 written in Python3
by JimBoCA jimboca3@gmail.com
"""

import polyinterface
import sys
import time
from nodes import Controller

import logging
LOGGER = polyinterface.LOGGER
# I want this logging
#logging.Formatter('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s')
# Default Format is:         '%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(module)s:%(funcName)s: %(message)s'
#                            '%(asctime)s %(threadName)-10s %(module)-13s %(levelname)-8s %(funcName)s: %(message)s [%(module)s:%(funcName)s]'
#polyinterface.set_log_format('%(asctime)s %(threadName)-10s %(name)-18s %(levelname)-8s %(message)s [%(module)s:%(funcName)s]')

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('ELK')
        polyglot.start()
        control = Controller(polyglot)
        control.updateNode()
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
