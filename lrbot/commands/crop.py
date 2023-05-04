import asyncio
import discord
import lrbot.response
import os
from lrbot.filemgr import FileManager

async def main(message: discord.Message) -> None:
    makeTrans = False
    transColor = 'white'
    density = 600
    imgExt = '.png'

    args = message.content.lower().split()

    if len(args) > 1:
        for arg in args[1:]:
            if arg == 'transparent' or arg == 'trans':
                # Make the background transparent
                makeTrans = True
            elif arg.startswith('dpi='):
                # Manually set density
                density = int(arg[4:])
    
    if len(message.attachments) < 1:
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
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
        await lrbot.response.reactToMessage(message, 'fail')

    # Delete the folder
    fm.clean()
    
    return

async def run(message: discord.Message) -> None:
    try:
        await main(message)
    except:
        # Clean up any created files
        FileManager(message.id, reinit=True).clean()
        await lrbot.response.reactToMessage(message, '💣')
    return