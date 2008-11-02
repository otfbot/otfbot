import sys, glob
sys.path.insert(1, "services")
sys.path.insert(1, "../services")
import configService

config=configService.configService("otfbot.yaml")

files=glob.glob("plugins/ircClient/*.py")
modules=[]
for file in files:
	plugin=file.split("plugins/irciClient/")[1].split(".py")[0]
	if not plugin=="__init__":
		modules.append(plugin)
config.set("ircClientPluginsEnabled", modules, 'main')

files=glob.glob("plugins/ircServer/*.py")
modules=[]
for file in files:
	plugin=file.split("plugins/ircServer/")[1].split(".py")[0]
	if not plugin=="__init__":
		modules.append(plugin)
config.set("ircServerPluginsEnabled", modules, 'main')

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
