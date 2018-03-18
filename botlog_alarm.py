import time
import json
from logwatcher import *
from slacker import Slacker
import ConfigParser
import io

Config = ConfigParser.ConfigParser()
Config.read('botlog.ini')
LogDir = Config.get('General', 'LogDir')
BotLogFile = Config.get('AlarmBot', 'BotLogFile')

SlackToken = Config.get('Slack', 'APIToken')
SlackSecurityChannel = Config.get('Slack', 'Channel')
SlackUser = Config.get('AlarmBot', 'SlackUser')
SlackAlarmChannel = Config.get('AlarmBot', 'SlackChannel')

DEBUG = Config.getboolean('General', 'Debug')

BotList = Config.items('Bots')
BotDict = {}
for tup in BotList:
    key = tup[0]
    BotDict[key] = tup[1]

# -----------------------------------------------------------------

tail_text = '%s monitor online.  Most recent messages below:\n' % (SlackUser)

def sendMsg(channel, timestamp, color, fallback, text):
    if timestamp == 'now':
        timestamp = time.strftime('%B %d %H:%M:%S %Z', time.localtime())

    attachments = []
    attachment_data = { 'fallback': fallback, 'color': color, 'text': text, 'mrkdwn_in':['text', 'pretext'] }
    attachments.append(attachment_data)

    slack.chat.post_message(channel, '_' + timestamp + '_', username=SlackUser, attachments=json.dumps(attachments))

    if DEBUG:
        print fallback
        print text



def callback(filename, lines, tailing):
    global tail_text

    if DEBUG:
        print 'callback ' + filename + ' is tailing ' + str(tailing)

    if filename == BotLogFile:
        if tailing and (lines == None):
            # finished tailing
            
            # send a startup message
            sendMsg(SlackAlarmChannel, 'now', '#439FE0', '%s monitor online' % (SlackUser), tail_text)
            sendMsg(SlackSecurityChannel, 'now', '#439FE0', '%s monitor online' % SlackUser, '%s monitor online' % SlackUser)
            return

        for line in lines:
            # Mar 16 12:33:54 alarmdecoder gunicorn[517]: --------------------------------------------------------------------------------
            # Mar 16 12:33:54 alarmdecoder gunicorn[517]: DEBUG in types [/opt/alarmdecoder-webapp/ad2web/notifications/types.py:260]:
            # Mar 16 12:33:54 alarmdecoder gunicorn[517]: Event: Zone <unnamed> (8) has been faulted.
            # Mar 16 12:33:54 alarmdecoder gunicorn[517]: --------------------------------------------------------------------------------
            # Mar 16 12:33:57 alarmdecoder gunicorn[517]: --------------------------------------------------------------------------------
            # Mar 16 12:33:57 alarmdecoder gunicorn[517]: DEBUG in types [/opt/alarmdecoder-webapp/ad2web/notifications/types.py:260]:
            # Mar 16 12:33:57 alarmdecoder gunicorn[517]: Event: Zone <unnamed> (8) has been restored.
            # Mar 16 12:33:57 alarmdecoder gunicorn[517]: --------------------------------------------------------------------------------
            # 0   1  2        3            4              5     ...
            try:
                fields = line.split()
            
                if DEBUG:
                    print len(fields)
                    print fields
                

                month = fields[0]
                day = fields[1]
                timehms = fields[2]
                timeparsed = time.strptime(month + ' ' + day + ' ' + timehms, '%b %d %H:%M:%S')
                timestamp = time.strftime('%B %d %H:%M:%S %Z', timeparsed)

                host = fields[3]
                if host in BotDict:
                    location = BotDict[host]

                    if (len(fields) >= 5) and (fields[5] == "Event:"):
                        desc = ' '.join(fields[6:])

                        fallback_msg = timestamp + ' ' + desc
                        full_msg = '*' + desc + '*'

                        color = '#000000'
                        if 'faulted' in desc:
                            color = 'warning'
                        elif 'restored' in desc:
                            color = 'good'

                        if tailing:
                            tail_text += '> _' + timestamp + '_ '  + full_msg + '\n'
                        else:
                            sendMsg(SlackAlarmChannel, timestamp, color, fallback_msg, full_msg)

                        if 'has been armed' in desc or 'has been disarmed' in desc:
                            sendMsg(SlackSecurityChannel, timestamp, color, fallback_msg, full_msg)
                            
                    else:
                        # random messages that are not parseable
                        pass
                else:
                    fallback_msg = 'Unknown bot logging to syslog.'
                    full_msg = '*Unknown bot* logging to syslog.'

                    if tailing:
                        tail_text += '> _' + timestamp + '_ ' + full_msg + '\n'
                    else:
                        sendMsg(SlackAlarmChannel, timestamp, 'warning', fallback_msg, full_msg)
                        
            except:
                if DEBUG:
                    print "parse error:"
                    print line


# init slack
slack = Slacker(SlackToken)

# start the log watcher
watcher = LogWatcher('/var/log/', callback, tail_lines=20)
watcher.loop()
