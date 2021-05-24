

NODE_DEF_MAP = {
    'area': {
        'ST': {
            'name':    'Armed Status',
            'nls':     'ASTATUS',
            'keys': {
                -1: 'Unknown',
                0:  'Disarmed',
                1:  'Armed Away',
                2:  'Amred Stay',
                3:  'Armed Stay Instant',
                4:  'Armed Night',
                5:  'Armed Niget Instant',
                6:  'Armed Vacation',
                7:  'Armed next Away Mode',
                8:  'Amred next Stay Mode',
                9:  'Force Arm to Away Mode',
                10: 'Force Arm to Stay Mode'
            }
        },
        'GV0': {
            'name':    'Alarm State',
            'nls':     'ALARM',
            'keys': {
                -1: 'Unknown',
                0:  'No Alarm Active',
                1:  'Entrance Delay is Active',
                2:  'Alarm Abort Delay Active',
                3:  'Fire Alarm',
                4:  'Medical Alarm',
                5:  'Police Alarm',
                6:  'Burglar Alarm',
                7:  'Aux 1 Alarm',
                8:  'Aux 2 Alarm',
                9:  'Aux 3 Alarm',
                10: 'Aux 4 Alarm',
                11: 'Carbon Monoxide Alarm',
                12: 'Emergency Alarm',
                13: 'Freeze Alarm',
                14: 'Gas Alarm',
                15: 'Heat Alarm',
                16: 'Water Alarm',
                17: 'Fire Supervisory',
                18: 'Verify Fire'
            }
        },
        'GV1': {
            'name':   'Arm Up State',
            'nls':    'ARMUP',
            'keys': {
                -1:  'Unknown',
                 0:  'Not Ready To Arm',
                 1:  'Ready To Arm',
                 2:  'Ready To Arm, but a zone violated and can be Force Armed',
                 3:  'Armed with Exit Timer working',
                 4:  'Armed Fully',
                 5:  'Force Armed with a force arm zone violated',
                 6:  'Armed with a bypass'
            }
        },
        'GV3': {
            'name':   'Violated Count',
            'uom':    56,
        },
        'GV4': {
            'name':   'Bypassed Count',
            'uom':    56,
        }
    },
    'zone': {
        'GV0': {
            'name': 'Physical Status',
            'nls':  'ZLST',
            'keys': {
                -1:  'Unknown',
                 0:  'Unconfigured',
                 1:  'Open',
                 2:  'EOL',
                 3:  'SHORT',
            }
        },
        'GV1': {
            'name': 'Triggered Alarm',
            'nls':  '',
            'keys': {
                 0:  'False',
                 1:  'True',
            }
        },
        'ST': {
            'name': 'Logical Status',
            'nls':  'ZPST',
            'keys': {
                -1:  'Unknown',
                0:  'Normal',
                1:  'Trouble',
                2:  'Violated',
                3:  'Bypassed',
            }
        }
    }
}
