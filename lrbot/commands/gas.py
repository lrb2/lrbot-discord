import discord
import lrbot.response
import operator
import re
import requests
import string
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
gasTypeProducts = {
    1:  'regular_gas',
    2:  'midgrade_gas',
    3:  'premium_gas',
    4:  'diesel',
    5:  'e85',
    12: 'e15',
}

maxStations = 10

delimsPrimary = [';', '&', 'and']
delimsSecondary = [',']
delimsAll = delimsPrimary + delimsSecondary

f = open(r'resources/state-abbreviations', 'r')
states = [state.lower().strip().split(',') for state in f.readlines()]
f.close()

# Get the initials of the state that the string refers to, if applicable
def getState(query: str) -> str:
    query = query.lower()
    for state in states:
        if query in state:
            return state[0]
    return ''

stateDefault = getState('Illinois')

async def main(message: discord.Message) -> None:
    args = message.content.lower().split(None, 2)
    
    # There must be an argument
    if len(args) < 2:
        await lrbot.response.reactToMessage(message, 'fail')
        return
    
    # If a gas type is provided before the location string, use it
    if args[1] in gasTypes and len(args) > 2:
        gasType = gasTypes[args[1]]
        locationStr = args[2]
    else:
        gasType = gasTypes['regular']
        locationStr = ' '.join(args[1:])
    
    locations = []
    
    # Check for delimiters
    if any(delim in locationStr for delim in delimsPrimary) and any(delim in locationStr for delim in delimsSecondary):
        # Both primary and secondary delimiters are used (most explicit)
        # Split by any primary delimiter
        regex = '|'.join(delimsPrimary)
        locations = [x.strip() for x in list(filter(None, re.split(regex, locationStr)))]
        # Split each location by any secondary delimiter
        for location in locations:
            regex = '|'.join(delimsSecondary)
            location = [x.strip() for x in list(filter(None, re.split(regex, location)))]
            # location should be [City, State]
            if len(location) > 2:
                await lrbot.response.reactToMessage(message, 'fail')
                return
            elif len(location) == 1:
                # Is the item just a ZIP code?
                if len(location) == 5 and re.match('^[0-9]*$', location):
                    # Add the ZIP code as a location
                    location = [location]
                else:
                    location.append(stateDefault)
            else:
                locationState = getState(location[1])
                if not locationState:
                    # The last item should be a valid state
                    await lrbot.response.reactToMessage(message, 'fail')
                    return
                location[1] = locationState
    elif any(delim in locationStr for delim in delimsAll):
        # Delimiters are used in another manner
        regex = '|'.join(delimsAll)
        locationsRaw = [x.strip() for x in list(filter(None, re.split(regex, locationStr)))]
        # Iterate backwards (finding states first)
        i = len(locationsRaw) - 1
        while i >= 0:
            # Is the item just a ZIP code?
            if len(locationsRaw[i]) == 5 and re.match('^[0-9]*$', locationsRaw[i]):
                # Add the ZIP code as a location
                locations.append([locationsRaw[i]])
                i -= 1
                continue
            # Is the item just a state (and not the first item)?
            state = getState(locationsRaw[i])
            if state and i > 0:
                # The prior item must be the city
                city = locationsRaw[i-1]
                locations.append([city, state])
                i = i - 2
                continue
            locationWords = locationsRaw[i].split()
            # Do the last two words form a state?
            if len(locationWords) > 2:
                state = getState(' '.join(locationWords[-2:]))
                if state:
                    # The previous words must be the city
                    city = ' '.join(locationWords[:-2])
                    locations.append([city, state])
                    i -= 1
                    continue
            # Is the last word a state?
            state = getState(locationWords[-1])
            if state:
                # The previous words must be the city
                city = ' '.join(locationWords[:-1])
                locations.append([city, state])
                i -= 1
                continue
            # Assume that only the city name is provided (use the default state)
            state = stateDefault
            city = locationsRaw[i]
            locations.append([city, state])
            i -= 1
            continue
    else:
        # No known delimiters are used
        locationsRaw = locationStr.split()
        lastState = None
        lastStateIndex = None
        # Iterate backwards (finding states first)
        i = len(locationsRaw) - 1
        while i >= 0:
            # Is the word a ZIP code (and not immediately before a state)?
            if len(locationsRaw[i]) == 5 and re.match('^[0-9]*$', locationsRaw[i]) and (lastState is None or lastStateIndex - i > 1):
                # Set location if this is not the last word
                if i < len(locationsRaw) - 1 and ((lastState is None and lastStateIndex is None) or (lastStateIndex is not None and lastStateIndex - i > 1)):
                    # If no state has been found yet
                    if lastState is None:
                            if lastStateIndex is None:
                                lastStateIndex = len(locationsRaw)
                            lastState = stateDefault
                    lastCity = ' '.join(locationsRaw[i+1:lastStateIndex])
                    locations.append([lastCity, lastState])
                # Add the ZIP code as a location
                locations.append([locationsRaw[i]])
                lastStateIndex = i
                lastState = None
                i -= 1
                continue
            # Do the last two words form a state (and not the first item or immediately before another state)?
            if i > 1 and ((lastState is None and lastStateIndex is None) or (lastStateIndex is not None and lastStateIndex - i > 1)):
                state = getState(' '.join(locationsRaw[i-1:i+1]))
                if state:
                    # Set location if this is not the last word
                    if i < len(locationsRaw) - 1:
                        # If no state has been found yet
                        if lastState is None:
                            if lastStateIndex is None:
                                lastStateIndex = len(locationsRaw)
                            lastState = stateDefault
                        lastCity = ' '.join(locationsRaw[i+1:lastStateIndex])
                        locations.append([lastCity, lastState])
                    # One or more prior words must be the city
                    lastStateIndex = i - 1
                    lastState = state
                    i = i - 2
                    continue
            # Is the word a state (and not the first item or immediately before another state)?
            if i > 0 and ((lastState is None and lastStateIndex is None) or (lastStateIndex is not None and lastStateIndex - i > 1)):
                state = getState(locationsRaw[i])
                if state:
                    # Set location if this is not the last word
                    if i < len(locationsRaw) - 1:
                        # If no state has been found yet
                        if lastState is None:
                            if lastStateIndex is None:
                                lastStateIndex = len(locationsRaw)
                            lastState = stateDefault
                        lastCity = ' '.join(locationsRaw[i+1:lastStateIndex])
                        locations.append([lastCity, lastState])
                    # One or more prior words must be the city
                    lastStateIndex = i
                    lastState = state
                    i -= 1
                    continue
            # Is this the first word?
            if i == 0:
                # If no state has been found yet
                if lastState is None:
                    if lastStateIndex is None:
                        lastStateIndex = len(locationsRaw)
                    lastState = stateDefault
                city = ' '.join(locationsRaw[i:lastStateIndex])
                locations.append([city, lastState])
                i -= 1
                continue
            i -= 1
            continue
    # locations should be a list filled with [City, State] or [ZIP]
    # Correct list order
    locations.reverse()
    
    # Locations parsed correctly
    await lrbot.response.reactToMessage(message, 'success')
    
    async with message.channel.typing():
        # Get gas prices lists
        requestURL = 'https://www.gasbuddy.com/graphql'
        requestOperationName = 'LocationBySearchTerm'
        requestQuery = '''query LocationBySearchTerm($brandId: Int, $cursor: String, $fuel: Int, $lat: Float, $lng: Float, $maxAge: Int, $search: String) {
            locationBySearchTerm(lat: $lat, lng: $lng, search: $search) {
                countryCode
                displayName
                latitude
                longitude
                regionCode
                stations(brandId: $brandId, cursor: $cursor, fuel: $fuel, maxAge: $maxAge) {
                    count
                    cursor {
                        next
                        __typename
                    }
                    results {
                        address {
                            country
                            line1
                            line2
                            locality
                            postalCode
                            region
                            __typename
                        }
                        name
                        prices {
                            cash {
                                nickname
                                posted_time
                                price
                                __typename
                            }
                            credit {
                                nickname
                                posted_time
                                price
                                __typename
                            }
                            discount
                            fuel_product
                            __typename
                        }
                        priceUnit
                        ratings_count
                        star_rating
                        __typename
                    }
                    __typename
                }
            }
        }'''
        requestHeaders = {
            'cache-control': 'no-cache',
            'origin': 'https://www.gasbuddy.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        }
        
        gasLocations = []
        gasStationsStrict = []
        gasStationsNearby = []
        
        locationRequests = []
        # Ensure that strict and nearby results are both found
        for location in locations:
            # Only works for city + state (not ZIP codes)
            if len(location) == 2:
                locationRequests.append({
                    'str':      ', '.join(location),
                    'strict':   True,
                    'zip':      False,
                    })
                locationRequests.append({
                    'str':      ' '.join(location),
                    'strict':   False,
                    'zip':      False,
                    })
            elif len(location) == 1:
                locationRequests.append({
                    'str':      location[0],
                    'strict':   False,
                    'zip':      True,
                    })
        
        for locationRequest in locationRequests:
            locationStr = locationRequest['str']
            isStrict = locationRequest['strict']
            isZIP = locationRequest['zip']
            requestVariables = {
                'fuel':     gasType,
                'maxAge':   0,
                'search':   locationStr,
            }
            requestData = {
                'operationName':    requestOperationName,
                'variables':        requestVariables,
                'query':            requestQuery,
            }
                    
            request = requests.post(url = requestURL, json = requestData, headers = requestHeaders)
            gasData = request.json()['data']['locationBySearchTerm']
            
            if isStrict or isZIP:
                gasLocations.append(gasData['displayName'])
            
            for gasStation in gasData['stations']['results']:
                # Format station address
                address = gasStation['address']['line1']
                # Correct street address for all-caps (unless it contains numbers, like a state highway)
                if address.upper() == address and not any(c.isdigit() for c in address.split(None, 1)[1]):
                    address = string.capwords(address)
                if gasStation['address']['line2']:
                    address += ', ' + gasStation['address']['line2']
                address += ', ' + gasStation['address']['locality'] + ', ' + gasStation['address']['region']
                # Remove last 4 from ZIP code, if provided
                address += ' ' + gasStation['address']['postalCode'].split('-',1)[0]
                
                name = gasStation['name']
                
                price = float()
                for gasPrice in gasStation['prices']:
                    if gasPrice['fuel_product'] == gasTypeProducts[gasType]:
                        if gasPrice['credit']:
                            price = gasPrice['credit']['price']
                            break
                        elif gasPrice['cash']:
                            price = gasPrice['cash']['price']
                            break
                if not price:
                    # No price found (ignore station)
                    continue
                
                unit = gasStation['priceUnit']
                
                rating = gasStation['star_rating']
                
                details = {
                    'name': name,
                    'address': address,
                    'price': price,
                    'unit': unit,
                    'rating': rating,
                }
                
                # Add station to the full list of stations
                if isStrict or (isZIP and locationStr in gasStation['address']['postalCode']):
                    gasStationsStrict.append(details)
                else:
                    gasStationsNearby.append(details)
        
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

async def run(message: discord.Message) -> None:
    try:
        await main(message)
    except:
        await lrbot.response.reactToMessage(message, '💣')
    return