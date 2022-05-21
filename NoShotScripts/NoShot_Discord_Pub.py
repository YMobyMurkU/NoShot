#requirements
#Use pip or similar to install: requests tailer
import sys
from pathlib import Path
import requests
import tailer


#function to post 
def PostDiscordMessage(channelWebHook, logEvent):
    #set message content
    jsonData = {'content' : '{}'.format(logEvent)}
    #create discord message post request
    discordResponse = requests.post(channelWebHook, json=jsonData)
    #get status code of post request
    responseCode = int((discordResponse.status_code))
    # if response code = 204 (success) print success msg to console
    if responseCode == 204:
        print(f'Success Posting Message: {logEvent}')
    #else print failure msg to console
    else:
        print(f'Failure Posting Message: {logEvent}')


def watch_log(logFile):
    #for each line in log file - note this begins with NEW data sent AFTER program is started
    lastLogEvent = ""
    for logEvent in tailer.follow(open(logFile)):
        try:
            #calls Post Discord Msg function with the channel's webhook and the log file's line
            if str(logEvent) != str(lastLogEvent):
                logEventSplit = logEvent.split(',')
                lastLogEventSplit = lastLogEvent.split(',')
                try:
                    if int(logEventSplit[2]) > int(lastLogEventSplit[2]):
                        if abs(int(logEventSplit[2]) - int(lastLogEventSplit[2])) >= 1:
                            logMessage = (f'ALERT: System: {logEventSplit[0]} | Hostile: {logEventSplit[2]} | Neutral: {logEventSplit[3]} | Criminal: {logEventSplit[1]}\n@here')
                            PostDiscordMessage(channelWebHook, f'{logMessage}')
                        else:
                            logMessage = (f'System: {logEventSplit[0]} | Hostile: {logEventSplit[2]} | Neutral: {logEventSplit[3]} | Criminal: {logEventSplit[1]}\n')
                            PostDiscordMessage(channelWebHook, f'{logMessage}')
                except IndexError:
                    continue
                    #print(f'Started Log Monitor for {logEventSplit[0]}')
                lastLogEvent = logEvent
        except KeyboardInterrupt:
            print('TERMINATING: NoShot Discord Services')


if __name__ == '__main__':
    cmdArgs = (sys.argv)
    logFile = cmdArgs[1]
    #print(logFile)
    channelWebHook = cmdArgs[2]
    #print(channelWebHook)
    logReport = watch_log(logFile)
