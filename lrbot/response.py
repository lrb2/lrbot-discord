from emoji import is_emoji

async def sendResponse(recipient, text = None, files = None, reference = None):
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

    if filesIsList:
        await recipient.send(
            content = text,
            files = files,
            reference = reference,
        )
    else:
        await recipient.send(
            content = text,
            file = files,
            reference = reference,
        )
    
    # Send any excess attachments as another message
    if filesQueued:
        await sendResponse(recipient, text, filesQueued, reference)

async def reactToMessage(reference, reaction = 'failure'):
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