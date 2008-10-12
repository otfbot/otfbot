from lib import config
import sys

config=config.config("otfbot.yaml")

#TODO: generate list with all modules as modsEnabled
sys.stdout.write("Network Name: ")
name=raw_input().strip()
config.set('enabled', True, 'main', name)
sys.stdout.write("Server hostname: ")
config.set('server', raw_input().strip(), 'main', name)
sys.stdout.write("First Channel: ")
config.set('enabled', True, 'main', name, raw_input().strip())
sys.stdout.write("Nickname: ")
config.set('nickname', raw_input().strip(), 'main')
config.set('encoding', 'UTF-8', 'main')
config.writeConfig()
