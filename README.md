# udi-SpanIO -  for Polyglot v3 

## SpanIO power Panel Node server
# udi-TeSpanIO  -  for Polyglot PG3x
## SpanIO Node server

This node server enables , monitors and controls of one or more SpanIO power panels in a system.
The nodes uses an unofficial derived API for local access to the panel - documentation exist at https://gist.github.com/hyun007/c689fbed10424b558f140c54851659e3 although it is not 100% up to date.

The node creates a separate node used to show the node is running and the number of SpanIO panels in the system.  Each panel is instantiated as a main node (named as IP address without '.'s).  Each group (one or more breakers) are created as a sub-note.  The node allows opening and closing the breaker (relay in the panel - not the main breaker).  The API supposedly supports changing the priority of the breaker, but in generates an internal error, so it is not exposed t user
The configuration takes a list of IP addresses (space separated) - Only use 1 per panel (ideally ethernet if available).  It is important that the IP address does not change.  There is also a flag to enable reading of a backup battery (percentage) if supported 

The nodes provides power consumption data, breaker state as well as some connection status information.  Exported Energy 

## Installation
To register the panel(s), one must start the node and then go to the panel, open the door and press the door contact (upper corner) 3 times (quickly) - the panel should then blink the light and it will go into register mode. Do this for all panels if more than 1 panel is installed 

After this nodes will be generated and til will start operating.   

## Notes 
The node has not been tested with ore than 1 SpanIO panel - there are likely bugs
Power on the breaker results in 2 numbers a for energy - Exported and Imported (Exported is exported from breaker panel to house circuits) - Imported energy is a return flow (My guess)
Energy last Hour/Day will not show data until the node has been running for a hour/day

shortPoll updates critical parameters and issues a heartbeat for each panel(Connection to grid and battery % - no update on circuits) 
longPoll updates all data for each panel 


