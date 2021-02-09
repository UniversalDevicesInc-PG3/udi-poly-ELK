# Polyglot V2 ELK Nodeserver

## Important Notices

I am not responsible for any issues related to this nodeserver including missing an alarm!

## Why use this when ISY has the ELK module?

The ELK Module will not be available on Polisy, the node server will be the supported method.

The node server also has advantages.  It creates a node for Areas, Zones, ... So you can put those nodes in scenes, or use them in programs just like any other node.

## Installation

Install from the Polyglot store.

### Configuration

Open the Configuration Page for the Nodeserver in the Polyglot UI and view the [Configuration Help](/POLYGLOT_CONFIG.md) available on that page.

After setting configuration then restart the nodeserver and all configured areas will be added.   There is a Node for each Area, and the Zone's for that area are grouped under it.  Sometimes the ISY fails to actually group some of the nodes, if you notices Zone's not grouped, then right click on it and select Group, which will fix them all.

## Requirements

This uses https://github.com/gwww/elkm1 which currently only supports an M1EXP in local non secure mode.

IF running on Raspberry Pi, you must be on the latest version, Buster with Python 3.6 or above, preferably 3.7.

## Using this Node Server

### General notes

If the Elk objects have characters in the name which are not allowed in ISY Node Names, those charcters will be stripped.

If you change a Elk object name it will not be automatically reflected on the ISY (currently).  You will have to delete the node in the Polyglot UI Node's page for the node server, then restart the node server.

If there is an alarm event, sending a "disarm" with the node server turns off the alarm, but does not reset it, just like when you do it at the Elk keypad.  You will have to send another "disarm" to reset it.  This is mentioned for users of UD Mobile who may want to disarm reset the sytem after an alarm.

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
    - Ready To Force Arm 
    - Armed With Exit Timer
    - Armed Fully
    - Force Armed
    - Armed With Bypass
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
- Poll Voltages
  - Enabled to poll the voltages on the Area's Zones.
- Zones Violated
  - The number of Zones currently violated
- Zones Bypassed
  - The number of Zones currently bypassed

#### Zone Node

Currently every Zone in the Area will be added as a Node if the Zone Definition is greater than Zero.  Nodes contain the following:
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
- Voltage
  - The current Zone Voltage.  Note this is not updated on change, it must be Polled.  By default this is polling is disabled, to enable set "Poll Voltages" on the Zone's Area.  The values are only updated on Short Poll intervals, which can be set in the Node Server Configuration Page.  It is also updated on a Zone query, so you can write ISY progrmas to force the query if you want faster updates, or just to update a single zone.
- Triggered
  - The zone has been manually triggered by a 3rd party app, or this app, when support is added.
  - True
  - False
- Area
  - The Area number the Zone is part of.
- Type
  - The Zone Type configured in the ELK, 37 different choices
- Send On For / Send Off For
  - Allow configuring of when the On and/or Off control signals are sent for the Zone Physical Status changes. This allows you to put the Node in a Scene and by default an On is sent when the Zone changes to Open, and an Off is sent when Zone changes to.  But this can be changed with these options:
    - Ignore
    - Open
    - EOL
    - Short
- Use Off Node
  - Setting this to True will create the Zone Off Node for this Zone, see Zone Off Node below for more information.

#### Zone Off Node

By default only a Zone node is created.  When you enable a Zone "Use Off Node" this will create another node for that Zone which is sent the "Off" commands.   This allows you to have separate nodes for On and Off so they can be in different Scenes if desired.

#### Output Node

There will be an Ouput node created for each Output you have listed in the outputs range.  The output is named based on the name in the Elk and has status (ST) showing On, Off, or Unknown.  The Unknown value should only happen when the output is first added until the Elk is queried to get the status.

When an Ouput is turned On or Off, a Control is also sent so you can put the node in a scene, or use Control in a ISY program.

When turning on an ELK output you can specify a time of zero which will keep the output on, or set the On Time to the number of seconds to wait before turning off.

## TODO and issues

https://github.com/jimboca/udi-poly-elk/issues

## Support

Please post any questions or issues to the sub-forum https://forum.universal-devices.com/forum/176-elk-node-server/ unless you know it's really a bug or enhancement then you can add it to https://github.com/jimboca/udi-poly-elk/issues


## Version History
- 0.4.2: 02/09/2021
  - [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
    - Fixed Output On/Off values
    - Fix crashed when outputs is null.
- 0.4.1: 02/08/2021
  - [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
    - Add missing Output.py file.
- 0.4.0: 02/07/2021
  - [Support Outputs and Virtual Outputs](https://github.com/jimboca/udi-poly-elk/issues/12)
- 0.4.0: 02/07/2021
  - [Add support for Zone voltage](https://github.com/jimboca/udi-poly-elk/issues/38)
    - Poll Voltages for Zones when Area Enables Poll Voltages setting.
- 0.3.2: 02/05/2021
  - [DOF not sent for EOL](https://github.com/jimboca/udi-poly-elk/issues/42)
    - Removed Send On/Off functionality
    - Added 'Send On For' default=Open 'Send Off For' default=EOL so users can control
- 0.3.1: 02/05/2021
  - Only wording changes for Arm Up State [Word Wrap Text Box](https://github.com/jimboca/udi-poly-elk/issues/44)
- 0.3.0: 02/04/2021
  - [Improve how violated/bypassed zones are counted](https://github.com/jimboca/udi-poly-elk/issues/40)
  - [Add support for Zone voltage](https://github.com/jimboca/udi-poly-elk/issues/38)
    - But currently on startup the voltage is always zero, it only updates occasionally when panel sync is done.
    - Asked on the elkm1_lib if this is a know issue [Voltage is not initialized on startup](https://github.com/gwww/elkm1/issues/40)
- 0.2.8: 01/29/2021
  - Update polyinterface requirement to latest.
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
