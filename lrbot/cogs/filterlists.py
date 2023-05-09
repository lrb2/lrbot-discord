from discord.ext import commands
from os import path

class FilterLists(commands.Cog):
    botId = None
    userWhitelist = None
    userBlacklist = None
    channelWhitelist = None
    channelBlacklist = None
    
    def __init__(self, bot: commands.Bot) -> None:
        self.botId = bot.user.id
        self.load()
        return
    
    def load(self):
        '''
        Loads the user and channel white- and blacklists.
        '''
        # Reset all filter lists
        self.userWhitelist = None
        self.userBlacklist = None
        self.channelWhitelist = None
        self.channelBlacklist = None
        # Get whitelisted users
        if path.exists(r'config/user_whitelist'):
            with open(r'config/user_whitelist', 'r') as file:
                self.userWhitelist = [int(line.rstrip()) for line in file]
        # Get whitelisted channels
        if path.exists(r'config/channel_whitelist'):
            with open(r'config/channel_whitelist', 'r') as file:
                self.channelWhitelist = [int(line.rstrip()) for line in file]
        # Get blacklisted users if no whitelist
        if not self.userWhitelist and path.exists(r'config/user_blacklist'):
            with open(r'config/user_blacklist', 'r') as file:
                self.userBlacklist = [int(line.rstrip()) for line in file]
            # Ignore own messages
            self.userBlacklist.append(self.botId)
        # Get blacklisted channels if no whitelist
        if not self.channelWhitelist and path.exists(r'config/channel_blacklist'):
            with open(r'config/channel_blacklist', 'r') as file:
                self.channelBlacklist = [int(line.rstrip()) for line in file]
    
    def permittedUserID(self, id: int) -> bool:
        '''
        Checks if responding to the given user ID is permitted.
        '''
        if self.userWhitelist:
            return id in self.userWhitelist
        elif self.userBlacklist:
            return id not in self.userBlacklist
        else:
            return True
    
    def permittedChannelID(self, id: int) -> bool:
        '''
        Checks if responding in the given channel ID is permitted.
        '''
        if self.channelWhitelist:
            return id in self.channelWhitelist
        elif self.channelBlacklist:
            return id not in self.channelBlacklist
        else:
            return True
    
    def permittedContext(self, ctx: commands.Context) -> bool:
        '''
        Checks if the given context is permitted.
        '''
        return self.permittedChannelID(ctx.channel.id) and self.permittedUserID(ctx.author.id)