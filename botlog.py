import time
import json
from logwatcher import *
from slacker import Slacker
import ConfigParser
import io

Config = ConfigParser.ConfigParser()
Config.read('botlog.ini')
LogDir = Config.get('General', 'LogDir')
BotLogFile = Config.get('General', 'BotLogFile')

SlackToken = Config.get('Slack', 'APIToken')
SlackChannel = Config.get('Slack', 'Channel')
SlackUser = Config.get('Slack', 'User')
DEBUG = Config.getboolean('General', 'Debug')

BotList = Config.items('Bots')
BotDict = {}
for tup in BotList:
    key = tup[0]
    BotDict[key] = tup[1]

# -----------------------------------------------------------------

tail_text = 'RFIDBot monitor online.  Most recent messages below:\n'

def sendMsg(timestamp, color, fallback, text):
    if timestamp == 'now':
        timestamp = time.strftime('%B %d %H:%M:%S %Z', time.localtime())

    attachments = []
    attachment_data = { 'fallback': fallback, 'color': color, 'text': text, 'mrkdwn_in':['text', 'pretext'] }
    attachments.append(attachment_data)

    slack.chat.post_message(SlackChannel, '_' + timestamp + '_', username=SlackUser, attachments=json.dumps(attachments))

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
            sendMsg('now', '#439FE0', 'RFIDBot monitor online', tail_text)
            return

        for line in lines:
            # ['Jan', '13', '10:33:36', '10.0.0.50', ':', 'adam.shrey', 'allowed']
            # 2016-01-09 16:22:50,002 WARNING Unknown card 1234123 
            fields = line.split()

            if DEBUG:
                print fields

            month = fields[0]
            day = fields[1]
            timehms = fields[2]
            timeparsed = time.strptime(month + ' ' + day + ' ' + timehms, '%b %d %H:%M:%S')
            timestamp = time.strftime('%B %d %H:%M:%S %Z', timeparsed)

            host = fields[3]
            if host in BotDict:
                location = BotDict[host]

                if ("allowed" in fields[6]) or ("DENIED" in fields[6]):
                    perm = fields[6]
                    user = fields[5]

                    fallback_msg = timestamp + ' ' + user + ' ' + perm + ' at ' + location
                    full_msg = '*' + user + '* ' + perm + ' at ' + location

                    color = 'good'
                    if "DENIED" in perm:
                        color = 'warning'

                    if tailing:
                        tail_text += '> _' + timestamp + '_ '  + full_msg + '\n'
                    else:
                        sendMsg(timestamp, color, fallback_msg, full_msg)

                elif "Unknown" in fields[5]:

                    fallback_msg = timestamp + ' Unknown RFID key at ' + location
                    full_msg = '*Unknown RFID key* at ' + location

                    if tailing:
                        tail_text += '> _' + timestamp + '_ ' + full_msg + '\n'
                    else:
                        sendMsg(timestamp, 'danger', fallback_msg, full_msg)
            else:
                fallback_msg = 'Unknown bot logging to syslog.'
                full_msg = '*Unknown bot* logging to syslog.'

                if tailing:
                    tail_text += '> _' + timestamp + '_ ' + full_msg + '\n'
                else:
                    sendMsg(timestamp, 'warning', fallback_msg, full_msg)
                    


# init slack
slack = Slacker(SlackToken)

# start the log watcher
watcher = LogWatcher('/var/log/', callback, tail_lines=20)
watcher.loop()
