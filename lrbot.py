import discord
import logging
import logging.handlers
import lrbot.config
import lrbot.exceptions
import lrbot.response
import lrbot.loops.reminder
import os
import sys
import traceback
from discord.ext import commands
from lrbot.cogs.filterlists import FilterLists
from lrbot.cogs.keywords import Keywords
from lrbot.cogs.reminders import Reminders

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logHandler = logging.handlers.RotatingFileHandler(
    filename = 'lrbot.log',
    encoding = 'utf-8',
    maxBytes = 32*1024*1024,
    backupCount = 5
)
logFormatter = logging.Formatter(
    fmt = '{asctime} [{levelname}] {name}: {message}',
    datefmt = '%Y-%m-%d %H:%M:%S',
    style = '{'
)
logHandler.setFormatter(logFormatter)
logger.addHandler(logHandler)

# Log all uncaught exceptions
hookLogger = logging.getLogger('discord.lrbot')
def logExceptHook(type, value, tb) -> None:
    tbStr = ''.join(traceback.format_tb(tb))
    hookLogger.critical(f'Uncaught exception: {type} {value}\n{tbStr}')
sys.excepthook = logExceptHook

commandNames = [
    'crop',
    'gas',
    'help',
    'ignore',
    'latex',
    'reload',
    'remindme'
]

# Make required folders, if missing
requiredFolders = ['working']
for requiredFolder in requiredFolders:
    os.makedirs(requiredFolder, exist_ok=True)

intents = discord.Intents.none()
intents.messages = True
intents.message_content = True

bot = commands.Bot(
    command_prefix = commands.when_mentioned_or(lrbot.config.settings['prefix']),
    case_insensitive = True,
    help_command = None,
    owner_id = int(lrbot.config.settings['owner']),
    intents = intents
)

@bot.event
async def on_ready() -> None:
    print(f'Logged in as {bot.user.name} ({bot.user.id}) using discord.py {discord.__version__}')
    
    # Add cogs
    await bot.add_cog(FilterLists(bot))
    await bot.add_cog(Keywords(bot))
    await bot.add_cog(Reminders(bot))
    
    # Add command extensions
    for commandName in commandNames:
        await bot.load_extension('lrbot.commands.' + commandName)
    
    # Sync list of available commands (if any)
    await bot.tree.sync()
    
    # Start the reminder loop
    bot.loop.create_task(lrbot.loops.reminder.run(bot))

async def logCommandErrors(ctx: commands.Context, cmdError: commands.CommandError) -> None:
    if isinstance(cmdError, commands.CommandNotFound):
        return
    
    # Get the actual error, not just a CommandInvokeError
    error = cmdError.__cause__
    
    message = ctx.message
    moduleLogger = logging.getLogger('discord.lrbot-' + ctx.command.name)
    
    if isinstance(error, lrbot.exceptions.RaisedException):
        # The exception is known and caught
        await lrbot.response.reactToMessage(message, 'fail')
        # Log it for information
        moduleLogger.info(f'Caught command failure: {type(error)} {error}\nMessage {message.id} by {message.author.name}: {message.content}')
    else:
        # Uncaught exception
        await lrbot.response.reactToMessage(message, '💣')
        # Log the error
        tbStr = ''.join(traceback.format_tb(error.__traceback__))
        moduleLogger.error(f'Uncaught exception: {type(error)} {error}\nMessage {message.id} by {message.author.name}: {message.content}\n{tbStr}')

bot.on_command_error = logCommandErrors

f = open(r'secret-token', 'r')
token = f.readline().strip()
f.close()
bot.run(
    token,
    log_handler = None
)