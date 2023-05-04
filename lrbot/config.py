import configparser

config = configparser.RawConfigParser()
config.read('config/settings.cfg')

settings = config['Common']
location = config['Location']