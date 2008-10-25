import sys, glob
from lib import config

config=config.config("otfbot.yaml")

files=glob.glob("plugins/ircClient/*.py")
modules=[]
for file in files:
	modules.append(file.split("plugins/ircClient/")[1].split(".py")[0])
config.set("ircClientPluginsEnabled", modules, 'main')
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
