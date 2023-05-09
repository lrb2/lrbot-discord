import discord
import json
import re
import logging
import lrbot.config
import lrbot.response
import traceback
from discord.ext import commands
from lrbot.cogs.filterlists import FilterLists

class Keywords(commands.Cog):
    bot: commands.Bot = None
    file = open(r'config/keywords.json', 'r+')
    flm: FilterLists = None
    keywords: dict = None
    logger = logging.getLogger('discord.lrbot-reminders')
    
    def __init__(self, bot: commands.Bot) -> None:
        self.load()
        self.bot = bot
        self.flm = bot.get_cog('FilterLists')
    
    def load(self) -> None:
        '''
        Updates reminders with the latest changes from the file.
        '''
        self.file.seek(0)
        self.keywords = json.load(self.file)
        return

    def save(self) -> None:
        '''
        Updates the reminders file with the latest changes.
        '''
        self.file.seek(0)
        json.dump(self.keywords, self.file)
        self.file.truncate()
        return
    
    async def runActions(self, keyword: dict, message: discord.Message) -> None:
        '''
        Runs the action defined for the keyword.
        '''
        for action in keyword['actions']:
            try:
                await lrbot.response.runAction(action, self.bot, message)
            except Exception as error:
                tbStr = ''.join(traceback.format_tb(error.__traceback__))
                self.logger.error(f'Uncaught exception: {type(error)} {error}\n{tbStr}')
                await lrbot.response.reactToMessage(message, '💣')
                continue
    
    def permittedContext(self, ctx: commands.Context) -> bool:
        return self.flm.permittedContext(ctx)
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not (self.flm.permittedChannelID(message.channel.id) and self.flm.permittedUserID(message.author.id)):
            return
        
        user = message.author.id
        channel = message.channel.id
        mentions = [mention.id for mention in message.mentions]
        
        for keyword in self.keywords:
            # Check if allowed user or channel
            if (
                ('user_whitelist' in keyword and not user in keyword['user_whitelist']) or
                ('user_blacklist' in keyword and 'user_whitelist' not in keyword and user in keyword['user_blacklist']) or
                ('channel_whitelist' in keyword and not channel in keyword['channel_whitelist']) or
                ('channel_blacklist' in keyword and 'channel_whitelist' not in keyword and channel in keyword['channel_blacklist'])
            ):
                continue
            
            for condition in keyword['conditions']:
                if (
                    not ('mentions' in condition and (
                        not message.mentions or
                        not set(mentions) == set(condition['mentions'])
                    )) and
                    not ('regex' in condition and not re.search(condition['regex'], message.content, re.IGNORECASE))
                ):
                    # The condition has been matched; run action
                    await self.runActions(keyword, message)
                    break