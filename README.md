# botlog.py
RFIDBots log to a central server running rsyslogd.  This program watches the logfile in realtime, parses out access attempts, and posts them to slack
on a configurable channel.

# botlog_tablet.py
Similar to above but POSTs accesses to the "welcome" touchscreen display application at the front door.
