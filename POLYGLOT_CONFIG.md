
# To Configure the ELK Nodeserver

- Set host to the host or ip address and port, e.g. 192.168.1.15:2101
- Set a user code, suggested to create a unique usercode for this NodeServer
- Set areas to the range of areas you would like to include

A range can be comma seperated to include just those numbers, or seperated with a dash to include numbers in between.  For example 0-2,4,6-7 will be 0,1,2,4,6,7
All ranges are zero based in the nodeserver, unlike the ELK which starts as one.  This is to match the decision made in the elkm1_lib.  I'm still not sure if I like that, but I wanted to stay consistent with the library.

Note that if you remove an Area, it will not be removed from the ISY or Polyglot.  This is intentional just in case it's an accident and you scenes or programs the reference the nodes.  You can go to the Nodes Page in the Polyglot UI and delete them using the X to the right of the node.
