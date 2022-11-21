import discord
import glob
import lrbot
from os import mkdir, path
from shutil import rmtree
import subprocess

async def main(message):
    args = message.content.lower().split()

    if len(args) < 2:
        return

    # First argument
    # Get template to use
    if args[1] == 'raw':
        template = None
    elif path.exists('latex/templates/' + args[1] + '/'):
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

    attachments = message.attachments

    code = None
    if codeIndex:
        # Text content exists
        code = message.content[codeIndex:]
        source = str(message.id) + ".tex"
    else:
        # An attachment must include LaTeX code
        # For now, require that it have the .tex extension
        for file in attachments:
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
    folder = 'latex/requests/' + str(message.id) + '/'
    mkdir(folder)

    # Try attachments first (more likely to fail)
    try:
        async with message.channel.typing():
            for file in attachments:
                await file.save(folder + file.filename)
    except:
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
    sourcePath = folder + source
    sourceBase = sourcePath[:-4]

    # Can add template to code in file if desired
    if template and source and code is None:
        sourceFile = open(sourcePath)
        code = sourceFile.read()
        sourceFile.close

    if code is not None:
        # Create the LaTeX file from the message content code
        createFile(sourcePath, code, template, extraPackages)

    # Run the LaTeX interpreter to generate a PDF
    #subprocess.call(['xelatex', '-interaction=batchmode', sourcePath, '-o', sourceBase + '.pdf'])
    subprocess.call(['xelatex', '-interaction=batchmode', '--output-directory=' + folder, sourcePath])

    files = None

    if pdfOnly:
        files = [discord.File(sourceBase + '.pdf')]
    else:
        # Use ImageMagick to convert the output to one or more images
        subprocess.call(['./magick', '-density', str(density), sourceBase + '.pdf', '-colorspace', 'rgb', '-trim', '+repage', sourceBase + '.png'])

        # Get all output images
        output = glob.glob(source[:-4] + "*.png", root_dir = folder)

        if len(output):
            files = []
            for outputPath in output:
                files.append(discord.File(folder + outputPath))

    # Compose the message
    await lrbot.response.sendResponse(message.channel, files = files, reference = message)

    # Delete the folder
    clean(message.id)

    return

def createFile(filePath, code, template = None, extraPackages = None):
    '''
    Creates a .tex file using the given code, template, and packages.
    '''
    file = open(filePath, 'a')

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
            packages.append(package)
        templateFile.close()
        # Add extra packages, without duplicates
        packages = list(set(packages + extraPackages))
        # Add the code
        for package in packages:
            # Check if the package requires predefined code
            packagePath = f'latex/packages/{package}.tex'
            if path.exists(packagePath):
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

def clean(id):
    '''
    Removes the folder created during the LaTeX process, if present.
    '''
    folder = 'latex/requests/' + str(id) + '/'
    if path.exists(folder):
        rmtree(folder)

async def run(message):
    try:
        await main(message)
    except:
        # Clean up any created files
        clean(message.id)
        await lrbot.response.reactToMessage(message, '💣')
        return