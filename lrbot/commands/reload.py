import discord
import lrbot.response
from discord.ext import commands
from lrbot.cogs.filterlists import FilterLists
from lrbot.cogs.keywords import Keywords
from lrbot.cogs.reminders import Reminders

@commands.command(name = 'reload')
@commands.is_owner()
async def main(
    ctx: commands.Context
) -> None:
    # Reload white- and blacklists
    flm: FilterLists = ctx.bot.get_cog('FilterLists')
    if flm is not None:
        flm.load()
    
    # Reload keywords from file
    km: Keywords = ctx.bot.get_cog('Keywords')
    if km is not None:
        km.load()
    
    # Reload reminders and reminder reminders from file
    rm: Reminders = ctx.bot.get_cog('Reminders')
    if rm is not None:
        rm.load()
    
    await lrbot.response.reactToMessage(ctx.message, 'success')

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    pass

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)