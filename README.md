# Polyglot V2 ELK Nodeserver

## Important Notices

I am not responsible for any issues related to this nodeserver including missing an alarm!

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

This has the following status:
- NodeServer Online
  - Nodeserver up and running
- ELK M1EXP Connected
  - Nodeserver is connected to the ELK
- Logger Level
  - Defines how much logging information is printed.

#### Area Node

By default only the area one, is added, change the areas configuraion if you have more than one.  The areas are 1-8, and the node names will match the names defined on your ELK.  They contain the following:
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
- Send On/Off
  - Allow configuring of when the On and/or Off control signals are sent for the Zone Physical Status changes. This allows you to put the Node in a Scene and by default an On is sent when the Zone changes to Open, and an Off is sent when Zone changes to SHORT or EOL.  But this can be changed with these options:
    - Send Both (The default)
    - Sond None
    - ON Only
    - OFF Only
    - Reverse Send Both (Send On for SHORT/EOL and Off for Open)
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

- 0.2.7: 01/21/2021
  - Fix logging when setting Zone ST & GV0
  - Change DON/DOF to Send On / Send Off in documentation and in nodeserver nls
  - [DOF not sent for EOL](https://github.com/jimboca/udi-poly-elk/issues/42)
    - Always send DOF for EOL and Short
- 0.2.6: 01/16/2021
  - Fix [All Zones in an Area are being added to ISY](https://github.com/jimboca/udi-poly-elk/issues/37)
- 0.2.5: 01/15/2021
  - Fix [Illegal characters or empty zone name issues](https://github.com/jimboca/udi-poly-elk/issues/35)
- 0.2.4: 01/14/2021
  - Fix [Illegal characters or empty zone name issues](https://github.com/jimboca/udi-poly-elk/issues/35)
  - Change logical and physical status [Logical vs Physical State](https://github.com/jimboca/udi-poly-elk/issues/34)
  - Fix [Don't print Unknown message EM errors](https://github.com/jimboca/udi-poly-elk/issues/30)
- 0.2.3: 01/05/2021
  - Fix profile
- 0.2.2: 01/04/2021
  - Add better logging to see what is happening
- 0.2.1: 01/04/2021
  - Add BaseNode so all nodes use common set/get driver methods for consistency and debugging aid
- 0.2.0: 12/26/2020
  - __IMPORTANT__ All Area and Zone node address will change, either delete them all in Polyglot UI or delete the nodeserver and add again
    - [Area and Zone numbers should match ELK numbers](https://github.com/jimboca/udi-poly-elk/issues/21)
    - Make sure to re-sync the ISY UDMobile App as well after re-adding
  - Fix [https://github.com/jimboca/udi-poly-elk/issues/26](Bypass button on zone node screen)
  - Fix [https://github.com/jimboca/udi-poly-elk/issues/25](Tracking of number of bypassed zones in area inconsisten)
- 0.1.9: 12/18/2020
  - Fix issues caused when sync_complete is called multiple times 
    - [Multiple changes happening after restarting Nodeserver](https://github.com/jimboca/udi-poly-elk/issues/18)
- 0.1.8: Fix Logging level for Debug + elkm1_lib so you can see wha the ELK is sending
- 0.1.7: Fix crash during stop when config is not ready, fix startup when config is ready
- 0.1.6: [Don't start ELK when Configuration is not setup yet](https://github.com/jimboca/udi-poly-elk/issues/16)
- 0.1.5: [Add configuration option to say what Area's to add instead of including them all](https://github.com/jimboca/udi-poly-elk/issues/11)
- 0.1.4: Add check for Python Version >= 3.6
- 0.1.3: Add Area and Zone Bypass commands, don't send DON/DOF on startup.
- 0.1.2: Only send DON/DOFF when status actually changes.
- 0.1.0: Update to work with elkm1_lib 0.8.8 and more code cleanup.
