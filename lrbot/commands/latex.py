import discord
import lrbot.response
import os
from lrbot.filemgr import FileManager
import subprocess

async def main(message: discord.Message) -> None:
    args = message.content.lower().split()

    if len(args) < 2:
        return

    # First argument
    # Get template to use
    if args[1] == 'raw':
        template = None
    elif os.path.exists('latex/templates/' + args[1] + '/'):
        template = args[1]
    else:
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
    validArgs = 1

    density = 300
    pdfOnly = False
    extraPackages = []

    if len(args) > 2:
        for arg in args[2:]:
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

    codeIndex = None
    if len(args) > validArgs + 1:
        codeIndex = message.content.index(args[validArgs]) + len(args[validArgs]) + 1

    # All remaining content is LaTeX
    # Check for LaTeX content, either in content or attachment
    code = None
    if codeIndex:
        # Text content exists
        code = message.content[codeIndex:]
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
        await lrbot.response.reactToMessage(message, 'fail')
        return

    # LaTeX content has been verified
    await lrbot.response.reactToMessage(message, 'success')

    # Save the message code and files
    fm = FileManager(message.id)
    attachments = await fm.saveMessageAttachments(message)

    # Can add template to code in file if desired
    if template and source and code is None:
        sourceFile = fm.openFile(source)
        code = sourceFile.read()
        sourceFile.close

    if code is not None:
        # Create the LaTeX file from the message content code
        generateFile(fm, source, code, template, extraPackages)

    # Run the LaTeX interpreter to generate a PDF
    subprocess.run([
        'xelatex',
        '-interaction=batchmode',
        '--output-directory=' + fm.getOutputFolder(),
        fm.getFilePath(source)
    ], timeout=120)

    if not pdfOnly:
        # Use ImageMagick to convert the output to one or more images
        sourceOutput = os.path.splitext(source)[0] + '.pdf'
        imgOutput = os.path.splitext(source)[0] + '.png'
        subprocess.run([
            './magick',
            '-density', str(density),
            fm.getFilePath(sourceOutput, output=True),
            '-colorspace', 'rgb',
            '-trim',
            '+repage',
            os.path.join(os.sep, fm.getOutputFolder(), imgOutput)
        ], timeout=120)

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

    # Compose the message
    await lrbot.response.sendResponse(
        message.channel,
        files = files,
        reference = message
    )

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

async def run(message: discord.Message) -> None:
    try:
        await main(message)
    except:
        # Clean up any created files
        FileManager(message.id, reinit=True).clean()
        await lrbot.response.reactToMessage(message, '💣')
    return