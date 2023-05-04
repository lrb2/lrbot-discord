import discord
import logging
import os
import lrbot.config
import lrbot.response
import lrbot.commands.crop
import lrbot.commands.gas
import lrbot.commands.help
import lrbot.commands.ignore
import lrbot.commands.keywords
import lrbot.commands.latex
import lrbot.commands.remindme
import lrbot.loops.reminder
from lrbot.keywordsmgr import KeywordsManager
from lrbot.remindermgr import ReminderManager

prefix = lrbot.config.settings['prefix']

# Make required folders, if missing
requiredFolders = ['working']
for requiredFolder in requiredFolders:
    os.makedirs(requiredFolder, exist_ok=True)

whitelistedUsers = None
whitelistedChannels = None
blacklistedUsers = None
blacklistedChannels = None

def loadFilterLists():
    '''
    Load the user and channel white- and blacklists.
    '''
    global whitelistedUsers, whitelistedChannels, blacklistedUsers, blacklistedChannels
    # Reset all filter lists
    whitelistedUsers = None
    whitelistedChannels = None
    blacklistedUsers = None
    blacklistedChannels = None
    # Get whitelisted users
    if os.path.exists(r'config/user_whitelist'):
        with open(r'config/user_whitelist', 'r') as file:
            whitelistedUsers = [int(line.rstrip()) for line in file]
    # Get whitelisted channels
    if os.path.exists(r'config/channel_whitelist'):
        with open(r'config/channel_whitelist', 'r') as file:
            whitelistedChannels = [int(line.rstrip()) for line in file]
    # Get blacklisted users if no whitelist
    if not whitelistedUsers and os.path.exists(r'config/user_blacklist'):
        with open(r'config/user_blacklist', 'r') as file:
            blacklistedUsers = [int(line.rstrip()) for line in file]
        # Ignore own messages
        blacklistedUsers.append(client.user.id)
    # Get blacklisted channels if no whitelist
    if not whitelistedChannels and os.path.exists(r'config/channel_blacklist'):
        with open(r'config/channel_blacklist', 'r') as file:
            blacklistedChannels = [int(line.rstrip()) for line in file]

intents = discord.Intents.none()
intents.messages = True
intents.message_content = True

client = discord.Client(intents = intents)

km = KeywordsManager(client)
rm = ReminderManager(client)

@client.event
async def on_ready() -> None:
    print(f'Logged in as {client.user}')
    
    # Load white/blacklists
    loadFilterLists()
    
    # Sync list of available commands (if any)
    await discord.app_commands.CommandTree(client).sync()
    
    # Start the reminder loop
    client.loop.create_task(lrbot.loops.reminder.run(rm))

@client.event
async def on_message(message: discord.Message) -> None:
    if not len(message.content):
        # There must be text in the message
        return
    if message.author == client.user:
        # Ignore the bot's own messages
        return
    if message.content[0] != prefix:
        # Check if condition for reminder reminders
        await rm.checkMessage(message)
        
        # Only check for keywords if whitelisted or not blacklisted
        if not (
            (blacklistedChannels and message.channel.id in blacklistedChannels) or
            (whitelistedChannels and not message.channel.id in whitelistedChannels) or
            (blacklistedUsers and message.author.id in blacklistedUsers) or
            (whitelistedUsers and not message.author.id in whitelistedUsers)
        ):
            await lrbot.commands.keywords.run(message, km)
        return
    
    command = message.content.split(None,1)[0][1:].lower()

    match command:
        case 'help':
            # Run help.py
            await lrbot.commands.help.run(message)
        case 'latex':
            # Run latex.py
            await lrbot.commands.latex.run(message)
        case 'crop':
            # Run crop.py
            await lrbot.commands.crop.run(message)
        case 'gas':
            # Run gas.py
            await lrbot.commands.gas.run(message)
        case 'ignore':
            # Run ignoreme.py
            await lrbot.commands.ignore.run(message)
            loadFilterLists()
        case 'reload':
            # Only usable by the owner
            if message.author.id == int(lrbot.config.settings['owner']):
                # Reload filter, keywords, and reminders lists
                loadFilterLists()
                km.load()
                rm.load()
                await lrbot.response.reactToMessage(message, 'success')
        case 'remindme':
            # Run remindme.py
            await lrbot.commands.remindme.run(message, rm)

logger = logging.FileHandler(filename='lrbot.log', encoding='utf-8', mode='w')

f = open(r'secret-token', 'r')
token = f.readline().strip()
f.close()
client.run(token, log_handler = logger)