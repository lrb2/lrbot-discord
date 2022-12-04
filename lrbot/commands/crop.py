import discord
import lrbot.response
import os
from lrbot.filemgr import FileManager
import subprocess

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

    for attachment in attachments:
        # Test if the file is processable
        if subprocess.run([
            './magick',
            'identify',
            '-regard-warnings',
            fm.getFilePath(attachment)
        ], timeout=30, capture_output=True).stderr:
            # An error was raised; not processable
            continue

        magick = [
            './magick',
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

        # Process the file
        subprocess.run(magick, timeout=120)
    
    outputFiles = fm.getOutputFiles()
    files = []

    for file in outputFiles:
        filePath = os.path.join(os.sep, fm.getOutputFolder(), file)
        files.append(discord.File(filePath))

    # Compose the message
    await lrbot.response.sendResponse(
        message.channel,
        files = files,
        reference = message
    )

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