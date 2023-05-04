import discord
from emoji import is_emoji

async def sendResponse(
    recipient: discord.abc.Messageable,
    text: str = None,
    files: list[discord.File] = None,
    reference: discord.Message = None,
    embeds: list[discord.Embed] = None,
    silent: bool = False
) -> None:
    '''
    Sends a message to the recipient entity (Messageable) (channel, user, etc.) including text and/or files.
    If the message is to be a reply, a reference (Message or MessageReference) must be provided.
    '''
    filesIsList = isinstance(files, list)
    if filesIsList and len(files) < 2:
        files = files[0]
        filesIsList = False
    
    # Max. 10 attachments per message
    filesQueued = None
    if filesIsList and len(files) > 10:
        filesQueued = files[10:]
        files = files[:9]
    
    # Max. 10 embeds per message
    embedsQueued = None
    if embeds is not None and len(embeds) > 10:
        embedsQueued = embeds[10:]
        embeds = embeds[:9]

    if filesIsList:
        await recipient.send(
            content = text,
            files = files,
            reference = reference,
            embeds = embeds,
            silent = silent
        )
    else:
        await recipient.send(
            content = text,
            file = files,
            reference = reference,
            embeds = embeds,
            silent = silent
        )
    
    # Send any excess attachments as another message
    if filesQueued or embedsQueued:
        await sendResponse(recipient, text, filesQueued, reference, embedsQueued, silent)

async def reactToMessage(
    reference: discord.Message,
    reaction: str = 'failure'
) -> None:
    '''
    Reacts to the source message with an error. Reaction can be an emoji, 'failure', 'fail, 'ok', or 'success'.
    '''
    match reaction:
        case 'failure' | 'fail':
            emoji = '❌'
        case 'success' | 'ok':
            emoji = '✅'
    
    if is_emoji(reaction):
        emoji = reaction
    elif emoji is None:
        return

    await reference.add_reaction(emoji)

async def runAction(
    action: dict,
    client: discord.Client,
    reference: discord.Message = None,
) -> None:
    '''
    Processes the given action dict.
    If a message is provided, any messages will reference that message.
    '''
    match action['type']:
        case 'message':
            # Use the specified channel, or the channel of the reference message.
            if 'channel' in action:
                responseChannel = client.get_partial_messageable(action['channel'])
                responseReference = None
            else:
                responseChannel = reference.channel
                responseReference = reference
            # Add mentions to the specified content.
            responseContent = ''
            if 'mention' in action:
                for id in action['mention']:
                    responseContent += '<@' + str(id) + '> '
            responseContent += action['content']
            # Add embeds if specified.
            responseEmbeds = []
            if 'embeds' in action:
                for embed in action['embeds']:
                    # Use Discord standard embed format (see https://discord.com/developers/docs/resources/channel#embed-object)
                    responseEmbeds.append(discord.Embed.from_dict(embed))
            # Make the message silent if specified.
            responseSilent = True if 'silent' in action and action['silent'] else False
            await sendResponse(
                responseChannel,
                responseContent,
                reference = responseReference,
                embeds = responseEmbeds,
                silent = responseSilent
            )