import discord
import lrbot.response
from discord.ext import commands
from lrbot.cogs.reminders import Reminders

@commands.command(name = 'remindme')
async def main(
    ctx: commands.Context
) -> None:
    rm: Reminders = ctx.bot.get_cog('Reminders')
    # TODO: Add functionality to create reminders and skip next n occurrences
    # Possibly just allow providing JSON and verify format

@main.error
async def on_error(ctx: commands.Context) -> None:
    await lrbot.response.reactToMessage(ctx.message, '💣')

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)