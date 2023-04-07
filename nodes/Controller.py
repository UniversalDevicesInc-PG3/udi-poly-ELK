from curses.ascii import SP
import sys
import time
import logging
import asyncio
import os
import markdown2
import re
import pkg_resources
from pyisy import constants as pyisy_constants
from datetime import datetime
from copy import deepcopy
from threading import Thread
from node_funcs import *
from nodes import AreaNode,OutputNode,LightNode,CounterNode,TaskNode
from udi_interface import Node,LOGGER,Custom,LOG_HANDLER,ISY
from const import SPEAK_WORDS,SPEAK_PHRASES,SYSTEM_TROUBLE_STATUS
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
from urllib.parse import parse_qsl,urlparse

# sys.path.insert(0, "../elkm1")
from elkm1_lib import Elk
from elkm1_lib.lights import Light
from elkm1_lib.const import (
    Max,
    ZoneType
)

persist_dir = "persist"
export_base = "isy_elk_export.xml"
export_file = persist_dir + "/" + export_base

class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            query = dict(parse_qsl(parsed_path.query))
            LOGGER.debug(f"REST: Got path={parsed_path} query={query}")
            if parsed_path.path == '/export':
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Disposition', 'attachment;'
                                f'filename={export_base}')
                self.end_headers()
                with open(export_file, 'rb') as file: 
                    self.wfile.write(file.read()) # Read the file and send the contents
                return True
            else:
                code = 500
                message = f"Unknown command {parsed_path.path}\r\n"
        except Exception as ex:
            LOGGER.error(f'do_GET: ',exc_info=True)
            code = 500
            message = f"Internal error {ex}\r\n"
        self.send_response(code)
        self.send_header('Content-Type',
                        'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))
        return False

    def log_message(self, fmt, *args):
        # Stop log messages going to stdout
        if args[1] == "200":
            LOGGER.debug(fmt % args)
        else:
            # TODO: Pass a receive error to the parent.
            LOGGER.error(fmt % args)
            LOGGER.error(f'code="{args[1]}"')

class Controller(Node):
    def __init__(self, poly, primary, address, name):
        self.ready = False
        # We track our drsiver values because we need the value before it's been pushed.
        super(Controller, self).__init__(poly, primary, address, name)
        self.hb = 0
        self.elk = None
        self.elk_st = None
        self.elk_thread = None
        self.config_st = None
        self.profile_done = False
        self.rest = None
        self.errors = 0
        self.n_queue = []
        self._area_nodes = {}
        self._output_nodes = {}
        self._keypad_nodes = {}
        self._counter_nodes = {}
        self._task_nodes = {}
        self.system_trouble_save = {}
        self.lights_to_trigger = {}
        self.logger = LOGGER
        self.lpfx = self.name + ":"
        self.poly.Notices.clear()
        self.tested = True
        self.isy = None
        self.handler_config_st = None
        self.handler_config_done_st = None
        self.sent_cstr = None
        # For the short/long poll threads, we run them in threads so the main
        # process is always available for controlling devices
        self.short_event = False
        self.long_event  = False
        self.Params      = Custom(poly, 'customparams')
        poly.subscribe(poly.START,             self.handler_start, address) 
        poly.subscribe(poly.POLL,              self.handler_poll)
        poly.subscribe(poly.CUSTOMPARAMS,      self.handler_params)
        poly.subscribe(poly.LOGLEVEL,          self.handler_log_level)
        poly.subscribe(poly.CONFIGDONE,        self.handler_config_done)
        poly.subscribe(poly.DISCOVER,          self.discover)
        poly.subscribe(poly.CONFIG,            self.handler_config)
        poly.subscribe(poly.ADDNODEDONE,       self.node_queue)
        poly.subscribe(poly.STOP,              self.handler_stop)
        #poly.subscribe(poly.ADDNODEDONE,       self.handler_add_node_done)
        poly.ready()
        poly.addNode(self, conn_status='ST')

    '''
    node_queue() and wait_for_node_event() create a simple way to wait
    for a node to be created.  The nodeAdd() API call is asynchronous and
    will return before the node is fully created. Using this, we can wait
    until it is fully created before we try to use it.
    '''
    def node_queue(self, data):
        self.n_queue.append(data['address'])
        # Start up ELK connection when controller node is all done being added.
        if (data['address'] == self.address):
            LOGGER.info(f'{self.lpfx} Checking for old ndoes to remove...')
            try:
                # Check for our old nodes to remove
                for i in range(1,256):
                    address = f'light_{i}'
                    node = self.poly.getNodeNameFromDb(address)
                    if node is not None:
                        LOGGER.warning(f"{self.lpfx} Deleting previously added node for Light address='{address}' {node}")
                        self.poly.delNode(address)
            except Exception as ex:
                LOGGER.error(f'{self.lpfx}',exc_info=True)
                self.inc_error(f"{self.lpfx} {ex}")
            LOGGER.info(f'{self.lpfx} Calling elk_start')
            self.elk_start()
            try:
                self.start_rest_server()
            except Exception as ex:
                LOGGER.error(f'{self.lpfx}',exc_info=True)
                self.inc_error(f"{self.lpfx} {ex}")


    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()

    def handler_config(self,data):
        #LOGGER.debug(f'{self.lpfx} {data}')        
        LOGGER.debug(f'{self.lpfx}')
        self.handler_config_st = True

    def handler_start(self):
        LOGGER.debug(f'{self.lpfx} enter')
        LOGGER.info(f"Started ELK NodeServer {self.poly.serverdata['version']}")
        self.heartbeat()

        configurationHelp = './configdoc.md';
        if os.path.isfile(configurationHelp):
            self.cfgdoc = markdown2.markdown_path(configurationHelp)
            self.poly.setCustomParamsDoc(self.cfgdoc)
        else:
            msg = f'config doc not found? {configurationHelp}'
            LOGGER.error(msg)
            self.inc_error(msg)
            
        LOGGER.debug(f'{self.lpfx} exit')

    def handler_config_done(self):
        LOGGER.debug(f'{self.lpfx} enter')
        self.poly.addLogLevel('DEBUG_MODULES',9,'Debug + Modules')
        self.handler_config_done_st = True
        LOGGER.debug(f'{self.lpfx} exit')

    def heartbeat(self):
        LOGGER.debug(f"{self.lpfx} hb={self.hb}")
        if self.hb == 0:
            self.reportCmd("DON", 2)
            self.hb = 1
        else:
            self.reportCmd("DOF", 2)
            self.hb = 0

    # Not necessary since callbacks handle this, but if status goes unknown or 
    # something else then this will reset it.
    def check_connection(self):
        if self.elk is None:
            st = 0
        elif self.elk.is_connected:
            st = 1
        else:
            st = 2
        LOGGER.debug(f"{self.lpfx} st={st} elk_st={self.elk_st}")
        self.set_st(st)

    def handler_poll(self, polltype):
        LOGGER.debug('start')
        try:
            if self.handler_config_done_st is None:
                LOGGER.warning('waiting for config handler to be called')
                return
            if not self.ready:
                LOGGER.warning('waiting for sync and node initialization to complete')
                return
            if 'longPoll' in polltype:
                self.longPoll()
            elif 'shortPoll' in polltype:
                self.shortPoll()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def shortPoll(self):
        LOGGER.debug('start')
        for an in self._area_nodes:
            self._area_nodes[an].shortPoll()
        if not self.tested:
            LOGGER.warning('Sending Test Zone Trouble')
                                   #28SS000000000100000000000000000000010A00
            # This tests Fire zone 17, which is likely not configured yet.
            self.elk.panel._ss_handler("000000000100000000000000000000010A")
            # This tests zone 1 which should be configured by now.
            #self.elk.panel._ss_handler("0000000000000000000000000000000001")
            self.tested = True
        LOGGER.debug('done')

    def longPoll(self):
        LOGGER.debug('start')
        self.heartbeat()
        self.check_connection()
        LOGGER.debug('done')

    # Start our REST server session
    def get_session(self):
        self.session = pgSession(self,self.name,LOGGER)

    # This is the callback for the panel
    def callback(self, element, changeset):
        try:
            LOGGER.info(f'{self.lpfx} element={element} type={type(element)} cs={changeset}')
            # Is it an exported light?
            if isinstance(element,Light):
                LOGGER.info(f'{self.lpfx} Got light: element={element} cs={changeset}')
                id = element.index + 1
                if id in self.lights_to_trigger:
                    address = self.lights_to_trigger[id]
                    if address is None:
                        msg = f"Trigger {id} is {self.lights_to_trigger[id]}"
                        LOGGER.error(f'{self.lpfx}: {msg}')
                        self.inc_error(f"{msg}")
                    else:
                        node = self.pyisy.nodes.get_by_id(address)
                        if node is None:
                            msg = f"No ISY device with address={address} got={node}"
                            LOGGER.error(f'{self.lpfx}: {msg}')
                            self.inc_error(f"{msg}")
                        else:
                            for key in changeset:
                                if key == 'status':
                                    val = int(changeset[key])
                                    res = False
                                    if val == 0:
                                        if node.status == 0:
                                            LOGGER.info(f'{self.lpfx} Node {node.address} already off status={node.status}')
                                        else:
                                            LOGGER.info(f'{self.lpfx} Turning node {node.address} off')
                                            res = node.turn_off()
                                    elif val == 1:
                                        if node.status == 0:
                                            LOGGER.info(f'{self.lpfx} Turning node {node.address} on')
                                            res = node.turn_on()
                                        else:
                                            LOGGER.info(f'{self.lpfx} Node {node.address} already on status={node.status}')
                                    else:
                                        if node.status == val:
                                            LOGGER.info(f'{self.lpfx} Node {node.address} already at {val}')
                                        else:
                                            LOGGER.info(f'{self.lpfx} Setting {node.address} to {val}')
                                            res = node.turn_on(val)
                                    LOGGER.info(f'res={res}')
                else:
                    LOGGER.error(f'{self.lpfx} Got unknown trigger light {id}: {self.lights_to_trigger}')
            else:
                # cs={'elkm1_version': '5.3.10', 'xep_version': '2.0.44'}
                #cs={'user_code_length': 4, 'temperature_units': 'F'}
                for key in changeset:
                    if key == 'elkm1_version' or key == 'xep_version' or key == 'user_code_length' or key == 'temperature_units':
                        LOGGER.info(f"{key}={changeset[key]}")
                    elif key == 'real_time_clock':
                        LOGGER.info(f"{key}={changeset[key]}")
                        # TODO: Toggle something to show we are receiving this?
                    elif key == 'remote_programming_status':
                        # Controller:callback: ELK Controller: cs={'remote_programming_status': <ElkRPStatus.CONNECTED: 1>}
                        if hasattr(changeset[key],'value'):
                            self.set_remote_programming_status(changeset[key].value)
                        else:
                            msg = f"Callback not sent enum, got {key}={changeset[key]}"
                            LOGGER.error(f'{self.lpfx}: {msg}',exc_info=True)
                            self.inc_error(f"{self.lpfx} {ex}")
                    elif key == 'system_trouble_status':
                        self.set_system_trouble_status(changeset[key])
                    else:
                        LOGGER.warning(f'{self.lpfx} Unhandled  callback: cs={changeset}')
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    # This is the callback for when a light changes
    # push the change to the elk if necessary
    def node_changed(self,node):
        LOGGER.info('%s node=%s' % (self.lpfx, node))
        # Set all the defaults
        # node.status will be 0-255
        LOGGER.info('%s ISY node %s changed to %s' % (self.lpfx, node['address'], node['status']));
        if node['status'] == pyisy_constants.ISY_VALUE_UNKNOWN:
            bri = 0
        else:
            bri = int(node['status'])
        # Get the node from the list
        light = None
        for n in self.lights_to_trigger:
            if self.lights_to_trigger[n] is not None and self.lights_to_trigger[n] == node['address']:
                if self.elk.lights[n-1].status == bri:
                    LOGGER.debug('%s Elk light already at %s' % (self.lpfx, bri))
                else:
                    LOGGER.debug('%s Setting Elk light to %s' % (self.lpfx, bri))
                    self.elk.lights[n-1].level(bri)

    def handler_log_level(self,level):
        LOGGER.info(f'enter: level={level}')
        if level['level'] < 10:
            LOGGER.info("Setting basic config to DEBUG...")
            LOG_HANDLER.set_basic_config(True,logging.DEBUG)
        else:
            LOGGER.info("Setting basic config to WARNING...")
            LOG_HANDLER.set_basic_config(True,logging.WARNING)
#        logging.getLogger("elkm1_lib.elk").setLevel(slevel)
#        logging.getLogger("elkm1_lib.proto").setLevel(slevel)
#        logging.getLogger("elkm1_lib").setLevel(slevel)
        LOGGER.info(f'exit: level={level}')

    def init_isy(self):
        try:
            if self.isy is None:
                self.pyisy = None
                pyisy_version = pkg_resources.get_distribution("pyisy").version
                LOGGER.warning(f"pyisy_version={pyisy_version}")
                self.isy = ISY(self.poly)
                while not self.isy.valid:
                    LOGGER.info(f"{self.lpfx} Waiting for isy.valid... {self.isy.valid}")
                    time.sleep(2)
            if self.isy is not None and self.pyisy is None:
                self.pyisy = self.isy.pyisy()
            LOGGER.info(f"{self.lpfx} got isy={self.isy} pyisy={self.pyisy} pyisy.connected={self.pyisy.connected}")
            if self.pyisy.connected:
                return True
            else:
                msg = 'Failed to connect to ISY see log file'
                LOGGER.error(msg)
                self.inc_error(msg)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")
        return False

    def is_isy_node(self,value):
        ret = None
        # Need the isy/pyisy object defined to check
        if self.isy is None and not self.init_isy():
            return ret
        try:
            for (_, child) in self.pyisy.nodes:
                ctype = type(child).__name__
                #LOGGER.debug(f'{self.lpfx} ctype={ctype} check={child} name={child.name}')
                if ctype != 'Folder' and (child.name == value or child.address == value):
                    ret = child
                    LOGGER.debug(f'{self.lpfx} ctype={ctype} got={ret}')
            LOGGER.info(f'{self.lpfx} for={value} got={ret}')
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")
        return ret

    def set_st(self, st, force=False):
        LOGGER.debug(f"{self.lpfx} elk_st={self.elk_st} st={st}")
        # Did connection status change?
        if self.elk_st != st:
            self.elk_st = st
            self.setDriver("GV1", st, uom=25,force=force)

    def query(self):
        LOGGER.info(f'{self.lpfx}')
        if self.elk is None:
            LOGGER.error(f'{self.lpfx} query called before node ready, ignoring...')
        try:
            self.check_params()
            self.set_drivers(force=True)
            self.reportDrivers()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def set_drivers(self,force=False):
        self.set_error(force=force)
        self.set_remote_programming_status(force=force)
        self.set_system_trouble_status(force=force)

    def set_error(self,val=None,force=False):
        if val is None:
            val = 0
        self.errors = val
        self.setDriver('ERR',self.errors,force=force)

    def inc_error(self,err_str,val=None):
        if val is None:
            val = 1
        now = datetime.now()
        self.errors += val
        self.setDriver('ERR',self.errors)
        if err_str is not None:
            self.err_notice('ns_error',err_str)

    def err_notice(self,name,err_str):
            self.poly.Notices[name] = f"ERROR: {datetime.now().strftime('%m/%d/%Y %H:%M:%S')} See log for: {err_str}"

    def dec_error(self,val=None):
        if val is None:
            val = 1
        self.errors -= val
        self.setDriver('ERR',self.errors)

    def set_remote_programming_status(self,val=None,force=False):
        if val is None:
            val = self.elk.panel.remote_programming_status
        self.setDriver('GV2',val,force=force)

    # This is sent a comma seperated list of all current system troubles
    def set_system_trouble_status(self,val=None,force=False):
        zp = re.compile(' zone ')
        LOGGER.debug(f'{self.lpfx} val={val} force={force}')
        if val is None:
            val = self.elk.panel.system_trouble_status
            LOGGER.debug(f'{self.lpfx} val={val}')
        # Set all to off
        for status in SYSTEM_TROUBLE_STATUS:
            SYSTEM_TROUBLE_STATUS[status]['value'] = 0
        # If we have any, then set them.
        status_by_zone = dict()
        if val != "":
            LOGGER.warning(f'{self.lpfx} Setting System Trouble Status for: {val}')
            for status in val.split(','):
                status = status.strip()
                m = zp.search(status)
                if m is None:
                    if status in SYSTEM_TROUBLE_STATUS:
                        LOGGER.warning(f'{self.lpfx} Setting System Trouble Status for: {status}')
                        SYSTEM_TROUBLE_STATUS[status]['value'] = 1
                    else:
                        msg = f"{self.lpfx} Unknown system trouble status '{status}' in '{val}' m={m}"
                        LOGGER.error(msg)
                        self.inc_error(msg)
                else:
                    zstatus = status[0:m.start()]
                    zone = int(status[m.end():])
                    if not zone in status_by_zone:
                        status_by_zone[zone] = list()
                    status_by_zone[zone].append(zstatus)
        # Set all our trouble status's
        for status in SYSTEM_TROUBLE_STATUS:
            if SYSTEM_TROUBLE_STATUS[status]['value'] == 1:
                LOGGER.warning(f'{self.lpfx} Setting System Trouble Status for: {status}=True')
            self.setDriver(SYSTEM_TROUBLE_STATUS[status]['driver'],SYSTEM_TROUBLE_STATUS[status]['value'],force=force)
        # Set/clear trouble status on all zones
        found = dict()
        for zn in range(1,Max.ZONES.value+1):
            found[zn] = False
            for an in self._area_nodes:
                znode = self._area_nodes[an].get_zone_node(zn)
                if znode is not None:
                    found[zn] = True
                    if zn in status_by_zone:
                        znode.set_system_trouble_status(status_by_zone[zn])
                    else:
                        znode.clear_system_trouble_status()
        for zn in status_by_zone:
            if not found[zn]:
                msg = f'{self.lpfx} Got zone system trouble "{status_by_zone[zn]}" for unconfigured zone {zn} this can happen on startup, will try to clear it when zone comes online'
                LOGGER.error(msg)
                self.inc_error(None)
                # Add our message, so we can clear it if the zone is seen later.
                self.err_notice(f'stbz_{zn}',msg)
                self.system_trouble_save[zn] = status_by_zone[zn]

    def get_system_trouble_status_for_zone(self,zn):
        if zn in self.system_trouble_save:
            # Delete the message because the node now exists
            self.poly.Notices.delete(f'stbz_{zn}')
            ret = self.system_trouble_save[zn]
            del self.system_trouble_save[zn]
            return ret
        return list()

    def query_all(self):
        LOGGER.info(f'{self.lpfx}')
        try:
            for node in self.poly.getNodes():
                self.poly.getNode(node).query()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def connected(self):
        LOGGER.info(f"{self.lpfx} Connected!!!")
        self.set_st(1)

    def disconnected(self):
        LOGGER.info(f"{self.lpfx} Disconnected!!!")
        self.set_st(2)

    def login(self, succeeded):
        if succeeded:
            LOGGER.info("Login succeeded")
            self.set_st(3)
        else:
            msg = f"{self.lpfx} Login Failed!!!"
            LOGGER.error(msg)
            self.set_st(4)
            self.inc_error(msg)

    def add_node(self,address,node):
        # See if we need to check for node name changes where ELK is the source
        cname = self.poly.getNodeNameFromDb(address)
        if cname is not None:
            LOGGER.debug(f"node {address} Requested: '{node.name}' Current: '{cname}'")
            # Check that the name matches
            if node.name != cname:
                if self.Params['change_node_names'] == 'true':
                    LOGGER.warning(f"Existing node name '{cname}' for {address} does not match requested name '{node.name}', changing to match")
                    self.poly.renameNode(address,node.name)
                else:
                    LOGGER.warning(f"Existing node name '{cname}' for {address} does not match requested name '{node.name}', NOT changing to match, set change_node_names=true to enable")
                    # Change it to existing name to avoid addNode error
                    node.name = cname
        LOGGER.debug(f"Adding: {node.name}")
        self.poly.addNode(node)
        self.wait_for_node_done()
        gnode = self.poly.getNode(address)
        if gnode is None:
            msg = f'Failed to add node address {address}'
            LOGGER.error(msg)
            self.inc_error(msg)
        return node

    def sync_complete(self):
        LOGGER.info(f"{self.lpfx} Sync of panel is complete...")
        if (True):  # Used when debugging
            # Ferce this again to make sure because when node starts up the first connected set_st may get overridden :(
            self.set_st(5)
            # TODO: Add driver for sync complete status, or put in ST?
            LOGGER.info(f"{self.lpfx} adding areas...")
            for an in range(Max.AREAS.value):
                if an in self._area_nodes:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Area {an+1} because it already defined."
                    )
                elif is_in_list(an+1, self.use_areas_list) is False:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Area {an+1} because it is not in areas range {self.use_areas} in configuration"
                    )
                else:
                    LOGGER.info(f"{self.lpfx} Adding Area {an}")
                    address = f'area_{an + 1}'
                    node = self.add_node(address,AreaNode(self, address, self.elk.areas[an]))
                    if node is not None:
                        self._area_nodes[an] = node
            LOGGER.info("adding areas done, adding outputs...")
            # elkm1_lib uses zone numbers starting at zero.
            for n in range(Max.OUTPUTS.value):
                if n in self._output_nodes:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Output {n+1} because it already defined."
                    )
                elif is_in_list(n+1, self.use_outputs_list) is False:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Output {n+1} because it is not in outputs range {self.use_outputs} in configuration"
                    )
                else:
                    LOGGER.info(f"{self.lpfx} Adding Output {n}")
                    address = f'output_{n + 1}'
                    node = self.add_node(address,OutputNode(self, address, self.elk.outputs[n]))
                    if node is not None:
                        self._output_nodes[n] = node
            LOGGER.info("adding outputs done")
            LOGGER.info("adding lights")
            try:
                # elkm1_lib uses zone numbers starting at zero.
                need_pyisy = False
                for n in range(Max.LIGHTS.value):
                    LOGGER.debug(f"Check light: {self.elk.lights[n]} is_default_name={self.elk.lights[n].is_default_name()}")
                    if self.elk.lights[n].is_default_name() or self.elk.lights[n].name == '':
                        LOGGER.info(
                            f"{self.lpfx} Skipping Light {n+1} because it set to default name or null '{self.elk.lights[n].name}'"
                        )
                        continue
                    if self.light_method == "ELKNAME":
                        node = self.is_isy_node(self.elk.lights[n].name)
                        if node is None:
                            self.lights_to_trigger[n+1] = None
                            LOGGER.warning(f"{self.lpfx} No node address or name match for '{self.elk.lights[n].name}'")
                        else:
                            need_pyisy = True
                            LOGGER.info(
                                f"{self.lpfx} Adding ISY Sync Light {n+1} {self.elk.lights[n].name} {node.address} because it's an existing light in IoP that I will trigger"
                            )
                            self.lights_to_trigger[n+1] = node.address
                            # Set ELK Light status to current ISY node status
                            self.node_changed({'address': node.address, 'status': node.status})
                            # Add ELK callback to myself to handle an exported light.
                            self.elk.lights[n].add_callback(self.callback)
                            # Add PyISY callback for when the node changes
                            node.status_events.subscribe(self.node_changed)
                if self.isy is not None:
                    if need_pyisy:
                        LOGGER.info(f'{self.lpfx} Enabling pyisy auto_update...')
                        self.pyisy.auto_update = True
                    else:
                        LOGGER.info(f'{self.lpfx} No ELK<->ISY Nodes, shuting down PyISY')
            except Exception as ex:
                LOGGER.error(f'{self.lpfx}',exc_info=True)
                self.inc_error(f"{self.lpfx} {ex}")
            LOGGER.info("adding lights done")
            for n in range(Max.COUNTERS.value):
                LOGGER.debug(f"Check counter: {self.elk.counters[n]} is_default_name={self.elk.counters[n].is_default_name()}")
                if n in self._counter_nodes:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Counter {n+1} because it already defined."
                    )
                elif self.elk.counters[n].is_default_name():
                    LOGGER.info(
                        f"{self.lpfx} Skipping Counter {n+1} because it set to default name"
                    )
                else:
                    LOGGER.info(f"{self.lpfx} Adding Counter {n}")
                    address = f'counter_{n + 1}'
                    node = self.add_node(address,CounterNode(self, address, self.elk.counters[n]))
                    if node is not None:
                        self._output_nodes[n] = node
            LOGGER.info("adding counters done")
            for n in range(Max.TASKS.value):
                LOGGER.debug(f"Check task: {self.elk.tasks[n]} is_default_name={self.elk.tasks[n].is_default_name()}")
                if n in self._task_nodes:
                    LOGGER.info(
                        f"{self.lpfx} Skipping Task {n+1} because it already defined."
                    )
                elif self.elk.tasks[n].is_default_name():
                    LOGGER.info(
                        f"{self.lpfx} Skipping Task {n+1} because it set to default name"
                    )
                else:
                    LOGGER.info(f"{self.lpfx} Adding Task {n}")
                    address = f'task_{n + 1}'
                    node = self.add_node(address,TaskNode(self, address, self.elk.tasks[n]))
                    if node is not None:
                        self._output_nodes[n] = node
            LOGGER.info("adding tasks done")
            # Only update profile on restart
            if not self.profile_done:
                self.write_profile()
                self.profile_done = True
            LOGGER.warning(f'{self.lpfx} All nodes added, ready to go...')
        self.ready = True
        self.update_config_docs()

    def update_config_docs(self):
        # '<style> table { cellpadding: 10px } </style>'
        try:
            if self.init_isy():
                hstr = 'https' if self.isy._isy_https else 'http'
                self.config_info = [
                '<h1>ELK To ISY Light Table</h1>',
                '<p>This table is refreshed after node server syncs with the elk, so it may be out of date for a few seconds</p>',
                '<ul><li>If light_method is ELKNAME'
                '<ul><li>If you want the ELK Lights to Control ISY Lights then add a Light in ElkRP2 whose name matches an existing ISY node name or address',
                f'To see a list of all your node names and address click <a href="{hstr}://{self.isy._isy_ip}:{self.isy._isy_port}/rest/nodes" target="_blank">ISY Nodes</a></li></ul>',
                '<li>If light_method is ELKID',
                f'<ul><li>All ISY nodes will be checked for ELKID=n in their notes to create an export file which can be dowloaded with the <a href="{self.rest_url}/export">export</a> link then imported into ElkRP2',
                '</ul></ul><table border=1>',
                '<tr><th colspan=2><center>ELK<th colspan=3><center>ISY</tr>',
                '<tr><th><center>Id<th><center>Name<th><center>Address<th><center>Name<th><center>Type</tr>']
                for n in self.lights_to_trigger:
                    self.config_info.append(f'<tr><td>&nbsp;{n}&nbsp;<td>{self.elk.lights[n-1].name}')
                    if self.lights_to_trigger[n] is None:
                        self.config_info.append('<td>&nbsp;None&nbsp;<td>&nbsp;None&nbsp;<td>&nbsp;&nbsp;')
                    else:
                        node = self.pyisy.nodes[self.lights_to_trigger[n]]
                        self.config_info.append(f'<td>&nbsp;{node.address}&nbsp;<td>&nbsp;{node.name}&nbsp;<td>&nbsp;{type(node).__name__}&nbsp;')
                    self.config_info.append('</tr>')
                self.config_info.append('</table>')
                #
                # Set the Custom Config Doc when it changes
                #
                s = "\n"
                cstr = s.join(self.config_info)
                if self.sent_cstr != cstr:
                    self.poly.setCustomParamsDoc(self.cfgdoc+cstr)
                    self.sent_cstr = cstr
            else:
                msg = f"ISY {self.isy} is not initialized, see log"
                self.inc_error(msg)
                LOGGER.error(msg)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            msg = f"update config docs error, see log file {ex}"
            self.inc_error(msg)

    def timeout(self, msg_code):
        msg = f"{self.lpfx} Timeout sending message {msg_code}!!!"
        LOGGER.error(msg)
        self.inc_error(msg)
        self.set_st(6)
        if msg_code == 'AS':
            msg = f"{self.lpfx} The above Arm System timeout is usually caused by incorrect user code, please check the Polyglot Configuration page for this nodeserver and restart the nodeserver."
            LOGGER.error(msg)
            self.inc_error(msg)

    def unknown(self, msg_code, data):
        # We don't care about email messages, or alarm reports
        if msg_code in ['EM','AR']:
            return
        if msg_code == 'KF' and data == '0000000000000':
            LOGGER.warning(f"{self.lpfx} Received unknown message which is known to come from M1 Touch app: {msg_code}:{data}")
            return
        self.set_st(7)
        msg = f"{self.lpfx} Unknown message {msg_code}: {data}"
        LOGGER.error(msg)
        self.inc_error(msg)

    def elk_start(self):
        LOGGER.debug(f'{self.lpfx} enter: config_st={self.config_st}')
        if not self.config_st:
            msg = "Can't start elk until configuration is completed"
            LOGGER.error(msg)
            self.poly.Notices['elk_start'] = msg
            # Build temporary profile
            self.write_profile()
            return False
        #
        # Build the config and start it in a thread
        #
        self.elk_config = {
            # TODO: Support secure which would use elks: and add 'keypadid': 'xxx', 'password': 'xxx'
            "url": "elk://"
            + self.host,
        }
        LOGGER.info(
            f"{self.lpfx} Starting Elk Thread, will process data when sync completes..."
        )
        self.elk_thread = Thread(name="ELK-" + str(os.getpid()), target=self._elk_start)
        self.elk_thread.daemon = True
        self.elk_thread.start()
        LOGGER.debug(f'{self.lpfx} exit:')

    def _elk_start(self):
        # We have to create a loop since we are in a thread
        LOGGER.info(f"{self.lpfx} started")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.elk = Elk(self.elk_config, loop=loop)
        LOGGER.debug(f'elk={self.elk} initialized, starting...')
        self.elk.panel.add_callback(self.callback)
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("login", self.login)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.add_handler("timeout", self.timeout)
        self.elk.add_handler("unknown", self.unknown)
        #self.elk.add_handler('KC', self.kc_handler)
        LOGGER.info(f"{self.lpfx} Connecting to Elk...")
        self.set_drivers(force=True)
        self.elk.connect()
        self.elk.run()

    #def kc_handler(keypad, key):
    #  LOGGER.warning(f"{keypad} {key}")

    async def elk_start_run(self):
        self.elk.run()
        return elk

    #
    # This processes ISY nodes and looks for ELKID=<n> to create
    # the lights_exported hash.
    #
    def export(self):
        LOGGER.info(f"{self.lpfx} start")
        if self.light_method == 'ELKID':
            # Need the isy/pyisy object defined to check
            if self.isy is None and not self.init_isy():
                return False
            try:
                LOGGER.warning("Export Started")
                self.lights_exported = {}
                if not os.path.exists(persist_dir):
                    os.makedirs(persist_dir)
                fh = open(export_file, "w")
                fh.write("<nodes>\n")
                for (_, node) in self.pyisy.nodes:
                    if node.description is not None:
                        LOGGER.debug(f"{self.lpfx} check {node.name} description={node.description}")
                        n = re.sub(r'ELKID=([0-9]+)',r'\1',node.description,flags=re.IGNORECASE).strip()
                        LOGGER.debug(f"{self.lpfx} got {n}")
                        self.lights_exported[int(n)] = node.address
                        fh.write("  <node>\n")
                        fh.write(f"    <address>{node.address}</address>\n")
                        fh.write(f"    <name>{node.name}</name>\n")
                        fh.write(f"    <type>{node.type}</type>\n")
                        fh.write(f"    <ELK-ID>{self.int_to_id(n)}</ELK-ID>\n")
                        fh.write("  </node>\n")
                fh.write("</nodes>\n")
                fh.close()
                LOGGER.warning("Export Completed")
                self.export_process()
            except Exception as ex:
                LOGGER.error(f'{self.lpfx}',exc_info=True)
                msg = f"export error, see log file {ex}"
                self.inc_error(msg)
        LOGGER.info(f"{self.lpfx} done")
    
    def int_to_id(self,n):
        n = int(n)
        return '%s%02d' % (chr(65+(int(n / 16))), int(( n / 16 - int( n / 16 )) * 16) )

    # 
    # This processes the lights_exported hash to setup proper callbacks on
    # ELK and ISY sides.
    #
    def export_process(self):
        LOGGER.info(f"{self.lpfx} Processing exports")
        # Need the isy/pyisy object defined to check
        if self.isy is None and not self.init_isy():
            return False
        for n in self.lights_exported:
            if self.pyisy.nodes.get_by_id(self.lights_exported[n]) is None:
                msg = f"ELKID={n} address={self.lights_exported[n]} not found in ISY?"
                LOGGER.error(f'{self.lpfx} {msg}')
                self.inc_error(msg)
                LOGGER.error(self.pyisy.nodes[self.lights_exported[n]])
            else:
                LOGGER.info(f"{self.lpfx} Adding ELKID={n} address={self.lights_exported[n]}")
                node = self.pyisy.nodes[self.lights_exported[n]]
                self.lights_to_trigger[n] = node.address
                # Set ELK Light status to current ISY node status
                self.node_changed({'address': node.address, 'status': node.status})
                # Add callback to myself to handle an exported light.
                self.elk.lights[int(n)-1].add_callback(self.callback)
                # Add PyISY callback for when the node changes
                node.status_events.subscribe(self.node_changed)
        self.update_config_docs()
        LOGGER.info(f"{self.lpfx} Processing exports done")

    def discover(self):
        # TODO: What to do here, kill and restart the thread?
        LOGGER.error(f"{self.lpfx} discover currently does nothing")
        pass

    def elkm1_run(self):
        self.elk.run()

    def delete(self):
        LOGGER.info(
            f"{self.lpfx} Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo."
        )
        self.rest_stop()
        self.elk_stop()

    def handler_stop(self):
        LOGGER.debug('NodeServer stopping.')
        self.rest_stop()
        self.elk_stop()
        LOGGER.debug('NodeServer stopped.')
        self.poly.stop()

    def rest_stop(self):
        if self.rest is not None:
            LOGGER.info("REST:stop: Shutdoing down and closing")
            self.rest.shutdown()
            self.rest.server_close()

    def start_rest_server(self):
        msg = False
        if self.rest is None:
            try:
                ni = self.poly.getNetworkInterface()
                LOGGER.info(f"Starting REST Server on {ni['addr']}...")
                self.rest = HTTPServer((ni['addr'], 0), MyServer)
                self.rest_url = 'http://{0}:{1}'.format(self.rest.server_address[0],self.rest.server_address[1])
                LOGGER.info(f"{self.lpfx} REST Server running on: {self.rest_url}")
                # Just keep serving until we are killed
                self.rest_thread  = Thread(target=self.rest.serve_forever)
                # Need this so the thread will die when the main process dies
                self.rest_thread.daemon = True
                self.rest_thread.start()
            except Exception as ex:
                LOGGER.error(f'{self.lpfx}',exc_info=True)
                msg = f"REST Server not started check log for error {ex}"
        else:
            msg = f"REST Sever already running ({self.rest})"
        if msg is not False:
            LOGGER.error(msg)
            self.inc_error(msg)
                
    def elk_stop(self):
        LOGGER.info(f'elk={self.elk} thread={self.elk_thread}')
        if self.elk is not None:
            LOGGER.warning('Stopping ELK monitor...')
            self.elk.disconnect()
            #self.set_st(2)
        if self.elk_thread is not None:
            LOGGER.warning('Stopping ELK thread...')
            # TODO: Wait for actual termination (if needed)
            self.elk_thread.join()
            if self.elk_thread.is_alive():
                msg = 'ELK thread did not exit?'
                LOGGER.error(msg)
                self.inc_error(msg)
            else:
                LOGGER.error('ELK thread done.')
        return True

    def elk_restart(self):
        LOGGER.warning(f"{self.lpfx} Restarting ELK Connection")
        if (self.elk_stop):
            self.elk_start()
        LOGGER.info(f"{self.lpfx} exit")

    def wm(self,key,msg):
        LOGGER.warning(msg)
        self.poly.Notices[key] = msg

    def handler_typed_params(self,params):
        LOGGER.debug(f'Loading typed params now {params}')
        return

    def handler_params(self,params):
        LOGGER.debug(f'enter: Loading typed data now {params}')
        self.Params.load(params)
        self.poly.Notices.clear()
        # Old unused params
        if "check_elk_lights" in params:
            self.Params.delete('check_elk_lights')
            return
        if "check_isy_elkid" in params:
            self.Params.delete('check_isy_elkid')
            return
        #
        # Make sure params exist
        #
        defaults = {
            "temperature_unit": "F",
            "host": "",
            "user_code": "",
            "areas": "1",
            "outputs": "",
            "change_node_names": "false",
            "light_method": "NONE",
        }
        for param in defaults:
            if not param in params:
                self.Params[param] = defaults[param]
                return
        try:
            self.check_params()
            # Example of exported lights
            self.export()
            if self.handler_config_done_st is True:
                self.elk_restart()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            msg = f"Check params error, see log file {ex}"
            self.inc_error(msg)
                
    def check_params(self):
        """
        Check all user params are available and valid
        """
        # Assume it's good unless it's not
        config_st = True
        #
        # Change Node Names
        #
        #
        # Temperature Units
        #
        if self.Params['light_method'] == "NONE" or self.Params['light_method'] == "ELKID" or self.Params['light_method'] == "ELKNAME":
            self.light_method = self.Params['light_method']
        else:
            self.wm('light_method',f"Light Method must be ELKID or ELKNAME not '{self.Params['light_method']}'")
            config_st = False
        #
        # Temperature Units
        #
        if self.Params['temperature_unit'] == "F":
            self.temperature_uom = 17
        elif self.Params['temperature_unit'] == "C":
            self.temperature_uom = 4
        else:
            self.wm('temperature_unit',f"Temperature Unit must be F or C not '{self.Params['temperature_unit']}'")
            config_st = False
        #
        # Host
        #
        if len(self.Params['host']) is None or len(self.Params['host']) == 0:
            self.wm('host',f"host not defined '{self.Params['host']}'")
            config_st = False
        else:
            LOGGER.debug(f"{self.lpfx} host={self.Params['host']}")
            self.host = self.Params['host']
        #
        # Code
        #
        if self.Params['user_code'] is None or len(self.Params['user_code']) == 0:
            self.wm('user_code',f"user_code not defined '{self.Params['user_code']}'")
            config_st = False
        else:
            try:
                self.user_code = int(self.Params['user_code'])
            except:
                config_st = False
                self.wm('user_code',f"user_code '{self.Params['user_code']} is not an integer, please fix, save and restart this nodeserver")
        #
        # Areas
        #
        self.use_areas = ""
        self.use_areas_list = ()
        if self.Params['areas'] is None or len(self.Params['areas']) == 0:
            self.wm('areas',f"areas not defined '{self.Params['areas']}' so none will be added")
        else:
            self.use_areas = self.Params['areas']
            try:
                self.use_areas_list = parse_range(self.use_areas)
            except:
                self.wm('areas',f"Failed to parse areas range '{self.use_areas}'  will not add any: {sys.exc_info()[1]}")
                config_st = False
        #
        # Outputs
        #
        self.use_outputs = ""
        self.use_outputs_list = ()
        if self.Params['outputs'] is None or len(self.Params['outputs']) == 0:
            self.wm('outputs',"outputs not defined, so none will be added")
        else:
            self.use_outputs = self.Params['outputs']
            try:
                self.use_outputs_list = parse_range(self.use_outputs)
            except:
                self.wm('outputs',f"Failed to parse outputs range '{self.use_areas}'  will not add any: {sys.exc_info()[1]}")
                config_st = False
        self.config_st = config_st
        LOGGER.debug(f'exit: config_st={config_st}')

    def write_profile(self):
        LOGGER.info(f"{self.lpfx} Starting...")
        #
        # Start the nls with the template data.
        #
        en_us_txt = "profile/nls/en_us.txt"
        make_file_dir(en_us_txt)
        LOGGER.info(f"{self.lpfx} Writing {en_us_txt}")
        nls_tmpl = open("template/en_us.txt", "r")
        nls      = open(en_us_txt,  "w")
        for line in nls_tmpl:
            nls.write(line)
        nls_tmpl.close()
        #
        # SPEAK_WORDS
        #
        nls.write("\n# SPEAK WORDS\n")
        swords = list()
        for idx,word in SPEAK_WORDS.items():
            swords.append(idx)
            nls.write(f"SPW-{idx} = {word}\n")
        #
        # SPEAK_PHRASES
        #
        nls.write("\n# SPEAK PHRASES\n")
        sphrases = list()
        if self.config_st:
            for zn in range(Max.ZONES.value):
                if self.elk.zones[zn].definition != ZoneType.DISABLED:
                    SPEAK_PHRASES[zn+1] = self.elk.zones[zn].name
        else:
            LOGGER.warning(f"{self.lpfx} Can't generate full profile until configuration is complete")
        for idx,word in SPEAK_PHRASES.items():
            sphrases.append(idx)
            nls.write(f"SPP-{idx} = {word}\n")

        #
        # Then write our custom NLS lines
        nls.write("\nUSER-0 = Unknown\n")
        if self.config_st:
            for n in range(Max.USERS.value - 3):
                LOGGER.debug(f"{self.lpfx} user={self.elk.users[n]}")
                nls.write(f"USER-{n+1} = {self.elk.users[n].name}\n")
        # Version 4.4.2 and later, user code 201 = Program Code, 202 = ELK RP Code, 203 = Quick Arm, no code.
        nls.write(f"USER-{Max.USERS.value-2} = Program Code\n")
        nls.write(f"USER-{Max.USERS.value-1} = ELK RP Code\n")
        nls.write(f"USER-{Max.USERS.value} = Quick Arm, no code\n")
        #
        # Now the keypad names
        nls.write("\n\nKEYPAD-0 = Unknown\n")
        if self.config_st:
            for n in range(Max.KEYPADS.value):
                LOGGER.debug(f"{self.lpfx} keypad={self.elk.keypads[n]}")
                nls.write(f"KEYPAD-{n+1} = {self.elk.keypads[n].name}\n")
        #
        # Now the zones names
        nls.write("\n\nZONE-0 = Unknown\n")
        if self.config_st:
            for n in range(Max.ZONES.value):
                LOGGER.debug(f"{self.lpfx} zone={self.elk.zones[n]}")
                nls.write(f"ZONE-{n+1} = {self.elk.zones[n].name}\n")
        nls.close()
        #
        # Start the custom editors with the template data.
        #
        word = reduce_subset(swords)
        phrase = reduce_subset(sphrases)
        template_f = "template/editors.xml"
        out_f = "profile/editor/custom.xml"
        LOGGER.debug("Reading {}".format(template_f))
        with open (template_f, "r") as myfile:
            data=myfile.read()
            myfile.close()
        # Write the editors file with our info
        LOGGER.debug("Writing {}".format(out_f))
        with open (out_f, "w") as out_h:
            out_h.write(data.format(word["full_string"],word["subset_string"],phrase["full_string"],phrase["subset_string"]))
            out_h.close()
        #
        # Update the ISY
        self.update_profile()
        LOGGER.info(f"{self.lpfx} Done...")

    def get_driver(self, mdrv, default=None):
        # Restore from DB for existing nodes
        try:
            val = self.getDriver(mdrv)
            LOGGER.info(f"{self.lpfx} {mdrv}={val}")
            if val is None:
                LOGGER.info(
                    f"{self.lpfx} getDriver({mdrv}) returned None which can happen on new nodes, using {default}"
                )
                val = default
        except:
            LOGGER.warning(
                f"{self.lpfx} getDriver({mdrv}) failed which can happen on new nodes, using {default}"
            )
            val = default
        return val

    def update_profile(self):
        LOGGER.info(f"{self.lpfx}")
        return self.poly.updateProfile()

    def cmd_query_all(self, command):
        try:
            LOGGER.info(f"{self.lpfx}")
            return self.query_all()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_update_profile(self, command):
        try:
            LOGGER.info(f"{self.lpfx}")
            return self.write_profile()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_discover(self, command):
        try:
            LOGGER.info(f"{self.lpfx}")
            return self.discover()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_export(self, command):
        try:
            LOGGER.info(f"{self.lpfx}")
            if self.light_method != "ELKID":
                msg = f'light_method is {self.light_method}, export only available for ELKID method'
                LOGGER.error(f'{self.lpfx} {msg}')
                self.inc_error(msg)
                return False
            return self.export()
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_speak_word(self, command):
        try:
            val = int(command.get('value'))
            if self.elk is None:
                LOGGER.warning(f"{self.lpfx} No ELK defined")
                return False
            LOGGER.info(f"{self.lpfx} {val}")
            # Get the word from the sorted list
            LOGGER.info(f"{self.lpfx} word={SPEAK_WORDS[val]}")
            return self.elk.panel.speak_word(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")

    def cmd_speak_phrase(self, command):
        try:
            val = int(command.get('value'))
            if self.elk is None:
                LOGGER.warning(f"{self.lpfx} No ELK defined")
                return False
            LOGGER.info(f"{self.lpfx} {val}")
            # Get the word from the sorted list
            LOGGER.info(f"{self.lpfx} phrase={SPEAK_PHRASES[val]}")
            return self.elk.panel.speak_phrase(val)
        except Exception as ex:
            LOGGER.error(f'{self.lpfx}',exc_info=True)
            self.inc_error(f"{self.lpfx} {ex}")


    id = "controller"
    commands = {
        "QUERY": query,
        "QUERY_ALL": cmd_query_all,
        "DISCOVER": cmd_discover,
        "EXPORT": cmd_export,
        "UPDATE_PROFILE": cmd_update_profile,
        "SPEAK_WORD": cmd_speak_word,
        "SPEAK_PHRASE": cmd_speak_phrase,
    }
    drivers = [
        {"driver": "ST", "value": 0, "uom": 25},
        {"driver": "ERR", "value": 0, "uom": 56},
        {"driver": "GV1", "value": 0, "uom": 25},
        {"driver": "GV2", "value": 0, "uom": 25},
        {"driver": "GV3", "value": 0, "uom": 2},
        {"driver": "GV5", "value": 0, "uom": 2},
        {"driver": "GV6", "value": 0, "uom": 2},
        {"driver": "GV7", "value": 0, "uom": 2},
        {"driver": "GV9", "value": 0, "uom": 2},
        {"driver": "GV10", "value": 0, "uom": 2},
        {"driver": "GV11", "value": 0, "uom": 2},
        {"driver": "GV12", "value": 0, "uom": 2},
        {"driver": "GV13", "value": 0, "uom": 2},
        {"driver": "GV14", "value": 0, "uom": 2},
        {"driver": "GV15", "value": 0, "uom": 2},
        {"driver": "GV16", "value": 0, "uom": 2},
        {"driver": "GV17", "value": 0, "uom": 2},
        {"driver": "GV19", "value": 0, "uom": 2},
        {"driver": "GV21", "value": 0, "uom": 2},
        {"driver": "GV22", "value": 0, "uom": 2},
        {"driver": "GV23", "value": 0, "uom": 2},
        {"driver": "GV24", "value": 0, "uom": 2},
    ]
