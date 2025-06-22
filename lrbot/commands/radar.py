import asyncio
import discord
import logging
import lrbot.config
import lrbot.exceptions
import lrbot.response
import os
from discord.ext import commands
from lrbot.filemgr import FileManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import MaxRetryError

# Set Chrome options
chromeOptions = webdriver.ChromeOptions()
chromeOptions.add_argument('--window-size=640,536') # 480p + 56 px NWS header
chromeOptions.add_argument('--headless')
chromeOptions.add_argument('--no-sandbox')
chromeOptions.add_argument('--disable-dev-shm-usage')
chromeOptions.add_argument('--disable-gpu')

@commands.command(name = 'radar')
async def main(
    ctx: commands.Context,
    *,
    arg: str = None
) -> None:
    message = ctx.message
    
    fm = FileManager(message.id)
    imgFolder = fm.getFolder()
    
    locationStr = None
    createGif = True
    if arg:
        args = arg.lower().split(None, 1)
        if args[0] == 'static':
            createGif = False
            if len(args) > 1:
                locationStr = args[1]
        else:
            locationStr = arg
            
    # Create Chrome webdriver
    chromeDriver = webdriver.Chrome(options=chromeOptions)
    
    # Set to the system timezone
    tz = 'UTC'
    try:
        with open('/etc/timezone', 'r') as timezone:
            systemTZ = timezone.read().strip()
            tzParams = {'timezoneId': systemTZ}
            chromeDriver.execute_cdp_cmd('Emulation.setTimezoneOverride', tzParams)
            tz = systemTZ
    except:
        logger = logging.getLogger('discord.lrbot-radar')
        logger.info(f'Unable to set Chrome webdriver timezone')
    
    await lrbot.response.reactToMessage(message, 'ok')
    
    if locationStr:
        # Go to National Weather Service Radar page, with Hazards set to 50% transparency and National Radar set to 100% opacity
        chromeDriver.get('https://radar.weather.gov/?settings=v1_eyJhZ2VuZGEiOnsiaWQiOiJ3ZWF0aGVyIiwiY2VudGVyIjpbLTk1LDM3XSwibG9jYXRpb24iOm51bGwsInpvb20iOjMsImxheWVyIjoiYnJlZl9xY2QifSwiYW5pbWF0aW5nIjpmYWxzZSwiYmFzZSI6InN0YW5kYXJkIiwiYXJ0Y2MiOmZhbHNlLCJjb3VudHkiOmZhbHNlLCJjd2EiOmZhbHNlLCJyZmMiOmZhbHNlLCJzdGF0ZSI6ZmFsc2UsIm1lbnUiOnRydWUsInNob3J0RnVzZWRPbmx5IjpmYWxzZSwib3BhY2l0eSI6eyJhbGVydHMiOjAuNSwibG9jYWwiOjAuNiwibG9jYWxTdGF0aW9ucyI6MC44LCJuYXRpb25hbCI6MX19')
    else:
        # Go to National Weather Service Radar page, showing National radar
        chromeDriver.get('https://radar.weather.gov/?settings=v1_eyJhZ2VuZGEiOnsiaWQiOiJuYXRpb25hbCIsImNlbnRlciI6Wy05NSwzN10sImxvY2F0aW9uIjpudWxsLCJ6b29tIjozLCJsYXllciI6ImJyZWZfcWNkIn0sImFuaW1hdGluZyI6ZmFsc2UsImJhc2UiOiJzdGFuZGFyZCIsImFydGNjIjpmYWxzZSwiY291bnR5IjpmYWxzZSwiY3dhIjpmYWxzZSwicmZjIjpmYWxzZSwic3RhdGUiOmZhbHNlLCJtZW51Ijp0cnVlLCJzaG9ydEZ1c2VkT25seSI6dHJ1ZSwib3BhY2l0eSI6eyJhbGVydHMiOjAuNSwibG9jYWwiOjAuNiwibG9jYWxTdGF0aW9ucyI6MC44LCJuYXRpb25hbCI6MX19')
    
    async with message.channel.typing():
        WebDriverWait(chromeDriver, timeout=10).until(
            lambda driver: driver.find_element(By.CLASS_NAME, 'search-container')
        )
        
        if locationStr:
            # Open the search box
            chromeDriver.find_element(By.CLASS_NAME, 'search-icon').click()
            # Find the search input
            searchInputElement = chromeDriver.find_element(By.CLASS_NAME, 'search-input')
            # Activate the search input
            #searchInputElement.click()
            # Enter the search term
            searchInputElement.send_keys(locationStr)
            # Wait a moment
            await asyncio.sleep(0.5)
            # Wait for a search result to be shown
            searchResultElement = WebDriverWait(chromeDriver, timeout=20).until(
                lambda driver: driver.find_element(By.XPATH, '(//div[contains(@class, "search-option-result")]/div[contains(@class, "search-option-label")])[1]')
                #lambda driver: driver.find_element(By.XPATH, '(//div[@class="cmi-radar-menu-panel-content"]/div[contains(@class, "search-option-result")]/div[contains(@class, "search-option-label")])[1]')
            )
            # Choose the first result
            searchResultElement.click()
        # Open the view settings
        #chromeDriver.find_element(By.XPATH, '//span[@class="cmi-radar-menu-agenda-bar-actions-item-icon"]').click()
        # Show alerts if static image
        #if locationStr and not createGif:
            # Wait for the Alerts button to become visible
            #WebDriverWait(chromeDriver, timeout=10).until(
            #    lambda driver: driver.find_element(By.XPATH, '(//span[@class="cmi-radar-menu-agenda-bar-actions-item-label"])[2]')
            #)
            # Expand Alerts
            #chromeDriver.find_element(By.XPATH, '(//span[@class="cmi-radar-menu-agenda-bar-actions-item-label"])[2]').click()
        # Wait a second for the zoom to settle in
        await asyncio.sleep(1.5)
        # Zoom in two times to the location
        if locationStr:
            zoomInElement = chromeDriver.find_element(By.CLASS_NAME, 'button-zoomin')
            for i in range(2):
                zoomInElement.click()
        
        # Find the step forward button
        stepForwardButton = chromeDriver.find_element(By.CLASS_NAME, 'button-stepfwd')
        # Get the 20 frames of radar
        for i in range(20):
            # Wait for the radar to load (hopefully)
            await asyncio.sleep(1)
            # Get the image path
            imgPath = os.path.join(os.sep, imgFolder, f'radar{str(i).zfill(2)}.png')
            # Save the screenshot
            chromeDriver.save_screenshot(imgPath)
            # Go to the next frame
            stepForwardButton.click()
            # Chop the screenshot here to give the radar more time to load
            magick = [
                'magick',
                imgPath,
                '-gravity', 'North',
                '-chop', '0x56',
                imgPath
            ]
            await asyncio.wait_for((await asyncio.create_subprocess_exec(*magick)).wait(), 300)
            # Stop here if not creating a GIF
            if not createGif:
                break
        
        finalURL = chromeDriver.current_url
        
        chromeDriver.quit()
        
        primaryImgPath = os.path.join(os.sep, imgFolder, 'radar00.png')
        sourceImgsPath = os.path.join(os.sep, imgFolder, 'radar*.png')
        colorPalettePath = os.path.join(os.sep, imgFolder, 'palette.gif')
        
        if createGif:
            # Generate a common color palette
            # (Fixes obvious changes in bottom gradient bar)
            magick = [
                'magick', 'convert',
                sourceImgsPath,
                '+append',
                '-colors', '256',
                '-unique-colors',
                colorPalettePath
            ]        
            await asyncio.wait_for((await asyncio.create_subprocess_exec(*magick)).wait(), 300)
            # Use ImageMagick to create a combined GIF
            magick = [
                'magick', 'convert',
                '-layers', 'OptimizePlus',
                '-delay', '25',
                sourceImgsPath,
                primaryImgPath,
                '-remap', colorPalettePath,
                '-loop', '0',
                os.path.join(os.sep, fm.getOutputFolder(), 'radar.gif')
            ]        
            await asyncio.wait_for((await asyncio.create_subprocess_exec(*magick)).wait(), 300)
        
        embedTitle = 'National Weather Service Radar'
        embedColor = discord.Color.from_str('#0099d8')
        radarEmbed = discord.Embed(
            title = embedTitle,
            url = finalURL,
            color = embedColor
        )
        radarEmbed.set_image(url = 'attachment://radar.gif' if createGif else 'attachment://radar0.png' )
        radarEmbed.set_footer(text = f'Time zone is {tz}')
        
        await lrbot.response.sendResponse(
            message.channel,
            files = [discord.File(fm.getFilePath('radar.gif', output = True) if createGif else primaryImgPath)],
            embeds = [radarEmbed],
            reference = message
        )
    
    # Delete the folder
    fm.clean()
    
    return

@main.error
async def on_error(ctx: commands.Context, error: commands.CommandError) -> None:
    try:
        # Try to clean up any created files
        FileManager(ctx.message.id, reinit=True).clean()
    except Exception as error:
        if not isinstance(error, FileNotFoundError):
            logger = logging.getLogger('discord.lrbot-radar')
            logger.warning(f'Working folder for {ctx.message.id} was not successfully cleaned after error')

async def setup(bot: commands.Bot) -> None:
    bot.add_command(main)