import aiohttp
import asyncio
import string

gasTypeProducts = {
    1:  'regular_gas',
    2:  'midgrade_gas',
    3:  'premium_gas',
    4:  'diesel',
    5:  'e85',
    12: 'e15',
}

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

async def getStations(locations: list[list[str]], gasType: int, strict: bool = True) -> dict[str, list[dict[str]]]:
    '''
    Gets a list of gas stations with prices from a list of locations ([City, ST] or [ZIP]) and gas type.
    Strict mode will only return results within the specified location; otherwise, nearby stations will be included.
    '''
    
    gasLocations = []
    gasStations = []
    
    locationRequests = []
    
    # Ensure that strict and nearby results are both found
    for location in locations:
        # Only works for city + state (not ZIP codes)
        if len(location) == 2:
            if strict:
                locationRequests.append({
                    'str':      ', '.join(location),
                    'strict':   True,
                    'zip':      False,
                    })
            else:
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
    
    gasDatas = []
    
    async with aiohttp.ClientSession(headers = requestHeaders) as session:
        for locationRequest in locationRequests:           
            gasDatas.append(await getData(locationRequest['str'], gasType, session))
            cursor = int(gasDatas[-1]['stations']['cursor']['next'])
            if int(gasDatas[-1]['stations']['count']) > cursor + 1:
                # Get another set of data
                gasDatas.append(await getData(locationRequest['str'], gasType, session, cursor))
            
            if locationRequest['strict'] or locationRequest['zip']:
                gasLocations.append(gasDatas[0]['displayName'])
            
            for gasData in gasDatas:
                for gasStation in gasData['stations']['results']:
                    # Format station address
                    address = await correctCaps(gasStation['address']['line1'])
                    if gasStation['address']['line2']:
                        address += ', ' + gasStation['address']['line2']
                    address += ', ' + (await correctCaps(gasStation['address']['locality']))
                    address += ', ' + gasStation['address']['region']
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
                    gasStations.append(details)
    
    return gasStations, gasLocations

async def getData(query: str, gasType: int, session: aiohttp.ClientSession, startFrom: int = None) -> dict:
    '''
    Search GasBuddy with the specified location string and gas type.
    '''
    requestVariables = {
        'fuel':     gasType,
        'maxAge':   0,
        'search':   query,
    }
    requestData = {
        'operationName':    requestOperationName,
        'variables':        requestVariables,
        'query':            requestQuery,
    }
    if startFrom:
        requestVariables['cursor'] = str(startFrom)
    
    request = await session.post(requestURL, json = requestData)
    data = await request.json()
    
    return data['data']['locationBySearchTerm']

async def correctCaps(str: str) -> str:
    '''
    Corrects strings that are all upper- or lowercase and shouldn't be.
    Does not correct strings containing numbers (like a state highway).
    '''
    if str.lower() == str or (
        str.upper() == str and
        not any(c.isdigit() for c in str.split(None, 1)[1])
    ):
        str = string.capwords(str)
    return str