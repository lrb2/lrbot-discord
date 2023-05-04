import discord
import os
import lrbot.response

helpFolder = os.path.join(
    os.sep,
    os.getcwd(),
    'help'
)

async def run(message: discord.Message) -> None:
    args = message.content.lower().split()

    source = 'help'

    if len(args) > 1:
        source = args[1]
    
    helpPath = helpFolder + os.sep + source
    
    if not os.path.exists(helpPath):
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
    await lrbot.response.reactToMessage(message, 'success')

    helpFile = open(helpPath)
    helpContents = helpFile.read()
    helpFile.close()

    helpTitle = 'lrbot Help'
    if source != 'help':
        helpTitle = helpTitle + ': $' + source

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