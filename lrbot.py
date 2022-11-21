import discord
import logging
import lrbot.response
import lrbot.commands.latex

intents = discord.Intents.none()
intents.messages = True
intents.message_content = True

client = discord.Client(intents = intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

prefix = '$'

@client.event
async def on_message(message):
    if not len(message.content):
        return
    if message.content[0] != prefix:
        return
    if message.author == client.user:
        return
    
    command = message.content.split(' ',1)[0][1:].lower()

    match command:
        case 'latex':
            # Run latex.py
            await lrbot.commands.latex.run(message)
            return
        case _:
            return

logger = logging.FileHandler(filename='lrbot.log', encoding='utf-8', mode='w')

f = open('secret-token')
token = f.readline().strip()
f.close()
client.run(token, log_handler = logger)