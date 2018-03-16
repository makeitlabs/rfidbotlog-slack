# Botlogs

This is a collection of quick hack scripts which run on a central log server that receives messages from remote nodes on our LAN that perform various security and access-control related tasks.  The host system is configured to receive syslog messages via rsyslog, and these scripts parse those logs in realtime and do various things such as post Slack messages, trigger a welcome sign-in station, trigger camera recording, etc.

## botlog.py
Doorbots log to a central server running rsyslogd.  This program watches the logfile in realtime, parses out access attempts, and posts them to slack on a configurable channel.

## botlog_nxwitness.py
Similar, but instead of Slack it POSTs accesses as events to our NXWitness camera server.

## botlog_tablet.py
Similar, but instead of Slack, it POSTs accesses to the "welcome" touchscreen display application at the front door.

## botlog_alarm.py
A bit different in that it watches a log file from our alarmdecoder Pi that is running rsyslogd.  It posts alarm events to a configurable Slack channel.



