import calendar
import datetime
import discord
import json
import logging
import re
import time
import traceback
import zoneinfo
import lrbot.response
from discord.ext import commands

class Reminders(commands.Cog):
    bot = None
    botId = None
    logger = logging.getLogger('discord.lrbot-reminders')
    reminders = dict()
    file = open(r'config/reminders.json', 'r+')
    
    def __init__(self, bot: commands.Bot) -> None:
        self.load()
        self.bot = bot
        self.botId = bot.user.id
        return

    def load(self) -> None:
        '''
        Updates reminders with the latest changes from the file.
        '''
        self.file.seek(0)
        self.reminders = json.load(self.file)
        self.logger.info('Reminders dict updated from file')
        return

    def save(self) -> None:
        '''
        Updates the reminders file with the latest changes.
        '''
        self.file.seek(0)
        json.dump(self.reminders, self.file)
        self.file.truncate()
        self.logger.info('Reminders dict saved to file')
        return

    async def runActions(self, reminder: dict) -> None:
        '''
        Runs the action defined by the reminder.
        '''
        for action in reminder['actions']:
            try:
                await lrbot.response.runAction(action, self.bot)
            except Exception as error:
                tbStr = ''.join(traceback.format_tb(error.__traceback__))
                self.logger.error(f'Uncaught exception: {type(error)} {error}\n{tbStr}')
        return

    async def updateNextRun(self, reminder: dict, skip: bool = False) -> dict:
        '''
        Updates the nextRun and nextCheck values in the provided reminder to the next valid occurrence.
        Next run times will be updated up to the next occurrence past the current time. 
        '''
        nextRun = None
        
        currentTime = time.time()
        targetTimestamp = max(reminder['nextRun'], currentTime) if skip == True else currentTime
        
        for pattern in reminder['repeat']:
            try:
                # Only update next run if it has passed
                while pattern['nextRun'] <= targetTimestamp:
                    tz = zoneinfo.ZoneInfo(pattern['tz'])
                    # All timestamps are stored in UTC; convert datetime object to specified time zone for logic
                    lastRunDate = datetime.datetime.fromtimestamp(
                        pattern['nextRun'],
                        tz = datetime.timezone.utc
                    ).astimezone(tz)
                    nextRunDate = lastRunDate
                    nextRunTimestamp = None
                    
                    # Check if another occurrence this day
                    if len(pattern['times']) > 1:
                        lastRunTimeDict = {
                            'h': lastRunDate.hour,
                            'm': lastRunDate.minute,
                            's': lastRunDate.second
                        }
                        lastRunTimeIndex = pattern['times'].index(lastRunTimeDict)
                        nextRunTimeIndex = lastRunTimeIndex + 1
                        if nextRunTimeIndex < len(pattern['times']):
                            # There should be another time today
                            nextRunDate = nextRunDate.replace(
                                hour = pattern['times'][nextRunTimeIndex]['h'],
                                minute = pattern['times'][nextRunTimeIndex]['m'],
                                second = pattern['times'][nextRunTimeIndex]['s']
                            )
                            nextRunTimestamp = nextRunDate.timestamp()
                    
                    # Get the next day if daily
                    if not nextRunTimestamp and pattern['period'] == 'day':
                        # Set day to the next day
                        nextRunDate += datetime.timedelta(days = pattern['every'])
                        # Set time to the earliest time
                        nextRunDate = nextRunDate.replace(
                            hour = pattern['times'][0]['h'],
                            minute = pattern['times'][0]['m'],
                            second = pattern['times'][0]['s']
                        )
                        nextRunTimestamp = nextRunDate.timestamp()
                    
                    # Check for another day this week or month
                    if not nextRunTimestamp and len(pattern['days']) > 1:
                        if pattern['period'] == 'week':
                            # Check for another day this week
                            lastRunDay = lastRunDate.weekday()
                        else:
                            # Check for another day this month
                            lastRunDay = lastRunDate.day
                        # Make sure that days are sorted ascending
                        pattern['days'].sort()
                        # Get index of the current day
                        lastRunDayIndex = pattern['days'].index(lastRunDay)
                        nextRunDayIndex = lastRunDayIndex + 1
                        if nextRunDayIndex < len(pattern['days']):
                            # There should be another day this week or month
                            # If the period is weekly or the day exists in the month
                            if (
                                pattern['period'] == 'week' or
                                pattern['days'][nextRunDayIndex] < calendar.monthrange(lastRunDate.year, lastRunDate.month)[1]
                            ):
                                # Set day to the next day
                                nextRunDate += datetime.timedelta(days = pattern['days'][nextRunDayIndex] - lastRunDay)
                                # Set time to the earliest time
                                nextRunDate = nextRunDate.replace(
                                    hour = pattern['times'][0]['h'],
                                    minute = pattern['times'][0]['m'],
                                    second = pattern['times'][0]['s']
                                )
                                nextRunTimestamp = nextRunDate.timestamp()
                    
                    # Check for another month this year
                    if not nextRunTimestamp and 'months' in pattern and len(pattern['months']) > 1:
                        lastRunMonth = lastRunDate.month
                        # Make sure that months are sorted ascending
                        pattern['months'].sort()
                        # Get index of the current month
                        lastRunMonthIndex = pattern['months'].index(lastRunMonth)
                        nextRunMonthIndex = lastRunMonthIndex + 1
                        if nextRunMonthIndex < len(pattern['months']):
                            # There should be another month this year
                            nextRunMonth = pattern['months'][nextRunMonthIndex]
                            # Ensure that the earliest day exists in the next month
                            while (
                                nextRunMonthIndex < len(pattern['months']) and
                                pattern['days'][0] > calendar.monthrange(lastRunDate.year, nextRunMonth)[1]
                            ):
                                # The day does not exist in the month, skip to next
                                nextRunMonthIndex + 1
                                nextRunMonth = pattern['months'][nextRunMonthIndex]
                            if nextRunMonthIndex < len(pattern['months']):
                                # Set month to the next month
                                # Set day and time to their earliest values
                                nextRunDate = nextRunDate.replace(
                                    month = pattern['months'][nextRunMonthIndex],
                                    day = pattern['days'][0],
                                    hour = pattern['times'][0]['h'],
                                    minute = pattern['times'][0]['m'],
                                    second = pattern['times'][0]['s']
                                )
                                nextRunTimestamp = nextRunDate.timestamp()
                    
                    # The only other option is another period!
                    if not nextRunTimestamp:
                        # Go to first run this period
                        if pattern['period'] == 'week':
                            lastRunDay = lastRunDate.weekday()
                            # Set day to the first day
                            nextRunDate -= datetime.timedelta(days = lastRunDay - pattern['days'][0])
                            # Add the specified number of weeks
                            nextRunDate += datetime.timedelta(weeks = pattern['every'])
                        else:
                            # Get the next year and month
                            nextYear = lastRunDate.year
                            nextMonth = lastRunDate.month
                            while True:
                                match pattern['period']:
                                    case 'year':
                                        nextYear += pattern['every']
                                    case 'month':
                                        nextMonth += pattern['every']
                                        while nextMonth > 12:
                                            nextYear += 1
                                            nextMonth -= 12
                                # Ensure that the earliest day exists within the month
                                if pattern['days'][0] <= calendar.monthrange(nextYear, nextMonth)[1]:
                                    # OK
                                    break
                                elif pattern['period'] == 'year' and len(pattern['months']) > 1:
                                    # Find the next valid month in the next year
                                    monthFound = False
                                    for month in pattern['months']:
                                        if pattern['days'][0] <= calendar.monthrange(nextYear, month)[1]:
                                            nextMonth = month
                                            monthFound = True
                                            break
                                    if monthFound:
                                        break
                            # Set date, and set time to the earliest time
                            nextRunDate = nextRunDate.replace(
                                year = nextYear,
                                month = nextMonth,
                                day = pattern['days'][0],
                                hour = pattern['times'][0]['h'],
                                minute = pattern['times'][0]['m'],
                                second = pattern['times'][0]['s']
                            )
                            
                        # Set time to the earliest time
                        nextRunDate = nextRunDate.replace(
                            hour = pattern['times'][0]['h'],
                            minute = pattern['times'][0]['m'],
                            second = pattern['times'][0]['s']
                        )
                        nextRunTimestamp = nextRunDate.timestamp()
                    
                    pattern['nextRun'] = nextRunTimestamp
            except Exception as error:
                tbStr = ''.join(traceback.format_tb(error.__traceback__))
                self.logger.error(f'Uncaught exception: {type(error)} {error}\n{tbStr}')
            
            if (
                not (
                    'until' in pattern and
                    pattern['until'] is not None and
                    pattern['until'] < pattern['nextRun']
                ) and
                (nextRun is None or pattern['nextRun'] < nextRun)
            ):
                nextRun = pattern['nextRun']
        
        # Remove patterns where until has passed
        reminder['repeat'][:] = [pattern for pattern in reminder['repeat'] if not (
            'until' in pattern and
            pattern['until'] is not None and
            pattern['until'] >= pattern['nextRun']
        )]
        
        if nextRun:
            reminder['nextRun'] = nextRun
                    
            if 'conditions' in reminder:
                # Get maximum leeway of all conditions
                maxLeeway = max((condition['leeway'] for condition in reminder['conditions']), default = None)
                if maxLeeway:
                    # Convert minutes to seconds and subtract from next run timestamp
                    reminder['nextCheck'] = nextRun - (maxLeeway * 60)
        
        return reminder
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        '''
        Checks if the message is a condition for a reminder reminder.
        '''
        # Ignore own messages
        if message.author.id == self.botId:
            return
        
        messageTime = message.created_at.timestamp()
        messageMentions = [mention.id for mention in message.mentions]
        
        # Loop through all reminders for items where time is between nextCheck and nextRun
        # Parse all matching conditions
        # If message meets condition, update lastMatch
        # If lastMatch for all conditions for a reminder is between nextCheck and nextRun, run updateNextRun()
        
        for reminder in self.reminders:
            # Check only eligible reminders
            if (
                'conditions' in reminder and
                'nextCheck' in reminder and
                messageTime > reminder['nextCheck'] and
                messageTime < reminder['nextRun']
            ):
                # Check all conditions
                for condition in reminder['conditions']:
                    if messageTime > reminder['nextRun'] - (condition['leeway'] * 60):
                        match condition['type']:
                            case 'no_message':
                                # Satisfy the condition if the message qualifies
                                if (
                                    not ('user' in condition and not message.author.id == condition['user']) and
                                    not ('channels' in condition and not message.channel.id in condition['channels']) and
                                    not ('mentions' in condition and (
                                        not message.mentions or
                                        not set(messageMentions) == set(condition['mentions'])
                                    )) and
                                    not ('regex' in condition and not re.search(condition['regex'], message.content, re.IGNORECASE))
                                ):
                                    # The condition has been matched
                                    self.logger.info(f'Condition matched for reminder reminder\nMessage {message.id} by {message.author.name}: {message.content}')
                                    # Update next run even though it hasn't passed yet
                                    reminder = await self.updateNextRun(reminder, skip = True)
                                    self.save()
        return