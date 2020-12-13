# Polyglot V2 ELK Nodeserver

## Important Notices

I am not responsible for any issues related to this nodeserver including missing an alarm!

Currently I have not fully tested the Alarm Status for when an alarm is active, I need to find the time to tell Alarm Relay I will be testing things, but I haven't done that yet...

## Installation

Install from the Polyglot store.

### Configuration

Open the Configuration Page for the Nodeserver in the Polyglot UI and view the [Configuration Help](/POLYGLOT_CONFIG.md) available on that page.

## Requirements

This uses https://github.com/gwww/elkm1 which currently only supports an M1EXP in local non secure mode.

IF running on Raspberry Pi, you must be on the latest version, Buster with Python 3.6 or above, preferably 3.7.

## Using this Node Server

### Nodes

#### ELK Controller

Currently called Controller, but will be changed.  This has the following status:
- NodeServer Online
  - Nodeserver up and running
- ELK M1EXP Connected
  - Nodeserver is connected to the ELK
- Logger Level
  - Defines how much logging information is printed.

#### Area Node

By default only the first area, is added, change the areas configuraion if you have more than one.  The areas are 0-7, and the node names will match the names defined on your ELK.  They contain the following:
- Alarm Status
  - If there is an Alarm
    - No Alarm Active
    - Entrance Delay is Active
    - Alarm Abort Delay Active
    - Fire Alarm
    - Medical Alarm
    - Police Alarm
    - Burglar Alarm
    - Aux 1 Alarm
    - Aux 2 Alarm
    - Aux 3 Alarm
    - Aux 4 Alarm
    - Carbon Monoxide Alarm
    - Emergency Alarm
    - Freeze Alarm
    - Gas Alarm
    - Heat Alarm
    - Water Alarm
    - Fire Supervisory
    - Verify Fire
- Armed Status
  - The current Armed status, can be controlled by the ISY
    - Unknown
      - Only set to this on startup until the status is Known, not settable by user.
    - Disarmed
    - Armed Away
    - Armed Stay
    - Armed Stay Instant
    - Armed Night
    - Armed Night Instant
    - Armed Vacation
    - Armed Next Away Mode (Probably should show this in Set list?)
    - Armed Next Stay Mode (Probably should show this in Set list?)
    - Force Arm To Away Mode (Need to test what this does, bypass?)
    - Force Arm To Stay Mode (Need to test what this does, bypass?)
- Arm Up State
  - The current Arm Up State
    - Unknown (Only on startup)
    - Not Ready To Arm
    - Ready To Arm
    - Ready To Arm, but a zone violated and can be Force Armed (Never seen this happen?)
    - Armed with Exit Timer working
    - Armed Fully
    - Force Armed with a force arm zone violated
    - Armed with a bypass
- Chime Mode
  - Unknown
  - Silent
  - Single Beep
  - Constantly Beeping
  - Single Beep while Constantly Beeping
  - Single Chime
  - Single Chime with Single Beep
  - Single Chime with Constantly Beeping
  - Single Chime with Single Beep and Constantly Beeping
- Zones Violated
  - The number of Zones currently violated
- Zones Bypassed
  - The number of Zones currently bypassed

#### Zone Node

Currently every Zone in the Area will be added as a Node.  They contain the following:
- Physical Status
  - UNKNOWN
  - Unconfigured
  - Open
  - EOL
  - SHORT
- Logical Status
  - UNKNOWN
  - Normal
  - Trouble
  - Violated
  - Bypassed
- Triggered
  - True
  - False
- Area
  - The Area number the Zone is part of.
- Type
  - The Zone Type configured in the ELK, 37 different choices
- DON/DOF
  - Allow configuring of DON/DOF are sent when the Zone Physical Status changes, this allows you to put the Node in a Scene and by default a DON is sent when the Zone changes to Open, and DOF is sent when Zone changes to SHORT.  But this can be changed with these options:
    - Send Both (The default)
    - Sond None
    - ON Only
    - OFF Only
    - Reverse Send Both (Send DON for SHORT and DOF for Open)
    - Reverse On Only
    - Reverse Off Only
- Use Off Node
  - Setting this to True will create the Zone Off Node for this Zone

#### Zone Off Node

This node is created for a Zone when "Use Off Node" is set to True.  This allows you to have separate nodes for On and Off so they can be in different Scenes if desired.

## TODO and issues

https://github.com/jimboca/udi-poly-elk/issues

## Support

Please post any questions or issues to the sub-forum https://forum.universal-devices.com/forum/176-elk-node-server/ unless you know it's really a bug or enhancement then you can add it to https://github.com/jimboca/udi-poly-elk/issues


## Version History

- 0.1.8: Fix Logging level for Debug + elkm1_lib so you can see wha the ELK is sending
- 0.1.7: Fix crash during stop when config is not ready, fix startup when config is ready
- 0.1.6: [Don't start ELK when Configuration is not setup yet](https://github.com/jimboca/udi-poly-elk/issues/16)
- 0.1.5: [Add configuration option to say what Area's to add instead of including them all](https://github.com/jimboca/udi-poly-elk/issues/11)
- 0.1.4: Add check for Python Version >= 3.6
- 0.1.3: Add Area and Zone Bypass commands, don't send DON/DOF on startup.
- 0.1.2: Only send DON/DOFF when status actually changes.
- 0.1.0: Update to work with elkm1_lib 0.8.8 and more code cleanup.
