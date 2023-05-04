import discord
import json
import lrbot.config
import lrbot.response

class KeywordsManager:
    client = None
    keywords = dict()
    file = open(r'config/keywords.json', 'r+')
    
    def __init__(self, client: discord.Client) -> None:
        self.load()
        self.client = client
        return

    def load(self) -> None:
        '''
        Updates reminders with the latest changes from the file.
        '''
        self.file.seek(0)
        self.keywords = json.load(self.file)
        return

    def save(self) -> None:
        '''
        Updates the reminders file with the latest changes.
        '''
        self.file.seek(0)
        json.dump(self.keywords, self.file)
        self.file.truncate()
        return
    
    async def runActions(self, keyword: dict, message: discord.Message) -> None:
        '''
        Runs the action defined for the keyword.
        '''
        for action in keyword['actions']:
            try:
                await lrbot.response.runAction(action, self.client, message)
            except:
                await lrbot.response.reactToMessage(message, '💣')
                continue