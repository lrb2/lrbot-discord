import configparser

config = configparser.RawConfigParser()
config.read('config/settings.cfg')

settings = config['Common']
crop = config['Crop']
latex = config['LaTeX']
gas = config['Gas']
location = config['Location']