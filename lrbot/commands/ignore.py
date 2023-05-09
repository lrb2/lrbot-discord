import discord
import lrbot
import lrbot.exceptions
import lrbot.response
import os
import typing
from discord.ext import commands
from lrbot.cogs.filterlists import FilterLists

@commands.command(name = 'ignore')
async def main(
    ctx: commands.Context,
    *users: typing.Union[discord.User, str]
) -> None:
    idsToIgnore = []
    for user in users:
        if isinstance(user, discord.abc.User):
            idsToIgnore.append(user.id)
        if user == 'me':
            idsToIgnore.append(ctx.author.id)
    
    if len(idsToIgnore) < 1:
        raise lrbot.exceptions.InvalidArgs('No valid users passed')
    
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
    
    # Reload the white- and blacklists
    flm: FilterLists = ctx.bot.get_cog('FilterLists')
    if flm is not None:
        flm.load()
    
    await lrbot.response.reactToMessage(ctx.message, 'success')

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    pass

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)