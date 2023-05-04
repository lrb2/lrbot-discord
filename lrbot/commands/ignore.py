import discord
import lrbot
import lrbot.response
import os

async def main(message: discord.Message) -> None:
    args = message.content.lower().split(None)
    
    idsToIgnore = []
    
    for mention in message.mentions:
        # Add all @ mentions first
        idsToIgnore.append(mention.id)
    
    for id in args[1:]:
        if id == 'me':
            idsToIgnore.append(message.author.id)
        else:
            try:
                # Try for any raw IDs (might just be the mention in text form)
                int(id)
                idsToIgnore.append(id)
            except ValueError:
                continue
    
    if os.path.exists(r'config/user_whitelist'):
        # Remove users from whitelist
        file = open(r'config/user_whitelist', 'r+')
        whitelistedIDs = [line.rstrip() for line in file]
        file.seek(0)
        for id in whitelistedIDs:
            if not any(idToIgnore == int(id) for idToIgnore in idsToIgnore):
                file.write(id + '\n')
        file.truncate()
        file.close()
    else:
        # Even if there is not yet a blacklist
        # Remove users from blacklist if they are already blacklisted (prevents duplicates)
        if os.path.exists(r'config/user_blacklist'):
            file = open(r'config/user_blacklist', 'r+')
        else:
            file = open(r'config/user_blacklist', 'a+')
        blacklistedIDs = [line.rstrip() for line in file]
        file.seek(0)
        for id in blacklistedIDs:
            if not any(idToIgnore == int(id) for idToIgnore in idsToIgnore):
                file.write(id + '\n')
        # Add users to blacklist
        for idToIgnore in idsToIgnore:
            file.write(str(idToIgnore) + '\n')
        file.truncate()
        file.close()
    
    await lrbot.response.reactToMessage(message, 'success')

async def run(message: discord.Message) -> None:
    #try:
    await main(message)
    #except:
    #    await lrbot.response.reactToMessage(message, '💣')
    return