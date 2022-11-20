import discord
import glob
import lrbot
from os import mkdir, path
from shutil import rmtree
import subprocess

async def main(message):
    args = message.content.split()

    # First argument
    # Get template to use
    if args[1] == 'raw':
        template = None
    elif path.exists('latex\\templates\\' + args[1] + '\\'):
        template = args[1]
    else:
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
    validArgs = 1
    
    # Second argument (optional): extra packages
    if len(args) > 2 and args[2].startswith('packages:'):
        extraPackages = args[2][10:].split(',')

        validArgs += 1

    if extraPackages is not None:
        codeIndex = message.content.index(extraPackages[-1]) + len(extraPackages[-1])
    else:
        codeIndex = message.content.index(args[1]) + len(args[1])

    # All remaining content is LaTeX
    # Check for LaTeX content, either in content or attachment

    attachments = message.attachments

    if len(args) > validArgs:
        # Text content exists
        code = message.content[codeIndex:]
        source = message.id + ".tex"
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
    folder = 'latex\\requests\\' + message.id + '\\'
    mkdir(folder)

    # Try attachments first (more likely to fail)
    try:
        async with message.channel.typing():
            for file in attachments:
                await file.save(folder)
    except:
        await lrbot.response.reactToMessage(message, 'fail')
        return

    if code is not None:
        # Create the LaTeX file from the message content code
        createFile(folder, source, code, template, extraPackages)
    
    # Run the LaTeX interpreter to generate a PDF
    subprocess.call(['pdftex', source])

    sourceBase = source[:-4]

    # Use ImageMagick to convert the output to one or more images
    subprocess.call(['magick', '-density 600', '"' + sourceBase + '.pdf"', '-trim', '-transparent white', '+repage', '"' + sourceBase + '.png"'])

    # Get all output images
    output = glob.glob(sourceBase + "*.png", root_dir = folder)

    # Compose the message
    await lrbot.response.sendResponse(message.channel, files = output, reference = message)

    # Delete the folder
    clean(message.id)

    return

def createFile(folder, filename, code, template = None, extraPackages = None):
    '''
    Creates a .tex file using the given code, template, and packages.
    '''
    file = open(folder + filename, 'a')

    if template is not None:
        # Add head
        template = open(f'latex\\templates\\{template}\\{template}-head.tex')
        file.write(template.read())
        template.close()
        
        # Add packages
        # Get template packages
        template = open(f'latex\\templates\\{template}\\{template}-packages')
        packages = []
        for package in template:
            packages.append(package)
        template.close()
        # Add extra packages, without duplicates
        packages = list(set(packages + extraPackages))
        # Add the code
        for package in packages:
            # Check if the package requires predefined code
            packagePath = f'latex\\packages\\{package}.tex'
            if path.exists(packagePath):
                packageFile = open(packagePath)
                file.write(packageFile.read())
                packageFile.close()
            else:
                file.write('\usepackage({' + package + '}\n')

        # Add pre-body
        template = open(f'latex\\templates\\{template}\\{template}-pre.tex')
        file.write(template.read())
        template.close()

        # Add body
        file.write(code)

        # Add post-body
        template = open(f'latex\\templates\\{template}\\{template}-post.tex')
        file.write(template.read())
        template.close()
    else:
        file.write(code)
    
    file.close()

def clean(id):
    '''
    Removes the folder created during the LaTeX process, if present.
    '''
    folder = 'latex\\requests\\' + id + '\\'
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