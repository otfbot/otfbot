from lib import config
import sys, glob

config=config.config("otfbot.yaml")

files=glob.glob("modules/ircClient/*.py")
modules=[]
for file in files:
	modules.append(file.split("modules/ircClient/")[1].split(".py")[0])
config.set("modsEnabled", modules, 'main')
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
