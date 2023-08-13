
# To Configure the ELK Nodeserver

## Custom Configuration Parameters

- Set `temperature_unit` to F or C
- Set `host` to the host or ip address and port, e.g. 192.168.1.15:2101
- Set `user_code`, suggested to create a unique usercode for this NodeServer
- Set `areas` to the range of areas you would like to include
- Set `outputs` to the range of outputs to include
- Set `change_node_names` to true makes ELK the source of node names so if they are changed then ISY names will be changed to match.
- Set `light_method` to ELKID to check for ELKID=n on ISY Nodes, or ELKNAME to check if the Elk Light Name matches and ISY Node name or address.
  - ELKALL
    - This creates an ISY Light node for every definded Light node on the ELk
  - ELKID
    - This works by right-clicking on a node in the ISY and adding a note with "ELKID=n" where n is a unique integer
    - After changing to ELKID method, you must wait until you see "Export Completed" warning message in the Log.
    - Then click on the "export" like provided below
    - If you change an ELKID on a node then you must restart the nodeserver for it to be seen.
  - ELKNAME
    - This attempts to match the name of an ISY Node with the Name of an ELK Light node to control. The table on this page will show the matches.

Note that if you remove an Area, it will not be removed from the ISY or Polyglot.  This is intentional just in case it's an accident and your scenes or programs reference the nodes.  

If you change light_method from ELKALL to another method, the Light nodes will not be removed.

You can go to the Nodes Page in the Polyglot UI and delete leftover nodes from changing ranges or light_method using the X to the right of the node.

### Ranges
A range can be comma seperated to include just those numbers, or seperated with a dash to include numbers in between.  For example 1-3,5,7-8 will be 1,2,3,5,7,8
All ranges start at one just like the numbering the Elk uses.





