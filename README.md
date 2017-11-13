# R5PSQmon
Responder 5 paging server queue monitor

*note this script is not supported by the vendor Rauland Borg and was custom developed to log /triage application issues such as 
message queue buildup.  From this script we have logged and tracked issues to determine that the default Responder 5
paging service will only support an approximate 38 message/min throughput.  This is not robust enough to support
large installations.  See the xml2tap application for a custom solution to overcome these issues.

This python script is meant to be run from the Responder 5 paging server on a periodic basis using a task scheduler. 

It provides the following features:
email a monitoring mailbox
email a support team
log values to a mysql database
provide a monitoring page for load balancing failover or url monitoring agents.

When scheduled it will read the default Responder 5 paging server webpage and parse out the current queue value.
It will compare the current parsed queue value with the last queue value to make a determination if the queue seems to be stalled.

It will email a monitor mailbox as well as a support team mailbox for issues.

It also has a status page that needs to be setup in the following folder:
C:/inetpub/wwwroot/r5pagemonitor/Default.htm

This status page can be used to automatically failover for a load balancer as well as be monitoring by url monitoring agents.

The following are the status page states:

ERROR: Paging Service is Down
ERROR: Paging Q hung with value: X
ERROR: Paging Q overloaded with value: X
OK: Paging Q value: X

The mysql database will need the following setup:
#tablename = r5psq
#Column definitions:
#ID int(11)
#ServerName varchar(45)
#QValue int(11)
#timestamp datetime (default value of CURRENT_TIMESTAMP)


