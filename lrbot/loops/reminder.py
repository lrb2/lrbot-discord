import asyncio
import time
import logging
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
    if reminderModified:
        # Remove reminders that will not reoccur (nextRun has passed and was not updated)
        rm.reminders[:] = [reminder for reminder in rm.reminders if reminder['nextRun'] > currentTime]
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
    
    currentTime = time.time()
    # On startup, do NOT process reminder reminders that have passed
    reminderModified = False
    for reminder in rm.reminders:
        if 'conditions' in reminder and reminder['nextRun'] <= currentTime:
            # Update the reminder with the next run timestamps
            reminder = await rm.updateNextRun(reminder)
            reminderModified = True
    if reminderModified:
        logger = logging.getLogger('discord.lrbot-reminders')
        logger.warning('One or more reminder reminders were skipped since they have already passed')
        # Remove reminders that will not reoccur (nextRun has passed and was not updated)
        rm.reminders[:] = [reminder for reminder in rm.reminders if reminder['nextRun'] > currentTime]
        rm.save()

    # Repeat the main function indefinitely
    while True:
        await main(rm)