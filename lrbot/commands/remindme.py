import discord
import lrbot.response
from lrbot.remindermgr import ReminderManager

async def main(message: discord.Message, rm: ReminderManager) -> None:
    args = message.content.lower().split(None, 2)
    
    # TODO: Add functionality to create reminders and skip next n occurrences
    # Possibly just allow providing JSON and verify format

async def run(message: discord.Message, rm: ReminderManager) -> None:
    try:
        await main(message, rm)
    except:
        await lrbot.response.reactToMessage(message, '💣')
    return