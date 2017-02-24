import time
import json
from logwatcher import *
import ConfigParser
import io
import requests

Config = ConfigParser.ConfigParser()
Config.read('botlog.ini')
LogDir = Config.get('General', 'LogDir')
BotLogFile = Config.get('General', 'BotLogFile')

Server = Config.get('WelcomeBot', 'Server')
ServerPort = Config.get('WelcomeBot', 'ServerPort')

DEBUG = Config.getboolean('General', 'Debug')

BotList = Config.items('Bots')
BotDict = {}
for tup in BotList:
    key = tup[0]
    BotDict[key] = tup[1]

# -----------------------------------------------------------------

tail_text = 'RFIDBot monitor online.  Most recent messages below:\n'

def sendMsg(timestamp, user,perm):
    '''Send an allowed or denied message'''
    if timestamp == 'now':
        timestamp = time.strftime('%B %d %H:%M:%S %Z', time.localtime())

    # Send Message
    uri = 'http://' + Server + ':' + ServerPort + '/ping/'
    msg = uri + user + '/' + perm
    if DEBUG:
        print(msg)
    r = requests.get(msg)

def callback(filename, lines, tailing):
    global tail_text

    if DEBUG:
        print 'callback ' + filename + ' is tailing ' + str(tailing)

    if filename == BotLogFile:
        if tailing and (lines == None):
            # finished tailing
            
            # send a startup message
            #sendMsg('now', '#439FE0', 'RFIDBot monitor online', tail_text)
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

                if ("allowed" in fields[6]):
                    perm = fields[6]
                    user = fields[5]

                    full_msg = '*' + user + '* ' + perm + ' at ' + location

                    if tailing:
                        tail_text += '> _' + timestamp + '_ '  + full_msg + '\n'
                    else:
                        sendMsg(timestamp, user, perm)

                elif "Unknown" in fields[5]:

                    full_msg = '*Unknown RFID key* at ' + location

                    if tailing:
                        tail_text += '> _' + timestamp + '_ ' + full_msg + '\n'
                    else:
                        #sendMsg(timestamp, 'danger', fallback_msg, full_msg)
			print('Danger ' + full_msg)
            else:
                full_msg = '*Unknown bot* logging to syslog.'

                if tailing:
                    tail_text += '> _' + timestamp + '_ ' + full_msg + '\n'
                else:
                    #sendMsg(timestamp, 'warning', fallback_msg, full_msg)
		    print(full_msg)
                    


# start the log watcher
watcher = LogWatcher('/var/log/', callback, tail_lines=20)
watcher.loop()
