


NODE_DEF_MAP = {
    'area': {
        'GV0': {
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
        'ST': {
            'name': 'Physical Status',
            'nls':  'ZPST',
            'keys': {
                -1:  'Unknown',
                 0:  'Unconfigured',
                 1:  'Open',
                 2:  'EOL',
                 3:  'SHORT',
            }
        },
        'GV0': {
            'name': 'Logical Status',
            'nls':  'ZLST',
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
