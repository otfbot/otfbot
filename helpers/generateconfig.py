#!/usr/bin/python
import sys, glob
base="../"
sys.path.insert(1, base+"services")
import config as configService

config=configService.configService(base+"otfbot.yaml")

files=glob.glob(base+"plugins/ircClient/*.py")
modules=[]
for file in files:
    plugin=file.split(base+"plugins/ircClient/")[1].split(".py")[0]
    if not plugin=="__init__":
        modules.append(plugin)
config.set("ircClientPlugins", modules, 'main')

files=glob.glob(base+"plugins/ircServer/*.py")
modules=[]
for file in files:
    plugin=file.split(base+"plugins/ircServer/")[1].split(".py")[0]
    if not plugin=="__init__":
        modules.append(plugin)
config.set("ircServerPlugins", modules, 'main')

files=glob.glob(base+"services/*.py")
modules=[]
for file in files:
    plugin=file.split(base+"services/")[1].split(".py")[0]
    if not plugin=="__init__" and not plugin=="config":
        modules.append(plugin)
config.set("services", modules, 'main')

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
