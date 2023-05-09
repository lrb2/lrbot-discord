import asyncio
import datetime
import discord
import math
import time
import lrbot.config
import lrbot.response
from discord.ext import commands
from lrbot.cogs.reminders import Reminders

async def main(rm: Reminders) -> None:
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
        

async def run(bot: commands.Bot) -> None:
    rm: Reminders = bot.get_cog('Reminders')
    
    # Repeat the main function indefinitely
    while True:
        await main(rm)