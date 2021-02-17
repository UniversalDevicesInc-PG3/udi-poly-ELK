import sys
import time
import logging
import asyncio
import os
from threading import Thread
from node_funcs import *
from nodes import AreaNode,OutputNode
from polyinterface import Controller, LOGGER, LOG_HANDLER

# sys.path.insert(0, "../elkm1")
from elkm1_lib import Elk
from elkm1_lib.const import Max
 
# asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
mainloop = asyncio.get_event_loop()

class Controller(Controller):
    def __init__(self, polyglot):
        # We track our drsiver values because we need the value before it's been pushed.
        super(Controller, self).__init__(polyglot)
        self.name = "ELK Controller"
        self.hb = 0
        self.elk = None
        self.elk_st = None
        self.elk_thread = None
        self.config_st = False
        self.driver = {}
        self._area_nodes = {}
        self._output_nodes = {}
        self._keypad_nodes = {}
        self.logger = LOGGER
        self.lpfx = self.name + ":"
        # Not using because it's called to many times
        # self.poly.onConfig(self.process_config)

    def start(self):
        LOGGER.info(f"{self.lpfx} start")
        # Don't check profile because we always write it later
        self.server_data = self.poly.get_server_data(check_profile=False)
        LOGGER.info(f"{self.lpfx} Version {self.server_data['version']}")
        self.set_debug_level()
        self.setDriver("ST", 1)
        self.heartbeat()
        self.check_params()
        if self.config_st:
            LOGGER.info(f"{self.lpfx} Calling elk_start...")
            self.elk_start()
        else:
            LOGGER.error(
                f"{self.lpfx} Not starting ELK since configuration not ready, please fix and restart"
            )

    def heartbeat(self):
        LOGGER.debug(f"{self.lpfx} hb={self.hb}")
        if self.hb == 0:
            self.reportCmd("DON", 2)
            self.hb = 1
        else:
            self.reportCmd("DOF", 2)
            self.hb = 0

    def shortPoll(self):
        LOGGER.debug(f'{self.lpfx}')
        for an in self._area_nodes:
            self._area_nodes[an].shortPoll()

    def longPoll(self):
        self.heartbeat()
        self.check_connection()

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
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

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

    def sync_complete(self):
        LOGGER.info(f"{self.lpfx} Sync of keypad is complete!!!")
        # TODO: Add driver for sync complete status, or put in ST?
        LOGGER.info(f"{self.lpfx} adding areas...")
        for an in range(Max.AREAS.value - 1):
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
                self._area_nodes[an] = self.addNode(AreaNode(self, self.elk.areas[an]))
        LOGGER.info("adding areas done, adding outputs...")
        # elkm1_lib uses zone numbers starting at zero.
        for n in range(Max.OUTPUTS.value - 1):
            if n in self._output_nodes:
                LOGGER.info(
                    f"{self.lpfx} Skipping Output {n+1} because it already defined."
                )
            elif is_in_list(n+1, self.use_outputs_list) is False:
                LOGGER.info(
                    f"{self.lpfx} Skipping Output {n+1} because it is not in outputs range {self.use_outputs} in configuration"
                )
            else:
                LOGGER.info(f"{self.lpfx} Adding Output {an}")
                self._output_nodes[an] = self.addNode(OutputNode(self, self.elk.outputs[n]))
        LOGGER.info("adding outputs done")
        self.write_profile()

    def timeout(self, msg_code):
        LOGGER.error(f"{self.lpfx} Timeout sending message {msg_code}!!!")

    def unknown(self, msg_code, data):
        if msg_code == 'Unknown message EM':
            return
        LOGGER.error(f"{self.lpfx} Unknown message {msg_code}: {data}!!!")

    def elk_start(self):
        self.elk_config = {
            # TODO: Support secure which would use elks: and add 'keypadid': 'xxx', 'password': 'xxx'
            "url": "elk://"
            + self.host,
        }
        # We have to create a loop since we are in a thread
        # mainloop = asyncio.new_event_loop()
        LOGGER.info(f"{self.lpfx} started")
        logging.getLogger("elkm1_lib").setLevel(logging.DEBUG)
        asyncio.set_event_loop(mainloop)
        self.elk = Elk(self.elk_config, loop=mainloop)
        LOGGER.info(f"{self.lpfx} Waiting for sync to complete...")
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("login", self.login)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.add_handler("timeout", self.timeout)
        self.elk.add_handler("unknown", self.unknown)
        LOGGER.info(f"{self.lpfx} Connecting to Elk...")
        self.elk.connect()
        LOGGER.info(
            f"{self.lpfx} Starting Elk Thread, will process data when sync completes..."
        )
        self.elk_thread = Thread(name="ELK-" + str(os.getpid()), target=self.elk.run)
        self.elk_thread.daemon = True
        self.elk_thread.start()

    def discover(self):
        # TODO: What to do here, kill and restart the thread?
        pass

    def elkm1_run(self):
        self.elk.run()

    def delete(self):
        LOGGER.info(
            f"{self.lpfx} Oh no I am being deleted. Nooooooooooooooooooooooooooooooooooooooooo."
        )

    def stop(self):
        LOGGER.debug(f"{self.lpfx} NodeServer stopping...")
        if self.elk is not None:
            self.elk.disconnect()
        if self.elk_thread is not None:
            # Wait for actual termination (if needed)
            self.elk_thread.join()
        LOGGER.debug(f"{self.lpfx} NodeServer stopping complete...")

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        LOGGER.info(f"{self.lpfx} Enter config={config}")
        LOGGER.info(f"{self.lpfx} process_config done")

    def check_params(self):
        """
        This is an example if using custom Params for keypad and password and an example with a Dictionary
        """
        self.removeNoticesAll()
        # Assume it's good unless it's not
        self.config_st = True
        # TODO: Only when necessary
        self.update_profile()
        default_host = "Your_ELK_IP_Or_Host:PortNum"
        if "host" in self.polyConfig["customParams"]:
            self.host = self.polyConfig["customParams"]["host"]
        else:
            self.host = default_host
            LOGGER.error(
                f"{self.lpfx} host not defined in customParams, please add it.  Using {self.host}"
            )
        default_code = "Your_ELK_Keypad_Code_for_Polyglot"
        if "keypad_code" in self.polyConfig["customParams"]:
            try:
                self.keypad_code = int(self.polyConfig["customParams"]["keypad_code"])
            except:
                self.keypad_code = default_code
                self.addNotice(
                    "ERROR keypad_code is not an integer, please fix, save and restart this nodeserver",
                    "host",
                )
        else:
            self.keypad_code = default_code
            LOGGER.error(
                f"{self.lpfx} keypad_code not defined in customParams, please add it.  Using {self.keypad_code}"
            )

        self.use_areas = self.getCustomParam("areas")
        self.use_areas_list = ()
        if self.use_areas == "":
            errs = "No areas defined in config so none will be added"
            LOGGER.error(errs)
            self.addNotice(errs, "areas")
        else:
            if self.use_areas is None:
                self.use_areas = "1"
            try:
                self.use_areas_list = parse_range(self.use_areas)
            except:
                errs = f"ERROR: Failed to parse areas range '{self.use_areas}'  will not add any areas: {sys.exc_info()[1]}"
                LOGGER.error(errs)
                self.addNotice(errs, "areas")
                self.config_st = False

        self.use_outputs = self.getCustomParam("outputs")
        self.use_outputs_list = ()
        if self.use_outputs == "" or self.use_outputs is None:
            LOGGER.warning("No outputs defined in config so none will be added")
        else:
            try:
                self.use_outputs_list = parse_range(self.use_outputs)
            except:
                errs = f"ERROR: Failed to parse outputs range '{self.use_outputs}'  will not add any outputs: {sys.exc_info()[1]}"
                LOGGER.error(errs)
                self.addNotice(errs, "outputs")
                self.config_st = False

        #self.use_keypads = self.getCustomParam("keypads")
        #self.use_keypads_list = ()
        #if self.use_keypads == "" or self.use_keypads is None:
        #    LOGGER.warning("No keypads defined in config so none will be added")
        #else:
        #    try:
        #        self.use_keypads_list = parse_range(self.use_keypads)
        #    except:
        #        errs = f"ERROR: Failed to parse keypads range '{self.use_keypads}'  will not add any keypads: {sys.exc_info()[1]}"
        #        LOGGER.error(errs)
        #        self.addNotice(errs, "keypads")
        #        self.config_st = False

        # Make sure they are in the params
        self.addCustomParam(
            {
                "host": self.host, 
                "keypad_code": self.keypad_code, 
                "areas": self.use_areas,
                "outputs": self.use_outputs,
                #"keypads": self.use_keypads
            }
        )

        # Add a notice if they need to change the keypad/password from the default.
        if self.host == default_host:
            # This doesn't pass a key to test the old way.
            self.addNotice(
                "Please set proper host in configuration page, and restart this nodeserver",
                "host",
            )
            self.config_st = False
        if self.keypad_code == default_code:
            # This doesn't pass a key to test the old way.
            self.addNotice(
                "Please set proper keypad_code in configuration page, and restart this nodeserver",
                "code",
            )
            self.config_st = False

        # self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

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
    # Then write our custom NLS lines.
    nls.write("\nUSER-0 = Unknown\n")
    for n in range(Max.USERS.value - 1):
        LOGGER.debug(f"{self.lpfx} user={self.elk.users[n]}")
        nls.write(f"USER-{n+1} = {self.elk.users[n].name}")
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

    def set_all_logs(self, level, slevel=logging.WARNING):
        LOGGER.info(
            f"Setting level={level} sublevel={slevel} CRITICAL={logging.CRITICAL} ERROR={logging.ERROR} WARNING={logging.WARNING},INFO={logging.INFO} DEBUG={logging.DEBUG}"
        )
        LOGGER.setLevel(level)
        #This sets for all modules
        #LOG_HANDLER.set_basic_config(True, slevel)
        #but we do each indivudally
        logging.getLogger("elkm1_lib.elk").setLevel(slevel)
        logging.getLogger("elkm1_lib.proto").setLevel(slevel)

    def set_debug_level(self, level=None):
        LOGGER.info(f"level={level}")
        mdrv = "GV2"
        if level is None:
            # Restore from DB for existing nodes
            level = self.get_driver(mdrv, 20)
        level = int(level)
        if level == 0:
            level = 20
        LOGGER.info(f"Seting {mdrv} to {level}")
        self.setDriver(mdrv, level)
        # 0=All 10=Debug are the same because 0 (NOTSET) doesn't show everything.
        slevel = logging.WARNING
        if level <= 10:
            if level < 10:
                slevel = logging.DEBUG
            level = logging.DEBUG
        elif level == 20:
            level = logging.INFO
        elif level == 30:
            level = logging.WARNING
        elif level == 40:
            level = logging.ERROR
        elif level == 50:
            level = logging.CRITICAL
        else:
            LOGGER.error(f"Unknown level {level}")
        #LOG_HANDLER.set_basic_config(True,logging.DEBUG)
        self.set_all_logs(level, slevel)

    def update_profile(self):
        LOGGER.info(f"{self.lpfx}")
        return self.poly.installprofile()

    def cmd_update_profile(self, command):
        LOGGER.info(f"{self.lpfx}")
        return self.update_profile()

    def cmd_set_debug_mode(self, command):
        val = int(command.get("value"))
        LOGGER.debug(f"val={val}")
        self.set_debug_level(val)

    id = "controller"
    commands = {
        "QUERY": query,
        "DISCOVER": discover,
        "UPDATE_PROFILE": cmd_update_profile,
        "SET_DM": cmd_set_debug_mode,
    }
    drivers = [
        {"driver": "ST", "value": 0, "uom": 2},
        {"driver": "GV1", "value": 0, "uom": 2},
        {"driver": "GV2", "value": logging.DEBUG, "uom": 25},
    ]
