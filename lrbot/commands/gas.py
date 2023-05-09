import discord
import lrbot.exceptions
import lrbot.gasprices
import lrbot.location
import lrbot.response
import operator
from discord.ext import commands
from lrbot.filemgr import FileManager

gasTypes = {
    'regular':  1,
    'reg':      1,
    'midgrade': 2,
    'mid':      2,
    'premium':  3,
    'prem':     3,
    'diesel':   4,
    'e85':      5,
    '85':       5,
    'unl88':    12,
    '88':       12,
    'e15':      12,
    '15':       12,
    1:          'Regular Gas',
    2:          'Midgrade Gas',
    3:          'Premium Gas',
    4:          'Diesel',
    5:          'E85',
    12:         'UNL88',
}

maxStations = 10

@commands.command(name = 'gas')
async def main(ctx: commands.Context, *, arg: str) -> None:
    message = ctx.message
    
    # There must be an argument
    if not arg:
        raise lrbot.exceptions.InvalidArgs('No arguments passed')
    
    args = arg.lower().split(None, 1)
    
    # If a gas type is provided before the location string, use it
    if args[0] in gasTypes and len(args) > 1:
        gasType = gasTypes[args[0]]
        locationStr = args[1]
    else:
        gasType = gasTypes['regular']
        locationStr = arg
    
    locations = await lrbot.location.parseLocationStr(locationStr)
    if not locations:
        raise lrbot.exceptions.InvalidArgs('No locations found')
    
    # Locations parsed correctly
    await lrbot.response.reactToMessage(message, 'success')
    
    async with message.channel.typing():
        gasStationsStrict, gasLocations = await lrbot.gasprices.getStations(locations, gasType, True)
        gasStationsNearby, _ = await lrbot.gasprices.getStations(locations, gasType, False)
        
        # Remove duplicates in each set (https://stackoverflow.com/a/9427216)
        gasStationsStrict = [dict(t) for t in {tuple(d.items()) for d in gasStationsStrict}]
        gasStationsNearby = [dict(t) for t in {tuple(d.items()) for d in gasStationsNearby}]
        # Sort all stations by price
        gasStationsStrict.sort(key=operator.itemgetter('price'))
        gasStationsNearby.sort(key=operator.itemgetter('price'))
        # Keep only the lowest stations in Strict
        del gasStationsStrict[maxStations:]
        # Remove elements that are still in Strict from Nearby
        gasStationsNearby = [station for station in gasStationsNearby if station not in gasStationsStrict]
        # Keep only the lowest stations in Nearby
        del gasStationsNearby[maxStations:]
        
        embedStrictTitle = gasTypes[gasType] + ' Prices In ' + ' and '.join(gasLocations)
        embedStrictColor = discord.Color.from_str('#dc4f41')
        embedStrictDesc = ''
        if len(gasStationsStrict) == 0:
            embedStrictDesc += 'No gas station prices were found matching the specified criteria.\n'
        for gasStation in gasStationsStrict:
            embedStrictDesc += '`'
            if gasStation['unit'] == 'dollars_per_gallon':
                embedStrictDesc += '$'
            embedStrictDesc += f'{gasStation["price"]:.2f}`'
            embedStrictDesc += ' | ' + gasStation['name']
            embedStrictDesc += ' @ ' + gasStation['address']
            embedStrictDesc += f' *({gasStation["rating"]:.1f}/5☆)*\n'
        embedStrictDesc += '*Only stations with known prices shown, up to ' + str(maxStations) + '. Data from GasBuddy*'
        gasEmbedStrict = discord.Embed(title = embedStrictTitle, description = embedStrictDesc, color = embedStrictColor)
        
        embedNearbyTitle = gasTypes[gasType] + ' Prices Near ' + ' and '.join(gasLocations)
        embedNearbyColor = discord.Color.from_str('#1d8e9a')   
        embedNearbyDesc = ''
        if len(gasStationsNearby) == 0:
            embedNearbyDesc += 'No gas station prices were found matching the specified criteria.\n'
        for gasStation in gasStationsNearby:
            embedNearbyDesc += '`'
            if gasStation['unit'] == 'dollars_per_gallon':
                embedNearbyDesc += '$'
            embedNearbyDesc += f'{gasStation["price"]:.2f}`'
            embedNearbyDesc += ' | ' + gasStation['name']
            embedNearbyDesc += ' @ ' + gasStation['address']
            embedNearbyDesc += f' *({gasStation["rating"]:.1f}/5☆)*\n'
        embedNearbyDesc += '*Only stations with known prices shown, up to ' + str(maxStations) + '. Data from GasBuddy*'
        gasEmbedNearby = discord.Embed(title = embedNearbyTitle, description = embedNearbyDesc, color = embedNearbyColor)
        
        await lrbot.response.sendResponse(
            message.channel,
            embeds = [gasEmbedStrict, gasEmbedNearby],
            reference = message
        )
    return

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    pass

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)