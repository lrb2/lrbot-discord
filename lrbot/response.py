from emoji import UNICODE_EMOJI_ENGLISH

async def sendResponse(recipient, text = None, files = None, reference = None):
    '''
    Sends a message to the recipient entity (Messageable) (channel, user, etc.) including text and/or files.
    If the message is to be a reply, a reference (Message or MessageReference) must be provided.
    '''
    filesIsList = isinstance(files, list)
    if filesIsList and len(files) < 2:
        files = files[0]
        filesIsList = False

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

async def reactToMessage(reference, reaction = 'failure'):
    '''
    Reacts to the source message with an error. Reaction can be an emoji, 'failure', 'fail, 'ok', or 'success'.
    '''
    match reaction:
        case 'failure' | 'fail':
            emoji = '❌'
        case 'success' | 'ok':
            emoji = '✅'
    
    if reaction in UNICODE_EMOJI_ENGLISH:
        emoji = reaction
    else:
        return

    await reference.add_reaction(emoji)