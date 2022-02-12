from curses.ascii import SP
import sys
import time
import logging
import asyncio
import os
import markdown2
from copy import deepcopy
from threading import Thread,Event
from node_funcs import *
from nodes import AreaNode,OutputNode
from udi_interface import Node,LOGGER,Custom,LOG_HANDLER
from threading import Thread,Event
from const import SPEAK_WORDS,SPEAK_PHRASES

# sys.path.insert(0, "../elkm1")
from elkm1_lib import Elk
from elkm1_lib.const import Max

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
        self.driver = {}
        self.n_queue = []
        self._area_nodes = {}
        self._output_nodes = {}
        self._keypad_nodes = {}
        self.logger = LOGGER
        self.lpfx = self.name + ":"
        self.poly.Notices.clear()
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
        poly.subscribe(poly.STOP,              self.stop)
        poly.subscribe(poly.CONFIG,            self.config)
        poly.subscribe(poly.ADDNODEDONE,       self.node_queue)
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

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()

    def config(self,data):
        LOGGER.debug(f'{data}')

    def handler_start(self):
        LOGGER.debug(f'{self.lpfx} enter')
        LOGGER.info(f"Started Airscape NodeServer {self.poly.serverdata['version']}")
        # Remove when conn_status is working
        self.setDriver("ST",1)
        self.heartbeat()

        configurationHelp = './configdoc.md';
        if os.path.isfile(configurationHelp):
	        cfgdoc = markdown2.markdown_path(configurationHelp)
	        self.poly.setCustomParamsDoc(cfgdoc)
        else:
            LOGGER.error(f'config doc not found? {configurationHelp}')
            
        LOGGER.debug(f'{self.lpfx} exit')

    def handler_config_done(self):
        LOGGER.debug(f'{self.lpfx} enter')
        self.poly.addLogLevel('DEBUG_MODULES',9,'Debug + Modules')
        # Currently not gaurunteed all config handlers are called, so wait
        # until custom params are processed
        count = 0
        while self.config_st is None and count < 60:
            LOGGER.warning("Waiting for config to be loaded...")
            time.sleep(1)
            count += 1
        if count == 60:
            LOGGER.error("Timeout waiting for config to load, check log for other errors.")
            exit
        self.elk_start()
        LOGGER.debug(f'{self.lpfx} exit')

    def heartbeat(self):
        LOGGER.debug(f"{self.lpfx} hb={self.hb}")
        if self.hb == 0:
            self.reportCmd("DON", 2)
            self.hb = 1
        else:
            self.reportCmd("DOF", 2)
            self.hb = 0

    def handler_poll(self, polltype):
        if polltype == 'longPoll':
            self.longPoll()
        elif polltype == 'shortPoll':
            self.shortPoll()

    def shortPoll(self):
        if not self.ready:
            LOGGER.info('waiting for sync to complete')
            return
        if self.short_event is False:
            LOGGER.debug('Setting up Thread')
            self.short_event = Event()
            self.short_thread = Thread(name='shortPoll',target=self._shortPoll)
            self.short_thread.daemon = True
            LOGGER.debug('Starting Thread')
            st = self.short_thread.start()
            LOGGER.debug(f'Thread start st={st}')
        # Tell the thread to run
        LOGGER.debug(f'thread={self.short_thread} event={self.short_event}')
        if self.short_event is not None:
            LOGGER.debug('calling event.set')
            self.short_event.set()
        else:
            LOGGER.error(f'event is gone? thread={self.short_thread} event={self.short_event}')

    def _shortPoll(self):
        while (True):
            self.short_event.wait()
            LOGGER.debug('start')
            for an in self._area_nodes:
                self._area_nodes[an].shortPoll()
            self.short_event.clear()
            LOGGER.debug('done')

    def longPoll(self):
        self.heartbeat()
        if not self.ready:
            LOGGER.info('waiting for sync to complete')
            return
        if self.long_event is False:
            LOGGER.debug('Setting up Thread')
            self.long_event = Event()
            self.long_thread = Thread(name='longPoll',target=self._longPoll)
            self.long_thread.daemon = True
            LOGGER.debug('Starting Thread')
            st = self.long_thread.start()
            LOGGER.debug('Thread start st={st}')
        # Tell the thread to run
        LOGGER.debug(f'thread={self.long_thread} event={self.long_event}')
        if self.long_event is not None:
            LOGGER.debug('calling event.set')
            self.long_event.set()
        else:
            LOGGER.error(f'event is gone? thread={self.long_thread} event={self.long_event}')

    def _longPoll(self):
        while (True):
            self.long_event.wait()
            LOGGER.debug('start')
            self.heartbeat()
            self.check_connection()
            self.long_event.clear()
            LOGGER.debug('done')

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

    def setDriver(self, driver, value):
        LOGGER.debug(f"{self.lpfx} {driver}={value}")
        self.driver[driver] = value
        super(Controller, self).setDriver(driver, value)

    def getDriver(self, driver):
        if driver in self.driver:
            return self.driver[driver]
        else:
            return super(Controller, self).getDriver(driver)

    # Should not be needed with new library?
    def check_connection(self):
        if self.elk is None:
            st = False
        elif self.elk.is_connected:
            st = True
        else:
            st = False
        LOGGER.debug(f"{self.lpfx} st={st} elk_st={self.elk_st}")
        self.set_st(st)

    def set_st(self, st):
        # Did connection status change?
        if self.elk_st != st:
            # We have been connected, but lost it...
            if self.elk_st is True:
                LOGGER.error(f"{self.lpfx} Lost Connection! Will try to reconnect.")
            self.elk_st = st
            if st:
                LOGGER.debug(f"{self.lpfx} Connected")
                self.setDriver("GV1", 1)
            else:
                LOGGER.debug(f"{self.lpfx} NOT Connected")
                self.setDriver("GV1", 0)

    def query(self):
        LOGGER.info(f'{self.lpfx}')
        self.check_params()
        self.reportDrivers()

    def query_all(self):
        LOGGER.info(f'{self.lpfx}')
        self.query()
        for node in self.poly.getNodes():
            self.poly.getNode(node).reportDrivers()

    def connected(self):
        LOGGER.info(f"{self.lpfx} Connected!!!")
        self.set_st(True)

    def disconnected(self):
        LOGGER.info(f"{self.lpfx} Disconnected!!!")
        self.set_st(False)

    def login(self, succeeded):
        if succeeded:
            LOGGER.info("Login succeeded")
        else:
            LOGGER.error(f"{self.lpfx} Login Failed!!!")

    def add_node(self,address,node):
        self.poly.addNode(node)
        self.wait_for_node_done()
        node = self.poly.getNode(address)
        if node is None:
            LOGGER.error('Failed to add node address')
        return node

    def sync_complete(self):
        LOGGER.info(f"{self.lpfx} Sync of keypad is complete!!!")
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
        # Only update profile on restart
        if not self.profile_done:
            self.write_profile()
            self.profile_done = True
        self.ready = True

    def timeout(self, msg_code):
        LOGGER.error(f"{self.lpfx} Timeout sending message {msg_code}!!!")
        if msg_code == 'AS':
            LOGGER.error(f"{self.lpfx} The above Arm System timeout is usually caused by incorrect user code, please check the Polyglot Configuration page for this nodeserver and restart the nodeserver.")

    def unknown(self, msg_code, data):
        if msg_code == 'EM':
            return
        LOGGER.error(f"{self.lpfx} Unknown message {msg_code}: {data}!!!")

    def elk_start(self):
        LOGGER.debug(f'{self.lpfx} enter: config_st={self.config_st}')
        if not self.config_st:
            msg = "Can't start elk until configuration is completed"
            LOGGER.error(msg)
            self.poly.Notices['elk_start'] = msg
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
        self.elk_thread = Thread(name="ELK-" + str(os.getpid()), target=self._elk_start())
        self.elk_thread.daemon = True
        self.elk_thread.start()

    def _elk_start(self):
        # We have to create a loop since we are in a thread
        LOGGER.info(f"{self.lpfx} started")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.elk = Elk(self.elk_config, loop=loop)
        LOGGER.debug(f'elk={self.elk} initialized, starting...')
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("login", self.login)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.add_handler("timeout", self.timeout)
        self.elk.add_handler("unknown", self.unknown)
        LOGGER.info(f"{self.lpfx} Connecting to Elk...")
        self.elk.connect()
        self.elk.run()
        #future = asyncio.run_coroutine_threadsafe(self.elk_start_run(), loop)
        #LOGGER.info(f'future={future}')
        #self.elk = future.result()

    async def elk_start_run(self):
        self.elk.run()
        return elk

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

    def elk_stop(self):
        LOGGER.info(f'elk={self.elk} thread={self.elk_thread}')
        if self.elk is not None:
            LOGGER.warning('Stopping ELK monitor...')
            self.elk.disconnect()
        if self.elk_thread is not None:
            LOGGER.warning('Stopping ELK thread...')
            # TODO: Wait for actual termination (if needed)
            self.elk_thread.join()
            if self.elk_thread.is_alive():
                LOGGER.error('ELK thread did not exit?')
            else:
                LOGGER.error('ELK thread done.')
        return True

    def elk_restart(self):
        LOGGER.warning(f"{self.lpfx} Restarting Nodeserver")
        if (self.elk_stop):
            self.elk_start()
        LOGGER.info(f"{self.lpfx} exit")

    def stop(self):
        LOGGER.warning(f"{self.lpfx} NodeServer stopping...")
        self.elk_stop()
        LOGGER.warning(f"{self.lpfx} NodeServer stopping complete...")

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
        self.check_params()
        self.elk_restart()
    
    def check_params(self):
        """
        Check all user params are available and valid
        """
        # Assume it's good unless it's not
        config_st = True
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
        for zn in range(Max.ZONES.value):
            if self.elk.zones[zn].definition > 0:
                SPEAK_PHRASES[zn+1] = self.elk.zones[zn].name
        for idx,word in SPEAK_PHRASES.items():
            sphrases.append(idx)
            nls.write(f"SPP-{idx} = {word}\n")

        #
        # Then write our custom NLS lines
        nls.write("\nUSER-0 = Unknown\n")
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
        for n in range(Max.KEYPADS.value):
            LOGGER.debug(f"{self.lpfx} keypad={self.elk.keypads[n]}")
            nls.write(f"KEYPAD-{n+1} = {self.elk.keypads[n].name}\n")
        #
        # Now the zones names
        nls.write("\n\nZONE-0 = Unknown\n")
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

    def cmd_update_profile(self, command):
        LOGGER.info(f"{self.lpfx}")
        return self.update_profile()

    def cmd_discover(self, command):
        LOGGER.info(f"{self.lpfx}")
        return self.discover()

    def cmd_speak_word(self, command):
        val = int(command.get('value'))
        LOGGER.info(f"{self.lpfx} {val}")
        # Get the word from the sorted list
        LOGGER.info(f"{self.lpfx} word={SPEAK_WORDS[val]}")
        return self.elk.panel.speak_word(val)

    def cmd_speak_phrase(self, command):
        val = int(command.get('value'))
        LOGGER.info(f"{self.lpfx} {val}")
        # Get the word from the sorted list
        LOGGER.info(f"{self.lpfx} phrase={SPEAK_PHRASES[val]}")
        return self.elk.panel.speak_phrase(val)


    id = "controller"
    commands = {
        "QUERY": query,
        "DISCOVER": cmd_discover,
        "UPDATE_PROFILE": cmd_update_profile,
        "SPEAK_WORD": cmd_speak_word,
        "SPEAK_PHRASE": cmd_speak_phrase,
    }
    drivers = [
        {"driver": "ST", "value": 0, "uom": 25},
        {"driver": "GV1", "value": 0, "uom": 2},
        {"driver": "GV2", "value": 0, "uom": 25},
    ]
