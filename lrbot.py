import discord
import logging
import os
import lrbot.response
import lrbot.commands.crop
import lrbot.commands.gas
import lrbot.commands.help
import lrbot.commands.latex

prefix = '$'

# Make required folders, if missing
requiredFolders = ['working']
for requiredFolder in requiredFolders:
    os.makedirs(requiredFolder, exist_ok=True)

intents = discord.Intents.none()
intents.messages = True
intents.message_content = True

client = discord.Client(intents = intents)

@client.event
async def on_ready() -> None:
    print(f'Logged in as {client.user}')
    
    # Sync list of available commands (if any)
    await discord.app_commands.CommandTree(client).sync()

@client.event
async def on_message(message: discord.Message) -> None:
    if not len(message.content):
        return
    if message.content[0] != prefix:
        return
    if message.author == client.user:
        return
    
    command = message.content.split(None,1)[0][1:].lower()

    match command:
        case 'help':
            # Run help.py
            await lrbot.commands.help.run(message)
            return
        case 'latex':
            # Run latex.py
            await lrbot.commands.latex.run(message)
            return
        case 'crop':
            # Run crop.py
            await lrbot.commands.crop.run(message)
            return
        case 'gas':
            # Run gas.py
            await lrbot.commands.gas.run(message)
            return
        case _:
            return

logger = logging.FileHandler(filename='lrbot.log', encoding='utf-8', mode='w')

f = open(r'secret-token', 'r')
token = f.readline().strip()
f.close()
client.run(token, log_handler = logger)