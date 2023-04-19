import re

delimsPrimary = [';', '&', 'and']
delimsSecondary = [',']
delimsAll = delimsPrimary + delimsSecondary

# stateDefault will be set on first run (cannot run coroutine prior)
stateDefault = None
stateDefaultStr = 'Illinois'

f = open(r'resources/state-abbreviations', 'r')
states = [state.lower().strip().split(',') for state in f.readlines()]
f.close()

async def getState(query: str) -> str:
    '''
    Returns the initials of the state that the provided string refers to.
    '''
    query = query.lower()
    for state in states:
        if query in state:
            return state[0]
    return ''

async def isZipCode(query: str) -> bool:
    '''
    Tests whether the provided string is a valid US ZIP code.
    '''
    return len(query) == 5 and re.match('^[0-9]*$', query)

async def parseLocationStr(locationStr: str) -> list[list[str]]:
    '''
    Parses a string containing a list of cities, states, and ZIP codes.
    Returns a list of locations ([city, state] or [ZIP code]) as interpreted, or an empty list on error.
    '''
    # Set default state on first run
    global stateDefault
    if stateDefault is None:
        stateDefault = await getState(stateDefaultStr)
    
    locations = []

    # Check for delimiters
    if (
        any(delim in locationStr for delim in delimsPrimary) and
        any(delim in locationStr for delim in delimsSecondary)
    ):
        # Both primary and secondary delimiters are used (most explicit)
        locations = await parseLocationStrMixed(locationStr)
    elif any(delim in locationStr for delim in delimsAll):
        # Only a single type of delimiter is used
        locations = await parseLocationStrSingle(locationStr)
    else:
        # No known delimiters are used
        locations = await parseLocationStrNone(locationStr)
    
    # locations should be a list filled with [City, State] or [ZIP]
    return locations

async def parseLocationStrMixed(locationStr: str) -> list[list[str]]:
    '''
    Parses a string containing a list of cities, states, and ZIP codes, using both primary and secondary delimiters.
    Returns a list of locations ([city, state] or [ZIP code]) as interpreted, or an empty list on error.
    '''
    locations = []
    # Split by any primary delimiter
    regex = '|'.join(delimsPrimary)
    locationsRaw = [x.strip() for x in list(filter(None, re.split(regex, locationStr)))]
    # Split each location by any secondary delimiter
    for location in locationsRaw:
        regex = '|'.join(delimsSecondary)
        location = [x.strip() for x in list(filter(None, re.split(regex, location)))]
        # location should be [City, State]
        if len(location) == 2:
            locationState = await getState(location[1])
            if locationState:
                # The last item must be a valid state
                locations.append([location[0], locationState])
        elif len(location) == 1:
            # Is the item not just a ZIP code? (missing a delimiter, or just without a state?)
            if not await isZipCode(location[0]):
                locations += await parseLocationStrNone(location[0])

    return locations

async def parseLocationStrSingle(locationStr: str) -> list[list[str]]:
    '''
    Parses a string containing a list of cities, states, and ZIP codes, using only one type of delimiter.
    Returns a list of locations ([city, state] or [ZIP code]) as interpreted, or an empty list on error.
    '''
    locations = []
    regex = '|'.join(delimsAll)
    locationsRaw = [x.strip() for x in list(filter(None, re.split(regex, locationStr)))]
    # Iterate backwards (finding states first)
    i = len(locationsRaw) - 1
    while i >= 0:
        # Is the item just a ZIP code?
        if await isZipCode(locationsRaw[i]):
            # Add the ZIP code as a location
            locations.append([locationsRaw[i]])
            i -= 1
            continue
        # Is the item just a state (and not the first item)?
        state = await getState(locationsRaw[i])
        if state and i > 0:
            # The prior item must be the city
            city = locationsRaw[i-1]
            locations.append([city, state])
            i = i - 2
            continue
        locationWords = locationsRaw[i].split()
        # Do the last two words form a state?
        if len(locationWords) > 2:
            state = await getState(' '.join(locationWords[-2:]))
            if state:
                # The previous words must be the city
                city = ' '.join(locationWords[:-2])
                locations.append([city, state])
                i -= 1
                continue
        # Is the last word a state?
        state = await getState(locationWords[-1])
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

    # Correct list order
    locations.reverse()

    return locations

async def parseLocationStrNone(locationStr: str) -> list[list[str]]:
    '''
    Parses a string containing a list of cities, states, and ZIP codes without delimiters.
    Returns a list of locations ([city, state] or [ZIP code]) as interpreted, or an empty list on error.
    '''
    locations = []
    locationsRaw = locationStr.split()
    lastState = None
    lastStateIndex = None
    # Iterate backwards (finding states first)
    i = len(locationsRaw) - 1
    while i >= 0:
        # Is the word not immediately before a state (but not a ZIP code)?
        if lastState is None or lastStateIndex - i > 1:
            # Is the word a ZIP code?
            if await isZipCode(locationsRaw[i]):
                # Set previously-found location if this is neither the last word nor immediately before a ZIP code
                if (
                    i < len(locationsRaw) - 1 and
                    not (lastStateIndex is not None and lastStateIndex - i <= 1)
                ):
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
            # Do the last two words form a state?
            if i > 1:
                state = await getState(' '.join(locationsRaw[i-1:i+1]))
                if state:
                    # Set previously-found location if this is neither the last word nor immediately before a ZIP code
                    if (
                        i < len(locationsRaw) - 1 and
                        not (lastStateIndex is not None and lastStateIndex - i <= 1)
                    ):
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
            # Is the word a state (and not the first item)?
            if i > 0:
                state = await getState(locationsRaw[i])
                if state:
                    # Set previously-found location if this is neither the last word nor immediately before a ZIP code
                    if (
                        i < len(locationsRaw) - 1 and
                        not (lastStateIndex is not None and lastStateIndex - i <= 1)
                    ):
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
    
    # Correct list order
    locations.reverse()

    return locations