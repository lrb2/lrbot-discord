import asyncio
import discord
import logging
import lrbot.config
import lrbot.exceptions
import lrbot.response
import os
from discord.ext import commands
from lrbot.filemgr import FileManager

@commands.command(name = 'crop')
async def main(
    ctx: commands.Context,
    *args: list[str]
) -> None:
    message = ctx.message
    
    makeTrans = False
    transColor = lrbot.config.crop['transColor']
    density = int(lrbot.config.crop['density'])
    imgExt = '.' + lrbot.config.crop['format']

    for arg in args:
        if arg == 'transparent' or arg == 'trans':
            # Make the background transparent
            makeTrans = True
        elif arg.startswith('dpi='):
            # Manually set density
            density = int(arg[4:])
    
    if len(message.attachments) < 1:
        raise lrbot.exceptions.InvalidFiles('No attachments passed')
    
    await lrbot.response.reactToMessage(message, 'success')
    
    fm = FileManager(message.id)
    attachments = await fm.saveMessageAttachments(message)
    fileProcesses = []

    for attachment in attachments:
        # Test if the file is processable
        magick = [
            'magick',
            'identify',
            '-regard-warnings',
            fm.getFilePath(attachment),
        ]
        fileTest = await asyncio.wait_for(asyncio.create_subprocess_exec(
            *magick,
            stderr = asyncio.subprocess.PIPE,
        ), 30)
        fileTestError = (await fileTest.communicate())[1]
        if fileTestError:
            # An error was raised; not processable
            continue

        magick = [
            'magick',
            '-density', str(density),
            fm.getFilePath(attachment),
            '-colorspace', 'rgb',
            '-trim'
        ]
        if makeTrans:
            magick.extend(['-transparent', transColor])
        magick.extend([
            '+repage',
            os.path.join(
                os.sep,
                fm.getOutputFolder(),
                os.path.splitext(attachment)[0] + imgExt)
        ])

        # Add the process to the queue
        fileProcesses.append(asyncio.wait_for((await asyncio.create_subprocess_exec(*magick)).wait(), 300))
    
    # Run all processes and wait for completion
    await asyncio.gather(*fileProcesses)
    
    outputFiles = fm.getOutputFiles()
    files = []

    for file in outputFiles:
        filePath = os.path.join(os.sep, fm.getOutputFolder(), file)
        files.append(discord.File(filePath))

    if files:
        # Compose the message
        await lrbot.response.sendResponse(
            message.channel,
            files = files,
            reference = message
        )
    else:
        raise lrbot.exceptions.InvalidFiles('No output files generated')

    # Delete the folder
    fm.clean()

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    try:
        # Try to clean up any created files
        FileManager(ctx.message.id, reinit=True).clean()
    except Exception as error:
        if not isinstance(error, FileNotFoundError):
            logger = logging.getLogger('discord.lrbot-crop')
            logger.warning(f'Working folder for {ctx.message.id} was not successfully cleaned after error')

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)