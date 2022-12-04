import discord
import os
from shutil import rmtree
from typing import TextIO

class FileManager:
    def __init__(
        self,
        id: int,
        reinit: bool = False
    ) -> None:
        '''
        Creates the working folder.
        '''
        self.id = str(id)
        self.folder = os.path.join(
            os.sep,
            os.getcwd(),
            'working',
            str(id)
        )
        self.outputFolder = os.path.join(
            os.sep,
            self.folder,
            'output'
        )
        self.attachments = []

        if not reinit:
            os.makedirs(self.outputFolder)
        
        return
    
    def getFolder(self) -> os.PathLike:
        '''
        Gets the full path of the working folder.
        '''
        return self.folder
    
    def getOutputFolder(self) -> os.PathLike:
        '''
        Gets the full path of the output subdirectory.
        '''
        return self.outputFolder
    
    def getFilePath(
        self,
        filename: str = None,
        extension: str = None,
        output: bool = False
    ) -> os.PathLike:
        '''
        Gets the full path of a file by filename (or extension if ID-named), if it exists.
        '''
        if extension is not None:
            filename = self.id + '.' + extension
        
        if output:
            path = self.outputFolder + os.sep + filename
        else:
            path = self.folder + os.sep + filename

        if not os.path.exists(path):
            raise FileNotFoundError
        return path
    
    def clean(self) -> None:
        '''
        Removes the folder and all of its contents.
        '''
        rmtree(self.folder)
        return
    
    def openFile(
        self,
        filename: str = None,
        mode: str = 'r',
        extension: str = None
    ) -> TextIO:
        '''
        Opens a managed file by filename (or extension if ID-named).
        '''
        if extension is not None:
            filename = self.id + '.' + extension
        path = self.getFilePath(filename)
        file = open(path, mode)
        return file

    def createFile(
        self,
        filename: str = None,
        mode: str = 'a',
        extension: str = None
    ) -> TextIO:
        '''
        Creates and opens a new file by filename (or extension if ID-named).
        If the file already exists, it is overwritten.
        '''
        if extension is not None:
            filename = self.id + '.' + extension
        path = self.folder + os.sep + filename
        if os.path.exists(path):
            os.remove(path)
        file = open(path, mode)
        return file

    async def saveMessageAttachments(
        self,
        message: discord.Message
    ) -> list[str]:
        '''
        Saves all Discord message attachments into the folder.
        '''
        async with message.channel.typing():
            for file in message.attachments:
                await file.save(self.folder + os.sep + file.filename)
                self.attachments.append(file.filename)
        print("OK")
        return self.attachments
    
    def getOutputFiles(self) -> list[os.PathLike]:
        '''
        Returns a list of the filenames in the output subfolder.
        '''
        items = os.listdir(self.outputFolder)
        outputFiles = []
        for item in items:
            path = os.path.join(os.sep, self.outputFolder, item)
            if os.path.isfile(path):
                outputFiles.append(item)
        return outputFiles