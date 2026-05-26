# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.10.16] - 2026-05-25

### Fixed

- **Startup on systems without an IPv4 default gateway:** the controller now resolves the local network interface lazily for config docs and the optional ELKID export REST server, so `getNetworkInterface()` failures no longer block startup or panel sync.

---

## Earlier releases

The following entries were migrated from `README.md` (original wording and dates preserved).

### 3.10.15 - 02/10/2024
- Prepare for next PG3x release. If using ELKID or ELKNAME you must enable the "Allow ISY Access by PLugin" on the configuration page.

### 3.10.14 - 02/03/2024
- Fix ISY Nodes IP address in Configuration Page

### 3.10.13 - 02/03/2024
- Fix [Issue with light_method=ELKNAME and old light_n nodes](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/104)
- Also lots of fixes for when light_method is changed, now no restarts should be necessary

### 3.10.12 - 02/01/2024
- Fixed keypad with Temperture sensor profile to match keypad.

### 3.10.11 - 12/28/2023
- Improved light_method=ELKID.  All users of this method MUST click on the "export" link on the configuration page to run the new export procedure.  If your ELKID's have not changed you don't need to re-import into ElkRP but it would be best.

### 3.10.8 - 12/27/2023
- Fix [Setting up ELK ns module](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/102)

### 3.10.7 - 12/26/2023
- Increase initialization timeout to allow for PyISY retries when no variables or network resources exist.
- Fix crash when ELKID is added to a scene
- Better parsing and error message for checking ELKID

### 3.10.6 - 12/16/2023
- Fix [Violated & Bypassed Zones not updating](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/95)

### 3.10.5 - 11/22/2023
- Fix Celcius Thermostat profile to remove Admin Console Errors

### 3.10.4 - 11/11/2023
- Set default ST (Nodeserver Online) to 1.

### 3.10.3 - 10/21/2023
- Restructure startup to avoid issues:
  - [AttributeError: 'Controller' object has no attribute 'change_node_names'](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/101)
  - [AttributeError: 'Controller' object has no attribute 'light_method'](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/100)

### 3.10.1 - 10/15/2023
- Fix bug in renameNode caused by PG3 interface change
- Fix crash when pyISY returns 0 for node_changed

### 3.10.0 - 09/04/2023
- Beta release of [Add Elk thermostats](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/50)

