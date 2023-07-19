import asyncio
import discord
import logging
import lrbot.config
import lrbot.exceptions
import lrbot.response
import os
from discord.ext import commands
from lrbot.filemgr import FileManager

@commands.command(name = 'latex')
async def main(
    ctx: commands.Context,
    *,
    query: str
) -> None:
    message = ctx.message
    
    args = query.lower().split(None, 5)

    if len(args) < 1:
        raise lrbot.exceptions.InvalidArgs('Too few arguments passed')

    # First argument
    # Get template to use
    if args[0] == 'raw':
        template = None
    elif os.path.exists('latex/templates/' + args[0] + '/'):
        template = args[0]
    else:
        raise lrbot.exceptions.InvalidArgs('Invalid template argument')
    
    validArgs = 1

    density = int(lrbot.config.latex['density'])
    imgExt = '.' + lrbot.config.latex['format']
    pdfOnly = False
    extraPackages = []

    if len(args) > 1:
        for arg in args[1:]:
            if arg.startswith('packages='):
                # Add extra packages to template
                extraPackages = arg[9:].split(',')
                validArgs += 1
            elif arg.startswith('dpi='):
                # Manually set density
                density = int(arg[4:])
                validArgs += 1
            elif arg == 'pdf':
                # Only create PDF without converting to images
                pdfOnly = True
                validArgs += 1
            else:
                # No more valid arguments
                break

    # All remaining content is LaTeX
    # Check for LaTeX content, either in content or attachment
    code = None
    source = None
    if len(args) > validArgs:
        # Text content exists
        codeIndex = query.lower().index(args[validArgs])
        code = query[codeIndex:]
        source = str(message.id) + ".tex"
    else:
        # An attachment must include LaTeX code
        # For now, require that it have the .tex extension
        for file in message.attachments:
            if file.filename.lower().endswith('.tex'):
                # A suitable file has been found
                source = file.filename
                break
    
    if source is None:
        raise lrbot.exceptions.InvalidFiles('No source files found')

    # LaTeX content has been verified
    await lrbot.response.reactToMessage(message, 'success')

    # Save the message code and files
    fm = FileManager(message.id)
    await fm.saveMessageAttachments(message)

    # Can add template to code in file if desired
    if template and source and code is None:
        sourceFile = fm.openFile(source)
        code = sourceFile.read()
        sourceFile.close

    if code is not None:
        # Create the LaTeX file from the message content code
        generateFile(fm, source, code, template, extraPackages)

    # Run the LaTeX interpreter to generate a PDF
    xelatex = [
        'xelatex',
        '-interaction=batchmode',
        '--output-directory=' + fm.getOutputFolder(),
        fm.getFilePath(source)
    ]
    await asyncio.wait_for((await asyncio.create_subprocess_exec(*xelatex)).wait(), 300)

    if not pdfOnly:
        # Use ImageMagick to convert the output to one or more images
        sourceOutput = os.path.splitext(source)[0] + '.pdf'
        imgOutput = os.path.splitext(source)[0] + imgExt
        magick = [
            'magick',
            '-density', str(density),
            fm.getFilePath(sourceOutput, output=True),
            '-colorspace', 'rgb',
            '-trim',
            '+repage',
            os.path.join(os.sep, fm.getOutputFolder(), imgOutput)
        ]
        await asyncio.wait_for((await asyncio.create_subprocess_exec(*magick)).wait(), 300)

    outputFiles = fm.getOutputFiles()
    files = []

    excludedExts = ['aux','log']
    if not pdfOnly:
        excludedExts.append('pdf')

    for file in outputFiles:
        ext = os.path.splitext(file)[1][1:].lower()
        
        # Skip unwanted files
        if ext in excludedExts:
            continue

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

    return

def generateFile(
    fm: FileManager,
    filename: str,
    code: str,
    template: str = None,
    extraPackages: list[str] = None
) -> None:
    '''
    Creates a .tex file using the given code, template, and packages.
    '''
    # Remove the file if it already exists (such as for applying a template to a file)
    
    file = fm.createFile(filename)

    if template is not None:
        # Add head
        templateFile = open(f'latex/templates/{template}/{template}-head.tex')
        file.write(templateFile.read())
        templateFile.close()
        
        # Add packages
        # Get template packages
        templateFile = open(f'latex/templates/{template}/{template}-packages')
        packages = []
        for package in templateFile:
            packages.append(package.rstrip())
        templateFile.close()
        # Add extra packages, without duplicates
        packages = list(set(packages + extraPackages))
        # Add the code
        for package in packages:
            # Check if the package requires predefined code
            packagePath = f'latex/packages/{package}.tex'
            if os.path.exists(packagePath):
                packageFile = open(packagePath)
                file.write(packageFile.read())
                packageFile.close()
            else:
                file.write('\\usepackage{' + package + '}\n')

        # Add pre-body
        templateFile = open(f'latex/templates/{template}/{template}-pre.tex')
        file.write(templateFile.read())
        templateFile.close()

        # Add body
        file.write(code)

        # Add post-body
        templateFile = open(f'latex/templates/{template}/{template}-post.tex')
        file.write(templateFile.read())
        templateFile.close()
    else:
        file.write(code)
    
    file.close()
    return

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    try:
        # Try to clean up any created files
        FileManager(ctx.message.id, reinit=True).clean()
    except Exception as error:
        if not isinstance(error, FileNotFoundError):
            logger = logging.getLogger('discord.lrbot-latex')
            logger.warning(f'Working folder for {ctx.message.id} was not successfully cleaned after error')

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)