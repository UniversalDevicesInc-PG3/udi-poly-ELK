
# To Configure the ELK Nodeserver

- Set temperature_unit to F or C
- Set host to the host or ip address and port, e.g. 192.168.1.15:2101
- Set a user code, suggested to create a unique usercode for this NodeServer
- Set areas to the range of areas you would like to include
- Set outputs to the range of outputs to include

A range can be comma seperated to include just those numbers, or seperated with a dash to include numbers in between.  For example 1-3,5,7-8 will be 1,2,3,5,7,8
All ranges start at one just like the numbering the Elk uses.

Note that if you remove an Area, it will not be removed from the ISY or Polyglot.  This is intentional just in case it's an accident and you scenes or programs the reference the nodes.  You can go to the Nodes Page in the Polyglot UI and delete them using the X to the right of the node.

When any value is changed you must restart the nodeserver for it to take affect.
