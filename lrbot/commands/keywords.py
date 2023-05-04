import discord
import re
import lrbot.response
from lrbot.keywordsmgr import KeywordsManager

async def main(message: discord.Message, km: KeywordsManager) -> None:
    user = message.author.id
    channel = message.channel.id
    mentions = [mention.id for mention in message.mentions]
    
    for keyword in km.keywords:
        # Check if allowed user or channel
        if (
            ('user_whitelist' in keyword and not user in keyword['user_whitelist']) or
            ('user_blacklist' in keyword and 'user_whitelist' not in keyword and user in keyword['user_blacklist']) or
            ('channel_whitelist' in keyword and not channel in keyword['channel_whitelist']) or
            ('channel_blacklist' in keyword and 'channel_whitelist' not in keyword and channel in keyword['channel_blacklist'])
        ):
            continue
        
        for condition in keyword['conditions']:
            if (
                not ('mentions' in condition and (
                    not message.mentions or
                    not set(mentions) == set(condition['mentions'])
                )) and
                not ('regex' in condition and not re.search(condition['regex'], message.content, re.IGNORECASE))
            ):
                # The condition has been matched; run action
                await km.runActions(keyword, message)
                break
    return

async def run(message: discord.Message, km: KeywordsManager) -> None:
    try:
        await main(message, km)
    except:
        await lrbot.response.reactToMessage(message, '💣')
    return