### 3.9.0 - 09/03/2023
- Enhancement [Allow Elk NS to Recognize Keypad Presses](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/69) see [Keypad Control events](README.md#keypad-control-events)
- Enhancement [Support ELK Remote button presses #90](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/90)

### 3.8.1 - 08/15/2023
- Properly set version

### 3.8.0 - 08/12/2023
- Added light_method ELKALL which creates an ISY Light node for all defined ELK Lights
- Add driver names so they show up in the PG3 UI
- Updated Configuration document

### 3.7.0 - 04/07/2023
- Added Export ability for [Support Elk Export](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/67)

### 3.6.5 - 04/01/2023
- Fix crash if no Elk lights are defined
- Add many traps to catch future errors in Light code
- Shutdown PyISY if no Elk<->Lights defined

### 3.6.4 - 03/31/2023
- Fix bug causing crash if a ELK Light name matches a folder name

### 3.6.0 - 03/15/2023
- Add support for ELK Lights see [Light Node](README.md#light-node) above for more information.

### 3.5.8 - 01/15/2023
- Fix elkm1_lib version

### 3.5.7 - 11/17/2022
- Fix crash that can happen on startup

### 3.5.5 - 10/23/2022
- Fix another bug related to fix for [Triggered and Violated zone not showing on area](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/89) which shows error "int() argument must be a string, a bytes-like object or a number, not 'ZoneType'"

### 3.5.4 - 10/22/2022
- Fix bug related to fix for [Triggered and Violated zone not showing on area](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/89) which shows error "int() argument must be a string, a bytes-like object or a number, not 'ZoneType'"

### 3.5.3 - 10/16/2022
- Fix: [Triggered and Violated zone not showing on area](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/89)
- Fix: [node command DOF not defined](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/87)

### 3.5.2 - 09/25/2022
- Fix: Properly initialize temperature for Zone and Keypad

### 3.5.1 - 09/25/2022
- Fix For: [Support Zone Specific System Trouble](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/86)
  - Now reporting correct zone numbers
- Fix: [Unconfigured Zone Error](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/88)

### 3.5.0 - 09/24/2022
- Enhancement: [Support Zone Specific System Trouble](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/86)
  - See [Zone](README.md#zone-node) System Trouble documentation above
- Enhancement: [Allow user to trigger alarms](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/82)
  - See [Zone](README.md#zone-node) Trigger documentation above
- Enhancement: [Support Zone Temperature](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/65)
  - See [Zone](README.md#zone-node) Temperature documentation above
- Fix: [Controller queried before panel was ready on Polisy reboot](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/85)

### 3.4.9 - 08/19/2022
- Fix issues with [ELM M1G System Trouble Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/78)
- Fix [Support Keypad callback for temperature updates](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/83)
- Fix: Ignore AR messages from panel
- Fix: Callback receiving strings instead of enum from trouble reports

### 3.4.8 - 08/18/2022
- Fix GV25 setting on controller

### 3.4.7 - 08/17/2022
- Fix bug not sending DON/DOF for Zones due to latest elkm1_lib
- Install released elkm1_lib instead of including in the release package now that is available

### 3.4.6 - 08/07/2022
- Fix press chime key for latest elkm1_lib

### 3.4.5 - 08/07/2022
- Update elkm1_lib version

### 3.4.4 - 08/06/2022
- Fixes for latest elkm1 lib changes for remote programming status and system trouble.
- There was a duplicated driver number for system trouble status, so all starting with GV4 have been incremented. Please check if you are already using them.

### 3.4.3 - 08/06/2022
- Error out early if Python version is not up to date.

### 3.4.2 - 08/06/2022
- Fix Arming and some benign warnings

### 3.4.1 - 08/05/2022
- More documentation cleanup, still needs more.
  - Added driver's to many Nodes, still more to go
- When node is queried the values are passed to PG3 with force option so they always update the ISY
  - This helps set initial ISY driver values during query-all on ISY restart
- Updates to work with latest elkm1_lib
  - Currently using local version with my enhancements for chime mode
- [Allow user to control Chime Mode](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/14)
  - Also allow setting desired Chime Mode on an area, which may require multiple chime button presses
  - Note that an ISY reboot is required to get the proper values to show up for chime mode in notifications and UD Mobile
- [ELM M1G System Trouble Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/78)
  - See [ELK Controller](README.md#elk-controller) System Trouble Status
- [Add Remote Programming Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/80)
  - See [ELK Controller](README.md#elk-ontroller) Remote Programming Status
- [Allow Elk NS to Recognize Keypad Presses](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues)
  - Now supports Last Key and Last Function key on each keypad
  - See [Key Pad Node](README.md#keypad-node)
- [Add ERROR driver to controller](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/62)
  - Attempt to trap all errors and show status on ISY and in PG3 UI
  - See [ELK Controller](README.md#elk-ontroller) Node server errors
- [M1 Touch Pro causes error](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/81)
  - Now just shows as a warning

### 3.3.8 - 07/25/2022
- Fixed to work with udi-interface 3.0.47
- Fixed longPoll/shortPoll not working properly

### 3.3.7 - 07/23/2022
- Properly Fixed: [Armed Status reported incorrectly as Armed Away when actually disarmed](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/77)
  - Version 3.3.6 had a bug which reset values for poll voltages, use off node, back to node server defaults so users who upgraded will need to go back and change the values on the ISY if they were not using the defaults.

### 3.3.6 - 07/21/2022
- Fix: [Armed Status reported incorrectly as Armed Away when actually disarmed](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/77)
- Add hooks for [ELM M1G System Trouble Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/78) now just need to initiate trouble to test further

### 3.3.5 - 06/21/2022
- Fix: [Crash setting Counter value](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/76)

### 3.3.4 - 06/05/2022
- Fix heartbeat being sent twice per long poll
- Remove creation of Threads for long and short poll, no longer needed since PG3 runs each in a new thread anyway.

### 3.3.3 - 06/05/2022
- Fix: [Output Nodes sending DON/DOF during query](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/75)

### 3.3.2 - 05/10/2022
- Fix issues with renameing nodes.  Requires PG3 3.0.62 and udi_interface 3.0.45

### 3.3.1 - 05/09/2022
- Bug: Fix Task query

### 3.3.0 - 05/08/2022
- Enhancement: [Add Driver for all the ELK status from the lib](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/7)
  - See [ELK M1EXP Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/blob/master/README.md#elk-controller)
- Enhancement: [Add Elk Lights](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/45)
  - See: See [Light Node](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/blob/master/README.md#light-node)
- Enhancement: [Add Elk Counters](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/49)
  - See: See [Counter Node](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/blob/master/README.md#counter-node)
- Enhancement: [Add Elk Tasks](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/51)
  - See: See [Task Node](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/blob/master/README.md#task-node)
- Enhancement: [Query should update voltages](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/66)
  - Added Zone Poll Voltages setting which if enabled will Poll the Voltage on each short poll when the Area Poll Voltage is enabled.
  - A query on a node will always poll the voltage even if Poll Voltage is False.
- Fix: [Allow output to control a scene](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/73)

### 3.2.8 - 05/05/2022
- Added configuration setting change_node_names.  If set to true then ISY node names will be changed to match the ELK.  Default is true.

### 3.2.7 - 04/14/2022
- Fix invalid init value which caused issues for UD Mobile

### 3.2.6 - 04/06/2022
- Move connecting to elk to after add node is complete to try and avoid race condition with setting m1exp connected state.
- Remove internal get/set Driver methods on controller
- Force set connected status after sync completes due to race condition on node startup
- Removed remenants of old logger level driver

### 3.2.3 - 04/05/2022
- Add more debugging to trace issue with ELK M1EXP Connection going False
- Upgraded elmk1_lib to 1.2.0

### 3.2.2 - 04/03/2022
- Fixed issue with profile for UD Mobile, but UD Mobile will need to add support for new _sys_short editor.

### 3.2.1 - 04/01/2022
- Fixed: [Remove non-ascii characters from display message](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/72)

### 3.2.0 - 03/31/2022
- Added [Send text to keypads](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/13)

### 3.1.4 - 03/08/2022
- Fix stop to call poly stop so it should quit properly when PG3 tells it to.

### 3.1.3 - 03/06/2022
- Fixed: [Fix support for All Alarm Status](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/71)
  - Should be fixed, but not tested for all values

### 3.1.2 - 02/13/2022
- Build a profile even when no ELK is all defined.

### 3.1.1 - 02/12/2022
- Query of controller no longer queries all nodes since the ISY Query program which typically runs every morning at 3am
  will query the controller and all other nodes which created a lot of extra traffic.

### 3.1.0 - 02/10/2022
- [Send speak to panel from list of defined phrases or words](https://github.com/UniversalDevicesInc-PG3/udi-poly-ELK/issues/57)

### 3.0.13 - 01/14/2022
- Add more debugging info to stop and restart

### 3.0.12 - 01/02/2022
- More reorganization to try and fix issues with user settable values not being restored

### 3.0.11 - 01/01/2022
- add nodequeue so only one node is added a a time to try and fix issues, but not working yet

### 3.0.10 - 01/01/2022
- Update to udi_interface 3.0.28

### 3.0.9 - 12/28/2021
- Update to udi_interface 3.0.27

### 3.0.8 - 12/26/2021
- Removed setting debug mode from controller, existing users need to delete controller node in polyglot UI before restarting NS

### 3.0.7 - 12/26/2021
- Back to using conn_status on controller now that udi_interface 3.0.26 fixes the issues

### 3.0.6 - 12/25/2021
- Fix setting controller.ST on startup
- Fix creating off_node

### 3.0.5 - 12/23/2021
- Remove new controller status, seems to be broken in udi interface 3.0.25

### 3.0.4 - 12/23/2021
- Add status for controller needed to show True, False, Failed
- Users on older PG3 versions will need to delete DB and recreate for it to work.

### 3.0.3 - 12/23/2021
- Update to latest udi_interface

### 3.0.2 - 11/23/2021
- Fix crash during query

### 3.0.1 - 11/22/2021
- Change how thread is started so ELK has it's own event loop
- This should fix issues with restarting sometimes failing

### 3.0.0 - 11/14/2021
- Initial conversion to PG3

### 0.5.17 - 06/27/2021
- Enhancement: [Test bad login](https://github.com/jimboca/udi-poly-elk/issues/4)
- Confirmed and Closed: [Test disconnect](https://github.com/jimboca/udi-poly-elk/issues/5)
- Confirmed: [Test elkm1 lib 1.0.0](https://github.com/jimboca/udi-poly-elk/issues/61)

### 0.5.16 - 06/26/2021
- Fix Bug trying to enable/disable Additional Trigger MOde

### 0.5.15 - 06/19/2021
- Fixes for Additional Trigger mode

### 0.5.14 - 06/17/2021
- Fix profile error from 0.5.12

### 0.5.13 - 06/17/2021
- Bug Fixed: [Zone query causes controller to crash](https://github.com/jimboca/udi-poly-elk/issues/59)

### 0.5.12 - 05/23/2021
- Enhancement for: [Violated Zone Reporting Armed Stay Mode vs Elk M1 Reporting](https://github.com/jimboca/udi-poly-elk/issues/40)
  - Add Last Triggered Zone and Entry/Exit Trigger option.  Please provide feedback.

### 0.5.11 - 04/30/2021
- Fixed: [discover called incorrectly for runCmd](https://github.com/jimboca/udi-poly-elk/issues/20)
- Enhancement for: [Violated Zone Reporting Armed Stay Mode vs Elk M1 Reporting](https://github.com/jimboca/udi-poly-elk/issues/40)
  - Now properly set Zone GV1 "Triggered Alarm" when a zone triggers an alarm

### 0.5.10 - 04/28/2021
- Fix when initial elk alarm_state is empty

### 0.5.6 - 0.5.9 - 04/06/2021
- Fixed to show proper temperature: [Keypad: Only show temperature if the keypad has a sensor](https://github.com/jimboca/udi-poly-elk/issues/52)

### 0.5.5 - 04/06/2021
- Fixed: [Keypad: Only show temperature if the keypad has a sensor](https://github.com/jimboca/udi-poly-elk/issues/52)

### 0.5.4 - 04/05/2021
- Fixed: [Can not turn off "use off node"](https://github.com/jimboca/udi-poly-elk/issues/56)
- Enhancement: [Keypad: Allow showing C or F](https://github.com/jimboca/udi-poly-elk/issues/53)
- Enhancement: [Keypad: Only show temperature if the keypad has a sensor](https://github.com/jimboca/udi-poly-elk/issues/52)
  - I can not test this, so I need someone with a temperature sensor in a keypad to confirm
- Documentation: [Violated Zone Reporting Armed Stay Mode vs Elk M1 Reporting](https://github.com/jimboca/udi-poly-elk/issues/46)
  - Added notes in README about Violated.

### 0.5.3 - 02/27/2021
- [Area: Add Last Violated Zone](https://github.com/jimboca/udi-poly-elk/issues/55)
- Set user names for Version 4.4.2 and later, user code 201 = Program Code, 202 = ELK RP Code, 203 = Quick Arm, no code
- Fix Max values to correct max, not minus 1

### 0.5.2 - 02/22/2021
- Put short/long poll in their own threads so they don't block others
- Do not set last user keypad in area last_log

### 0.5.1 - 02/19/2021
- [Add Elk Keypads](https://github.com/jimboca/udi-poly-elk/issues/48)
  - Added debug when keypad is not added for debugging
- [Add support for last user](https://github.com/jimboca/udi-poly-elk/issues/47)
  - Fix setting last_user on keypads when it happens
  - Set User 203 name to "No Code User"
- [Keypad: Add last keypad to Area](https://github.com/jimboca/udi-poly-elk/issues/54)

### 0.5.0 - 02/17/2021
- [Add Elk Keypads](https://github.com/jimboca/udi-poly-elk/issues/48)
  - Added, but can't do function keys yet, need to add support to Python elkm1 library
- [Add support for last user](https://github.com/jimboca/udi-poly-elk/issues/47)
  - Added for Keypads and Area

### 0.4.3 - 02/09/2021
- [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
  - Change wording from Time to Seconds, profile and doc change only.

### 0.4.2 - 02/08/2021
- [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
  - Fixed Output On/Off values
  - Fix crashed when outputs is null.

### 0.4.1 - 02/08/2021
- [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
  - Add missing Output.py file.

### 0.4.0 - 02/07/2021
- [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)

### 0.4.0 - 02/07/2021
- [Add support for Zone voltage](https://github.com/jimboca/udi-poly-elk/issues/38)
  - Poll Voltages for Zones when Area Enables Poll Voltages setting.

### 0.3.2 - 02/05/2021
- [DOF not sent for EOL](https://github.com/jimboca/udi-poly-elk/issues/42)
  - Removed Send On/Off functionality
  - Added 'Send On For' default=Open 'Send Off For' default=EOL so users can control

### 0.3.1 - 02/05/2021
- Only wording changes for Arm Up State [Word Wrap Text Box](https://github.com/jimboca/udi-poly-elk/issues/44)

### 0.3.0 - 02/04/2021
- [Improve how violated/bypassed zones are counted](https://github.com/jimboca/udi-poly-elk/issues/40)
- [Add support for Zone voltage](https://github.com/jimboca/udi-poly-elk/issues/38)
  - But currently on startup the voltage is always zero, it only updates occasionally when panel sync is done.
  - Asked on the elkm1_lib if this is a know issue [Voltage is not initialized on startup](https://github.com/gwww/elkm1/issues/40)

### 0.2.8 - 01/29/2021
- Update polyinterface requirement to latest.

### 0.2.7 - 01/21/2021
- Fix logging when setting Zone ST & GV0
- Change DON/DOF to Send On / Send Off in documentation and in nodeserver nls
- [DOF not sent for EOL](https://github.com/jimboca/udi-poly-elk/issues/42)
  - Always send DOF for EOL and Short

### 0.2.6 - 01/16/2021
- Fix [All Zones in an Area are being added to ISY](https://github.com/jimboca/udi-poly-elk/issues/37)

### 0.2.5 - 01/15/2021
- Fix [Illegal characters or empty zone name issues](https://github.com/jimboca/udi-poly-elk/issues/35)

### 0.2.4 - 01/14/2021
- Fix [Illegal characters or empty zone name issues](https://github.com/jimboca/udi-poly-elk/issues/35)
- Change logical and physical status [Logical vs Physical State](https://github.com/jimboca/udi-poly-elk/issues/34)
- Fix [Don't print Unknown message EM errors](https://github.com/jimboca/udi-poly-elk/issues/30)

### 0.2.3 - 01/05/2021
- Fix profile

### 0.2.2 - 01/04/2021
- Add better logging to see what is happening

### 0.2.1 - 01/04/2021
- Add BaseNode so all nodes use common set/get driver methods for consistency and debugging aid

### 0.2.0 - 12/26/2020
- __IMPORTANT__ All Area and Zone node address will change, either delete them all in Polyglot UI or delete the node server and add again
  - [Area and Zone numbers should match ELK numbers](https://github.com/jimboca/udi-poly-elk/issues/21)
  - Make sure to re-sync the ISY UDMobile App as well after re-adding
- Fix [https://github.com/jimboca/udi-poly-elk/issues/26](Bypass button on zone node screen)
- Fix [https://github.com/jimboca/udi-poly-elk/issues/25](Tracking of number of bypassed zones in area inconsisten)

### 0.1.9 - 12/18/2020
- Fix issues caused when sync_complete is called multiple times
  - [Multiple changes happening after restarting Node server](https://github.com/jimboca/udi-poly-elk/issues/18)

### 0.1.8
- Fix Logging level for Debug + elkm1_lib so you can see wha the ELK is sending

### 0.1.7
- Fix crash during stop when config is not ready, fix startup when config is ready

### 0.1.6
- [Don't start ELK when Configuration is not setup yet](https://github.com/jimboca/udi-poly-elk/issues/16)

### 0.1.5
- [Add configuration option to say what Area's to add instead of including them all](https://github.com/jimboca/udi-poly-elk/issues/11)

### 0.1.4
- Add check for Python Version >= 3.6

### 0.1.3
- Add Area and Zone Bypass commands, don't send DON/DOF on startup.

### 0.1.2
- Only send DON/DOFF when status actually changes.

### 0.1.0
- Update to work with elkm1_lib 0.8.8 and more code cleanup.
