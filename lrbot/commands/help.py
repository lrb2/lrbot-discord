import discord
import os
import lrbot.config
import lrbot.exceptions
import lrbot.response
from discord.ext import commands

@commands.command(name = 'help')
async def main(
    ctx: commands.Context,
    cmd: str = 'help'
) -> None:
    message = ctx.message
    
    helpPath = 'help/' + cmd
    
    if not os.path.exists(helpPath):
        raise lrbot.exceptions.InvalidArgs('No matching help file found.')
    
    await lrbot.response.reactToMessage(message, 'success')

    helpFile = open(helpPath)
    helpContents = helpFile.read()
    helpFile.close()

    helpTitle = 'lrbot Help'
    if cmd != 'help':
        helpTitle = helpTitle + ': ' + lrbot.config.settings['prefix'] + cmd

    helpEmbed = discord.Embed(
        title = helpTitle,
        type = 'article',
        description = helpContents
    )

    await lrbot.response.sendResponse(
        message.channel,
        reference = message,
        embeds = [helpEmbed]
    )
    return

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    pass

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)