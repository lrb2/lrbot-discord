import asyncio
import datetime
import discord
import math
import time
import lrbot.config
import lrbot.response
from lrbot.remindermgr import ReminderManager

async def main(rm: ReminderManager) -> None:
    currentTime = time.time()
    # Check for reminders that are due or have passed
    reminderModified = False
    for reminder in rm.reminders:
        if reminder['nextRun'] <= currentTime:
            # Process the reminder
            await rm.runActions(reminder)
            # Update the reminder with the next run timestamps
            reminder = await rm.updateNextRun(reminder)
            reminderModified = True
    
    # Remove reminders that will not reoccur (nextRun has passed and was not updated)
    if reminderModified:
        #rm.reminders[:] = [reminder for reminder in rm.reminders if reminder['nextRun'] > currentTime]
        rm.save()

    # Find next soonest run
    sleepUntil = min((reminder['nextRun'] for reminder in rm.reminders), default = None)
    sleepTime = 60*60 if sleepUntil is None else sleepUntil - time.time()
    if sleepTime < 60*60:
        # Sleep until the next run
        await asyncio.sleep(sleepTime)
    else:
        # Re-check hourly
        await asyncio.sleep(60*60)
    return
        

async def run(rm: ReminderManager) -> None:
    #try:
        # Repeat the main function indefinitely
    while True:
        await main(rm)
    #except:
        #await lrbot.response.sendResponse(
        #    (await rm.client.fetch_user(int(lrbot.config.settings['owner']))),
        #    'An error has been caught in the reminder loop. The reminder loop is suspended until the container is restarted.'
        #)
        #return